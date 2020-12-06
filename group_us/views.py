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
        ret["message"] = "File Not Found"
        return json.dumps(ret), 404
    else:
        obj = matching.getFromFile(id)
        hasSecret, name = obj.hasSecret(secret)
        if (not hasSecret or obj.deadline < time.time()):
            ret["message"] = "Invalid URL or Deadline Passed"
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
        ret["message"] = "File Not Found"
        return json.dumps(ret), 404
    else:
        obj = matching.getFromFile(id)
        if (not obj.hasSecret(secret) or obj.deadline < time.time()):
            ret["message"] = "Invalid URL or Deadline Passed"
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
    ret = {"status": 0}
    data = request.get_json()
    if(len(data["member_names"]) != len(data["member_emails"])):
        ret["message"] = "Bad Request. Check The Form Once Again."
        return json.dumps(ret), 400

    th = Thread(target=do_in_background, kwargs={'data': data})
    th.start()
    return json.dumps({"status": 1}), 201