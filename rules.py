from core import *
import collections

class Rule:
    def __init__(self, initial, final):
        self.initial = initial
        self.final = final

        self.internal_ref = RefTable()
        self.min_initial_depth = {}
        self.max_final_depth = {}
        self.list_initial_nodes = collections.defaultdict(list)
        self.list_final_nodes = collections.defaultdict(list)

        def handle_initial(node, depth=None):
            if not isinstance(node, ValueNode) or depth is None:
                return
            self.list_initial_nodes[node.value].append(node)
            if (node.value not in self.min_initial_depth
                or self.min_initial_depth > depth):
                self.min_initial_depth[node.value] = depth

        def handle_final(node, depth=None):
            if not isinstance(node, ValueNode):
                return
            self.list_final_nodes[node.value].append(node)
            if (node.value not in self.max_final_depth
                or self.max_final_depth < depth):
                self.max_final_depth[node.value] = depth

        self.initial.recurse(handle_initial)
        self.final.recurse(handle_final)

    def groups_together(self, val1, val2):
        if (val1 is None or val2 is None
            or not self.list_final_nodes.has_key(val1)
            or not self.list_final_nodes.has_key(val2)):
            return False

        for node1 in self.list_final_nodes[val1]:
            for node2 in self.list_final_nodes[val2]:
                if lca(node1, node2) is self.final:
                    return False

        return True
        
    # constructs a mapping of variables in self.initial to target
    def map_onto(self, target):
        self.internal_ref.clear()

        def do_mapping(init_node, target_node):
            if not isinstance(init_node, FunctionNode):
                assert self.internal_ref.get_variable(init_node.value) is None
                self.internal_ref.add_variable(init_node.value, target_node)
                return
            assert init_node.name() == target_node.name()
            for i in xrange(len(init_node.children)):
                do_mapping(init_node.children[i], target_node.children[i])
        do_mapping(self.initial, target)

    # constructs tree from template
    def construct_node(self, node, parent=None):
        if not isinstance(node, FunctionNode):
            ret = self.internal_ref.get_variable(node.value).copy()
            ret.parent = parent
            return ret
        
        node.parent = parent
        for i, child in enumerate(node.children):
            node.children[i] = self.construct_node(child, parent=node)
        return node

    def construct_result(self):
        result = self.final.copy()
        result.validate()
        return self.construct_node(result)

        


class RuleParser:
    def __init__(self):
        pass


def apply_rule(node, rule):
    rule.map_onto(node)
    return rule.construct_result()
    



def print_node(node, depth=0):
    print '--' * depth, node.name()
    for n in node.children:
        print_node(n, depth=(depth + 1))


# def sub(a, b):
#     return a - b

# def add(a, b):
#     return a + b

# ft = RefTable()
# ft.add_variable('add', Function('add', add, 2))
# ft.add_variable('sub', Function('sub', sub, 2))

# root = parse('add(x,add(y,z))', ft)
# print_node(root)

# rule = Rule(parse('add(a,add(b,c))', ft), parse('add(add(a,b),c)', ft))
# print_node(apply_rule(root, rule))


