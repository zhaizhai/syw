class Function:
    def __init__(self, name, fn, num_args, notation=None):
        self.name = name
        self.fn = fn
        self.num_args = num_args
        self.notation = notation

        if self.notation is None:
            self.notation = [name + '('] 
            for x in zip(range(num_args), [','] * (num_args - 1) + [')']):
                self.notation.extend(x)

    def eval(self, *args):
        return self.fn(*args)

class RefTable:
    def __init__(self):
        self.vars = {}

    def add_variable(self, var, binding):
        self.vars[var] = binding

    def get_variable(self, var):
        if var in self.vars:
            return self.vars[var]
        return None

    def reverse_lookup(self, val):
        for var in self.vars:
            if self.vars[var] is val:
                return var
        return None

    def clear(self):
        self.vars = {}


class Node:
    def __init__(self, parent=None):
        self.parent = parent
        self.children = []

    def name(self):
        raise NotImplementedError()        

    def copy(self):
        raise NotImplementedError()

    def recurse(self, fn, depth=0):
        for child in self.children:
            child.recurse(fn, depth=depth+1)
        fn(self, depth=depth)

    def substitute(self, replacement):
        assert self.parent is not None
        replacement.parent = self.parent
        for i, c in enumerate(self.parent.children):
            if c is self:
                self.parent.children[i] = replacement
                return
        assert False

    def validate(self):
        for child in self.children:
            assert child.parent is self
            child.validate()

class ValueNode(Node):
    def __init__(self, value, **kw):
        Node.__init__(self, **kw)
        self.value = value

    def name(self):
        if not isinstance(self.value, str):
            return 'const'
        return self.value

    def copy(self):
        return ValueNode(self.value)

class FunctionNode(Node):
    def __init__(self, fn, **kw):
        Node.__init__(self, **kw)
        self.fn = fn
        self.children = [None] * fn.num_args

    def name(self):
        return self.fn.name

    def copy(self):
        cp = FunctionNode(self.fn)
        for i, arg in enumerate(self.children):
            if arg:
                cp.children[i] = arg.copy()
                cp.children[i].parent = cp
        return cp

def get_ancestry(n):
    if n is None:
        return []
    return get_ancestry(n.parent) + [n]

def lca(n1, n2):
    anc1 = get_ancestry(n1)
    anc2 = get_ancestry(n2)
    
    ret = None
    for x1, x2 in zip(anc1, anc2):
        if x1 is not x2:
            break
        ret = x1
    return ret

def parse_helper(s, fn_table):
    # returns (node, remaining string)

    s = s.replace(' ', '')

    delim = 0
    while delim < len(s) and s[delim] not in ['(', ',', ')']:
        delim += 1
    delim_char = s[delim] if delim < len(s) else None

    if delim == 0:
        return parse_helper(s[1:], fn_table)

    if delim_char == '(':
        # function token
        left = s.find('(')
        name = s[:left]
        s = s[left + 1:]

        children = []
        while s[0] != ')':
            node, s = parse_helper(s, fn_table)
            children.append(node)
        
        ret = FunctionNode(fn_table.get_variable(name))
        ret.children = children
        for child in children:
            child.parent = ret
        return (ret, s[1:])
    else:
        right = 0
        while right < len(s) and s[right].isalnum():
            right += 1
        return (ValueNode(s[:right]), s[right:])
        
def parse(s, fn_table):
    ret, left = parse_helper(s, fn_table)
    assert left == ''
    return ret

