from rig_symbolic import C0, C1, Compose, Id, Not, Plus, Swap11, Tensor, Var, normalize, to_disco


def test_rule_a():
    f, g = Var("f", 2), Var("g", 2)
    assert normalize(C1(Compose(g, f))) == Compose(C1(g), C1(f))


def test_rule_b():
    assert normalize(C1(Id(3))) == Id(4)


def test_rule_c():
    f = Var("f", 2)
    assert normalize(C1(Plus(f, Id(1)))) == Plus(C1(f), Id(1))


def test_rule_d():
    f = Var("f", 2)
    lhs = Compose(Plus(Not(), Id(2)), Compose(C0(f), Plus(Not(), Id(2))))
    assert normalize(lhs) == C1(f)


def test_rule_e():
    f = Var("f", 2)
    assert normalize(Compose(C0(f), C1(f))) == Plus(Id(1), f)


def test_rule_f():
    f1, f2 = Var("f1", 2), Var("f2", 2)
    assert normalize(Compose(C0(f1), C1(f2))) == Compose(C1(f2), C0(f1))


def test_rule_g():
    x = C1(Not())
    lhs = Compose(x, Compose(Swap11(), Compose(x, Compose(Swap11(), x))))
    assert normalize(lhs) == Swap11()


def test_rule_h():
    f = Var("f", 2)
    lhs = Compose(C1(C1(f)), Tensor(Swap11(), Id(2)))
    rhs = Compose(Tensor(Swap11(), Id(2)), C1(C1(f)))
    assert normalize(lhs) == normalize(rhs)


def test_discopy_render():
    d = to_disco(C1(Var("f", 1)))
    assert d is not None
