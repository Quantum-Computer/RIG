from __future__ import annotations

from collections import Counter
from typing import List, Tuple

from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Operator


def _extract_ctrl_target(qc: QuantumCircuit, inst) -> Tuple[List[int], int] | None:
    op = inst.operation
    name = op.name.lower()
    if name not in {"mcx", "cx", "ccx", "c3x", "c4x"}:
        return None
    qubits = [qc.find_bit(q).index for q in inst.qubits]
    return qubits[:-1], qubits[-1]


def factor_shared_controls_phase1(qc: QuantumCircuit) -> QuantumCircuit:
    """Auto factor common controls for MCX-like sequences.

    Detects a dominant shared control set across instructions and factors it out,
    compiling inner target logic first, then re-applying shared controls.
    """
    parsed = []
    for inst in qc.data:
        x = _extract_ctrl_target(qc, inst)
        if x is None:
            raise ValueError("Unsupported gate in strict phase1 pass; expected MCX/CX family only")
        parsed.append(x)

    # Infer common shared controls by majority vote intersection.
    counts = Counter(c for ctrls, _ in parsed for c in ctrls)
    threshold = len(parsed)
    shared = sorted([q for q, n in counts.items() if n == threshold])
    if not shared:
        return qc.copy()

    # Build target register map
    target_qubits = sorted(set(t for _, t in parsed) | set(c for ctrls, t in parsed for c in ctrls if c not in shared))
    tmap = {q: i for i, q in enumerate(target_qubits)}

    inner = QuantumCircuit(len(target_qubits))
    for ctrls, tgt in parsed:
        residual = [c for c in ctrls if c not in shared]
        if len(residual) != 1:
            raise ValueError("Phase1 strict pass currently supports residual single-control target logic")
        inner.cx(tmap[residual[0]], tmap[tgt])

    inner_opt = transpile(inner, basis_gates=["cx", "u"], optimization_level=3)

    out = QuantumCircuit(qc.num_qubits)
    for inst in inner_opt.data:
        op = inst.operation
        qargs = [inner_opt.find_bit(q).index for q in inst.qubits]
        gate = op.control(len(shared))
        physical_targets = [target_qubits[i] for i in qargs]
        out.append(gate, shared + physical_targets)

    return out


def equivalent(a: QuantumCircuit, b: QuantumCircuit) -> bool:
    return Operator(a).equiv(Operator(b))
