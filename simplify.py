from core import *
from rules import *



def assess(base, node, rule):
    try:
        rule.map_onto(base)
    except AssertionError:
        return -1

    handle = rule.internal_ref.reverse_lookup(node)
    if handle is None:
        return -1
    return rule.min_initial_depth[handle] - rule.max_final_depth[handle]

def find_best_rule(base, node, rule_matchers):
    best_val, best_rule = -1, None

    for rule_matcher in rule_matchers:
        for rule in rule_matcher.generate_rules(base):
            val = assess(base, node, rule)
            if val > best_val:
                best_val, best_rule = val, rule
                
    return best_val, best_rule

def find_best_move(node, rule_matchers):
    best_val, best_pivot, best_rule = 0, None, None

    for pivot in get_ancestry(node):
        val, rule = find_best_rule(pivot, node, rule_matchers)
        if best_val < val:
            best_val, best_pivot, best_rule = val, pivot, rule

    return best_pivot, best_rule

def check_groups_together(base, node, target, rule_matchers):
    for rule_matcher in rule_matchers:
        for rule in rule_matcher.generate_rules(base):
            rule.map_onto(base)
            if rule.groups_together(rule.internal_ref.reverse_lookup(node),
                                    rule.internal_ref.reverse_lookup(target)):
                return rule
    return None

def recover(node, new_root):
    if new_root.node_id == node.node_id:
        return new_root

    for child in new_root.children:
        ret = recover(node, child)
        if ret is not None:
            return ret
    return None
    
def move_towards(root, node, target, rule_matchers):
    root_cp = root.copy()
    node, target = recover(node, root_cp), recover(target, root_cp)
    assert None not in (node, target)

    while True:
        base = lca(node, target)

        quick_rule = check_groups_together(base, node, target, rule_matchers)
        if quick_rule is not None:
            if base is root_cp:
                return apply_rule(base, quick_rule)
            base.substitute(apply_rule(base, quick_rule))
            return root_cp

        pivot, rule = find_best_move(node, rule_matchers)

        if rule is None:
            # couldn't make move
            return None

        replacement = apply_rule(pivot, rule)
        node = recover(node, replacement)
        assert node is not None

        if pivot is root_cp:
            root_cp = replacement
        else:
            pivot.substitute(replacement)



if __name__ == '__main__':

    def equals(a, b):
        return a == b

    def sub(a, b):
        return a - b

    def add(a, b):
        return a + b

    ft = RefTable()
    ft.add_variable('add', Function('add', add, 2))
    ft.add_variable('sub', Function('sub', sub, 2))
    ft.add_variable('equals', Function('equals', equals, 2))

    all_rules = load_from_file('rules.txt', ft)

    root = parse('equals(add(add(x,add(y,z)),v),w)', ft)
    print_node(root)

    new_root = move_towards(root, root.children[0].children[0].children[0], 
                            root.children[1], all_rules)

    if new_root is not None:
        root = new_root
    print_node(root)


