from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Tuple

from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Operator


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
    base = tuple(ctrls[:-1])
    local = ctrls[-1]
    return ParsedMCX(base, local, tgt)


def factor_shared_controls_phase1(qc: QuantumCircuit) -> QuantumCircuit:
    """AST-like structural factoring over MCX families without global-control hack.

    Parses each op as (base_controls, local_control -> target), groups by base_controls,
    optimizes target-level logic per group, then rewraps each group with its own controls.
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
        touched = sorted({o.local_control for o in ops} | {o.target for o in ops})
        tmap = {q: i for i, q in enumerate(touched)}

        inner = QuantumCircuit(len(touched))
        for o in ops:
            inner.cx(tmap[o.local_control], tmap[o.target])

        inner_opt = transpile(inner, basis_gates=["cx", "u"], optimization_level=3)

        for inst in inner_opt.data:
            op = inst.operation
            qargs = [inner_opt.find_bit(q).index for q in inst.qubits]
            cgate = op.control(len(base_controls)) if len(base_controls) > 0 else op
            mapped_targets = [touched[i] for i in qargs]
            out.append(cgate, list(base_controls) + mapped_targets)

    return out


def equivalent(a: QuantumCircuit, b: QuantumCircuit) -> bool:
    return Operator(a).equiv(Operator(b))
