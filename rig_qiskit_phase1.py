from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Tuple

from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator

from rig_equations import Base, Compose, Id, normalize


@dataclass(frozen=True)
class ParsedMCX:
    base_controls: Tuple[int, ...]
    local_control: int
    target: int


def _parse_mcx_like(qc: QuantumCircuit, inst) -> ParsedMCX | None:
    name = inst.operation.name.lower()
    if name not in {"mcx", "cx", "ccx", "c3x", "c4x"}:
        return None
    q = [qc.find_bit(x).index for x in inst.qubits]
    ctrls, tgt = q[:-1], q[-1]
    if len(ctrls) < 1:
        return None
    return ParsedMCX(tuple(ctrls[:-1]), ctrls[-1], tgt)


def _ops_to_term(ops: List[ParsedMCX]):
    term = None
    for o in ops:
        node = Base(f"cx:{o.local_control}->{o.target}", 2)
        term = node if term is None else Compose(term, node)
    return term if term is not None else Id(0)


def _term_to_ops(term) -> List[Tuple[int, int]]:
    if isinstance(term, Id):
        return []
    if isinstance(term, Base) and term.name.startswith("cx:"):
        x = term.name.split(":", 1)[1]
        a, b = x.split("->")
        return [(int(a), int(b))]
    if isinstance(term, Compose):
        return _term_to_ops(term.left) + _term_to_ops(term.right)
    raise ValueError(f"Unsupported normalized term: {term}")


def factor_shared_controls_phase1(qc: QuantumCircuit) -> QuantumCircuit:
    """Syntactic phase-1 factoring: parse -> term normalize -> rebuild.

    This path intentionally avoids qiskit transpiler in the factoring core.
    """
    parsed: List[ParsedMCX] = []
    for inst in qc.data:
        p = _parse_mcx_like(qc, inst)
        if p is None:
            raise ValueError("Unsupported gate in phase1 pass; expected MCX/CX family only")
        parsed.append(p)

    groups: Dict[Tuple[int, ...], List[ParsedMCX]] = defaultdict(list)
    for p in parsed:
        groups[p.base_controls].append(p)

    out = QuantumCircuit(qc.num_qubits)
    for base_controls, ops in groups.items():
        norm = normalize(_ops_to_term(ops))
        reduced_pairs = _term_to_ops(norm)

        for c, t in reduced_pairs:
            # reconstructed local controlled-X, then add base controls
            if len(base_controls) == 0:
                out.cx(c, t)
            else:
                out.mcx(list(base_controls) + [c], t)

    return out


def equivalent(a: QuantumCircuit, b: QuantumCircuit) -> bool:
    return Operator(a).equiv(Operator(b))
