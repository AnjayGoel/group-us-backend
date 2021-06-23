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
    project_gen = Project.objects(uid=file_id)

    if project_gen.count() != 1:
        return ret

    project: Project = next(project_gen)
    if not project.has_secret(secret) or project.deadline < time():
        ret["message"] = "Invalid URL or Deadline Passed"
        return str(ret), 404
    else:
        def fill_in_background(data: Dict):
            pref = [0] * project.num_member
            for i in range(len(data)):
                index = next(x for x in project.members if x.name == data[i]["name"]).index
                pref[index] = data[i]["score"]

            project.preferences[project.get_index_from_secret(secret)] = pref
            project.save()
            if project.has_deadline_passed() or project.is_complete():
                project.solve()

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

        project = Project(
            deadline=data["deadline"],
            members=members,
            owner=owner,
            title=data["title"],
            grp_size=int(data["grpSize"]),
            num_member=len(members),
        )
        project.preferences = [[0] * project.num_member] * project.num_member

        project.save()
        project.send_init_mails()

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
