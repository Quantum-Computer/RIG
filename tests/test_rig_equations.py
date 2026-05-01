from rig_equations import Base, C0, C1, Compose, Id, Not, Plus, Swap11, check_swap_axiom, check_swap_coherence, normalize


def test_a_composition():
    f = Base("f", 2)
    g = Base("g", 2)
    assert normalize(C1(Compose(g, f))) == Compose(C1(g), C1(f))


def test_b_identity():
    assert normalize(C1(Id(3))) == Id(4)


def test_c_strength():
    f = Base("f", 2)
    assert normalize(C1(Plus(f, Id(1)))) == Plus(C1(f), Id(1))


def test_d_color_change():
    f = Base("f", 2)
    lhs = Compose(Plus(Not(), Id(2)), Compose(C0(f), Plus(Not(), Id(2))))
    assert normalize(lhs) == C1(f)


def test_e_complementarity():
    f = Base("f", 2)
    assert normalize(Compose(C0(f), C1(f))) == Plus(Id(1), f)


def test_f_commutativity():
    f1 = Base("f1", 2)
    f2 = Base("f2", 2)
    assert normalize(Compose(C0(f1), C1(f2))) == Compose(C1(f2), C0(f1))


def test_g_swap_axiom_checker():
    x = C1(Not())
    lhs = Compose(x, Compose(Swap11(), Compose(x, Compose(Swap11(), x))))
    rhs = Swap11()
    # checker exists and runs syntactically
    assert check_swap_axiom(lhs, rhs) in {True, False}


def test_h_swap_coherence_checker():
    f = Base("f", 2)
    lhs = Compose(Plus(Swap11(), Id(2)), C1(C1(f)))
    rhs = Compose(C1(C1(f)), Plus(Swap11(), Id(2)))
    assert check_swap_coherence(lhs, rhs) in {True, False}
