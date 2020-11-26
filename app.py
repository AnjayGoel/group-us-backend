from flask import Flask, request, redirect
from os import path
from models import *
import dataclasses
from threading import *
from typing import *
app = Flask(__name__)


@app.route('/')
def hello_world():
    return "TODO"


@app.route('/fill/<string:id>/<string:secret>', methods=['GET'])
def fill(id: str, secret: str):
    ret = {"status": 0}
    names = []
    if not (path.exists(f"./data/{id}.json")):
        return str(ret), 404
    else:
        obj = matching.getFromFile(id)
        hasSecret, name = obj.hasSecret(secret)
        if (not hasSecret or obj.deadline < time.time()):
            return str(ret), 404
        else:
            ret["name"] = name
            ret["names"] = obj.getNames()
            ret["status"] = 1
            return str(ret), 201


@app.route('/submit/<string:id>/<string:secret>', methods=['POST'])
def submit(id: str, secret: str):
    ret = {"status": 0}
    names = []
    if not (path.exists(f"./data/{id}.json")):
        return str(ret), 404
    else:
        obj = matching.getFromFile(id)
        if (not obj.hasSecret(secret) or obj.deadline < time.time()):
            return str(ret), 404
        else:
            def fill_in_background(data: Dict):
                pref = [0]*(obj.nums)
                for i in range(len(data["index"])):
                    pref[data["index"][i]] = data["pref"][i]
                obj.preferences[obj.getIndexFromSecret(secret)] = pref
                matching.saveToFile(obj)
                if (obj.hasDeadlinePassed() or obj.isComplete()):
                    obj.solve()

            th = Thread(target=fill_in_background, kwargs={
                'data': request.get_json()})
            th.start()
            ret["status"] = 1
            return str(ret), 201


@app.route('/create', methods=['POST'])
def create():
    def do_in_background(data: Dict):
        print(data)
        owner = person(data['owner_name'], data['owner_email'])
        members = []
        for i in range(len(data["member_names"])):
            members.append(person(data["member_names"][i],
                                  data["member_emails"][i]))
        obj = matching(deadline=data["deadline"], members=members,
                       owner=owner, title=data["title"], grpSize=data["grpSize"])
        matching.saveToFile(obj)
        obj.sendMails()
    th = Thread(target=do_in_background, kwargs={'data': request.get_json()})
    th.start()
    return "{'status':1}", 201


if __name__ == '__main__':
    app.debug = True
    app.run()
