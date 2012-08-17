class Function(object):
    def __init__(self, name, fn, num_args):
        self.name = name
        self.fn = fn
        self.num_args = num_args
        
    def eval(self, *args):
        return self.fn(*args)

class RefTable(object):
    def __init__(self):
        self.vars = {}

    def add_variable(self, var, binding):
        self.vars[var] = binding

    def get_variable(self, var):
        if var in self.vars:
            return self.vars[var]
        return None

    def keys(self):
        return self.vars.keys()

    def values(self):
        return self.vars.values()

    def reverse_lookup(self, val):
        for var in self.vars:
            if self.vars[var] is val:
                return var
        return None

    def clear(self):
        self.vars = {}


class Node(object):
    def __init__(self, parent=None):
        self.parent = parent
        self.children = []

    def name(self):
        raise NotImplementedError()        

    def copy(self):
        raise NotImplementedError()

    def get_ix_in_parent(self):
        if self.parent is None:
            return None
        for i, child in enumerate(self.parent.children):
            if child is self:
                return i
        raise Exception("Couldn't find self in parent's children!")

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
        super(ValueNode, self).__init__(**kw)
        self.value = value

    def __repr__(self):
        return self.name()

    def name(self):
        if not isinstance(self.value, str):
            return 'const'
        return self.value

    def copy(self):
        return ValueNode(self.value)

class FunctionNode(Node):
    def __init__(self, fn, **kw):
        super(FunctionNode, self).__init__(**kw)
        self.fn = fn
        self.children = ([None] * fn.num_args
                         if fn.num_args is not None else
                         [])

    def __repr__(self):
        return self.name()

    def name(self):
        return self.fn.name

    def copy(self):
        cp = FunctionNode(self.fn)
        cp.children = [None] * len(self.children)
        for i, arg in enumerate(self.children):
            if arg:
                cp.children[i] = arg.copy()
                cp.children[i].parent = cp
        return cp

class VarArgsNode(Node):
    def __init__(self, var_name, pattern=None, **kw):
        super(VarArgsNode, self).__init__(**kw)
        self.var_name = var_name
        self.pattern = pattern or ValueNode(var_name)

    def __repr__(self):
        return '*' + self.pattern.name()

    def name(self):
        return self.var_name

    def copy(self):
        return VarArgsNode(self.var_name, pattern=self.pattern.copy())

    
def print_node(node, depth=0):
    print '--' * depth, node
    for n in node.children:
        print_node(n, depth=(depth + 1))

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

def make_var_args_node(root):

    def replace_var_arg(node):
        if isinstance(node, VarArgsNode):
            var_name = node.name()
            node.substitute(node.pattern)
            return var_name

        ret = None
        for child in node.children:
            new_ret = replace_var_arg(child)
            assert None in (ret, new_ret)
            ret = ret or new_ret        
        return ret
    
    var_name = replace_var_arg(root)
    return VarArgsNode(var_name, pattern=root)

def parse_helper(s, fn_table):
    # returns (node, remaining string)

    s = s.replace(' ', '')

    delim = 0
    while delim < len(s) and s[delim] not in '(,)':
        delim += 1
    delim_char = s[delim] if delim < len(s) else None

    if delim == 0:
        return parse_helper(s[1:], fn_table)

    if delim_char == '(':
        if s[0] == '*':
            ret, s = parse_helper(s[1:], fn_table)
            return make_var_args_node(ret), s

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
        while right < len(s) and s[right] not in '(,)':
            right += 1
        
        node = (VarArgsNode(s[1:right]) 
                if s[0] == '*' else
                ValueNode(s[:right]))
        return (node, s[right:])
        
def parse(s, fn_table):
    ret, left = parse_helper(s, fn_table)
    assert left == ''
    return ret


