
class Function:
    def __init__(self, name, fn, num_args):
        self.name = name
        self.fn = fn
        self.num_args = num_args

    def eval(self, *args):
        return self.fn(*args)

    def copy(self):
        return Function(self.name, self.fn, self.num_args)


class RefTable:
    def __init__(self):
        self.functions = {}
        self.rules = {}

    def add_function(func):
        self.functions[func.name] = func
    
    def add_rule(self):
        
        pass



class Node:
    def __init__(self, ref_table):
        self.ref_table = ref_table
        self.children = []

    def name(self):
        raise NotImplementedError()        

    def copy(self):
        raise NotImplementedError()

    def eval(self):
        raise NotImplementedError()

    def recurse(self, fn):
        for child in self.children:
            child.recurse(fn, order)
        fn(self)

class ValueNode(Node):
    def __init__(self, value, ref_table):
        Node.__init__(self, ref_table)
        self.value = value

    def name(self):
        if not isinstance(self.value, str):
            return 'const'
        return self.value

    def copy(self):
        return ValueNode(self.value, self.ref_table)

    def eval(self):
        return (self.value if not isinstance(self.value, str) 
                else self.ref_table.lookup(self.value))

class FunctionNode(Node):
    def __init__(self, fn, ref_table):
        Node.__init__(self, ref_table)
        self.fn = fn
        self.children = [None] * fn.num_args

    def name(self):
        return self.fn.name

    def copy(self):
        cp = FunctionNode(self.fn, self.ref_table)
        for i, arg in enumerate(self.children):
            if arg:
                cp.children[i] = arg.copy()
        return cp
        
    def eval(self):
        arg_vals = [arg.eval() for arg in self.children]
        return self.fn.eval(*arg_vals)


class Rule:
    def __init__(self, initial, final):
        self.initial = initial
        self.final = final
        self.validate()

        self.initial_to_final = {}
        initial.recurse(lambda n: self.initial_to_final[n.name()] = [])

        def check_mapping(node):
            if node.name() not in self.initial_to_final:
                raise Exception('Undefined reference ' + node.name())
            self.initial_to_final[node.name()].append(node)

        final.recurse(check_mapping)

        self.final_to_initial = {}
        for init_node in self.initial_to_final:
            for final_node in self.initial_to_final[node]:
                assert final_node not in self.final_to_initial
                self.final_to_initial[final_node] = init_node
                
    def validate(self):
        if initial.ref_table is not final.ref_table:
            raise Exception('Initial and final ref table mismatch!')        
        


class RuleParser:
    def __init__(self):
        pass


def apply(node, rule):
    
    realize_initial = {}
    def match(n1, n2):
        assert len(n1.children) == len(n2.children)
        if not n1.children:
            realize_initial[n1] = n2
            return

        assert n1.fn is n2.fn
        for c1, c2 in zip(n1.children, n2.children):
            match(c1, c2)
    match(rule.initial, node)

    def make_copy(n):
        if not n.children:
            return realize_initial[rule.final_to_initial[n]].copy()
        cp = FunctionNode(n.fn.copy(), node.ref_table)
        for i, child in n.children:
            cp.children[i] = make_copy(child)
        return cp

    make_copy(rule.final)
    # TODO: do something with newly constructed tree
