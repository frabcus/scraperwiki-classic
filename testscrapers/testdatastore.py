"""Tests all the datastore functions in the save module of datastore"""

from scraperwiki.datastore import *


# from save import retrieve, delete, insert, save
d1, d2, d3, d10, d20, d30, d100, d200, d300 = "d1", "d2", "d3", "d10", "d20", "d30", "d100", "d200", "d300"

delete({})
insert({"A":d1, "B":d2, "C":d3})

r1 = retrieve({})
assert len(r1) == 1
r1f = r1[0]
assert r1f["A"] == d1 and r1f["B"] == d2 and r1f["C"] == d3

insert({"A":d1, "B":d20, "E":d30})
assert len(retrieve({})) == 2

r2 = retrieve({"B":d20})
assert len(r2) == 1
r2f = r2[0]
assert r2f["A"] == d1 and r2f["B"] == d20 and r2f["E"] == d30 and "C" not in r2f

assert len(retrieve({"A":None})) == 2
assert len(retrieve({"A":d1})) == 2
assert len(retrieve({"A":d10})) == 0

r3 = retrieve({"C":None})
assert len(r3) == 1
r3f = r3[0]
assert r3f["A"] == d1 and r3f["B"] == d2 and r3f["C"] == d3

save(["B", "C"], {"A":d100, "B":d2, "C":d300})

assert len(retrieve({"C":None})) == 2
save(["B", "C"], {"A":d100, "B":d2, "C":d3})
assert len(retrieve({"C":None})) == 2

delete({"C":None})
assert len(retrieve({})) == 1

print "Done"


