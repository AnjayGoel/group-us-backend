import dataclasses
import secrets
import shutil
from datetime import datetime
from time import time

from group_us import *
from group_us.algorithm import *
from group_us.email_utils import BASE_URL, EmailProducer


# from flask_mongoengine import MongoEngine as me


def get_rand():
    return secrets.token_urlsafe(16)


class Person(me.EmbeddedDocument):
    name = me.StringField()
    email = me.StringField()
    index = me.IntField()
    secret = me.StringField(default=get_rand)


class Project(me.Document):
    uid = me.StringField(unique=True, default=get_rand)
    deadline = me.IntField(default=lambda: int(time()) + 7 * 24 * 60 * 60)
    num_member = me.IntField(default=0)
    finished = me.BooleanField(default=False)
    title = me.StringField(default="No Title")
    grp_size = me.IntField(default=4)
    owner = me.EmbeddedDocumentField(Person)
    members = me.EmbeddedDocumentListField(Person)
    preferences = me.ListField(me.ListField(me.IntField()))
    final_groups = me.ListField(me.ListField(Person))

    def is_complete(self) -> bool:
        return np.count_nonzero(np.array(self.preferences) == -1) == 0

    def has_deadline_passed(self) -> bool:
        return time() > self.deadline

    def has_secret(self, secret: str):
        has = False
        name = ""
        for member in self.members:
            if member.secret == secret:
                has = True
                name = member.name
                break
        return has, name

    def get_names(self):
        lst = []
        for i, mem in enumerate(self.members):
            lst.append(mem.name)
        return lst

    def get_index_from_secret(self, secret: str) -> int:
        for member in self.members:
            if member.secret == secret:
                return member.index
        return -1

    def send_init_mails(self):
        logger.debug("Sending Init Emails")
        email_client = EmailProducer.get_instance()
        for i in self.members:
            email_client.produce(recipient=[i.email], subject=f"{self.title} Group Formation Preferences",
                                 body="<br>".join([i.name,
                                                   f"""
                                               Please Fill Out this <a href="{BASE_URL}/fillPreference/{self.uid}/{i.secret}">form</a> for {self.title}. 
                                               Deadline is {datetime.fromtimestamp(self.deadline).strftime(
                                                       "%H:%M %d-%m-%Y")}. Group Size is {self.grp_size}""",
                                                   "Form Created By", self.owner.name]))

        logger.debug("Sent Init Emails")

    def send_final_mail(self):
        logger.debug("Sending Final Mails")
        email_client = EmailProducer.get_instance()
        groups_list = []
        for group in self.final_groups:
            groups_list.append(' '.join([member.name for member in group]))

        for idx, group in enumerate(self.final_groups):
            for member in group:
                email_client.produce(recipient=[member.email], subject=f"Group Allocation for {self.title}",
                                     body="<br>".join([member.name, f"Your Group for {self.title} consists of:",
                                                       groups_list[idx]]))
        email_client.produce(recipient=[self.owner.email], subject=f"Group Allocation for {self.title}",
                             body="<br>".join(
                                 [self.owner.name, f"The Groups For {self.title} are:",
                                  '<br>'.join(groups_list)]))
        logger.debug("Sent Final Emails")
        email_client.close()

    def solve(self):
        logger.debug(f"Solving {self.uid}")
        arr = np.array(self.preferences)
        arr[arr < 0] = 0

        score, groups = Game(
            arr, r=self.grp_size, iter2=2, iter1=2).solve()
        logger.debug(f"{score}----{groups}")
        self.final_groups = []
        for grp in groups:
            temp_grp = []
            for mem_idx in grp:
                temp_grp.append(self.members[mem_idx])
            self.final_groups.append(temp_grp)

        self.send_final_mail()
