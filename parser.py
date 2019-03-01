relations = ['on', 'above', 'below', 'left', 'right', 'at', 'touching', 'near', 'front', 'behind', 'over', 'under', 'in', 'between']
colors = ['black', 'red' ,'brown', 'green', 'blue', 'yellow']
arguments = ['bed', 'picture', 'poster', 'lamp', 'cardbox', 'box', 'lamp', 'table', 'block', 'book', 'chair', 'bookshelf', 'ceiling light', 'ceiling fan', 'desk', 'sofa', 'tv', 'trash bin', 'pencil', 'laptop', 'apple', 'bowl', 'plate', 'banana', 'pencil holder', 'note', 'west', 'east', 'north', 'wall', 'ceiling', 'floor', 'vase', 'rose']
parts = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', 'pencil', 'holder', 'east', 'north', 'west', 'ceiling', 'trash', 'bin', 'wall', 'light', 'fan', 'trash']
determiners = ['a', 'the', 'other', 'another', 'all']
pronouns = ['it', 'this', 'these', 'those']
conj = ['and']
numerals = ['one', 'two', 'three']
scene_objects = []

class Token:
    def __init__(self, token):
        self.token = token

    def signature(self):
        return "token"

    def __repr__(self):
        return self.signature() + ":" + self.token

class Conj(Token):
    def __init__(self, token, arg=None):
        self.token = token
        self.arg = arg

    def conjoin(self, arg):
        if self.arg is None:
            return Conj(self.token, arg)
        elif type(arg) is Mod and type(self.arg) is Argument:
            return CompleteConj(self.token, [self.arg, Argument(self.arg.token, arg)])
        elif type(arg) is Argument and type(self.arg) is Mod:
            return CompleteConj(self.token, [Argument(arg.token, self.arg), arg])
        else:
            return CompleteConj(self.token, self.args + [arg])

    def signature(self):
        return "conj"

    def __repr__(self):
        return super().__repr__() + " - " + self.arg.__repr__()

class RightConj(Conj):
    def __init__(self, token, arg=None):
        self.token = token
        self.arg = arg

    def conjoin(self, arg):
        return CompleteConj(self.token, [self.arg, arg])

    def signature(self):
        return "rconj"

class RightArgConj(Conj):
    def __init__(self, token, arg=None):
        self.token = token
        self.arg = arg

    def conjoin(self, arg):
        return CompleteConj(self.token, [self.arg, arg])

    def signature(self):
        return "rargconj"    

class CompleteConj(Token):
    def __init__(self, token, args):
        self.token = token
        self.args = args

    def __repr__(self):
        ret_val = super().__repr__() + " - "
        for arg in self.args:
            ret_val += arg.__repr__() + " - "
        return ret_val

    def signature(self):
        return "compconj"

class Part(Token):
    def __init__(self, token, plural=False):
        self.token = token
        self.plural = plural

    def signature(self):
        return "part"
    
class Idx(Token):
    def __init__(self, token):
        self.token = token

    def signature(self):
        return "idx"

class Num(Token):
    def __init__(self, token):
        self.token = token

    def signature(self):
        return "num"

    def __repr__(self):
        return self.signature() + ":" + self.token

class Pro(Token):
    def __init__(self, token):
        self.token = token

    def signature(self):
        return "pro"

class Det(Token):
    def __init__(self, token):
        self.token = token

    def signature(self):
        return "det"

class Mod(Token):
    def __init__(self, det="", adj="", num=""):
        self.det = det
        self.adj = adj
        self.num = num

    def signature(self):
        return "mod"

    def __repr__(self):
        return self.signature() + ":" + self.det + " " + self.num + " " + self.adj

class Argument(Token):
    def __init__(self, argument, mod=None, plural=False):
        self.token = argument
        self.mod = mod
        self.plural = plural

    def signature(self):
        return "arg"

    def __str__(self):
        md = self.mod.__repr__() if self.mod is not None else ""
        return self.signature() + ":" + md + " " + self.token.__str__()

class Relation(Token):
    def __init__(self, relation, relatums=[], referents=[]):
        self.token = relation
        self.relatums = relatums
        self.referents = referents

    def signature(self):
        return "rel"

    def __repr__(self):
        ret_val = self.signature() + ":" + self.token + "\n"
        for arg in self.relatums:
            ret_val += arg.__str__() + "\n"
        for arg in self.referents:
            ret_val += arg.__str__() + "\n"
        return ret_val

def set_objects(scene_objects):
    global arguments
    arguments = scene_objects

def init_parser(objects):
    global scene_objects
    scene_objects = [name.lower() for name in objects]

def replace_args(argument):
    #if "wall" in argument.token:
    #    return Argument("world_" + "_".join(argument.token.lower().split()), argument.mod)
    if argument.mod is not None and argument.mod.adj is not None and (argument.mod.adj + " " + argument.token).lower() in scene_objects:
        return Argument((argument.mod.adj + " " + argument.token).lower(), argument.mod)
    return argument

def match_word(word, word_class):
    for w in word_class:
        if word == w or word[:-1] == w and word[-1] == 's' or word[:-3] + 'f' == w or \
           word[:-2] == w and word[-2:-1] == "es":
            return w
    return None

def is_plural(word):
    for w in arguments:
        if word != w and word[:-1] == w and word[-1] == 's' or word[:-3] + 'f' == w or \
           word[:-2] == w and word[-2:-1] == "es":
            return True
    for w in parts:
        if word != w and word[:-1] == w and word[-1] == 's' or word[:-3] + 'f' == w or \
           word[:-2] == w and word[-2:-1] == "es":
            return True
    return False
    
def tokenize(word):
    if word in relations:
        return Relation(word)
    elif word in pronouns:
        return Pro(word)
    elif word in conj:
        return Conj(word)
    elif word in colors:
        return Mod(adj=word)
    elif word in determiners:
        return Mod(det=word)
    elif word in numerals:
        return Num(word)
        #return Mod(num=word)
    if  word == "all":
        return Num("two")
    w = match_word(word, arguments)
    if w is not None:
        return Argument(w, None, is_plural(word))    
    w = match_word(word, parts)
    if w is not None:
        return Part(w, is_plural(word))
    return None

grammar = {}
grammar["mod", "mod"] = lambda mod1, mod2: Mod(mod1.det + mod2.det, mod1.adj + mod2.adj, mod1.num + mod2.num)
grammar["mod", "arg"] = lambda mod, arg: Argument(arg.token, mod, arg.plural)
grammar["arg", "rel"] = lambda x, y: Relation(y.token, y.relatums + [x], y.referents)
grammar["rel", "arg"] = lambda x, y: Relation(x.token, x.relatums, x.referents + [y]) if y.plural == False else Relation(x.token, x.relatums, x.referents + [y, y])
grammar["rel", "part"] = lambda rel, part: \
                         Relation(rel.token, rel.relatums, rel.referents[:-1] + [Argument(rel.referents[-1].token + " " + part.token, rel.referents[-1].mod, rel.referents[-1].plural)]) \
                         if len(rel.referents) > 0 else \
                            Relation(rel.token, rel.relatums, [Argument(part.token, None, part.plural)])
#grammar["mod", "conj"] = lambda mod, conj: conj.conjoin(mod)
#grammar["arg", "conj"] = lambda arg, conj: conj.conjoin(arg)
grammar["arg", "rargconj"] = lambda arg, conj: conj.conjoin(arg)
grammar["mod", "rargconj"] = lambda mod, conj: conj.conjoin(Argument(conj.arg.token, mod, conj.arg.plural))
grammar["conj", "arg"] = lambda conj, arg: RightArgConj(conj.token, arg)
grammar["part", "part"] = lambda part1, part2: Argument(part1.token + " " + part2.token, None, part1.plural or part2.plural)
grammar["arg", "part"] = lambda arg, part: Argument(arg.token + " " + part.token, arg.mod, arg.plural)
grammar["rel", "compconj"] = lambda rel, compconj: Relation(rel.token, rel.relatums, compconj.args)
grammar["rel", "rel"] = lambda rel1, rel2: rel2
grammar["mod", "rel"] = lambda mod, rel: rel
grammar["rel", "rargconj"] = lambda rel, rconj: Relation(rel.token, rel.relatums, rconj.conjoin(rel.referents[0]).args)
grammar["num", "arg"] = lambda num, arg: CompleteConj("and", [arg, arg]) if num.token == "two" \
                        else CompleteConj("and", [arg, arg, arg])

def parse(response):
    parse_stack = []
    response = response.lower().split()
        
    resp = [tokenize(item) for item in response if issubclass(type(tokenize(item)), Token)]
    response = []
    plural_marker = False
    for item in resp:
        if type(item) == Num or type(item) == Mod and item.det == "the":
            plural_marker = True
        if (type(item) == Argument or type(item) == Part) and len(response) > 0 and\
           (type(response[-1]) == Argument or type(response[-1]) == Part):
            response[-1] = Argument(response[-1].token + " " + item.token, None, item.plural)            
        else:
            response += [item]
     
    print ("RESP: {}".format(response))
    if response == []:
        return None
    idx = 0    
    current = response[0]
    while idx < len(response):
        if parse_stack != [] and (parse_stack[-1].signature(), current.signature()) in grammar:
            #print ("BEFORE. stack: {} current: {}".format(parse_stack[-1], current))
            current = grammar[(parse_stack[-1].signature(), current.signature())](parse_stack[-1], current)
            parse_stack.pop()
            #if parse_stack !=[]:
            #    print ("AFTER. stack: {} current: {}".format(parse_stack[-1], current))
        else:
            parse_stack += [current]
            idx += 1
            if idx < len(response):
                current = response[idx]
    for item in parse_stack:
        if type(item) is Relation and item.token is not None and item.referents is not []:
            item.relatums = [replace_args(arg) for arg in item.relatums]
            item.referents = [replace_args(arg) for arg in item.referents]
            return item
    return None





