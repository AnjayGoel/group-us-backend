from os.path import isfile, join
from posix import listdir
import threading
from flask import Flask, request, redirect
from os import path
import dataclasses
from threading import *
from flask_cors import CORS, cross_origin
from typing import *
from dotenv import load_dotenv

from group_us import *
from group_us.models import *

cors = CORS(app)
load_dotenv()
app.config['CORS_HEADERS'] = 'Content-Type'
deadlines = []


@cross_origin()
@app.route('/fill/<string:id>/<string:secret>', methods=['GET'])
def fill(id: str, secret: str):
    ret = {"status": 0}
    names = []
    if not (path.exists(os.path.join(dataDir, f"{id}.json"))):
        return json.dumps(ret), 404
    else:
        obj = matching.getFromFile(id)
        hasSecret, name = obj.hasSecret(secret)
        if (not hasSecret or obj.deadline < time.time()):
            return json.dumps(ret), 404
        else:
            ret["name"] = name
            ret["title"] = obj.title
            ret["owner_name"] = obj.owner.name
            ret["names"] = obj.getNames()
            ret["status"] = 1
            return json.dumps(ret), 201


@ cross_origin()
@ app.route('/submit/<string:id>/<string:secret>', methods=['POST'])
def submit(id: str, secret: str):
    ret = {"status": 0}
    names = []
    if not (path.exists(os.path.join(dataDir, f"{id}.json"))):
        return json.dumps(ret), 404
    else:
        obj = matching.getFromFile(id)
        if (not obj.hasSecret(secret) or obj.deadline < time.time()):
            return str(ret), 404
        else:
            def fill_in_background(data: Dict):
                pref = [0]*(obj.nums)
                for i in range(len(data)):
                    index = obj.members.index(
                        next(x for x in obj.members if x.name == data[i][0]))
                    pref[index] = data[i][1]
                obj.preferences[obj.getIndexFromSecret(secret)] = pref
                matching.saveToFile(obj)
                if (obj.hasDeadlinePassed() or obj.isComplete()):
                    obj.solve()

            th = Thread(target=fill_in_background, kwargs={
                "data": request.get_json()["data"]})
            th.start()
            ret["status"] = 1
            return json.dumps(ret), 201


@ cross_origin()
@ app.route('/create', methods=['POST'])
def create():
    def do_in_background(data: Dict):

        owner = person(data['owner_name'], data['owner_email'])
        members = []
        for i in range(len(data["member_names"])):
            members.append(person(data["member_names"][i],
                                  data["member_emails"][i]))
        obj = matching(deadline=data["deadline"], members=members,
                       owner=owner, title=data["title"], grpSize=int(data["grpSize"]))
        matching.saveToFile(obj)
        deadlines.append([obj.id, obj.deadline])
        obj.sendInitMails()
    th = Thread(target=do_in_background, kwargs={'data': request.get_json()})
    th.start()
    return json.dumps({"status": 1}), 201


def check_for_deadlines():
    files = [f for f in listdir(dataDir)
             if isfile(join(dataDir, f))]
    for f in files:
        obj = matching.getFromFile(f.split(".")[0])
        deadlines.append([obj.id, obj.deadline])
    while True:
        time.sleep(60*5)
        due = [x for x in deadlines if x[1] < time.time()]
        for i in due:
            obj = matching.getFromFile(i[0])
            if not obj == None:
                def temp(obj=None):
                    obj.solve()
                Thread(target=temp, kwargs={
                    'obj': obj}).start()


th = Thread(target=check_for_deadlines)
th.start()
