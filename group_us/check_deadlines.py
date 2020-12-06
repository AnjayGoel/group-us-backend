import threading
from threading import *
from os import *
from os.path import *
import time
from group_us.algorithm import *
from group_us.models import *
from group_us import *

def check_deadline():
    print("Checking for deadlines")
    deadlines = []
    files = [f for f in listdir(dataDir) if isfile(join(dataDir, f))]
    for f in files:
        obj = matching.getFromFile(f.split(".")[0])
        if obj == None:
            continue
        deadlines.append([obj.id, obj.deadline])
    due = [x for x in deadlines if x[1] < time.time()]
    for i in due:
        obj = matching.getFromFile(i[0])
        if not obj == None:
            def temp(obj=None):
                obj.solve()
            Thread(target=temp, kwargs={
                'obj': obj}).start()
