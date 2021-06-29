import logging
import os
import smtplib
import time
from email.mime.text import MIMEText

import pymongo.errors as pme
from celery import Task
from pymongo import MongoClient

from api.algorithm import *
from group_us.celery import app

logger = logging.getLogger(__name__)


class email_task(Task):
    _connection = None

    def connect(self):
        self._connection = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=10)
        self._connection.login(
            os.getenv("SRG_EMAIL"),
            os.getenv("SRG_PASSWORD")
        )
        logger.info("SMTP Connected, sleeping for 2 seconds")
        time.sleep(2)

    @property
    def connection(self):
        if self._connection is None:
            self.connect()
        return self._connection


class mongo_task(Task):
    _connection = None
    _collection = None

    def connect(self):
        self._connection = MongoClient(
            host=
            f'mongodb+srv://{os.getenv("MONGO_USERNAME")}:'
            f'{os.getenv("MONGO_PASSWORD")}@{os.getenv("MONGO_HOST")}'
            f'/{os.getenv("MONGO_DB")}?retryWrites=true&w=majority'
        )
        logger.info("Mongo Connected, sleeping for 2 seconds")
        time.sleep(2)

    @property
    def connection(self):
        if self._connection is None:
            self.connect()
        return self._connection

    @property
    def collection(self):
        if self._collection is None:
            self._collection = self.connection[os.getenv("MONGO_DB")]["projects"]
        return self._collection


@app.task(
    base=email_task,
    name='send_email',
    task_acks_late=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3, 'countdown': 5}
)
def send_email(recipient, subject, body):
    try:
        msg = MIMEText(body, 'html')
        msg["From"] = "GroupUs"
        msg["To"] = ", ".join(recipient if isinstance(
            recipient, list) else [recipient])
        msg["Subject"] = subject
        send_email.connection.sendmail(msg["From"], msg["To"], msg.as_string())
    except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected) as err:
        send_email.connect()
        raise err


@app.task(
    base=mongo_task,
    name='insert_or_update',
    task_acks_late=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3, 'countdown': 5}
)
def insert_or_update_project(obj):
    insert_or_update_project.collection.update({"uid": obj["uid"]}, {"$set": obj}, upsert=True)


@app.task(
    base=mongo_task,
    name="check_deadline",
)
def check_deadline():
    try:
        uids = check_deadline.collection.find({"finished": False, "deadline": {"$lt": int(time.time())}})
    except (pme.ConnectionFailure, pme.AutoReconnect) as err:
        check_deadline.connect()
        raise err
    for obj in uids:
        solve_and_mail_results.delay(obj["uid"])


@app.task(
    base=mongo_task,
    name='solve_and_send',
    task_acks_late=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3, 'countdown': 5}
)
def solve_and_mail_results(uid):
    try:
        project = solve_and_mail_results.collection.find_one({"uid": uid})
    except (pme.ConnectionFailure, pme.AutoReconnect) as err:
        check_deadline.connect()
        raise err

    if project is None:
        return

    logger.debug(f"Solving {uid}")
    arr = np.array(project["preferences"])
    arr[arr < 0] = 0
    score, groups = Matching(
        arr,
        group_size=project["grp_size"],
        iter_count=2,
        final_iter_count=2
    ).solve()
    final_groups = []
    for grp in groups:
        temp_grp = []
        for mem_idx in grp:
            temp_grp.append(next(member for member in project["members"] if member["index"] == mem_idx))
        final_groups.append(temp_grp)

    groups_list = []
    for group in final_groups:
        groups_list.append(', '.join([member["name"] for member in group]))

    for idx, group in enumerate(final_groups):
        for member in group:
            send_email.delay(
                recipient=[member["email"]],
                subject=f"Group Allocation for {project['project_title']}",
                body="<br>".join([member['name'], f"Your Group for {project['project_title']} consists of:",
                                  groups_list[idx]])
            )
    send_email.delay(
        recipient=[project['organizer_email']],
        subject=f"Group Allocation for {project['project_title']}",
        body="<br>".join([project['organizer_name'], f"The Groups For {project['project_title']} are:",
                          '<br>'.join(groups_list)])
    )

    status_modifications = {"uid": project["uid"], "finished": True}
    insert_or_update_project.delay(status_modifications)

    logger.debug("Sent Final Emails")
