class TreeNode(object):
    def __init__(self, content=None, children=None):
        self.content = content
        self.children = children

    def printable(self):
        return (self.content if isinstance(self.content, str) \
                else (self.content.printable() if self.content is not None else "")) \
                     + (" [" + " ".join([child.printable() for child in self.children if child is not None]) + "]" if self.children is not None else "")

    def get_type(self):
        return str(type(self)).split("'")[1].split(".")[1]

relations = ['on.p', 'to_the_left_of.p', 'to_the_right_of.p', 'in_front_of.p', 'behind.p', 'above.p', 'below.p', 'over.p', 'under.p', 'near.p', 'touching.p', 'at.p', 'between.p']

grammar = {}

grammar[("TAdj", "TNoun")] = lambda x, y: NArg(name = y.content, mods = [x])
grammar[("TAdj", "NArg")] = lambda x, y: NArg(name = y.content, mods = y.mods + [x], det = y.det, plur = y.plur)

grammar[("TName", "TNoun")] = lambda x, y: NArg(name = x.content + " " + y.content)
grammar[("TPlur", "TNoun")] = lambda x, y: NArg(name = y.content, plur = True)

grammar[("TDet", "NArg")] = lambda x, y: NArg(name = y.content, mods = y.mods, det = x, plur = y.plur)
grammar[("TDet", "TNoun")] = lambda x, y: NArg(name = y.content, det = x)
grammar[("NArg", "TPrep", "NArg")] = lambda x, y, z: NRel(y.content, [x, z])
grammar[("TQ", "NRel")] = lambda x, y: NYesNo(y)



class NRel(TreeNode):
    def __init__(self, token, args):
        self.content = token
        self.children = args
    
class Block(object):
    def __init__(self, token):
        self.block = token

class TDet(TreeNode):
    def __init__(self, content=None):
        super(TDet, self).__init__(content, None)

class TPrep(TreeNode):
    def __init__(self, content=None):
        super(TPrep, self).__init__(content, None)

class TNoun(TreeNode):
    def __init__(self, content=None):
        super(TNoun, self).__init__(content, None)

class TName(TreeNode):
    def __init__(self, content=None):
        super(TName, self).__init__(content, None)

class TPro(TreeNode):
    def __init__(self, content=None):
        super(TPro, self).__init__(content, None)

class TAdj(TreeNode):
    def __init__(self, content=None):
        super(TAdj, self).__init__(content, None)

class TPlur(TreeNode):
    def __init__(self):
        pass

    def printable(self):
        return "plur"

class TPred(TreeNode):
    def __init__(self, content=None):
        super(TPred, self).__init__(content, None)

class TQ(TreeNode):
    def __init__(self):
        pass

    def printable(self):
        return "?"


class NColl(TreeNode):
    def __init__(self, children):
        super(NColl, self).__init__(None, children)

class NYesNo(TreeNode):
    def __init__(self, content):
        super(NYesNo, self).__init__(content, None)

class NArg(TreeNode):
    def __init__(self, name=None, mods=[], det=None, plur=False):
        self.content = name
        self.mods = mods
        self.det = det
        self.plur = plur

    def printable(self):
        return (self.content if isinstance(self.content, str) \
                else (self.content.printable() if self.content is not None else "")) \
                     + "[[" + " ".join([x.printable() for x in self.mods if x is not None]) + "] "\
                     + (self.det.printable() if self.det is not None else "") + " " + str(self.plur) + "]"
    
    
       
class ULFQuery(object):
    def __init__(self, input):
        self.query = self.parse_tree(self.lispify(input))

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
        #print ("TREE:", tree)
        if type(tree) != list:
            return self.terminal_node(tree)
        else:
            old_tree = tree
            tree = list(map(self.parse_tree, tree))            
            print ("TOKEN_TREE:", old_tree, "\nSYMBOL_TREE:", tree, "\n:TREE_CONTENT:", " ".join([x.printable() for x in tree]),"\n")
        if tree[0].get_type() == "TQ":
            return NYesNo(tree[1])
        elif len(tree) == 2:
            #print (tree)
            if (tree[0].get_type(), tree[1].get_type()) in grammar:               
                print("result:", grammar[(tree[0].get_type(), tree[1].get_type())](tree[0], tree[1]).printable())
                return grammar[(tree[0].get_type(), tree[1].get_type())](tree[0], tree[1])
        elif len(tree) == 3:
            if (tree[0].get_type(), tree[1].get_type(), tree[2].get_type()) in grammar:
                print("result:", grammar[(tree[0].get_type(), tree[1].get_type(), tree[2].get_type())](tree[0], tree[1], tree[2]).printable())
                return grammar[(tree[0].get_type(), tree[1].get_type(), tree[2].get_type())](tree[0], tree[1], tree[2])      
        
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

'''
str = "(? ((the.d (|SRI|.n block.n)) on.p (the.d (|Target|.n block.n))))"
str = "(? ((some.d block.n) on.p (the.d (|Target|.n block.n))))"
str = "((what.d block.n) on.p (the.d (|SRI|.n block.n)))"
str = "((the.d (|SRI|.n block.n)) on.p what.pro)"
str = "((coll-of |B1| |B2| |B3|) (semval (what.d shape-pred.n)))"
query = ULFQuery(str)
print (query.query)
'''

#det = Det("test", ["children"])
#print(det.printable())
