from __future__ import annotations

from dataclasses import dataclass
from typing import Union

from discopy.monoidal import Box, Diagram, Ty


@dataclass(frozen=True)
class Id:
    n: int


@dataclass(frozen=True)
class Var:
    name: str
    n: int


@dataclass(frozen=True)
class Not:
    pass


@dataclass(frozen=True)
class Swap11:
    pass


@dataclass(frozen=True)
class Compose:
    left: "Term"
    right: "Term"


@dataclass(frozen=True)
class Plus:
    left: "Term"
    right: "Term"


@dataclass(frozen=True)
class Tensor:
    left: "Term"
    right: "Term"


@dataclass(frozen=True)
class C0:
    inner: "Term"


@dataclass(frozen=True)
class C1:
    inner: "Term"


Term = Union[Id, Var, Not, Swap11, Compose, Plus, Tensor, C0, C1]


def normalize(term: Term) -> Term:
    changed = True
    out = term
    while changed:
        changed = False
        new = _step(out)
        if new != out:
            out = new
            changed = True
    return out


def _step(t: Term) -> Term:
    if isinstance(t, Compose):
        l = normalize(t.left)
        r = normalize(t.right)

        if isinstance(l, Id):
            return r
        if isinstance(r, Id):
            return l

        # (e) C0(f);C1(f)=id1+f
        if isinstance(l, C0) and isinstance(r, C1) and l.inner == r.inner:
            return Plus(Id(1), l.inner)

        # (f) C0(f1);C1(f2)=C1(f2);C0(f1)
        if isinstance(l, C0) and isinstance(r, C1):
            return Compose(r, l)

        # (d) (x+id);C0(f);(x+id)=C1(f)
        if isinstance(l, Plus) and isinstance(r, Compose):
            if _is_not_plus_id(l) and isinstance(r.left, C0) and isinstance(r.right, Plus) and _is_not_plus_id(r.right):
                return C1(r.left.inner)

        # (g) C1(x);s;C1(x);s;C1(x)=s
        flat = _flatten_compose(Compose(l, r))
        if _is_rule_g(flat):
            return Swap11()

        # (h) swap coherence canonicalize to swap-left form
        if isinstance(l, C1) and isinstance(l.inner, C1) and isinstance(r, Tensor) and isinstance(r.left, Swap11):
            return Compose(r, l)

        return Compose(l, r)

    if isinstance(t, C1):
        inner = normalize(t.inner)
        # (a)
        if isinstance(inner, Compose):
            return Compose(C1(inner.left), C1(inner.right))
        # (b)
        if isinstance(inner, Id):
            return Id(inner.n + 1)
        # (c)
        if isinstance(inner, Plus) and isinstance(inner.right, Id):
            return Plus(C1(inner.left), inner.right)
        return C1(inner)

    if isinstance(t, C0):
        return C0(normalize(t.inner))

    if isinstance(t, Plus):
        return Plus(normalize(t.left), normalize(t.right))

    if isinstance(t, Tensor):
        return Tensor(normalize(t.left), normalize(t.right))

    return t


def _flatten_compose(t: Term):
    if isinstance(t, Compose):
        return _flatten_compose(t.left) + _flatten_compose(t.right)
    return [t]


def _is_not_plus_id(t: Term) -> bool:
    return isinstance(t, Plus) and isinstance(t.left, Not) and isinstance(t.right, Id)


def _is_rule_g(seq) -> bool:
    return (
        len(seq) == 5
        and isinstance(seq[0], C1) and isinstance(seq[0].inner, Not)
        and isinstance(seq[1], Swap11)
        and isinstance(seq[2], C1) and isinstance(seq[2].inner, Not)
        and isinstance(seq[3], Swap11)
        and isinstance(seq[4], C1) and isinstance(seq[4].inner, Not)
    )


def to_disco(term: Term) -> Diagram:
    """Render normalized term as a DisCoPy diagram (symbolic labels)."""
    t = normalize(term)
    return _to_disco_raw(t)


def _to_disco_raw(t: Term) -> Diagram:
    if isinstance(t, Id):
        return Diagram.id(Ty(*(["q"] * t.n)))
    if isinstance(t, Var):
        ty = Ty(*(["q"] * t.n))
        return Box(t.name, ty, ty)
    if isinstance(t, Not):
        return Box("X", Ty("q"), Ty("q"))
    if isinstance(t, Swap11):
        return Diagram.swap(Ty("q"), Ty("q"))
    if isinstance(t, C1):
        inner = _to_disco_raw(t.inner)
        dom = Ty("q") @ inner.dom
        cod = Ty("q") @ inner.cod
        return Box("C1", dom, cod)
    if isinstance(t, C0):
        inner = _to_disco_raw(t.inner)
        dom = Ty("q") @ inner.dom
        cod = Ty("q") @ inner.cod
        return Box("C0", dom, cod)
    if isinstance(t, Plus):
        return _to_disco_raw(t.left) @ _to_disco_raw(t.right)
    if isinstance(t, Tensor):
        return _to_disco_raw(t.left) @ _to_disco_raw(t.right)
    if isinstance(t, Compose):
        return _to_disco_raw(t.left) >> _to_disco_raw(t.right)
    raise TypeError(t)
