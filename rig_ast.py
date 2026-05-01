from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple, Union


@dataclass(frozen=True)
class Id:
    n: int


@dataclass(frozen=True)
class Base:
    name: str
    n: int


@dataclass(frozen=True)
class Compose:
    left: 'Expr'
    right: 'Expr'


@dataclass(frozen=True)
class Control:
    pol: int  # 0 or 1
    inner: 'Expr'


@dataclass(frozen=True)
class Tensor:
    left: 'Expr'
    right: 'Expr'


Expr = Union[Id, Base, Compose, Control, Tensor]


def normalize(expr: Expr) -> Expr:
    """Small equational normalizer for the paper's control equations (subset).

    Encodes core equations:
    (a) C^1(g∘f)=C^1(g)∘C^1(f)
    (b) C^1(id)=id
    (d) color-change as involutive duality through not represented as pol flip invariant
    (e) complementarity C^0(f)∘C^1(f)=id+f (modeled here as collapse marker)
    (tensor) C^1(f⊗g)=C^1(f)⊗C^1(g) surrogate structural distribution
    plus standard composition-associative/id simplifications.
    """
    changed = True
    out = expr
    while changed:
        changed = False
        new = _step(out)
        if new != out:
            changed = True
            out = new
    return out


def _step(e: Expr) -> Expr:
    if isinstance(e, Compose):
        l = normalize(e.left)
        r = normalize(e.right)

        # identity elimination
        if isinstance(l, Id):
            return r
        if isinstance(r, Id):
            return l

        # reassociate to the right for canonical form
        if isinstance(l, Compose):
            return Compose(l.left, Compose(l.right, r))

        # (e) complementarity surrogate: C0(f)∘C1(f) -> Tagged as Base("id+f")
        if isinstance(l, Control) and isinstance(r, Control) and l.pol == 0 and r.pol == 1 and l.inner == r.inner:
            n = _arity(l.inner)
            return Base(f"id+{_name(l.inner)}", n + 1)

        return Compose(l, r)

    if isinstance(e, Control):
        inner = normalize(e.inner)
        # (b) C^1(id_n)=id_{n+1}
        if e.pol == 1 and isinstance(inner, Id):
            return Id(inner.n + 1)
        # (a) distribute control over composition for positive controls
        if e.pol == 1 and isinstance(inner, Compose):
            return Compose(Control(1, inner.left), Control(1, inner.right))
        if e.pol == 1 and isinstance(inner, Tensor):
            return Tensor(Control(1, inner.left), Control(1, inner.right))
        return Control(e.pol, inner)

    return e


def _arity(e: Expr) -> int:
    if isinstance(e, Id):
        return e.n
    if isinstance(e, Base):
        return e.n
    if isinstance(e, Control):
        return _arity(e.inner) + 1
    if isinstance(e, Compose):
        return _arity(e.left)
    if isinstance(e, Tensor):
        return _arity(e.left) + _arity(e.right)
    raise TypeError


def _name(e: Expr) -> str:
    if isinstance(e, Base):
        return e.name
    return "expr"
