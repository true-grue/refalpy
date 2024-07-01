from refalpy import refal

imports = {
    'add': lambda arg: (arg[0] + arg[1],)
}


@refal(imports)
def rules():
    pal[_] = True
    pal[s] = True
    pal[s.a, e.b, s.a] = pal[e.b]
    pal[e.x] = False

    reverse[_] = _
    reverse[s.a, e.b] = reverse[e.b], s.a

    rle[s.x, e.tail] = rle[{s.x, 1}, e.tail]
    rle[{s.x, s.c}, s.x, e.tail] = rle[{s.x, add[s.c, 1]}, e.tail]
    rle[{s.x, s.c}, s.y, e.tail] = {s.x, s.c}, rle[{s.y, 1}, e.tail]
    rle[e.x] = e.x

    uniq[e.p1, s.x, e.p2, s.x, e.p3] = uniq[e.p1, s.x, e.p2, e.p3]
    uniq[e.x] = e.x

    zip[{s.x, e.a}, {t.x, e.b}] = {s.x, t.x}, zip[{e.a}, {e.b}]
    zip[{}, {}] = _


def test():
    assert rules('pal', tuple('abba')) == (True,)
    assert rules('pal', tuple('abcd')) == (False,)
    assert rules('reverse', tuple('abc')) == ('c', 'b', 'a')
    assert rules('rle', tuple('aaaabbbcca')) == (
        ('a', 4), ('b', 3), ('c', 2), ('a', 1))
    assert rules('uniq', tuple('aaaabbbcca')) == ('a', 'b', 'c')
    assert rules('zip', ((1, 2, 3, 4), ('a', 'b', 'c', 'd'))) == (
        (1, 'a'), (2, 'b'), (3, 'c'), (4, 'd'))
