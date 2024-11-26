from refalpy import refal

imports = {
    'add': lambda arg: (arg[0] + arg[1],),
    'sub': lambda arg: (arg[0] - arg[1],),
    'mul': lambda arg: (arg[0] * arg[1],),
    'div': lambda arg: (arg[0] / arg[1],),
    'type': lambda arg: (type(arg[0]).__name__,)
}


@refal(imports)
def rules():
    op['int'] = 'push'
    op['str'] = 'load'

    comp[{s.var, '=', t.expr}, e.prog] = comp[t.expr], {
        'store', s.var}, comp[e.prog]
    comp[{t.a, '+', t.b}] = comp[t.a], comp[t.b], 'add'
    comp[{t.a, '-', t.b}] = comp[t.a], comp[t.b], 'sub'
    comp[{t.a, '*', t.b}] = comp[t.a], comp[t.b], 'mul'
    comp[{t.a, '/', t.b}] = comp[t.a], comp[t.b], 'div'
    comp[s.val] = {op[type[s.val]], s.val}
    comp = _

    get[{e.x, {s.key, t.val}, e.y}, s.key] = t.val
    set[{e.x, {s.key, t.val}, e.y}, s.key, t.new] = {e.x, {s.key, t.new}, e.y}
    set[{e.x}, s.key, t.val] = {e.x, {s.key, t.val}}

    interp[{t.cmd, e.code}, t.stack, t.env] = interp[{
        e.code}, step[t.cmd, t.stack, t.env]]
    interp[{}, {}, t.env] = t.env

    step['add', {e.stack, s.x, s.y}, t.env] = {e.stack, add[s.x, s.y]}, t.env
    step['sub', {e.stack, s.x, s.y}, t.env] = {e.stack, sub[s.x, s.y]}, t.env
    step['mul', {e.stack, s.x, s.y}, t.env] = {e.stack, mul[s.x, s.y]}, t.env
    step['div', {e.stack, s.x, s.y}, t.env] = {e.stack, div[s.x, s.y]}, t.env
    step[{'push', s.x}, {e.stack}, t.env] = {e.stack, s.x}, t.env
    step[{'load', s.var}, {e.stack}, t.env] = {
        e.stack, get[t.env, s.var]}, t.env
    step[{'store', s.var}, {e.stack, s.val}, t.env] = {
        e.stack}, set[t.env, s.var, s.val]

    sem[e.prog] = interp[{comp[e.prog]}, {}, {}]


def test():
    prog = (
        ('n', '=', 10),
        ('s', '=', (('n', '*', ('n', '+', 1)), '/', 2))
    )
    assert rules('sem', prog) == ((('n', 10), ('s', 55.0)),)


test()