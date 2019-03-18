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

        return output
        #return (self.content if isinstance(self.content, str) \
        #        else (self.content.__str__() if self.content is not None else "")) \
        #             + (" [" + " ".join([child.__str__() for child in self.children if child is not None]) + "]" if self.children is not None else "")

    def get_type(self):
        return str(type(self)).split("'")[1].split(".")[1]

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
grammar['between.p'] = lambda x: TPrep(x)
grammar['side-by-side-with.p'] = lambda x: TPrep(x)
grammar['on_top_of.p'] = lambda x: TPrep(x)

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
grammar['thing.n'] = lambda x: NArg(obj_type = None, obj_id = None)
grammar['{thing}.n'] = lambda x: NArg(obj_type = None, obj_id = None)


grammar['red.a'] = lambda x: TAdj(x)
grammar['green.a'] = lambda x: TAdj(x)
grammar['blue.a'] = lambda x: TAdj(x)

grammar['left.a'] = lambda x: TAdj(x)
grammar['right.a'] = lambda x: TAdj(x)
grammar['top.a'] = lambda x: TAdj(x)
grammar['high.a'] = lambda x: TAdj(x)
grammar['low.a'] = lambda x: TAdj(x)
grammar['last.a'] = lambda x: TAdj(x)
grammar['first.a'] = lambda x: TAdj(x)

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

grammar['which.d'] = lambda x: TDet(x)
grammar['the.d'] = lambda x: TDet(x)
grammar['a.d'] = lambda x: TDet(x)
grammar['other.d'] = lambda x: TDet(x)

grammar['|Nvidia|'] = lambda x: TName(x)
grammar['|Toyota|'] = lambda x: TName(x)
grammar['|McDonalds|'] = lambda x: TName(x)
grammar['|SRI|'] = lambda x: TName(x)
grammar['|Starbucks|'] = lambda x: TName(x)
grammar['|Texaco|'] = lambda x: TName(x)

grammar['|nvidia|'] = lambda x: TName(x)
grammar['|toyota|'] = lambda x: TName(x)
grammar['|mcdonalds|'] = lambda x: TName(x)
grammar['|sri|'] = lambda x: TName(x)
grammar['|starbucks|'] = lambda x: TName(x)
grammar['|texaco|'] = lambda x: TName(x)





#grammar[("TTenseMarker", "TCopulaBe")] = lambda x, y: NVerbHead(TCopulaBe, TTenseMarker)
grammar[("TSuperMarker", "TAdj")] = lambda x, y: TAdj(content = y.content, mod = x)

grammar[("TName", "NArg")] = lambda x, y: NArg(obj_type = y.obj_type, obj_id = x.content)
grammar[("TDet", "NArg")] = lambda x, y: NArg(obj_type = y.obj_type, obj_id = y.obj_id, mods = y.mods, det = x, plur = y.plur)
grammar[("TAdj", "NArg")] = lambda x, y: NArg(obj_type = y.obj_type, obj_id = y.obj_id, mods = y.mods + [x], det = y.det, plur = y.plur)
grammar[("TPlurMarker", "NArg")] = lambda x, y: NArg(obj_type = y.obj_type, obj_id = y.obj_id, mods = y.mods + [x], det = y.det, plur = True)


grammar[("TAdj", "TNoun")] = lambda x, y: NArg(obj_type = y.content, mods = [x])

grammar[("TName", "TNoun")] = lambda x, y: NArg(obj_type = x.content + " " + y.content)
grammar[("TPlur", "TNoun")] = lambda x, y: NArg(obj_type = y.content, plur = True)

grammar[("TDet", "TNoun")] = lambda x, y: NArg(obj_type = y.content, det = x)
grammar[("NArg", "TPrep", "NArg")] = lambda x, y, z: NRel(y.content, [x, z])
grammar[("TQ", "NRel")] = lambda x, y: NYesNo(y)

class NVerbHead(TreeNode):
    __name__ = "NVerbHead"
    
    def __init__(self, content, children=None):
        self.content = content
        self.children = children

class NRel(TreeNode):
    __name__ = "NRel"
    def __init__(self, token, args):
        self.content = token
        self.children = args

class TCopulaBe(TreeNode):
    __name__ = "TCopulaBe"
    def __init__(self, content=None):
        super(TCopulaBe, self).__init__(content, None)

    #def __str__(self):
    #    return "BE"
    
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

class TSubMarker(TreeNode):
    __name__ = "TSubMarker"
    def __init__(self):
        super().__init__(content, None)

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

class TName(TreeNode):
    __name__ = "TName"
    def __init__(self, content=None):
        super(TName, self).__init__(content, None)

class TPro(TreeNode):
    __name__ = "TPro"
    def __init__(self, content=None):
        super(TPro, self).__init__(content, None)

class TAdj(TreeNode):
    __name__ = "TAdj"
    def __init__(self, content=None, mod=None):
        super(TAdj, self).__init__(content, None)
        self.mod = mod

class TAdv(TreeNode):
    __name__ = "TAdv"
    def __init__(self, content=None):
        super(TAdv, self).__init__(content, None)

class TPred(TreeNode):
    __name__ = "TPred"
    def __init__(self, content=None):
        super(TPred, self).__init__(content, None)

class TUnknown(TreeNode):
    __name__ = "TUnknown"
    def __init__(self, content=None):
        super(TUnknown, self).__init__(content, None)

class NColl(TreeNode):
    def __init__(self, children):
        super(NColl, self).__init__(None, children)

class NYesNo(TreeNode):
    def __init__(self, content):
        super(NYesNo, self).__init__(content, None)

class NArg(TreeNode):
    __name__ = "NArg"
    def __init__(self, obj_type=None, obj_id=None, mods=[], det=None, plur=False):
        self.obj_type = obj_type
        self.obj_id = obj_id
        self.mods = mods
        self.det = det
        self.plur = plur

    def __str__(self):
        return self.obj_type+":\n" + self.obj_id.__str__() + "\n"+ self.mods.__str__() + "\n" +\
            self.det.__str__() + "\n" + self.plur.__str__()
    

    def printable(self):
        return (self.content if isinstance(self.content, str) \
                else (self.content.printable() if self.content is not None else "")) \
                     + "[[" + " ".join([x.printable() for x in self.mods if x is not None]) + "] "\
                     + (self.det.printable() if self.det is not None else "") + " " + str(self.plur) + "]"
    
    
       
class ULFQuery(object):
    def __init__(self, input):
        self.lispified = self.lispify(input)
        self.preprocessed = self.process_sub(self.lispified)
        self.query_tree = self.parse_tree(self.preprocessed)

    def terminal_node(self, token):
        if token in relations:
            return TPrep(token)
        elif '.d' in token or token == 'k':
            return TDet(token)
        elif '|' in token:
            return TName(token)
        elif '.pro' in token:
            return TPro(token)
        elif token == 'coll-of' or token == 'semval':
            return TPred(token)
        elif '.n' in token:
            return TNoun(token)
        elif token == '?':
            return TQ()
        elif token == 'plur':
            return TPlur()

    def parse_tree(self, tree):
        print ("INIT: ", tree)
        if type(tree) == str:
            if tree in grammar:
                #print (tree, grammar[tree])
                print ("PROC: ", tree)
                return grammar[tree](tree)
            else:
                print ("PROC: ", tree)
                return TUnknown(tree)

        tree = [self.parse_tree(node) for node in tree]

        if type(tree[0]) == TNModMarker:
            tree[1].mods += tree[2:]
            return tree[1]

        while len(tree) >= 2 and (tree[0].__name__, tree[1].__name__) in grammar:
            substitute = grammar[(tree[0].__name__, tree[1].__name__)](tree[0], tree[1])
            #print("result: ", substitute)
            tree[0] = substitute

        print ("PROC: ", tree)
        return tree[0] #if len(tree) == 1 else tree

    def process_sub(self, tree, expr=None):
        if type(tree) == list:
            if tree[0] == 'sub':
                return self.process_sub(tree[2], tree[1])
            else:
                return [self.process_sub(branch, expr) for branch in tree]
        else:
            return expr if (tree == "*h" and expr is not None) else tree

        '''       
        if type(tree) != list:
            return self.terminal_node(tree)
        else:
            old_tree = tree
            tree = list(map(self.parse_tree, tree))            
            print ("TOKEN_TREE:", old_tree, "\nSYMBOL_TREE:", tree, "\n:TREE_CONTENT:", " ".join([x.printable() for x in tree]),"\n")
        if tree[0].get_type() == "TQ":
            return NYesNo(tree[1])
        elif len(tree) == 2:
            if (tree[0].get_type(), tree[1].get_type()) in grammar:               
                print("result:", grammar[(tree[0].get_type(), tree[1].get_type())](tree[0], tree[1]).printable())
                return grammar[(tree[0].get_type(), tree[1].get_type())](tree[0], tree[1])
        elif len(tree) == 3:
            if (tree[0].get_type(), tree[1].get_type(), tree[2].get_type()) in grammar:
                print("result:", grammar[(tree[0].get_type(), tree[1].get_type(), tree[2].get_type())](tree[0], tree[1], tree[2]).printable())
                return grammar[(tree[0].get_type(), tree[1].get_type(), tree[2].get_type())](tree[0], tree[1], tree[2])'''
        
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
             
    def parse(self, input):
        current = ""
        nodes = []        
        for char in input:
            if char == '(':
                pass
            elif char == ' ':
                if current != "":
                    nodes += [TreeNode(current)]
                    current = ""                    
            else:
                current += char                

        if input[0] == '(':
            nodes += [self.parse(input[1:])]
        elif input[0] == ')':
            return TreeNode(None, nodes)



def lispify(input):
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
             

'''
str = "(? ((the.d (|SRI|.n block.n)) on.p (the.d (|Target|.n block.n))))"
str = "(? ((some.d block.n) on.p (the.d (|Target|.n block.n))))"
str = "((what.d block.n) on.p (the.d (|SRI|.n block.n)))"
str = "((the.d (|SRI|.n block.n)) on.p what.pro)"
str = "((coll-of |B1| |B2| |B3|) (semval (what.d shape-pred.n)))"
query = ULFQuery(str)
print (query.query)
'''
f = open("sqa_input.bw")
for ulf in f.readlines():
    ulf = ulf.lower().strip()
    if ";;" not in ulf and ulf != "":
        print (ulf)
        query = ULFQuery(ulf)
        print (query.preprocessed)
        print (query.query_tree)
        #break

#det = Det("test", ["children"])
#print(det.printable())
