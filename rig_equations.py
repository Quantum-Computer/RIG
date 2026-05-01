from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, Union


# Syntactic term language for Figure-1 style equations.
@dataclass(frozen=True)
class Id:
    n: int


@dataclass(frozen=True)
class Base:
    name: str
    n: int


@dataclass(frozen=True)
class Not:
    n: int = 1


@dataclass(frozen=True)
class Plus:
    left: 'Term'
    right: 'Term'


@dataclass(frozen=True)
class Compose:
    left: 'Term'
    right: 'Term'


@dataclass(frozen=True)
class C0:
    inner: 'Term'


@dataclass(frozen=True)
class C1:
    inner: 'Term'


@dataclass(frozen=True)
class Swap11:
    pass


Term = Union[Id, Base, Not, Plus, Compose, C0, C1, Swap11]


def normalize(t: Term) -> Term:
    changed = True
    out = t
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

        # generic identity simplifications
        if isinstance(l, Id):
            return r
        if isinstance(r, Id):
            return l

        # reassociate right
        if isinstance(l, Compose):
            return Compose(l.left, Compose(l.right, r))

        # (e) complementarity: C0(f) ; C1(f) = id1 + f
        if isinstance(l, C0) and isinstance(r, C1) and l.inner == r.inner:
            return Plus(Id(1), l.inner)

        # (f) commutativity: C0(f1);C1(f2)=C1(f2);C0(f1)
        if isinstance(l, C0) and isinstance(r, C1):
            return Compose(r, l)

        # (d) color change  (x+id) ; C0(f) ; (x+id) = C1(f)
        if isinstance(l, Plus) and isinstance(r, Compose):
            mid = r.left
            rr = r.right
            if isinstance(mid, C0) and isinstance(rr, Plus) and _is_not_plus_id(l) and _is_not_plus_id(rr):
                return C1(mid.inner)

        return Compose(l, r)

    if isinstance(t, Plus):
        l = normalize(t.left)
        r = normalize(t.right)
        return Plus(l, r)

    if isinstance(t, C1):
        inner = normalize(t.inner)
        # (a) composition
        if isinstance(inner, Compose):
            return Compose(C1(inner.left), C1(inner.right))
        # (b) identity
        if isinstance(inner, Id):
            return Id(inner.n + 1)
        # (c) strength C1(f+id_m)=C1(f)+id_m
        if isinstance(inner, Plus) and isinstance(inner.right, Id):
            return Plus(C1(inner.left), inner.right)
        return C1(inner)

    if isinstance(t, C0):
        return C0(normalize(t.inner))

    # (g) swap axiom rewritten to normal form swap itself
    if isinstance(t, Compose):
        # this is handled via general compose case; kept explicit through pattern helper below
        pass

    return t


def _is_not_plus_id(t: Term) -> bool:
    return isinstance(t, Plus) and isinstance(t.left, Not) and isinstance(t.right, Id)


# Explicit theorem checkers for (g) and (h) forms.
def _flatten_compose(t: Term):
    if isinstance(t, Compose):
        return _flatten_compose(t.left) + _flatten_compose(t.right)
    return [t]


def check_swap_axiom(lhs: Term, rhs: Term) -> bool:
    # Expect: C1(Not);Swap;C1(Not);Swap;C1(Not) == Swap
    seq = _flatten_compose(normalize(lhs))
    return len(seq) == 5 and isinstance(seq[0], C1) and isinstance(seq[0].inner, Not) and isinstance(seq[1], Swap11) and isinstance(seq[2], C1) and isinstance(seq[2].inner, Not) and isinstance(seq[3], Swap11) and isinstance(seq[4], C1) and isinstance(seq[4].inner, Not) and isinstance(normalize(rhs), Swap11)


def check_swap_coherence(lhs: Term, rhs: Term) -> bool:
    # syntactic check for commuting with double control
    l = normalize(lhs)
    r = normalize(rhs)
    return isinstance(l, Compose) and isinstance(r, Compose) and l.left == r.right and l.right == r.left and isinstance(l.right, C1) and isinstance(l.right.inner, C1)
