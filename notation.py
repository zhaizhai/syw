from functools import wraps
from core import *

def with_parens(fn):
    @wraps(fn)
    def helper(_, node, **kw):
        ret = fn(_, node, **kw)

        if node.parent is not None:
            assert isinstance(node.parent, FunctionNode)
            if node.fn.precedence <= node.parent.fn.precedence:
                ret = ['('] + ret + [')']            
        return ret
    return helper

class Notation(object):
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
        return notation

class OpNotation(Notation):
    def __init__(self, opchar):
        self.opchar = opchar

    @with_parens
    def get_notation(self, node):
        assert isinstance(node, FunctionNode)

        args = node.fn.num_args
        if args is None:
            args = len(node.children)

        notation = [0]
        for x in zip([self.opchar] * (args - 1), range(1, args)):
            notation.extend(x)
        return notation

class ModifierNotation(Notation):
    def __init__(self, modchar):
        self.modchar = modchar

    @with_parens
    def get_notation(self, node):
        assert len(node.children) == 1
        return [self.modchar, 0]
