from models import *
import time
import dataclasses
owner = person("owner", "owner.com")
mems = [person("a", "a.com"), person(
    "b", "b.com"), person("c", "c.com"), person("d", "d.com"), person("e", "e.com")]
a = matching(deadline=time.time()+100, owner=owner, members=mems)
dict_dat = dataclasses.asdict(a)
b = matching(**dict_dat)
print(dataclasses.asdict(b))
