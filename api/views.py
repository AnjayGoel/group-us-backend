import json

from django.http import HttpResponse, JsonResponse

from api import *
from .tasks import *

logger = logging.getLogger(__name__)

BASE_URL = os.getenv('BASE_URL')


def index(request):
    return HttpResponse("Group Us Api")


def create_poll(request):
    if request.method == "OPTIONS":
        return HttpResponse("")
    elif request.method == "POST":
        try:
            project = json.loads(request.body)
            project = prepare_project_json(project)
            insert_or_update_project.delay(project)
            send_init_mail(project)
            return JsonResponse({"status": 1}, status=201)
        except:
            logger.exception("Exception during create poll")
            return JsonResponse({"status": 0}, status=400)
    else:
        return HttpResponse(status=405)


def vote(request, proj_id, mem_id):
    if request.method == "OPTIONS":
        return HttpResponse("")

    try:
        project = mc.get(proj_id, mem_id)
    except:
        logger.exception("Exception when fetching document")
        return JsonResponse({"status": 0, "message": "Internal Error"}, status=500)

    if project is None:
        return JsonResponse({"status": 0, "message": "Invalid Url"}, status=400)

    elif deadline_passed(project):
        return JsonResponse({"status": 0, "message": "Deadline Passed"}, status=400)

    elif project["finished"]:
        return JsonResponse({"status": 0, "message": "Groups Already Formed"}, status=400)

    else:
        if request.method == "GET":
            try:
                return JsonResponse(get_vote_list_resp(project, mem_id), status=201)
            except:
                logger.exception("Exception during get vote list")
                return JsonResponse({"status": 0, "message": "Some Error"})

        elif request.method == "POST":
            try:
                resp_mems = json.loads(request.body)["data"]
                modifications = modify_preference(project, mem_id, resp_mems)
                insert_or_update_project.delay(modifications)
                if is_complete(project):
                    solve_and_mail_results.delay(project["uid"])
                return JsonResponse({"status": 1}, status=201)
            except:
                logger.exception("Exception during post vote list")
                return JsonResponse({"status": 0, "message": "Some Error"}, status=500)


def trigger_check_deadline(request):
    logger.info("Check Deadline Triggered")
    check_deadline.delay()
    return HttpResponse("Checking for due projects...")
