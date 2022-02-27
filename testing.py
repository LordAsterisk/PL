# This file is used for internal testing.

from PL import *
# from Experimenting import *


################### Testing #####################

# First we define all the predicates that will be tested.
male = Predicate("male")
female = Predicate("female")
child = Predicate("child")
parent = Predicate("parent")
father = Predicate("father")
mother = Predicate("mother")
sibling = Predicate("sibling")
uncle = Predicate("uncle")
aunt = Predicate("aunt")
ancestor = Predicate("ancestor")
first_cousin = Predicate("first_cousin")
collatz = Predicate("collatz")
inboth = Predicate("inboth")
increment_all = Predicate("increment_all")
just_ate = Predicate("just_ate")
is_digesting = Predicate("is_digesting")
count = Predicate("count")
always_true = Predicate("always_true")
basicList = Predicate("basicList")
merge = Predicate("merge")

# #### facts/rules ####

+male("bob")
+male("john")
+male("ben")
+male("martin")
+male("edmund")
+male("david")
+male("isidore")
+male("william")
+male("ferdinand")
+male("morris")
+male("alphonse")
+male("jiri")
+female("kathryn")
+female("beatrice")
+female("rachel")
+female("lillian")
+female("alice")
+female("rosa")
+female("marjorie")
+female("emma")
+female("nellie")
+female("eva")
+female("bertha")
+female("fergie")

# A is the child of B
+child("bob", "john")
+child("bob", "kathryn")
+child("beatrice", "john")
+child("beatrice", "kathryn")
+child("john", "ben")
+child("john", "rachel")
+child("lillian", "ben")
+child("lillian", "rachel")
+child("kathryn", "rosa")
+child("kathryn", "martin")
+child("alice", "martin")
+child("alice", "rosa")
+child("ferdinand", "martin")
+child("ferdinand", "fergie")
+child("marjorie", "edmund")
+child("marjorie", "lillian")
+child("david", "lillian")
+child("david", "edmund")
+child("ben", "isidore")
+child("ben", "bertha")
+child("william", "isidore")
+child("william", "bertha")
+child("emma", "isidore")
+child("emma", "bertha")
+child("morris", "alphonse")
+child("morris", "emma")
+child("nellie", "alphonse")
+child("nellie", "emma")
+child("eva", "alphonse")
+child("eva", "emma")
+child("jiri", "alphonse")
+child("jiri", "emma")

parent("A", "B") >> [child("B", "A")]

father("A", "B") >> [male("A"), parent("A", "B")]
mother("A", "B") >> [female("A"), parent("A", "B")]

sibling("A", "B") >> [parent("X", "A"), parent("X", "B"), "A \= B"]

uncle("A", "B") >> [parent("X", "B"), sibling("A", "X"), male("A")]
aunt("A", "B") >> [parent("X", "B"), sibling("A", "X"), female("A")]

ancestor("A", "B") >> [parent("A", "B")]
ancestor("A", "B") >> [parent("A", "X"), ancestor("X", "B")]

first_cousin("A", "B") >> [parent("X", "A"), sibling("Y", "X"), parent("Y", "B")]

+collatz("N", "N")
collatz("N0", "N") >> [equals("0", "N0 % 2"), equals("N1", "N0 / 2"), collatz("N1", "N")]
collatz("N0", "N") >> [equals("1", "N0 % 2"), equals("N1", "3 * N0 + 1"), collatz("N1", "N")]

inboth("A", "B", "X") >> [member("X", "A"), member("X", "B")]

+just_ate("deer", "grass")
+just_ate("tiger", "deer")

is_digesting("A", "B") >> [just_ate("A", "B")]
is_digesting("A", "B") >> [just_ate("A", "C"), is_digesting("C", "B")]

+count("A", "A")
count("A", "C") >> [equals("B", "A" |plus| 1), count("B", "C")]

+always_true()

increment_all([], "X") >> [setEqual("X", [])]
increment_all(["H", "|", "T"], "X") >> [equals("Y", "H + 1"), increment_all("T", "Z"), setEqual("X", ["Y", "|", "Z"])]

+basicList(["a", "b", "c"])

+merge("A", [], "A")
+merge([], "B", "B")
merge(["H1", "|", "T1"], ["H2", "|", "T2"], "X") >> ["H1 < H2", merge("T1", ["H2", "|", "T2"], "Z"), setEqual("X", ["H1", "|", "Z"])]
merge(["H1", "|", "T1"], ["H2", "|", "T2"], "X") >> ["H1 >= H2", merge(["H1", "|", "T1"], "T2", "Z"), setEqual("X", ["H2", "|", "Z"])]

# ##########################################

# ### All tests below succeed! ###

# success = -male("X")
# success = -child("bob", "X")
# success = -child("X", "Y")
# success = -child("X", "bob")
# success = -child("X", "john")
# success = -child("rosa", "isidore")
# success = -parent("rosa", "kathryn")
# success = -parent("rosa", "X")
# success = -father("john", "X")
# success = -mother("rosa", "X")
# success = -mother("john", "X")
# success = -mother("X", "john")
# success = -ancestor("X", "bob")
# success = -ancestor("ben", "X")
# success = -collatz("10", "X")
# success = -member("X", ["bob", "apple", "shirt", "pip"])
# success = -inboth(["green", "red", "orange"], ["apple", "orange", "pear"], "orange")
# success = -inboth(["1", "2", "3", "4"], ["2", "5", "6", "1"], "X")
# success = -write("hi")
# success = -equals("X", "2 + 4")
# success = -equals("6", "2 + 4")
# success = -equals("6", "2 + 8")
# success = -equals("X", "2 + hi")    # Maybe print error instead???
# success = -fail()
# success = -is_digesting("tiger", "grass")
# success = -is_digesting("X", "Y")
# success = -count(0, "X")
# success = -always_true()
# success = -setEqual("X", [])
# success = -increment_all(["12", "99", "4", "-7"], "X")
# success = -basicList(["X", "Y", "Z"])



### Testing Zone ###


success = -equals("X", 2 |plus| (4 |times| 5))
# success = -equals("X", 2 |plus| 4 |times| 5)
# success = -equals(4, 2 |plus| "X" |plus| 5)     # is/equals pred can't have vars on right side.








#### Test queries below FAIL ####  ???

# success = -sibling("john", "X")
# success = -first_cousin("david", "X")
# success = -first_cousin("jiri", "X")
# success = -merge(["1", "4", "5", "10", "11", "13"], ["3", "4", "1000"], "X")
# child(X, emma), male(X).
# success = -(child("X", "emma") & male("X"))   <- ugly, but maybe this???
# child(alice, rosa), female(alice).











### To see all results #####
for s in success:   # Can also be '-success' to reduce typing '-' elsewhere.
    print(s)

# #### Alternatives for specific cases ####
# for s in -male("X"):
#     print(s)

# print(next(success))
# print(next(success))

# ### To see only some results ####
# for _ in range(5):
#     print(next(success))





