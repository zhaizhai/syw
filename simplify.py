from core import *
from rules import *



def assess(base, target, rule):
    try:
        rule.map_onto(base)
    except AssertionError:
        return -1

    handle = rule.internal_ref.reverse_lookup(target)
    if handle is None:
        return -1
    return rule.min_initial_depth[handle] - rule.max_final_depth[handle]

def find_best_pivot(target, rule):
    ret = max((assess(node, target, rule), node) for node in get_ancestry(target))
    return ret if ret[0] > 0 else None

def find_best_rule(target, rule_list):
    best = None
    for rule in rule_list:
        best_pivot = find_best_pivot(target, rule)
        if best_pivot is None:
            continue
        gain, pivot = best_pivot

        if best is None or gain > best[0]:
            best = (gain, pivot, rule)
    return best


def move_towards(root, node, target, rule_list):

    while True:
        base = lca(node, target)
        
        for rule in rule_list:
            try:
                rule.map_onto(base)
            except AssertionError:
                continue

            if rule.groups_together(rule.internal_ref.reverse_lookup(node),
                                    rule.internal_ref.reverse_lookup(target)):

                if base is root:
                    return apply_rule(base, rule)
                base.substitute(apply_rule(base, rule))
                return root

        best_rule = find_best_rule(node, rule_list)
        if best_rule is None:
            # TODO: what to do if fail
            return None
        gain, pivot, rule = best_rule
        if gain <= 0:
            # TODO: what to do if fail
            return None

        pivot.substitute(apply_rule(pivot, rule))

        # TODO: we actually need to keep track of where new_node and
        # new_target are
        if lca(new_node, target) is not base:
            return root
        node = new_node




if __name__ == 'main':

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

    all_rules = []
    with open('rules.txt') as f:
        for line in f:
            line = line.strip().replace(' ', '')
            if not line:
                continue

            first, second = line.split('=')
            all_rules.append(Rule(parse(first, ft), parse(second, ft)))

    root = parse('equals(add(x,add(y,z)),w)', ft)
    print_node(root)

    root = move_towards(root, root.children[0].children[0], root.children[1], all_rules)
    print_node(root)


