class VM:
    def __init__(self, code, funcs):
        self.holes = {}
        self.alts = []
        self.stack = []
        self.rstack = []
        self.funcs = funcs
        self.code = code
        self.pc = 0


def is_list(x):
    return isinstance(x, (tuple, list))


def eat_left(vm, h0, h1):
    lst, i, j = vm.holes[h0]
    vm.holes[h1] = (lst, i + 1, j)
    return lst, i, i + 1


def eat_right(vm, h0, h1):
    lst, i, j = vm.holes[h0]
    vm.holes[h1] = (lst, i, j - 1)
    return lst, j - 1, j


def empty(vm, h):
    _, i, j = vm.holes[h]
    return i == j


def left_sym(vm, h0, h1, h2):
    if empty(vm, h0):
        return False
    lst, i, j = eat_left(vm, h0, h1)
    if is_list(lst[i]):
        return False
    vm.holes[h2] = (lst, i, j)
    return True


def right_sym(vm, h0, h1, h2):
    if empty(vm, h0):
        return False
    lst, i, j = eat_right(vm, h0, h1)
    if is_list(lst[i]):
        return False
    vm.holes[h2] = (lst, i, j)
    return True


def left_term(vm, h0, h1, h2):
    if empty(vm, h0):
        return False
    vm.holes[h2] = eat_left(vm, h0, h1)
    return True


def right_term(vm, h0, h1, h2):
    if empty(vm, h0):
        return False
    vm.holes[h2] = eat_right(vm, h0, h1)
    return True


def left_value(vm, h0, h1, val):
    if empty(vm, h0):
        return False
    lst, i, _ = eat_left(vm, h0, h1)
    return lst[i] == val


def right_value(vm, h0, h1, val):
    if empty(vm, h0):
        return False
    lst, i, _ = eat_right(vm, h0, h1)
    return lst[i] == val


def left_same(vm, h0, h1, h2):
    if empty(vm, h0):
        return False
    lst1, a, b = eat_left(vm, h0, h1)
    lst2, c, d = vm.holes[h2]
    return lst1[a:b] == lst2[c:d]


def right_same(vm, h0, h1, h2):
    if empty(vm, h0):
        return False
    lst1, a, b = eat_right(vm, h0, h1)
    lst2, c, d = vm.holes[h2]
    return lst1[a:b] == lst2[c:d]


def left_list(vm, h0, h1, h2):
    if empty(vm, h0):
        return False
    lst, i, _ = eat_left(vm, h0, h1)
    if not is_list(lst[i]):
        return False
    vm.holes[h2] = (lst[i], 0, len(lst[i]))
    return True


def right_list(vm, h0, h1, h2):
    if empty(vm, h0):
        return False
    lst, i, _ = eat_right(vm, h0, h1)
    if not is_list(lst[i]):
        return False
    vm.holes[h2] = (lst[i], 0, len(lst[i]))
    return True


def alt(vm, pc):
    vm.alts.append(pc)
    return True


def open_exp(vm, h0, h1, h2):
    lst, i, j = vm.holes[h0]
    vm.holes[h1] = (lst, i, j)
    vm.holes[h2] = (lst, i, i)
    alt(vm, vm.pc)
    vm.pc += 1
    return True


def extend_exp(vm, h0, h1):
    _, _, end_j = vm.holes[h0]
    lst, i, j = vm.holes[h1]
    if j == end_j:
        return False
    vm.holes[h0] = lst, j + 1, end_j
    vm.holes[h1] = lst, i, j + 1
    return alt(vm, vm.pc - 1)


def push_list(vm, lst):
    vm.stack.append(lst)
    return True


def push_hole(vm, h):
    lst, i, j = vm.holes[h]
    return push_list(vm, lst[i:j])


def make_list(vm):
    vm.stack[-1] = (vm.stack[-1],)
    return True


def concat(vm):
    lst = vm.stack.pop()
    vm.stack[-1] += lst
    return True


def call(vm, f):
    arg = vm.stack.pop()
    code = vm.funcs[f]
    if callable(code):
        return push_list(vm, code(arg))
    vm.rstack.append((vm.holes, vm.code, vm.pc))
    vm.holes = {0: (arg, 0, len(arg))}
    vm.code = code
    vm.alts = [0]
    return False


def ret(vm):
    vm.holes, vm.code, pc = vm.rstack.pop()
    vm.alts.append(pc if vm.rstack else None)
    return False


def execute_func(f, arg, funcs):
    vm = VM([(push_list, arg), (call, f)], funcs)
    execute(vm)
    return vm.stack.pop()


def execute(vm):
    while vm.pc is not None:
        op, *args = vm.code[vm.pc]
        vm.pc += 1
        if not op(vm, *args):
            if not vm.alts:
                raise RuntimeError('matching error')
            vm.pc = vm.alts.pop()
