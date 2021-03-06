import uuid

G_NODE_ID = 0
def create_node_uuid():
    global G_NODE_ID
    G_NODE_ID += 1
    return G_NODE_ID

class Function(object):
    def __init__(self, name, fn, num_args, precedence=-1):
        self.name = name
        self.fn = fn
        self.num_args = num_args
        self.precedence = precedence

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
    def __init__(self, parent=None, node_id=None, tags=''):
        self.parent = parent
        self.children = []
        self.node_id = (node_id if node_id is not None 
                        else create_node_uuid())
        self.tags = tags

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
        return '%r %r' % (self.name(), self.node_id)

    def name(self):
        if not isinstance(self.value, str):
            return 'const'
        return self.value

    def copy(self, retain_id=True):
        return ValueNode(self.value, 
                         node_id=(self.node_id if retain_id else None),
                         tags=self.tags)

class FunctionNode(Node):
    def __init__(self, fn, **kw):
        super(FunctionNode, self).__init__(**kw)
        self.fn = fn
        self.children = ([None] * fn.num_args
                         if fn.num_args is not None else
                         [])

    def __repr__(self):
        return '%r %r' % (self.name(), self.node_id)

    def name(self):
        return self.fn.name

    def copy(self, retain_id=True):
        cp = FunctionNode(self.fn, 
                          node_id=(self.node_id if retain_id else None),
                          tags=self.tags)
        cp.children = [None] * len(self.children)
        for i, arg in enumerate(self.children):
            if arg:
                cp.children[i] = arg.copy(retain_id=retain_id)
                cp.children[i].parent = cp
        return cp

class VarArgsNode(Node):
    def __init__(self, var_name, pattern=None, **kw):
        super(VarArgsNode, self).__init__(**kw)
        self.var_name = var_name
        self.pattern = pattern or ValueNode(var_name)

    def __repr__(self):
        return '*' + self.pattern.name() + (' %r' % self.node_id)

    def name(self):
        return self.var_name

    def copy(self, retain_id=True):
        return VarArgsNode(self.var_name, pattern=self.pattern.copy(retain_id=retain_id),
                           node_id=(self.node_id if retain_id else None),
                           tags=self.tags)

    
def print_node(node, depth=0):
    print '--' * depth, node
    for n in node.children:
        print_node(n, depth=(depth + 1))

def get_ancestry(n, limit=None):
    if n is None:
        return []
    elif n is limit:
        return [n]
    return get_ancestry(n.parent, limit=limit) + [n]

# determine whether node1 and node2 should be considered equal
# VarArgsNodes always compare to False
def check_equals(node1, node2):
    if node1 is node2:
        return True
    if type(node1) != type(node2):
        return False

    if isinstance(node1, ValueNode):
        # TODO: case where node1 and node2 are numbers?
        return node1.name() == node2.name()
    elif isinstance(node1, VarArgsNode):
        return False
    elif isinstance(node1, FunctionNode):
        if len(node1.children) != len(node2.children):
            return False
        if node1.fn is not node2.fn:
            return False
        return all(check_equals(child1, child2) 
                   for child1, child2 
                   in zip(node1.children, node2.children))
    # TODO: raise exception?
    return False

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


def parse_name(raw_name):
    assert any(c.isalnum() for c in raw_name), "%r is not a valid name!" % raw_name

    tags = ''
    while not raw_name[0].isalnum():
        tags += raw_name[0]
        raw_name = raw_name[1:]
    return raw_name, tags

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
        name, tags = parse_name(s[:left])
        s = s[left + 1:]

        children = []
        while s[0] != ')':
            node, s = parse_helper(s, fn_table)
            children.append(node)
        
        ret = FunctionNode(fn_table.get_variable(name), tags=tags)
        ret.children = children
        for child in children:
            child.parent = ret
        return (ret, s[1:])
    else:
        right = 0
        while right < len(s) and s[right] not in '(,)':
            right += 1

        node_type = VarArgsNode if s[0] == '*' else ValueNode
        name, tags = parse_name(s[1:right] if s[0] == '*' else s[:right])
        return (node_type(name, tags=tags), s[right:])

        
def parse(s, fn_table):
    ret, left = parse_helper(s, fn_table)
    assert left == ''
    return ret


