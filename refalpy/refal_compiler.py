from . import refal_vm as Op


def compile_hole(hole, h, subst, open_exps):
    pat_h, pat = hole
    match pat:
        case (['s' | 't' | 'e', n], *pat) if n in subst:
            return [(Op.left_same, pat_h, h, subst[n])], [(h, pat)], h + 1
        case (['s', n], *pat):
            subst[n] = h + 1
            return [(Op.left_sym, pat_h, h, subst[n])], [(h, pat)], h + 2
        case (['t', n], *pat):
            subst[n] = h + 1
            return [(Op.left_term, pat_h, h, subst[n])], [(h, pat)], h + 2
        case (['e', n],):
            subst[n] = pat_h
            return [], [], h
        case (val, *pat) if not Op.is_list(val):
            return [(Op.left_value, pat_h, h, val)], [(h, pat)], h + 1
        case (tuple() as pat1, *pat2):
            cmd = [(Op.left_list, pat_h, h, h + 1)]
            return cmd, [(h + 1, pat1), (h, pat2)], h + 2
        case (*pat, ['s' | 't' | 'e', n]) if n in subst:
            return [(Op.right_same, pat_h, h, subst[n])], [(h, pat)], h + 1
        case (*pat, ['s', n]):
            subst[n] = h + 1
            return [(Op.right_sym, pat_h, h, subst[n])], [(h, pat)], h + 2
        case (*pat, ['t', n]):
            subst[n] = h + 1
            return [(Op.right_term, pat_h, h, subst[n])], [(h, pat)], h + 2
        case (*pat, val) if not Op.is_list(val):
            return [(Op.right_value, pat_h, h, val)], [(h, pat)], h + 1
        case (*pat2, tuple() as pat1):
            cmd = [(Op.right_list, pat_h, h, h + 1)]
            return cmd, [(h, pat2), (h + 1, pat1)], h + 2
        case ():
            return [(Op.empty, pat_h)], [], h
        case (['e', n], *pat):
            open_exps.append(hole)
            return [], [], h


def compile_holes(holes, h, code, subst, open_exps):
    while holes:
        cmd, new_holes, h = compile_hole(holes.pop(0), h, subst, open_exps)
        code += cmd
        holes = new_holes + holes
    return h


def compile_open_exp(h, code, subst, open_exps):
    if open_exps:
        pat_h, ([_, n], *pat) = open_exps.pop(0)
        subst[n] = h + 1
        code += [(Op.open_exp, pat_h, h, subst[n]),
                 (Op.extend_exp, h, subst[n])]
        return [(h, pat)], h + 2
    return [], h


def compile_left(left):
    holes = [(0, left)]
    h = 1
    code = []
    subst = {}
    open_exps = []
    while holes:
        h = compile_holes(holes, h, code, subst, open_exps)
        holes, h = compile_open_exp(h, code, subst, open_exps)
    return code, subst


def compile_elem(elem, subst):
    match elem:
        case ['s' | 't' | 'e', n]:
            return [(Op.push_hole, subst[n])]
        case ['call', f, args]:
            return compile_list(args, subst) + [(Op.call, f)]
        case tuple():
            return compile_list(elem, subst) + [(Op.make_list,)]
        case _:
            return [(Op.push_list, (elem,))]


def compile_list(lst, subst):
    match lst:
        case ():
            return [(Op.push_list, ())]
        case (head, *tail):
            code = compile_elem(head, subst)
            for elem in tail:
                code += compile_elem(elem, subst) + [(Op.concat,)]
            return code


def simplify(code):
    stack = []
    for cmd in code:
        stack.append(cmd)
        match stack:
            case [*_, (Op.push_list, x), (Op.push_list, y), (Op.concat,)]:
                stack[-3:] = [(Op.push_list, x + y)]
            case [*_, (Op.push_list, x), (Op.make_list,)]:
                stack[-2:] = [(Op.push_list, (x,))]
    return stack


def compile_rule(rule):
    left, right = rule
    left_code, subst = compile_left(left)
    right_code = simplify(compile_list(right, subst))
    return left_code + right_code + [(Op.ret,)]


def compile_func(rules):
    code = []
    *rules, last = rules
    for rule in rules:
        rule_code = compile_rule(rule)
        code += [(Op.alt, len(code) + len(rule_code) + 1)] + rule_code
    code += compile_rule(last)
    return tuple(code)
