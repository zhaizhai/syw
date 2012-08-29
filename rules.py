from core import *
import collections

class RuleMatcher:
    def __init__(self, initial, final):
        self.initial = initial
        self.final = final
        self.internal_ref = RefTable()

        self.unpack_vals = {}
        # TODO: we didn't even set internal ref yet! currently it
        # doesn't do anything
        for node in self.internal_ref.values():
            if isinstance(node, VarArgsNode):
                self.unpack_vals[node.name()] = 0

        # TODO: cache generated rules

    def unpack(self, node, n):
        assert isinstance(node, VarArgsNode)

        node_list = []
        for i in xrange(n):
            def sub_name(cur_node, depth=None):
                if (isinstance(cur_node, ValueNode) 
                    and cur_node.name() == node.var_name):
                    cur_node.value = node.var_name + str(i)
            pattern_copy = node.pattern.copy()
            pattern_copy.recurse(sub_name)
            node_list.append(pattern_copy)
        return node_list
                                      
    def generate_rules(self, target):

        def iter_children(rule_children, target_children):
            if not rule_children and not target_children:
                yield
            if not rule_children:
                return
            
            next = rule_children[0]
            if isinstance(next, VarArgsNode):
                assert isinstance(next.pattern, ValueNode)

                for i in xrange(len(target_children) + 1):
                    self.unpack_vals[next.name()] = i
                    for _ in iter_children(rule_children[1:], target_children[i:]):
                        yield
            else:
                if not target_children:
                    return
                for _ in iter_depth(next, target_children[0]):
                    for __ in iter_children(rule_children[1:], target_children[1:]):
                        yield
            
        def iter_depth(rule_node, target_node):
            assert not isinstance(rule_node, VarArgsNode)
            if isinstance(rule_node, FunctionNode):
                if (not isinstance(target_node, FunctionNode) or rule_node.name() != target_node.name()):
                    return
                for _ in iter_children(rule_node.children, target_node.children):
                    yield
            elif isinstance(rule_node, ValueNode):
                yield

        def do_unpack_layer(node):
            new_children = []
            for child in node.children:
                if isinstance(child, VarArgsNode):
                    val = self.unpack_vals[child.name()]
                    new_children.extend(self.unpack(child, val))
                else:
                    do_unpack_layer(child)
                    new_children.append(child)

            node.children = new_children
            for child in new_children:
                child.parent = node

        for _ in iter_depth(self.initial, target):
            rule_initial = self.initial.copy()
            do_unpack_layer(rule_initial)

            rule_final = self.final.copy()
            do_unpack_layer(rule_final)

            rule = Rule(rule_initial, rule_final)
            rule.map_onto(target)
            if rule.is_consistent():
                yield rule            
        

class Rule:
    def __init__(self, initial, final):
        self.initial = initial
        self.final = final
        self.target = None

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
        self.target = target
        self.internal_ref.clear()

        def do_mapping(init_node, target_node):
            if not isinstance(init_node, FunctionNode):
                # may overwrite existing value..
                self.internal_ref.add_variable(init_node.value, target_node)
                return
            # TODO: probably assert function equality?
            assert init_node.name() == target_node.name()
            for i in xrange(len(init_node.children)):
                do_mapping(init_node.children[i], target_node.children[i])
        do_mapping(self.initial, target)

    # determines whether the current mapping is consistent
    def is_consistent(self):
        def check_consistent(init_node, target_node):
            if isinstance(init_node, ValueNode):
                return check_equals(target_node, self.internal_ref.get_variable(init_node.value))
            return all(check_consistent(init_child, target_child) 
                       for init_child, target_child 
                       in zip(init_node.children, target_node.children))
        return check_consistent(self.initial, self.target)

    # constructs tree from template
    def construct_node(self, node, parent=None):
        if not isinstance(node, FunctionNode):
            to_copy = self.internal_ref.get_variable(node.value)
            ret = to_copy.copy(retain_id=('@' not in node.tags))
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

        
def load_from_file(file_name, ft):
    auto_rules = []
    pivot_rules = []
    with open(file_name) as f:
        for line in f:
            line = line.strip().replace(' ', '')
            if not line or line[0] == '#':
                continue

            rule_type, line = line.split(':')
            first, second = line.split('=')
            rule = RuleMatcher(parse(first, ft), parse(second, ft))

            if rule_type == 'RULE':
                pivot_rules.append(rule)
            elif rule_type == 'AUTO':
                auto_rules.append(rule)
    return (pivot_rules, auto_rules)


def apply_rule(node, rule):
    rule.map_onto(node)
    return rule.construct_result()

if __name__ == '__main__':
    def sub(a, b):
        return a - b

    def add(a, b):
        return a + b

    def _sum(*n):
        return sum(n)

    def mult(x, y):
        return x * y

    def equals(x, y):
        return x == y

    ft = RefTable()
    ft.add_variable('equals', Function('equals', equals, 2))
    ft.add_variable('add', Function('add', add, 2))
    ft.add_variable('sub', Function('sub', sub, 2))
    ft.add_variable('sum', Function('sum', _sum, None))
    ft.add_variable('mult', Function('mult', mult, 2))

    root = parse('add(x,add(*y,z))', ft)
    root = parse('sum(sum(ww, wx, wy, wz), x, sum(yw, yx, yy, yz), z)', ft)
    root = parse('mult(sum(w, x, y), z)', ft)
    root = parse('equals(add(x,add(y, z)), w)', ft)

    initial = parse('equals(add(a, b), c)', ft)
    final = parse('equals(b, sub(c, a))', ft)
    rg = RuleMatcher(initial, final)
    for rule in rg.generate_rules(root):
        print_node(rule.initial)

# rule = Rule(parse('add(a,add(b,c))', ft), parse('add(add(a,b),c)', ft))
# print_node(apply_rule(root, rule))


