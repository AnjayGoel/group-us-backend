import email
import time
import numpy as np
import secrets
from dataclasses import dataclass
import dataclasses
from typing import *
from os import makedirs, path
import json
from email.mime.text import MIMEText
import shutil

from datetime import datetime
from group_us import *
from group_us.utils import BASE_URL, EmailClient
from group_us.algorithm import *


@dataclass
class person:
    name: str
    email: str
    secret: str

    def __init__(self, name: str, email: str, secret: str = None):
        self.name = name
        self.email = email
        if (secret is not None):
            self.secret = secret
        else:
            self.secret = secrets.token_urlsafe(16)

        super().__init__()


@dataclass
class matching:
    id: str
    deadline: float = time.time() + 7 * 24 * 60 * 60
    nums: int = 0
    title: str = None
    grpSize: int = 4
    owner: person = None
    members: List[person] = None
    preferences: List[List[int]] = None
    finalGrps: List[List[members]] = None

    def __init__(self, deadline: float = - 1, owner: person = None, title: str = "", members: List[person] = None, id: str = None, nums=None, preferences=None, grpSize: int = None, finalGrps: List[List[members]] = None):
        self.owner = owner
        self.members = members
        if (deadline > 0):
            self.deadline = deadline
        else:
            self.deadline = time.time() + 2*24*60*60

        if (preferences != None):
            self.preferences = preferences
        else:
            self.preferences = [[-1]*len(members)]*len(members)
        if nums != None:
            self.nums = nums
        else:
            self.nums = len(members)

        if grpSize != None:
            self.grpSize = grpSize
        else:
            self.grpSize = 4

        if title != None:
            self.title = title
        else:
            self.grpSize = "None"

        if finalGrps != None:
            self.finalGrps = finalGrps
        else:
            self.finalGrps = []

        if id != None:
            self.id = id
        else:
            self.id = secrets.token_urlsafe(16)

        super().__init__()

    def getDict(self):
        return dataclasses.asdict(self)

    @classmethod
    def getFromFile(cls, id: str):
        if (os.path.exists(os.path.join(dataDir, f"{id}.json"))):
            f = open(os.path.join(dataDir, f"{id}.json"), "r")
            obj = json.load(f)
            f.close()
            x = cls(**obj)
            x.owner = person(**obj["owner"])
            x.members = []
            for i in obj["members"]:
                x.members.append(person(**i))

            return x
        else:
            return None

    @classmethod
    def saveToFile(cls, obj):
        if not os.path.exists(dataDir):
            os.makedirs(dataDir)

        f = open(os.path.join(dataDir, f"{obj.id}.json"), "w")
        logger.debug(f.name)
        json.dump(dataclasses.asdict(obj), f, indent=2)
        f.close()

    def isComplete(self) -> bool:
        return np.count_nonzero(np.array(self.preferences) == -1) == 0

    def hasDeadlinePassed(self) -> bool:
        return time.time() > self.deadline

    def hasSecret(self, secret: str):
        has = False
        name = ""
        for i in self.members:
            if (i.secret == secret):
                has = True
                name = i.name
                break
        return has, name

    def getNames(self):
        lst = []
        for i, mem in enumerate(self.members):
            lst.append(mem.name)
        return lst

    def getIndexFromSecret(self, secret: str) -> int:
        ind = -1
        for i in range(len(self.members)):
            if (self.members[i].secret == secret):
                ind = i
                break
        return ind

    def sendInitMails(self):
        logger.debug("Sending Init Emails")
        email = EmailClient()
        for i in self.members:
            email.send_email(recipient=[i.email], subject=f"{self.title} Group Formation Preferences",
                             body="<br>".join([i.name, f"""Please Fill Out this <a href="{BASE_URL}/fillPreference/{self.id}/{i.secret}">form</a> for {self.title}. Deadline is {datetime.fromtimestamp(self.deadline).strftime("%H:%M %d-%m-%Y")}. Group Size is {self.grpSize}""", "Form Created By", self.owner.name]))

        logger.debug("Sent Init Emails")
        email.close()

    def sendFinalMail(self):
        logger.debug("Sending Final Mails")
        email = EmailClient()
        finalMembersAll = []
        for i in self.finalGrps:
            finalMembersAll.append(' '.join([x.name for x in i]))
        for i, grp in enumerate(self.finalGrps):
            for j in grp:
                email.send_email(recipient=[j.email], subject=f"Group Allocation for {self.title}",
                                 body="<br>".join([j.name, f"Your Group for {self.title} consits of:", finalMembersAll[i]]))
        email.send_email(recipient=[self.owner.email], subject=f"Group Allocation for {self.title}", body="<br>".join(
            [self.owner.name, f"The Groups For {self.title} are:", '<br>'.join(finalMembersAll)]))
        logger.debug("Sent Final Emails")
        email.close()

    def solve(self):
        logger.debug(f"Solving {self.id}")
        arr = np.array(self.preferences)
        arr[arr < 0] = 0

        score, grps = Game(
            arr, r=self.grpSize, iter2=2, iter1=2).solve()
        logger.debug(f"{score}----{grps}")
        self.finalGrps = []
        for grp in grps:
            tempGrp = []
            for memInd in grp:
                tempGrp.append(self.members[memInd])
            self.finalGrps.append(tempGrp)
        if not os.path.exists(os.path.join(dataDir, "complete", "")):
            os.makedirs(os.path.join(dataDir, "complete", ""))
        open(os.path.join(dataDir, "complete", f"{self.id}.json"), "w").close()
        shutil.move(os.path.abspath(os.path.join(dataDir, f"{self.id}.json")),
                    os.path.abspath(os.path.join(
                        dataDir, "complete", f"{self.id}.json")))
        self.sendFinalMail()
