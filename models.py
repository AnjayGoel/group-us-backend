import time
from utils import BASE_URL, send_email
import numpy as np
import secrets
from dataclasses import dataclass
import dataclasses
from typing import *
from algorithm import *
from os import path
import json
import pickle
import pprint


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
        if (deadline > time.time()):
            self.deadline = deadline
        else:
            self.deadline = time.time() + 7*24*60*60

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
        if (os.path.exists(f"./data/{id}.json")):
            f = open(f"./data/{id}.json", "r")
            obj = json.load(f)
            f.close()
            x = cls(**obj)
            x.owner = person(**obj["owner"])
            x.members = []
            for i in obj["members"]:
                x.members.append(person(**i))

            print(id)
            print(x.id)
            print("\n----------------------\n")
            return x
        else:
            return None

    @classmethod
    def saveToFile(cls, obj):
        print("-------saving to file----------")
        print(dataclasses.asdict(obj))
        f = open(f"./data/{obj.id}.json", "w")
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
            lst.extend([i, mem.name])
        return lst

    def getIndexFromSecret(self, secret: str) -> int:
        ind = -1
        for i in range(len(self.members)):
            if (self.members[i].secret == secret):
                ind = i
                break
        return ind

    def sendMails(self):
        print("Send Init Emails")
        for i in self.members:
            # send_email()
            pass

    def sendFinalMail(self):
        print("Send Final Mails")
        # send to owner
        for i in self.finalGrps:
            for j in i.members:
                # send_email()
                pass

    def initEmailContent(self, id: str):
        p = next(x for x in self.members if x.id == id)
        return f"{p.name}\nPlease Fill Out this form {BASE_URL}/fill/{self.id}/{p.secret} for {self.title}. From\n{self.owner}"

    def finalEmailToOwnerContent(self, id: str):
        grpStr = ""
        for i in self.finalGrps:
            tempStr = ""
            for j in i:
                tempStr += f"{i.name}, "
            grpStr += (tempStr+"\n")
        p = next(x for x in self.members if x.id == id)
        return f"{self.owner}\n Final Groups For {self.title} are: \n{grpStr}"

    def solve(self):
        arr = np.array(self.preferences)

        if (len(arr[arr < 0]) != 0):
            mean = arr[arr > 0].mean()
            if (mean == np.nan):
                mean = 5.0
            arr[arr < 0] = mean

        score, grps = Game(
            arr, r=self.grpSize, iter2=2, iter1=2).solve()
        self.finalGrps = []
        for grp in grps:
            tempGrp = []
            for memInd in grp:
                tempGrp.append(self.members[memInd])
            self.finalGrps.append(tempGrp)
        print(self.finalGrps)
        self.sendFinalMail()
