# Trying to allow the user to only imput strings.

from copy import deepcopy

# args is a list of strings.
def solve(goal = []):
    newGoal = stringsToTerms(goal)
    for success in tryGoal(Goal(newGoal[0], *newGoal[1:])):
        yield success


# This will take a list, for example [just_ate, "A", "C"], and convert all the strings to Terms.
def stringsToTerms(oldList, memo = {}):     # Memo is a dict of terms already created
    newList = []
    for word in oldList:
        # Represent duplicate strings as the same Term.
        if word in memo:
            nextWord = memo[word]
        # If the word is a predicate, don't change it.
        elif isinstance(word, Predicate):
            nextWord = word
        # Otherwise, if the first letter is uppercase, it is a Var.
        elif word[0].isupper():     
            memo[word] = Var(word)
            nextWord = memo[word]
        # All other strings (including mathematical expressions) are consts.
        else:                       
            memo[word] = Const(word)
            nextWord = memo[word]
        # Later add lists by checking if word[0] is []! ???
        newList.append(nextWord)
    return newList
    

class Predicate(): 
    def __init__(self, name): 
        self.name = name            # The name of the predicate
        self.alternatives = {}      # Dict filled with all of the predicate alternatives, with arity as key.
    def __repr__(self):
        return self.name

# is_digesting.add(["A", "B"], [[just_ate, "A", "C"], [is_digesting, "C", "B"]])


    def add(self, args = [], goals = []):
        """
        'add' is used to add clauses (fact or rules) for a predicate.

        It is called with a list of the args that appear in the head of the clause being added,
        followed (optionally) by a list of goals that, if followed, can satisfy the query.
        """
        # Memo is a dictionary of all terms in this alt.
        # This makes sure that no terms are duplicates.
        memo = {}       
        args = stringsToTerms(args, memo)
        goals = [stringsToTerms(goal, memo) for goal in goals]
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

# class List    ???

def tryGoal(goal):
    # Keep copy of goal args. This is not a deep copy, so changed values will remain changed here.
    originalArgs = [arg for arg in goal.args]
    if len(goal.args) in goal.pred.alternatives:
        alts = deepcopy(goal.pred.alternatives[len(goal.args)], memo = {})      # Deepcopy the alts of correct arity so that they may be used again later without changes.
        # If a variable already has a value, this goal cannot change it.
        # To ensure the value does not get reset, the variable must be changed to a Const.
        for argIndex, arg in enumerate(goal.args):
            if isinstance(arg, Var) and arg.value != "Undefined":
                goal.args[argIndex] = Const(arg.value)
        # Only yield if it succeeded, since failing one alt doesn't mean that the goal failed.
        for alt in alts:
            altAttempts = tryAlt(goal, alt)
            # Only yield if it succeeded, since failing one alt doesn't mean that the goal failed.
            for attempt in altAttempts:
                if attempt:
                    # Yield vars, or True if this succeeded without changing vars.
                    yield [arg for arg in goal.args if isinstance(arg, Var) and arg.value != "Undefined"] or True
            # Clear any args that were defined in this goal, so they may be reused for the next alt.
            for arg in goal.args:
                if isinstance(arg, Var):
                    changePath(arg, "Undefined")
    # If no predicate exists with this number of arguments, it may be a built-in predicate.
    elif goal.pred == write and len(goal.args) == 1:
            print(goal.args[0].value)
            yield True
    # After trying all alts, reset any Vars that were turned into Consts.
    goal.args = originalArgs
    yield False               # If all the alts failed, then the goal failed.


# This tries the current alternative to see if it succeeds.
def tryAlt(query, alt):
    goalsToTry = alt.goals          # A list of goals that must be satisfied for this alt to succeed.
    if not tryUnify(query.args, alt.args):    # If the alt can't be unified, then it fails.
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
def tryUnify(queryArgs, altArgs):
    # First check if they are able to unify.
    for queryArg, altArg in zip(queryArgs, altArgs):
        # if isinstance(queryArg, list) or isinstance(altArg, list):
        #     tryUnify(queryArg, altArg)
        if queryArg and altArg and queryArg != altArg:  # If the args both have values and not equal, fail.
            return False
        # Remove the alt's previous children.
        altArg.children.clear()
    # If it reaches this point, they can be unified.
    for queryArg, altArg in zip(queryArgs, altArgs):              # Loop through the query and alt arguments.
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
        if queryArg:
            altArg.value = queryArg.value
        changePath(altArg, altArg.value)  # Set all unified terms to new value.   
    return True                                 # If it reaches this point, they can be unified.


def changePath(arg, newValue):
    # if isinstance(arg, Term) and not isinstance(arg, Const):
    if isinstance(arg, Term):
        arg.value = newValue
        for child in arg.children:
            # if child value already is new value, maybe don't need to change child's path? Try later! ???
            changePath(child, newValue)         # Change each parent to the new value.



# #### Built-in Predicates ####

# # The Prolog is/2 predicate, with a different name because "is" already exists in Python.
# equals = Predicate("equals")
# equals.add([Var("Q"), Var("Q")])

# # fail/0. This works differently from other goals, as users do not need to type Goal(fail)
# failPredicate = Predicate("failPredicate")
# fail = Goal(failPredicate)

# # write/1
# write = Predicate("write")


# class Foo():
#     def __init__(self, num):
#         self.num_val = num
#     def __add__(self, addend):
#         if isinstance(addend, Foo):
#             return Foo(self.num_val + addend.num_val)
#         return Foo(self.num_val + addend) 
#     def __str__(self):
#         return f"{self.num_val}"

# myFoo = Foo(18)
# res = eval("myFoo + 2")
# print(res) 