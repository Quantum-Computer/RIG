"""
The "Phantom Bottleneck" Trap (Blind Test)
==========================================
Can the Rig Phase 1 Engine optimize an entangled control
sequence that DOES NOT mathematically cancel to zero?
"""

import time
import warnings
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Operator

warnings.filterwarnings('ignore')


def run_blind_trap():
    num_controls = 3
    num_targets = 4
    num_qubits = num_controls + num_targets

    c = [0, 1, 2]
    t = [3, 4, 5, 6]

    print("=" * 80)
    print(" PHASE 1: QISKIT SEMANTIC SYNTHESIS (Max Power Heuristics)")
    print("=" * 80)

    qc_qiskit = QuantumCircuit(num_qubits)
    qc_qiskit.mcx(c + [t[0]], t[1])
    qc_qiskit.mcx(c + [t[1]], t[2])
    qc_qiskit.mcx(c + [t[1]], t[2])
    qc_qiskit.mcx(c + [t[2]], t[3])
    qc_qiskit.mcx(c + [t[2]], t[3])
    qc_qiskit.mcx(c + [t[0]], t[1])
    qc_qiskit.mcx(c + [t[0]], t[3])

    print("  [Qiskit] Transpiling blind sequence...")
    t0 = time.time()
    opt_qiskit = transpile(qc_qiskit, basis_gates=['cx', 'u'], optimization_level=3)
    qiskit_cx = opt_qiskit.count_ops().get('cx', 0)
    print(f"  -> Qiskit Total CX Count : {qiskit_cx}")
    print(f"  -> Qiskit transpile time : {time.time() - t0:.3f}s")

    print("\n" + "=" * 80)
    print(" RIG PHASE 1 ENGINE (Control Factoring Only)")
    print("=" * 80)
    print("  [Rig Phase 1] Factoring shared control wires conceptually...")

    inner_qc = QuantumCircuit(num_targets)
    inner_qc.cx(0, 1)
    inner_qc.cx(1, 2)
    inner_qc.cx(1, 2)
    inner_qc.cx(2, 3)
    inner_qc.cx(2, 3)
    inner_qc.cx(0, 1)
    inner_qc.cx(0, 3)

    inner_opt = transpile(inner_qc, basis_gates=['cx', 'u'], optimization_level=3)

    qc_rig = QuantumCircuit(num_qubits)
    for inst in inner_opt.data:
        instr = inst.operation
        qargs = inst.qubits
        c_gate = instr.control(num_controls)
        target_indices = [num_controls + inner_opt.find_bit(q).index for q in qargs]
        qc_rig.append(c_gate, c + target_indices)

    final_rig = transpile(qc_rig, basis_gates=['cx', 'u'], optimization_level=3)
    rig_cx = final_rig.count_ops().get('cx', 0)
    print(f"  -> Rig Phase 1 CNOTs : {rig_cx}")

    print("\n" + "=" * 80)
    print(" THE VERDICT")
    print("=" * 80)
    print(f"Standard Qiskit CNOTs : {qiskit_cx}")
    print(f"Rig Phase 1 CNOTs     : {rig_cx}")

    match = Operator(qc_qiskit).equiv(Operator(qc_rig))
    print(f"Unitary Match         : {match}")


if __name__ == "__main__":
    run_blind_trap()
