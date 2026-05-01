from rig_ast import Base, Compose, Control, Id, Tensor, normalize


def test_control_over_identity():
    e = Control(1, Id(2))
    assert normalize(e) == Id(3)


def test_control_over_composition():
    f = Base("f", 1)
    g = Base("g", 1)
    e = Control(1, Compose(g, f))
    assert normalize(e) == Compose(Control(1, g), Control(1, f))


def test_complementarity_surrogate():
    f = Base("f", 2)
    e = Compose(Control(0, f), Control(1, f))
    n = normalize(e)
    assert isinstance(n, Base)
    assert n.name == "id+f"


def test_control_over_tensor_uneven_boxes():
    f = Base("h", 1)
    g = Base("g3", 3)
    e = Control(1, Tensor(f, g))
    assert normalize(e) == Tensor(Control(1, f), Control(1, g))
