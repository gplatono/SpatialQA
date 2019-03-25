from collections import defaultdict

class TreeNode(object):
    __name__ = "TreeNode"
    def __init__(self, content=None, children=None):
        self.content = content
        self.children = children

    def __str__(self):
        if self.content is None and self.__name__ != "NArg":
            return self.__name__
        output = self.__name__ + ": "
        if type(self.content) == str:
            output += self.content
        elif self.content is not None:
            output += self.content.__str__()

        if type(self.children) == list and len(self.children) > 0:
            output += "[" + ";".join([child.__str__() for child in self.children]) + "]"
        return output

relations = ['on.p', 'to_the_left_of.p', 'to_the_right_of.p', 'in_front_of.p', 'behind.p', 'above.p', 'below.p', 'over.p', 'under.p', 'near.p', 'touching.p', 'at.p', 'between.p',
             'side-by-side-with.p', 'on_top_of.p']

grammar = {}

grammar['on.p'] = lambda x: TPrep(x)
grammar['to_the_left_of.p'] = lambda x: TPrep(x)
grammar['to_the_right_of.p'] = lambda x: TPrep(x)
grammar['in_front_of.p'] = lambda x: TPrep(x)
grammar['behind.p'] = lambda x: TPrep(x)
grammar['above.p'] = lambda x: TPrep(x)
grammar['below.p'] = lambda x: TPrep(x)
grammar['over.p'] = lambda x: TPrep(x)
grammar['under.p'] = lambda x: TPrep(x)
grammar['near.p'] = lambda x: TPrep(x)
grammar['touching.p'] = lambda x: TPrep(x)
grammar['at.p'] = lambda x: TPrep(x)
grammar['in.p'] = lambda x: TPrep(x)
grammar['between.p'] = lambda x: TPrep(x)
grammar['side_by_side_with.p'] = lambda x: TPrep(x)
grammar['on_top_of.p'] = lambda x: TPrep(x)

grammar['touch.v'] = lambda x: TPrep(x)
grammar['contain.v'] = lambda x: TPrep(x)
grammar['face.v'] = lambda x: TPrep(x)
grammar['color.n'] = lambda x: TPrep(x)

grammar['halfway.adv-a'] = lambda x: TAdv(x)
grammar['slightly.adv-a'] = lambda x: TAdv(x)
grammar['directly.adv-a'] = lambda x: TAdv(x)

#grammar['block.n'] = lambda x: TNoun(x)
#grammar['{block}.n'] = lambda x: TNoun(x)
grammar['block.n'] = lambda x: NArg(obj_type = x)
grammar['{block}.n'] = lambda x: NArg(obj_type = x)
grammar['table.n'] = lambda x: NArg(obj_type = x, obj_id = "TABLE")
grammar['stack.n'] = lambda x: NArg(obj_type = x, obj_id = "STACK")
grammar['row.n'] = lambda x: NArg(obj_type = x, obj_id = "STACK")
grammar['thing.n'] = lambda x: NArg(obj_type = x, obj_id = None)
grammar['{thing}.n'] = lambda x: NArg(obj_type = x, obj_id = None)
grammar['what.pro'] = lambda x: NArg()

grammar['corner-of.n'] = lambda x: TRelNoun(x)
grammar['edge-of.n'] = lambda x: TRelNoun(x)
grammar['side-of.n'] = lambda x: TRelNoun(x)
grammar['center-of.n'] = lambda x: TRelNoun(x)
grammar['middle-of.n'] = lambda x: TRelNoun(x)
grammar['part-of.n'] = lambda x: TRelNoun(x)
grammar['height-of.n'] = lambda x: TRelNoun(x)
grammar['length-of.n'] = lambda x: TRelNoun(x)



grammar['how.mod-a'] = lambda x: TAdvAdjMod(x)
grammar['very.mod-a'] = lambda x: TAdvAdjMod(x)
grammar['halfway.mod-a'] = lambda x: TAdvAdjMod(x)
grammar['slightly.mod-a'] = lambda x: TAdvAdjMod(x)
grammar['directly.mod-a'] = lambda x: TAdvAdjMod(x)


grammar['red.a'] = lambda x: TAdj(x)
grammar['green.a'] = lambda x: TAdj(x)
grammar['blue.a'] = lambda x: TAdj(x)
grammar['clear.a'] = lambda x: TAdj(x)

grammar['left.a'] = lambda x: TAdj(x)
grammar['right.a'] = lambda x: TAdj(x)
grammar['top.a'] = lambda x: TAdj(x)
grammar['front.a'] = lambda x: TAdj(x)
grammar['back.a'] = lambda x: TAdj(x)
grammar['high.a'] = lambda x: TAdj(x)
grammar['low.a'] = lambda x: TAdj(x)
grammar['last.a'] = lambda x: TAdj(x)
grammar['first.a'] = lambda x: TAdj(x)
grammar['short.a'] = lambda x: TAdj(x)
grammar['long.a'] = lambda x: TAdj(x)
grammar['middle.a'] = lambda x: TAdj(x)
grammar['tall.a'] = lambda x: TAdj(x)
grammar['many.a'] = lambda x: TAdj(x)
grammar['far.a'] = lambda x: TAdj(x)

grammar['one.a'] = lambda x: TNumber(x)
grammar['one.d'] = lambda x: TNumber(x)
grammar['two.a'] = lambda x: TNumber(x)
grammar['two.d'] = lambda x: TNumber(x)
grammar['three.a'] = lambda x: TNumber(x)
grammar['three.d'] = lambda x: TNumber(x)
grammar['few.a'] = lambda x: TNumber(x)
grammar['several.a'] = lambda x: TNumber(x)


grammar['plur'] = lambda x: TPlurMarker()
grammar['pres'] = lambda x: TTenseMarker()
grammar['be.v'] = lambda x: TCopulaBe()
grammar['nquan'] = lambda x: TQuanMarker()
grammar['fquan'] = lambda x: TQuanMarker()
grammar['most-n'] = lambda x: TSuperMarker()
grammar['most'] = lambda x: TSuperMarker()
grammar['sub'] = lambda x: TSubMarker()
grammar['?'] = lambda x: TQMarker()
grammar['n+preds'] = lambda x: TNModMarker()
grammar['prog'] = lambda x: TAspectMarker(prog=True, perf=False)
grammar['perf'] = lambda x: TAspectMarker(prog=False, perf=True)
grammar['k'] = lambda x: TNReifierMarker()
grammar['='] = lambda x: TEqualsMarker()


grammar['that.rel'] = lambda x: TRelativizer(content=x)

grammar['which.d'] = lambda x: TDet(x)
grammar['the.d'] = lambda x: TDet(x)
grammar['a.d'] = lambda x: TDet(x)
grammar['other.d'] = lambda x: TDet(x)
grammar['every.d'] = lambda x: TDet(x)
grammar['other.a'] = lambda x: TDet(x)
grammar['any.d'] = lambda x: TDet(x)
grammar['some.d'] = lambda x: TDet(x)
grammar['what.d'] = lambda x: TDet(x)
grammar['all.d'] = lambda x: TDet(x)

grammar['|Nvidia|'] = lambda x: TName(x)
grammar['|Toyota|'] = lambda x: TName(x)
grammar['|McDonalds|'] = lambda x: TName(x)
grammar['|SRI|'] = lambda x: TName(x)
grammar['|Starbucks|'] = lambda x: TName(x)
grammar['|Texaco|'] = lambda x: TName(x)
grammar['|Target|'] = lambda x: TName(x)
grammar['|nvidia|'] = lambda x: TName(x)
grammar['|toyota|'] = lambda x: TName(x)
grammar['|mcdonalds|'] = lambda x: TName(x)
grammar['|sri|'] = lambda x: TName(x)
grammar['|starbucks|'] = lambda x: TName(x)
grammar['|texaco|'] = lambda x: TName(x)
grammar['|target|'] = lambda x: TName(x)
grammar['|nvidia|.n'] = lambda x: TName(x)
grammar['|toyota|.n'] = lambda x: TName(x)
grammar['|mcdonalds|.n'] = lambda x: TName(x)
grammar['|sri|.n'] = lambda x: TName(x)
grammar['|starbucks|.n'] = lambda x: TName(x)
grammar['|texaco|.n'] = lambda x: TName(x)
grammar['|target|.n'] = lambda x: TName(x)


grammar['not.adv-s'] = lambda x: TNeg()

grammar['or.cc'] = lambda x: TConj(x)
grammar['and.cc'] = lambda x: TConj(x)

#Verb + tense/aspect rules
grammar[("TTenseMarker", "TCopulaBe")] = lambda x, y: NVP(content=y, children=[NVerbParams(tense=x)])
grammar[("NVerbParams", "TCopulaBe")] = lambda x, y: NVP(content=y, children=[x])
grammar[("TTenseMarker", "TVerb")] = lambda x, y: NVP(content=y, children=[NVerbParams(tense=x)] + y.children)
grammar[("NVerbParams", "TVerb")] = lambda x, y: NVP(content=y, children=[x] + y.children)

grammar[("TAspectMarker", "TAspectMarker")] = lambda x, y: TAspectMarker(prog = x.prog or y.prog, perf = x.perf or y.perf)
grammar[("TTenseMarker", "TAspectMarker")] = lambda x, y: NVerbParams(tense = x, aspect = y)


#Adjective modifier rules
grammar[("TSuperMarker", "TAdj")] = lambda x, y: TAdj(content = y.content, mod = x)
grammar[("TAdvAdjMod", "TAdj")] = lambda x, y: TAdj(content = y.content, mod = x)

#Determiner rules
grammar[("TQuanMarker", "TAdj")] = lambda x, y: NDet(y) if (y.content != "many.a" or y.mod is None or y.mod.content != "how.mod-a") else NCardDet()


#Argument + modifier rules
grammar[("TName", "NArg")] = lambda x, y: NArg(obj_type = y.obj_type, obj_id = x.content)
grammar[("TDet", "NArg")] = lambda x, y: NArg(obj_type = y.obj_type, obj_id = y.obj_id, mods = y.mods, det = x, plur = y.plur)
grammar[("NDet", "NArg")] = lambda x, y: NArg(obj_type = y.obj_type, obj_id = y.obj_id, mods = y.mods, det = x, plur = y.plur)
grammar[("NCardDet", "NArg")] = lambda x, y: NArg(obj_type = y.obj_type, obj_id = y.obj_id, mods = y.mods, det = x, plur = y.plur)

grammar[("TAdj", "NArg")] = lambda x, y: NArg(obj_type = y.obj_type, obj_id = y.obj_id, mods = y.mods + [x], det = y.det, plur = y.plur)
grammar[("TPlurMarker", "NArg")] = lambda x, y: NArg(obj_type = y.obj_type, obj_id = y.obj_id, mods = y.mods, det = y.det, plur = True)
grammar[("TNReifierMarker", "NArg")] = lambda x, y: y

grammar[("TRelNoun", "NArg")] = lambda x, y: NArg(obj_type = x.content[:-5], obj_id = x.content[:-5].upper(), mods = [y])


grammar[("TNumber", "NArg")] = lambda x, y: NArg(obj_type = y.obj_type, obj_id = y.obj_id, mods = y.mods + [x], det = y.det, plur = y.plur)

grammar[("TConj", "NArg")] = lambda x, y: NConjArg(x, children = [y])
grammar[("NArg", "TConj")] = lambda x, y: NConjArg(y, children = [x])
grammar[("Narg", "NConjArg")] = lambda x, y: NConjArg(y.content, children = y.children + [x])
grammar[("NConjArg", "NArg")] = lambda x, y: NConjArg(x.content, children = x.children + [y])

grammar[("TEqualsMarker", "NArg")] = lambda x, y: y


#Relational rules
grammar[("TPrep", "NArg")] = lambda x, y: NRel(x, children=[y])
grammar[("TPrep", "NConjArg")] = lambda x, y: NRel(x, children=[y])
grammar[("TNeg", "NRel")] = lambda x, y: NRel(y.content, y.children, neg=True)
grammar[("NArg", "NRel")] = lambda x, y: NRel(content=y.content, children=[x]+y.children, neg = y.neg)
grammar[("NConjArg", "NRel")] = lambda x, y: NRel(content=y.content, children=[x]+y.children, neg = y.neg)

grammar[("NVP", "NRel")] = lambda x, y: y
grammar[("NVerbParams", "NRel")] = lambda x, y: y

grammar[("NVP", "TAdj")] = lambda x, y: NRel(y, children=[])

grammar[("TAdv", "NRel")] = lambda x, y: NRel(y.content, y.children, y.neg, y.mods + [x])

grammar[("TDet", "TPrep")] = lambda x, y: y
grammar[("TAdj", "TPrep")] = lambda x, y: y




#Sentence-level rules
grammar[("NRel", "TQMarker")] = lambda x, y: NSentence(x, True)
class TRelativizer(TreeNode):
    __name__ = "TRelativizer"
    def __init__(self, content=None):
        super().__init__(content, None)


class TCopulaBe(TreeNode):
    __name__ = "TCopulaBe"
    def __init__(self, content=None):
        super(TCopulaBe, self).__init__(content, None)

class TPlurMarker(TreeNode):
    __name__ = "TPlurMarker"
    def __init__(self):
        super(TPlurMarker, self).__init__(None, None)

class TQuanMarker(TreeNode):
    __name__ = "TQuanMarker"
    def __init__(self):
        super(TQuanMarker, self).__init__(None, None)

class TSuperMarker(TreeNode):
    __name__ = "TSuperMarker"
    def __init__(self, content=None):
        super(TSuperMarker, self).__init__(None, None)

class TNReifierMarker(TreeNode):
    __name__ = "TNReifierMarker"
    def __init__(self):
        super(TNReifierMarker, self).__init__()

class TAspectMarker(TreeNode):
    __name__ = "TAspectMarker"
    def __init__(self, prog=False, perf=False):
        super(TAspectMarker, self).__init__(None, None)
        self.prog = prog
        self.perf = perf

    def __str__(self):
        return "PROG=" + str(self.prog) + ":PERF=" + str(self.perf)

class TSubMarker(TreeNode):
    __name__ = "TSubMarker"
    def __init__(self):
        super().__init__(content, None)

class TEqualsMarker(TreeNode):
    __name__ = "TEqualsMarker"
    def __init__(self):
        super().__init__(None, None)

class TNeg(TreeNode):
    __name__ = "TNeg"
    def __init__(self):
        super().__init__(None, None)

    def __str__(self):
        return "NOT"

class TTenseMarker(TreeNode):
    __name__ = "TTenseMarker"
    def __init__(self, content=None):
        super().__init__(content, None)

class TQMarker(TreeNode):
    __name__ = "TQMarker"
    def __init__(self):
        super().__init__()

    def __str__(self):
        return "?"

class TNModMarker(TreeNode):
    __name__ = "TNModMarker"
    def __init__(self, content=None):
        super(TNModMarker, self).__init__()
      
class TDet(TreeNode):
    __name__ = "TDet"
    def __init__(self, content=None):
        super(TDet, self).__init__(content, None)

class TPrep(TreeNode):
    __name__ = "TPrep"
    def __init__(self, content=None):
        super(TPrep, self).__init__(content, None)

class TNoun(TreeNode):
    __name__ = "TNoun"
    def __init__(self, content=None):
        super(TNoun, self).__init__(content, None)

class TRelNoun(TreeNode):
    __name__ = "TRelNoun"
    def __init__(self, content=None):
        super(TRelNoun, self).__init__(content, None)

class TAdvAdjMod(TreeNode):
    __name__ = "TAdvAdjMod"
    def __init__(self, content=None):
        super(TAdvAdjMod, self).__init__(content, None)

class TName(TreeNode):
    __name__ = "TName"
    def __init__(self, content=None):
        super(TName, self).__init__(content, None)

class TPro(TreeNode):
    __name__ = "TPro"
    def __init__(self, content=None):
        super(TPro, self).__init__(content, None)

class TNumber(TreeNode):
    __name__ = "TNumber"
    def __init__(self, content=None):
        super(TNumber, self).__init__(content, None)

class TAdj(TreeNode):
    __name__ = "TAdj"
    def __init__(self, content, mod=None):
        super(TAdj, self).__init__(content, None)
        self.mod = mod

class TAdv(TreeNode):
    __name__ = "TAdv"
    def __init__(self, content=None):
        super(TAdv, self).__init__(content, None)

class TConj(TreeNode):
    __name__ = "TConj"
    def __init__(self, content=None):
        super(TConj, self).__init__(content, None)

class TUnknown(TreeNode):
    __name__ = "TUnknown"
    def __init__(self, content=None):
        super(TUnknown, self).__init__(content, None)

class NVerbParams(TreeNode):
    __name__ = "NVerbParams"    
    def __init__(self, tense=None, aspect=None):
        self.tense = tense
        self.aspect = aspect

    def __str__(self):
        return self.tense.__str__() + ":" + self.aspect.__str__()

class NDet(TreeNode):
    __name__ = "NDet"
    def __init__(self, content=None):
        super(NDet, self).__init__(content, None)

class NCardDet(TreeNode):
    __name__ = "NCardDet"
    def __init__(self):
        super(NCardDet, self).__init__(None, None)

    def __str__(self):
        return "HOWMANY"

class NVP(TreeNode):
    __name__ = "NVP"
    def __init__(self, content, children=[]):
        self.content = content
        self.children = children
        

class NRel(TreeNode):
    __name__ = "NRel"
    def __init__(self, content, children=None, neg=False, mods=[]):
        super().__init__(content, None)
        self.content = content
        self.children = children
        self.neg = neg
        self.mods = mods

    def __str__(self):
        output = "RELATION={"
        if self.neg == True:
            output += "NOT "
        for mod in self.mods:
            output += ": " + mod.__str__()
        output += self.content.__str__()
        for idx in range(len(self.children)):
            output += "\nARG" + str(idx) + " " + self.children[idx].__str__()
        output += "\n}"
        return output
        

class NConjArg(TreeNode):
    __name__ = "NConjArg"
    def __init__(self, content, children=None):
        super().__init__(content, None)
        self.content = content
        self.children = children

class NArg(TreeNode):
    __name__ = "NArg"
    def __init__(self, obj_type=None, obj_id=None, mods=[], det=None, plur=False):
        super(NArg, self).__init__(None, None)
        self.obj_type = obj_type
        self.obj_id = obj_id
        self.mods = mods
        self.det = det
        self.plur = plur

    def __str__(self):
        if self.mods is not None:
            for item in self.mods:
                if item is not None and hasattr(item, "children") and item.children is not None and self in item.children:
                    print ("ERROR!!!: ", self.content, item.content)
                    return ""
        output = "ARGUMENT={" + str(self.obj_type)+"; " + str(self.obj_id) + "; " + str(self.det) + "; " + str(self.plur) + "; ["
        for mod in self.mods:
            output += mod.__str__() + ", "
        output+= "]}"
        return output
    

class NSentence(TreeNode):
    __name__ = "NSentence"
    def __init__(self, content, is_question=True):
        super().__init__(content, None)
        self.content = content
        self.is_question = is_question
  
       
class ULFQuery(object):
    def __init__(self, input):
        input = self.preprocess(input)
        self.query_tree = self.parse_tree(input)

    def preprocess(self, ulf):
        ulf = self.lispify(ulf)
        print ("QUERY: ", ulf)
        ulf = self.process_sub_rep(ulf)
        print ("PRECONJPROP QUERY: ", ulf)
        ulf = self.propagate_conj(ulf, [])[0]
        print ("PREPROC QUERY: ", ulf, "\n")        
        return ulf

    def parse_tree(self, tree):
        if type(tree) == str:
            if tree in grammar:
                return grammar[tree](tree)
            else:
                print ("UNKNOWN!!! - " + tree)
                return TUnknown(tree)

        #print ("INITIAL TREE: ", tree)
        tree = [self.parse_tree(node) for node in tree]
        
        if type(tree[0]) == TNModMarker:
            tree[1].mods += tree[2:]
            return tree[1]

        while len(tree) >= 2 and (tree[0].__name__, tree[1].__name__) in grammar:
           # if tree[0].__name__ == "NArg" and tree[1].__name__ == "NRel" and tree[1] in tree[0].mods:
           #     print ("ERROR!!!: ",tree[0],tree[1])
            substitute = grammar[(tree[0].__name__, tree[1].__name__)](tree[0], tree[1])
            tree = [substitute] + tree[2:]

        while len(tree) >= 2 and (tree[-2].__name__, tree[-1].__name__) in grammar:
            substitute = grammar[(tree[-2].__name__, tree[-1].__name__)](tree[-2], tree[-1])
            tree = tree[:-3] + [substitute]

        print ("TREE:", tree)
        print ("\n".join([node.__str__() for node in tree]))

        #print ("PROC: ", tree)
        return tree[0]

    def process_sub(self, tree, sub_expr=None):
        if type(tree) == list:
            if tree[0] == 'sub':
                return self.process_sub(tree[2], tree[1])
            else:
                return [self.process_sub(branch, sub_expr) for branch in tree]
        else:
            return sub_expr if (tree == "*h" and sub_expr is not None) else tree

    def process_sub_rep(self, tree, sub_expr=None, rep_expr=None):
        if type(tree) == list:
            if tree[0] == 'sub':
                return self.process_sub_rep(tree[2], tree[1], rep_expr)
            elif tree[0] == "rep":
                return self.process_sub_rep(tree[1], sub_expr, tree[2])
            else:
                return [self.process_sub_rep(branch, sub_expr, rep_expr) for branch in tree]
        else:
            return sub_expr if (tree == "*h" and sub_expr is not None) else \
                rep_expr if (tree == "*p" and rep_expr is not None) else tree

    def lispify(self, input):
        stack = []
        current = []
        token = ""
        for char in input:
            if char == '(':
                stack.append(current)
                current = []
            elif char == ')':
                if token != "":
                    current += [token]
                    token = ""                
                if (len(stack) > 0):
                    stack[-1].append(current)
                    current = stack[-1]
                    stack.pop()                    
            elif char == ' ':
                if token != "":
                    current += [token]
                    token = ""
            else:
                token += char
        return current[0]

    def propagate_conj(self, ulf, prefix=[]):
        if type(ulf) == str and ".cc" not in ulf:
            return (ulf, False)
        for item in ulf:
            if ".cc" in item:
                ulf.remove(item)
                ret_val = [item]
                for token in ulf:                    
                    for pref_item in prefix:
                        token = [pref_item, token]
                    ret_val += [token]
                return (ret_val, True)
        
        if (ulf[0][-2:] == ".a" or ulf[0][-2:] == ".d"):
            ret_val, val = self.propagate_conj(ulf[1], [ulf[0]] + prefix)
            if val == True:
                return (ret_val, True)
            else:
                return (ulf, False)

        return ([self.propagate_conj(item, prefix)[0] for item in ulf], False)
                     
f = open("sqa_input.bw")
test = ["the.d", ["red.a", ["block.n", "or.cc", "stack.n"]]]
test2 = ["sub", ["what.d", "color.n"], [["pres", "be.v"], ["rep", [["farthest.a", "*p"], "block.n"], ["to.p", ["the.d", "right.n"]]], "*h"]]
ulfs = f.readlines()
for ulf in ulfs:
    #print (ulf)
    print ("\n" + str(1 + ulfs.index(ulf)) + " out of " + str(len(ulfs)))
    ulf = ulf.lower().strip().replace("{", "").replace("}", "")
    if ";;" not in ulf and ulf != "":
        #print (ulf)
        query = ULFQuery(ulf)
        print (query.query_tree)
        #print (query.process_sub_rep(test2))
        input("Press Enter to continue...")
