import ast
import inspect
from .refal_vm import execute_func
from .refal_compiler import compile_func


class Refal:
    def __init__(self, tree, imports):
        self.ir = parse_refal(tree)
        self.funcs = imports | compile_refal(self.ir)


def parse_elem(tree):
    match tree:
        case ast.Dict():
            return ()
        case ast.Attribute(ast.Name('s' | 't' | 'e' as ty), name):
            return [ty, f'{ty}.{name}']
        case ast.Constant(val):
            return val
        case _:
            raise SyntaxError(ast.unparse(tree))


def parse_left_elem(tree):
    match tree:
        case ast.Set(lst):
            return tuple(parse_left_elem(elem) for elem in lst)
        case _:
            return parse_elem(tree)


def parse_left(tree):
    match tree:
        case ast.Tuple(lst):
            return tuple(parse_left_elem(elem) for elem in lst)
        case _:
            return (parse_left_elem(tree),)


def parse_right_elem(tree):
    match tree:
        case ast.Set(lst):
            return tuple(parse_right_elem(elem) for elem in lst)
        case ast.Subscript(ast.Name(name), args):
            return ['call', name, parse_right(args)]
        case ast.Name(name):
            return ['call', name, ()]
        case _:
            return parse_elem(tree)


def parse_right(tree):
    match tree:
        case ast.Name('_'):
            return ()
        case ast.Tuple(lst):
            return tuple(parse_right_elem(elem) for elem in lst)
        case _:
            return (parse_right_elem(tree),)


def parse_refal(tree):
    ir = {}
    for rule in tree:
        match rule:
            case ast.Assign([ast.Subscript(ast.Name(name), left)], right):
                left, right = parse_left(left), parse_right(right)
            case ast.Assign([ast.Name(name)], right):
                left, right = (), parse_right(right)
            case _:
                raise SyntaxError(ast.unparse(rule))
        if name not in ir:
            ir[name] = []
        ir[name].append((left, right))
    return ir


def compile_refal(ir):
    funcs = {}
    for name, rules in ir.items():
        funcs[name] = compile_func(rules)
    return funcs


def refal(imports):
    def deco(f):
        tree = ast.parse(inspect.getsource(f))
        o = Refal(tree.body[0].body, imports)
        return lambda *args: execute_func(o.funcs, *args) if args else o
    return deco
