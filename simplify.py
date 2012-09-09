from core import *
from rules import *



def apply_auto(root, auto_matchers):
    new_children = []
    for child in root.children:
        replacement = apply_auto(child, auto_matchers)
        replacement.parent = root
        new_children.append(replacement)
    root.children = new_children

    for matcher in auto_matchers:
        for rule in matcher.generate_rules(root):
            root = apply_rule(root, rule)
    return root

def recover(node, new_root):
    if new_root.node_id == node.node_id:
        return new_root

    for child in new_root.children:
        ret = recover(node, child)
        if ret is not None:
            return ret
    return None


class Manipulator(object):
    def __init__(self, root, rule_matchers):
        self.root = root
        self.rule_matchers = rule_matchers

    def assess(self, pivot, node, rule, desired_parent=None):
        rule.map_onto(pivot)
        handle = rule.internal_ref.reverse_lookup(node)
        if handle != 'x': # TODO
            return -1

        final_parent = rule.final_node.parent
        if (isinstance(final_parent, FunctionNode)
            and final_parent.fn is desired_parent):
            return 2
        return 1

    def find_best_rule(self, base, node, desired_parent=None):
        best_val, best_rule = -1, None

        for rule_matcher in self.rule_matchers:
            for rule in rule_matcher.generate_rules(base):
                val = self.assess(base, node, rule, desired_parent=desired_parent)
                if val > best_val:
                    best_val, best_rule = val, rule

        return best_val, best_rule

    def find_best_move(self, node, limit=None, desired_parent=None):
        best_val, best_pivot, best_rule = 0, None, None

        for pivot in get_ancestry(node, limit=limit):
            val, rule = self.find_best_rule(pivot, node, desired_parent=desired_parent)
            if best_val < val:
                best_val, best_pivot, best_rule = val, pivot, rule

        return best_pivot, best_rule

    def move_up(self, base, node, desired_parent=None):
        print 'move %r up to %r' % (node, base)

        root_cp = self.root.copy()
        node, base = recover(node, root_cp), recover(base, root_cp)
        assert None not in (node, base)

        pivot, rule = self.find_best_move(node, limit=base, desired_parent=desired_parent)
        if rule is None:
            return False

        # TODO: how do we recover all this stuff?
        replacement = apply_rule(pivot, rule)
        assert recover(node, replacement) is not None

        if pivot is root_cp:
            self.root = replacement
        else:
            pivot.substitute(replacement)
            self.root = root_cp
        return True

    def move_towards(self, node, target, desired_parent=None):
        base = lca(node, target)
        make_move = True

        while make_move and base is not None:
            make_move = self.move_up(base, node, desired_parent=desired_parent)
            node, base = recover(node, self.root), recover(base, self.root)
            # print_node(self.root)
