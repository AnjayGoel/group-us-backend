import logging
import os
import secrets
import traceback
from datetime import datetime
from time import time

from pymongo import MongoClient

from .tasks import send_email

logger = logging.getLogger(__name__)
BASE_URL = os.getenv('BASE_URL')


def get_default_deadline():
    return int(time()) + 7 * 24 * 60 * 60


def get_rand_string():
    return secrets.token_urlsafe(16)


def deadline_passed(project):
    if project["deadline"] < int(time()):
        return True
    else:
        return False


def modify_preference(project, mem_id, resp_mems):
    pref = [0] * project["num_members"]

    mem_idx = next(
        member["index"] for member in project["members"] if member["uid"] == mem_id)

    for resp_mem in resp_mems:
        obj_idx = next(
            member["index"] for member in project["members"] if member["name"] == resp_mem["name"])
        pref[obj_idx] = resp_mem["score"]

    dct = {"uid": project["uid"], f"preferences.{mem_idx}": pref}
    project["preferences"][mem_idx] = pref
    return dct


def is_complete(project):
    for i in project["preferences"]:
        for j in i:
            if j < 0:
                return False
    return True


def get_vote_list_resp(project, mem_id):
    try:
        resp = {
            "status": 1,
            "message": "success",
            "names": [],
            "project_title": project["project_title"],
            "organizer_name": project["organizer_name"],
            "deadline": project["deadline"],
            "grp_size": project["grp_size"]
        }
        for mem in project["members"]:
            resp["names"].append(mem["name"])
            if mem["uid"] == mem_id:
                resp["name"] = mem["name"]
        return resp
    except:
        traceback.print_exc()
        return {"status": 0, "message": "Some Error"}


def prepare_project_json(project):
    project["num_members"] = len(project["members"])
    project["uid"] = get_rand_string()
    project["finished"] = False
    project["preferences"] = [[-1] * project["num_members"]] * project["num_members"]
    project["final_groups"] = []
    for idx in range(len(project["members"])):
        project["members"][idx]["index"] = idx
        project["members"][idx]["uid"] = get_rand_string()
    return project


def send_init_mail(project):
    for member in project["members"]:
        send_email.delay(
            recipient=[member["email"]],
            subject=f"{project['project_title']} Group Formation Preferences",
            body="<br>".join([member["name"],
                              f"""
                                         Please Fill Out this <a href="{BASE_URL}/fillPreference/{project['uid']}/{member['uid']}">form</a> for {project['project_title']}. 
                                         Deadline is {datetime.fromtimestamp(project['deadline']).strftime(
                                  "%H:%M %d-%m-%Y")}. Group Size is {project['grp_size']}""",
                              "Form Created By", project["organizer_name"]])
        )


class MongoHandler:
    def __init__(self):
        self.client = MongoClient(
            host=f'mongodb+srv://{os.getenv("MONGO_USERNAME")}:{os.getenv("MONGO_PASSWORD")}@{os.getenv("MONGO_HOST")}/{os.getenv("MONGO_DB")}?retryWrites=true&w=majority')
        self.collection = self.client[os.getenv("MONGO_DB")]["projects"]

    def get(self, proj_id, mem_uid):
        return self.collection.find_one({"uid": proj_id, "members.uid": mem_uid})

    def remove(self, obj):
        if self.collection.find({'uid': obj["uid"]}).count():
            self.collection.delete_one({"uid": obj["uid"]})
