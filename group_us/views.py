from flask import request
from flask_cors import CORS, cross_origin

from group_us.models import *

cors = CORS(app)
load_dotenv()
app.config['CORS_HEADERS'] = 'Content-Type'
deadlines = []


@cross_origin()
@app.route('/fill/<file_id>/<string:secret>', methods=['GET'])
def fill(file_id: str, secret: str):
    ret = {"status": 0}
    project_gen = Project.objects(uid=file_id)
    if project_gen.count() != 1:
        return ret

    project: Project = next(project_gen)
    has_secret, member_name = project.has_secret(secret)
    if not has_secret or project.deadline < time():
        ret["message"] = "Invalid URL or Deadline Passed"
        return json.dumps(ret), 404
    else:
        ret["name"] = member_name
        ret["title"] = project.title
        ret["owner_name"] = project.owner.name
        ret["names"] = project.get_names()
        ret["status"] = 1
        return json.dumps(ret), 201


@cross_origin()
@app.route('/submit/<file_id>/<string:secret>', methods=['POST'])
def submit(file_id: str, secret: str):
    ret = {"status": 0}
    if not (path.exists(os.path.join(dataDir, f"{file_id}.json"))):
        ret["message"] = "File Not Found"
        return json.dumps(ret), 404
    else:
        obj = Project.get_from_file(file_id)
        if not obj.has_secret(secret) or obj.deadline < time.time():
            ret["message"] = "Invalid URL or Deadline Passed"
            return str(ret), 404
        else:
            def fill_in_background(data: Dict):
                pref = [0] * obj.num_member
                for i in range(len(data)):
                    index = obj.members.index(
                        next(x for x in obj.members if x.name == data[i]["name"]))
                    pref[index] = data[i]["score"]
                obj.preferences[obj.get_index_from_secret(secret)] = pref
                Project.save_to_file(obj)
                if obj.has_deadline_passed() or obj.is_complete():
                    obj.solve()

            th = Thread(target=fill_in_background, kwargs={
                "data": request.get_json()["data"]})
            th.start()
            ret["status"] = 1
            return json.dumps(ret), 201


@cross_origin()
@app.route('/create', methods=['POST'])
def create():
    def do_in_background(data: Dict):
        owner = Person(name=data['owner_name'], email=data['owner_email'], index=-1)
        members = []
        for idx, member in enumerate(data["members"]):
            members.append(
                Person(
                    name=member["name"],
                    email=member["email"],
                    index=idx
                ))

        obj = Project(
            deadline=data["deadline"],
            members=members,
            owner=owner,
            title=data["title"],
            grp_size=int(data["grpSize"]),
            num_member=len(members),
        )
        obj.save()
        obj.send_init_mails()

    ret = {"status": 0}
    data = request.get_json()

    th = Thread(target=do_in_background, kwargs={'data': data})
    th.start()
    return json.dumps({"status": 1}), 201


@cross_origin()
@app.route('/check', methods=['GET'])
def check():
    Thread(
        target=check_deadline
    ).start()

    return "Done"
