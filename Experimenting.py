# Removing DefinedIn!

from copy import deepcopy

class Predicate():
    def __init__(self, name):
        self.name = name            # The name of the predicate
        self.alternatives = {}      # Dict filled with all of the predicate alternatives, with arity as key.
    def __repr__(self):
        return self.name
    def add(self, args = [], goals = []):
        """
        'add' is used to add clauses (fact or rules) for a predicate.

        It is called with a list of the args that appear in the head of the clause being added,
        followed (optionally) by a list of goals that, if followed, can satisfy the query.
        """
        if len(args) in self.alternatives:
            self.alternatives[len(args)].append(Alt(args, goals))
        else:
            self.alternatives[len(args)] = [Alt(args, goals)]


# Goals must be completed in order to satisfy a query.
class Goal():
    def __init__(self, pred, *args):
        self.pred = pred                # The predicate that is being queried.
        self.args = list(args)          # Create a list of the goal's arguments.
    def __str__(self):
        return "goalPred: " + self.pred.name + "\nGoalArgs: " + str(self.args) + "\n"
    def __deepcopy__(self, memo):
        if not id(self) in memo:
            result = Goal(self.pred, *deepcopy(self.args, memo)) # This uses * to unpack the resulting list.
            memo[id(self)] = result     # This is used to prevent unnecessary copies and infinite recursion.
        else:
            result = memo[id(self)]     # If the goal was already copied, don't copy again.
        return result


# Alts are individual alternatives that were added to a predicate.
class Alt():
    def __init__(self, args, goals):
        self.args = args
        self.goals = goals
    def __str__(self):
        return "altArgs: " + str(self.args) + "\naltGoals: " + str(self.goals) + "\n"
    def __repr__(self):
        return repr(self.name + " = " + str(self.value))
    def __deepcopy__(self, memo):
        if not id(self) in memo:
            result = Alt(deepcopy(self.args, memo), deepcopy(self.goals, memo))
            memo[id(self)] = result
        else:
            result = memo[id(self)]     # If a copy was already made, use that one.
        return result


# Variables, Constants, and Mathematical expressions are all Terms.
class Term():
    def __init__(self, name, value):
        self.name = name
        self.value = str(value)
        self.children = []                  # The children are the variables that will change if this term has a value.
    def __eq__(self, other):
        return self.value == other.value    # This is used to compare terms.
    def __bool__(self):
        return self.value != "Undefined"    # A term is false it if has no value.
    def __str__(self):
        return self.name + " = " + str(self.value)  # This is used to print the term.
    def __repr__(self):
        return repr(self.name + " = " + str(self.value))
    def __hash__(self):
        return hash(repr(self))
    # Overload math operations.
    # This create methods on the fly to avoid typing repetitive code.
    for op_name, op in [("add", "+"), ("sub", "-"), ("mul", "*"), ("truediv", "/"), ("floordiv", "//"), ("mod", "%"), ("pow", "**")]:
        exec(f"""\
def __{op_name}__(self, other):
    return Math(self, f"{op}", other)
def __r{op_name}__(self, other):
    return Math(self, f"{op}", other)
""", globals(), locals())

class Var(Term):
    def __init__(self, name):
        super().__init__(name = name, value = "Undefined")    # Initialize the Var.
    def __copy__(self):
        return Var(self.name)
    def __deepcopy__(self, memo):
        if not self.name in memo:
            if self.value != "Undefined":              # If this Var already has a value, turn it into a Const???
                result = Const(self.value)
            else:
                result = Var(self.name)
            memo[self.name] = result
        else:
            result = memo[self.name]    # If the Var was already copied, don't re-copy.

        return result


class Const(Term):  # A constant, aka an atom or number.
    def __init__(self, value):
        # Consts are defined wherever they were created.
        super().__init__(name = "Const", value = value)
    def __copy__(self):
        return Const(self.value)
    def __deepcopy__(self, memo):
        if not id(self) in memo:
            result = Const(self.value)
            memo[id(self)] = result
        else:
            result = memo[id(self)]     # If the Const was already copied, don't re-copy.
        return result


class Math(Term):          # A mathematical expression.
    def __init__(self, operand1, operator, operand2):
        self.left = operand1
        self.operator = operator
        self.right = operand2
        super().__init__(name = "Math", value = "Undefined")
    def doMath(self):
        if isinstance(self.left, Math) and not self.left:
            self.left = self.left.doMath()
        try:                # Try to evaluate the math expression.
            self.value = str(eval(self.left.value + self.operator + self.right.value))
        except:             # If the expression cannot be evaluated, the value becomes false, safely failing the unification.
            self.value = False
    def __copy__(self):
        return Math(self.left, self.operator, self.right)
    def __deepcopy__(self, memo):
        if not id(self) in memo:
            newLeft = deepcopy(self.left, memo)
            newRight = deepcopy(self.right, memo)
            result = Math(newLeft, self.operator, newRight)
            memo[id(self)] = result
        else:
            result = memo[id(self)]         # If this was already copied, don't re-copy.
        return result


def tryGoal(originalGoal):
    goal = deepcopy(originalGoal, memo = {})
    try:        # This fails if the predicate has no goals added.
        alts = goal.pred.alternatives[len(goal.args)]
        # for index, alt in enumerate(alts):
        # for alt, originalAlt in zip(alts, originalAlts):
        for alt in alts:
            altAttempts = tryAlt(goal, alt)
            # Only yield if it succeeded, since failing one alt doesn't mean that the goal failed.
            for attempt in altAttempts:
                if attempt:
                    yield [arg for arg in goal.args if arg.value != "Undefined"] or True     # Yield vars, or True if this succeeded without changing vars. <- old comment???
            # Clear any args that were defined in this goal, so they may be reused for the next alt.
            for arg in goal.args:
                # if arg.definedIn is goal:       # If the arg was defined in this goal, reset it and all things unified from it.
                if isinstance(arg, Var):    # ???
                    changePath(arg, "Undefined")
    except:
        # If the goal is write/1, print argument to screen.
        if goal.pred == write and len(goal.args) == 1:
            print(goal.args[0].value)
            yield True
    yield False                             # If all the alts failed, then the goal failed.


# This tries the current alternative to see if it succeeds.
def tryAlt(query, alt):
    goalsToTry = alt.goals          # A list of goals that must be satisfied for this alt to succeed.
    if not tryUnify(query, alt):    # If the alt can't be unified, then it fails.
        yield False
    elif len(goalsToTry) > 0:       # If this alt has goals, try them.
        for success in tryGoals(goalsToTry):
            yield success
    else:
        yield True  # If there are no goals to try, this alt succeeded.



def tryGoals(goalsToTry):
    goals = [tryGoal(goal) for goal in goalsToTry]  # A list of [tryGoal(goal1), tryGoal(goal2), etc]
    currGoal = 0                                    # This is the index for the goal we are currently trying.
    failed = False
    while not failed:
        while 0 <= currGoal < len(goals):           # The goals succeed it currGoal reaches the end.
            currGoalArgs = next(goals[currGoal])    # Try the goal at the current index.
            if currGoalArgs:                        # This goal succeeded and args have been instantiated.
                currGoal += 1
            else:
                if currGoal == 0:   # If the first goal fails, there are no more things to try, and the function fails.
                    failed = True
                    break
                goals[currGoal] = tryGoal(goalsToTry[currGoal])  # Reset the generator.
                currGoal -= 1
        if not failed:
            yield True          # If we got here, then all the goals succeeded.
            currGoal -= 1       # Go back a goal to try for another solution.


# This function tries to unify the query and alt args, and returns a bool of its success.
def tryUnify(query, alt):
    # First check if they are able to unify.
    for queryArg, altArg in zip(query.args, alt.args):
        if queryArg and altArg and queryArg != altArg:  # If the args both have values and not equal, fail.
            return False
    # If it reaches this point, they can be unified.
    for queryArg, altArg in zip(query.args, alt.args):              # Loop through the query and alt arguments.
        # If either arg is a math term, evaluate it.
        if isinstance(queryArg, Math):
            queryArg.doMath()
            if not queryArg.value:      # The math failed.
                return False
        if isinstance(altArg, Math):
            altArg.doMath()
            if not altArg.value:        # The math failed.
                return False
        altArg.children.append(queryArg)         # The children are the variables we want to find out.
        # If the alt argument is the one with the value, all its children should be set to the same value.
        if altArg:
            changePath(altArg, altArg.value)  # Set all unified terms to new value.
        # If the query argument is the one with a value, set the parent level to that value.
        # This way the path will always be correct, so it will never need to be looped through with changePath.
        elif queryArg:
            altArg.value = queryArg.value        

    return True                                 # If it reaches this point, they can be unified.


def changePath(arg, newValue):
    if isinstance(arg, Term):
        for child in arg.children:
            child.value = newValue
            changePath(child, newValue)         # Change each parent to the new value.



#### Built-in Predicates ####

# The Prolog is/2 predicate, with a different name because "is" already exists in Python.
equals = Predicate("equals")
equals.add([Var("Q"), Var("Q")])

# fail/0. This works differently from other goals, as users do not need to type Goal(fail)
failPredicate = Predicate("failPredicate")
fail = Goal(failPredicate)

# write/1
write = Predicate("write")