from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import QFT
from qiskit.quantum_info import Operator

from rig_engine import RigControlEngine, ControlledGateSpec, PlacedControlledOp


@dataclass
class TrapResult:
    label: str
    depth: int
    size: int
    cx: int
    ops: dict


def make_controlled_block(n_controls: int, block: QuantumCircuit):
    return block.to_gate(label=block.name).control(n_controls)


def collect(label: str, qc: QuantumCircuit, optimization_level: int = 3) -> TrapResult:
    tqc = transpile(qc, basis_gates=["u", "cx"], optimization_level=optimization_level)
    ops = tqc.count_ops()
    return TrapResult(label, tqc.depth(), tqc.size(), int(ops.get("cx", 0)), dict(ops))


def run_once(n_controls=4, n_a=4, n_b=4, optimization_level=3):
    A = QFT(num_qubits=n_a, do_swaps=False).decompose()
    B = QFT(num_qubits=n_b, do_swaps=False).decompose()

    # Direct Qiskit circuit
    total = n_controls + n_a + n_b
    ctrl = list(range(n_controls))
    a = list(range(n_controls, n_controls + n_a))
    b = list(range(n_controls + n_a, total))

    direct = QuantumCircuit(total, name="direct")
    direct.append(make_controlled_block(n_controls, A), ctrl + a)
    direct.append(make_controlled_block(n_controls, B), ctrl + b)
    direct.append(make_controlled_block(n_controls, A.inverse()), ctrl + a)
    direct.append(make_controlled_block(n_controls, B.inverse()), ctrl + b)

    # Automatic rig simplification path
    eng = RigControlEngine()
    gA = eng.register_gate("A", Operator(A).data)
    gB = eng.register_gate("B", Operator(B).data)
    gAi = eng.register_gate("Ai", Operator(A.inverse()).data)
    gBi = eng.register_gate("Bi", Operator(B.inverse()).data)
    ctrl_word = tuple([1] * n_controls)

    ops = [
        PlacedControlledOp(ControlledGateSpec(gate=gA, controls_top=ctrl_word), target_offset=0),
        PlacedControlledOp(ControlledGateSpec(gate=gB, controls_top=ctrl_word), target_offset=n_a),
        PlacedControlledOp(ControlledGateSpec(gate=gAi, controls_top=ctrl_word), target_offset=0),
        PlacedControlledOp(ControlledGateSpec(gate=gBi, controls_top=ctrl_word), target_offset=n_a),
    ]
    simp = eng.simplify_controlled_chain(ops)

    rig_auto = QuantumCircuit(total, name="rig_auto")
    for op in simp:
        c = eng.controlled_qiskit_circuit(op.spec).to_gate()
        qargs = ctrl + list(range(n_controls + op.target_offset, n_controls + op.target_offset + op.spec.gate.arity))
        rig_auto.append(c, qargs)

    sem_identity = len(simp) == 0

    d = collect("direct_qiskit", direct, optimization_level)
    r = collect("rig_auto_plus_qiskit", rig_auto, optimization_level)

    print("=== Shared-Control Trap Results ===")
    print(f"controls={n_controls}, A={n_a}, B={n_b}, opt={optimization_level}")
    print(f"automatic rig simplification to empty: {sem_identity}")
    for x in [d, r]:
        print(f"\n[{x.label}] depth={x.depth} size={x.size} cx={x.cx} ops={x.ops}")


if __name__ == "__main__":
    run_once()
