from functools import wraps
from core import *

def with_parens(fn):
    @wraps(fn)
    def helper(_, node, **kw):
        orient, ret = fn(_, node, **kw)

        if node.parent is not None and orient == Notation.HORIZ_FLOW:
            assert isinstance(node.parent, FunctionNode)
            if node.fn.precedence <= node.parent.fn.precedence:
                ret = ['('] + ret + [')']            
        return orient, ret
    return helper

class Notation(object):
    HORIZ_FLOW, VERT_FLOW = range(2)

    def get_notation(self, node):
        raise NotImplementedError


class DefaultNotation(Notation):
    def get_notation(self, node):
        assert isinstance(node, FunctionNode)

        args = node.fn.num_args
        if args is None:
            args = len(node.children)

        notation = [node.fn.name + '(']
        for x in zip(range(args), [','] * (args - 1) + [')']):
            notation.extend(x)
        return (self.HORIZ_FLOW, notation)

class OpNotation(Notation):
    def __init__(self, opchar, flow=Notation.HORIZ_FLOW):
        self.opchar = opchar
        self.flow = flow

    @with_parens
    def get_notation(self, node):
        assert isinstance(node, FunctionNode)

        args = node.fn.num_args
        if args is None:
            args = len(node.children)

        notation = [0]
        for x in zip([self.opchar] * (args - 1), range(1, args)):
            notation.extend(x)
        return (self.flow, notation)

class ModifierNotation(Notation):
    def __init__(self, modchar):
        self.modchar = modchar

    @with_parens
    def get_notation(self, node):
        assert len(node.children) == 1
        return (self.HORIZ_FLOW, [self.modchar, 0])
