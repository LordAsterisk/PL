# The PL Module offers Prolog functionality for Python programmers.
# Created by Sawyer Redstone.

import itertools

# Take a list, string, or int, and convert it to type Term.
def create(term, memo = {}):
    if str(term) in memo:
        return memo[str(term)]
    if isinstance(term, int) or isinstance(term, float):   # Numbers are constants.
        memo[str(term)] = Const(term)
    elif isinstance(term, Math):
        # Make new math term so each alt has unchanged starting math.
        newMath = Math(term.function)
        newMath.mathList = [create(item, memo) if not callable(item) else item for item in term.mathList]
        memo[str(term)] = newMath
    elif isinstance(term, list):
        # If the list is empty, it is a Const; otherwise it is a ListPL.
        memo[str(term)] = ListPL([create(item, memo) for item in term]) if term else Const(term)
    elif isinstance(term, Goal):
        memo[str(term)] = Goal(term.pred, [create(item, memo) for item in term.args])
    elif term[0].isupper() or term[0] == "_":
        memo[str(term)] = Var(term)
    # Otherwise, it is a Const.
    else:
        memo[str(term)] = Const(term)
    return memo[str(term)]


class Predicate():
    def __init__(self, name):
        self.name = name            # The name of the predicate
        self.alternatives = {}      # Dict filled with all of the predicate alternatives, with arity as key.
    def __repr__(self):
        return self.name
    def __call__(self, *args):
        return Goal(self, args)

# Query is an iterator.
# Use query << [list of goals] for queries.
class Query():
    def __init__(self):
        self.goals = []
        self.successes = []
        self.size = None
    def __lshift__(self, goals):
        # Memo is a dictionary of all args in the goals.
        # This makes sure that no terms are duplicates.
        memo = {}
        goals = [Goal(goal.pred, [create(arg, memo) for arg in goal.args]) for goal in goals]
        attempt = tryGoals(goals)
        # loop through the generator self.size times, or until end if size is not specified.
        # for _ in itertools.islice(attempt, self.size):
        for attempt in itertools.islice(attempt, self.size):
            success = attempt[0]
            wasCut = attempt[1]
            if not success:
                break
            args = {}
            for argName in memo:
                if isinstance(memo[argName], Var):
                    args[argName] = str(flatten(memo[argName].value))
            if len(args) > 0:
                # print("TEST: " + str(args))    # For debugging. ***
                self.successes.append(args)
            else:
                # print("TEST: True")    # For debugging. ***
                self.successes.append(True)
            if wasCut:
                break
        if self.successes == []:
            self.successes.append(False)
        # Reset the size for future queries, in the case where multiple queries are made at once.
        self.size = None
    def __iter__(self):
        return iter(self.successes)
    # query(3) makes the query only show 3 results.
    def __call__(self, num):
        self.size = num
        return self
    def __getitem__(self, num):
        return self.successes[num]


# Goals must be completed in order to satisfy a query.
class Goal():
    def __init__(self, pred = [], args = []):
        self.pred = pred            # The predicate that is being queried.
        self.args = list(args)      # Create a list of the goal's arguments.
    def __str__(self):
        return "goalPred: " + self.pred.name + "\nGoalArgs: " + str(self.args) + "\n"
    # Add rules as: head >> [goal1, goal2]
    # Add facts as head >> []
    def __rshift__(self, others):
        if len(self.args) in self.pred.alternatives:
            self.pred.alternatives[len(self.args)].append(Alt(self.args, others))
        else:
            self.pred.alternatives[len(self.args)] = [Alt(self.args, others)]
    # Alternatively, add facts as +head.
    # '+' for putting info IN (facts).
    def __pos__(self):
        self >> []      # Treat a fact as a rule with no goals.



# Alts are individual alternatives that were added to a predicate.
class Alt():
    def __init__(self, args, goals):
        self.args = args
        self.goals = goals
    def __str__(self):
        return "altArgs: " + str(self.args) + "\naltGoals: " + str(self.goals) + "\n"
    def __repr__(self):
        return repr(self.name + " = " + str(self.value))


# This function tries to unify the query and alt args, and returns a bool of its success.
def tryUnify(queryArgs, altArgs):
    for queryArg, altArg in zip(queryArgs, altArgs):    # Loop through the query and alt arguments.
        # Check if unification is possible before unifying.
        if queryArg != altArg:
            return False
        queryArg.unifyWith(altArg)
    return True                                 # If it reaches this point, they can be unified.


# Variables and Constants are Terms.
class Term():
    def __init__(self, name, value):
        self.name = name
        self.value = value
        self.children = []                  # The children are the variables that will change if this term has a value.
    @staticmethod
    def changeType(word):
        if isinstance(word, list):
            if word == []:
                return Const(word)
            elif word[0].value == "|":
                return word[-1]
            return ListPL(word)
        # All other values are Consts.
        return Const(word)
    # This checks if they *can* be equal.
    def __eq__(self, other):
        return self.value == other.value or not self or not other
    def __bool__(self):
        return self.value != "Undefined"    # A term is false it if has no value.
    def __repr__(self):
        return str(self.value)
    def __str__(self):
        return str(self.value)
    def __hash__(self):
        return hash(repr(self))
    def unifyWith(self, altArg):
        altArg.children.append(self)                        # The children are the variables we want to find out.
        if self:
            altArg.value = self.value     # Maybe make this equal to a copy of the value, in case the value is a list. ***
        changePath(altArg, altArg.value)  # Set all unified terms to new value.
        return True


class Var(Term):
    def __init__(self, name, value = "Undefined"):
        self.name = name
        self.value = value
        super().__init__(name = self.name, value = self.value)    # Initialize the Var.
    def __repr__(self):
        return repr(self.name + " = " + str(self.value))


class Const(Term):  # A constant, aka an atom.
    def __init__(self, value):
        super().__init__(name = "Const", value = value)


# To use math, write the operation surrounded with |.
# For example, '3 + 4' would be written as '3 |plus| 4'.
# (Idea from: https://code.activestate.com/recipes/384122/)
class Math(Term):
    def __init__(self, function):
        self.mathList = []
        self.function = function
        self.children = []     # The children are the variables that will change if this term has a value.
    def __ror__(self, other):
        # Make a new Math object so built-in objects won't change.
        newMath = Math(self.function)
        newMath.mathList = [other, self.function]
        return newMath
    def __or__(self, other):
        # Check if 'other' is built-in. (Add other built-in here! ***)
        if other is plus or other is minus:
            other = other.function
        if self.mathList[-1] is times or self.mathList[-1] is div or self.mathList[-1] is mod:
            op = self.mathList.pop()
            addend = self.mathList.pop()
            newMath = addend | op | other
            self.mathList.append(newMath)
        self.mathList.append(other)
        return self
    # This gives the object the .value attribute.
    @property
    def value(self):
        result = self.mathList[0].value
        for index, item in enumerate(self.mathList):
            if callable(item):
                addend = self.mathList[index+1].value
                result = item(result, addend)
        return result
    def __str__(self):
        return str(self.mathList)
    def __repr__(self):
        return str(self)
    def __hash__(self):
        return hash(tuple(self.mathList))


plus = Math(lambda x, y: x + y)
minus = Math(lambda x, y: x - y)
times = Math(lambda x, y: x * y)
div = Math(lambda x, y: x / y)
mod = Math(lambda x, y: x % y)




class ListPL(Term):
    def __init__(self, lst, name = "List"):
        self.head = lst[0]
        self.tail = Term.changeType(lst[1:])
        self.lst = lst
        super().__init__(name = name, value = lst)
    def __len__(self):
        return len(self.value)
    def __eq__(self, other):
        if isinstance(other.value, list) and other.value:       # ***
            other = ListPL(other.value)
        if self.tail and not isinstance(self.tail, ListPL):     # Should this be here? ***
            self.tail = Term.changeType(self.tail.value)
        if isinstance(other, ListPL):
            return self.head == other.head and self.tail == other.tail
        return super().__eq__(other)
    def unifyWith(self, altArg):
        if isinstance(altArg.value, list) and altArg.value:       # ***
            altArg = ListPL(altArg.value)
        if isinstance(altArg, ListPL):
            if self.head.unifyWith(altArg.head) and self.tail.unifyWith(altArg.tail):   # Later needs to clear path of all this? ***
                return True
            return False
        return super().unifyWith(altArg)
    def __repr__(self):
        return str(self)
    def __str__(self):
        return str(self.value)
    def __repr__(self):
        return str(self.lst)


def tryGoal(goal):
    wasCut = False
    # Keep copy of original goal args. This is not a deep copy, so changed values will remain changed here.
    # This allows Vars that are temporary changed to Consts to return back to their Var form.
    originalArgs = [arg for arg in goal.args]
    if len(goal.args) in goal.pred.alternatives:
        alts = goal.pred.alternatives[len(goal.args)]       # The list of all alts with matching arity.
        # If a variable already has a value, this goal cannot change it.
        # To ensure the value does not get reset, the variable must be changed to a Const.
        for argIndex, arg in enumerate(goal.args):
            if isinstance(arg, Var) and arg.value != "Undefined":
                goal.args[argIndex] = Term.changeType(arg.value)
        # Only yield if it succeeded, since failing one alt doesn't mean that the goal failed.
        for alt in alts:
            altAttempts = tryAlt(goal, alt)
            # Only yield if it succeeded, since failing one alt doesn't mean that the goal failed.
            for attempt in altAttempts:
                success = attempt[0]
                wasCut = attempt[1]
                if success:
                    # Yield vars, or True if this succeeded without changing vars.
                    # yield findVars(goal.args) or True
                    yield (findVars(goal.args) or True, wasCut)
                if wasCut:
                    break
            # Clear any args that were defined in this goal, so they may be reused for the next alt.
            for arg in goal.args:
                if isinstance(arg, Var):
                    changePath(arg, "Undefined")
    # If no predicate exists with this number of arguments, it may be a built-in predicate.
    elif goal.pred == write and len(goal.args) == 1:
            print(goal.args[0].value)
            yield True, wasCut
    elif goal.pred == lt_:
        yield (goal.args[0].value < goal.args[1].value, wasCut)
    elif goal.pred == le_:
        yield (goal.args[0].value <= goal.args[1].value, wasCut)
    elif goal.pred == gt_:
        yield (goal.args[0].value > goal.args[1].value, wasCut)
    elif goal.pred == ge_:
        yield (goal.args[0].value >= goal.args[1].value, wasCut)
    elif goal.pred == cut:
        wasCut = True
        yield True, wasCut
    elif goal.pred == setEqual:
        if tryUnify([goal.args[0]], [goal.args[1]]):
            yield (findVars(goal.args) or True, wasCut)
    elif goal.pred == notEqual:
        if goal.args[0].value != goal.args[1].value:
            yield (findVars(goal.args) or True, wasCut)
    elif goal.pred == not_:
        yield (not next(tryGoal(goal.args[0])), wasCut)
    # After trying all alts, reset any Vars that were turned into Consts.
    goal.args = originalArgs
    yield False, wasCut               # If all the alts failed, then the goal failed.


# This tries the current alternative to see if it succeeds.
def tryAlt(query, alt):
    wasCut = False
    # Memo is a dictionary of all terms in this alt.
    # This makes sure that no terms are duplicates.
    memo = {}
    altArgs = [create(arg, memo) for arg in alt.args]
    altGoals = [Goal(goal.pred, [create(arg, memo) for arg in goal.args]) for goal in alt.goals]
    goalsToTry = altGoals          # A list of goals that must be satisfied for this alt to succeed.
    if not tryUnify(query.args, altArgs):    # If the alt can't be unified, then it fails.
        yield False, wasCut
    elif len(goalsToTry) > 0:       # If this alt has goals, try them.
        for attempt in tryGoals(goalsToTry):
            success = attempt[0]
            wasCut = attempt[1]
            if success:
                yield attempt
            if wasCut:
                break
    else:
        yield True, wasCut  # If there are no goals to try, this alt succeeded.


def tryGoals(goalsToTry):
    wasCut = False
    goals = [tryGoal(goal) for goal in goalsToTry]  # A list of [tryGoal(goal1), tryGoal(goal2), etc]
    currGoal = 0                                    # This is the index for the goal we are currently trying.
    failed = False
    while not failed:
        while 0 <= currGoal < len(goals):           # The goals succeed it currGoal reaches the end.
            if wasCut and goalsToTry[currGoal].pred == cut:
                failed = True
                break
            if goalsToTry[currGoal].pred == cut:
                wasCut = True
            currGoalAttempt = next(goals[currGoal])
            success = currGoalAttempt[0]
            wasCut = currGoalAttempt[1]
            if success:                        # This goal succeeded and args have been instantiated.
                currGoal += 1
            else:
                if currGoal == 0 or wasCut:   # If the first goal fails, there are no more things to try, and the function fails.
                    failed = True
                    break
                goals[currGoal] = tryGoal(goalsToTry[currGoal])  # Reset the generator.
                currGoal -= 1
        if not failed:
            yield True, wasCut     # If we got here, then all the goals succeeded.
            currGoal -= 1       # Go back a goal to try for another solution.
    yield False, wasCut


def changePath(arg, newValue):
    if isinstance(arg, Var):
        arg.value = newValue
    for child in arg.children:
        # if child value already is new value, maybe don't need to change child's path? Try later! ***
        changePath(child, newValue)         # Change each parent to the new value.


# Returns a list of all Vars found in a list.
def findVars(args):
    result = []
    for arg in args:
        if isinstance(arg, ListPL):
            result.extend(findVars(arg.value))
        if isinstance(arg, Var) and arg.name[0] != "_":
            if isinstance(arg.value, list):
                arg = Var(arg.name, arg.value)
            result.append(arg)
    return result


# This flattens a list with "|" into a list with values, not terms.
def flatten(toFlatten):
    if not isinstance(toFlatten, list):
        return toFlatten
    lst = toFlatten[:]
    if len(lst) > 2 and lst[-2].value == "|":
        tail = lst.pop()
        lst.pop()
        lst.extend(flatten(tail.value))
    return [item.value if isinstance(item, Term) else item for item in lst]


# #### Built-in Features ####

# The Prolog is/2 predicate, with a different name because "is" already exists in Python.
is_ = Predicate("is_")
is_("Q", "Q") >> []

# fail/0.
fail = Predicate("failPredicate")

write = Predicate("write")

member = Predicate("member")
member("X", ["X", "|", "_"]) >> []
member("X", ["_", "|", "T"]) >> [member("X", "T")]

append_ = Predicate("append_")
append_([], "W", "W") >> []
append_(["H", "|", "T"], "X", ["H", "|", "S"]) >> [append_("T", "X", "S")]


# cut (!) predicate.
cut = Predicate("cut")

# # once/1

# =/2 predicate.
setEqual = Predicate("setEqual")
notEqual = Predicate("notEqual")

# # # Use this for all comparisons, such as >, =,
# # compare = Predicate("compare")

# evaluate = Predicate("evaluate")

# (\+)/1 predicate.
not_ = Predicate("not_")
# not_("A") >> ["A", cut(), fail()]
# not_("_") >> []

mynot = Predicate("mynot")      # *** Doesn't work.
mynot("A") >> ["A", cut(), fail()]
mynot("_") >> []

# </2 predicate.
lt_ = Predicate("less than")
le_ = Predicate("less than or equal")
gt_ = Predicate("greater than")
ge_ = Predicate("greater than or equal")


between = Predicate("between")
between("N", "M", "K") >> [le_("N", "M"), setEqual("K", "N")]
between("N", "M", "K") >> [lt_("N", "M"), is_("N1", "N" |plus| 1), between("N1", "M", "K")]

len_ = Predicate("len_")
len_([], 0) >> []
len_(["_", "|", "T"], "A") >> [len_("T", "B"), is_("A", "B" |plus| 1)]

# permutation([],[]).
# permutation([H|T],S) :- permutation(T,P),append(X,Y,P),append(X,[H|Y],S).
permutation_ = Predicate("permutation_")
permutation_([], []) >> []
permutation_(["H", "|", "T"], "S") >> [permutation_("T", "P"), append_("X", "Y", "P"), append_("X", ["H", "|", "Y"], "S")]

# Use to make queries.
query = Query()
