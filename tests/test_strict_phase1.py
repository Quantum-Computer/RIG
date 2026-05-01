from qiskit import QuantumCircuit, transpile

from rig_qiskit_phase1 import factor_shared_controls_phase1, equivalent


def test_strict_phase1_blind_sequence():
    c = [0, 1, 2]
    t = [3, 4, 5, 6]
    qc = QuantumCircuit(7)
    qc.mcx(c + [t[0]], t[1])
    qc.mcx(c + [t[1]], t[2])
    qc.mcx(c + [t[1]], t[2])
    qc.mcx(c + [t[2]], t[3])
    qc.mcx(c + [t[2]], t[3])
    qc.mcx(c + [t[0]], t[1])
    qc.mcx(c + [t[0]], t[3])

    rig = factor_shared_controls_phase1(qc)
    assert equivalent(qc, rig)

    qiskit_cx = transpile(qc, basis_gates=['cx', 'u'], optimization_level=3).count_ops().get('cx', 0)
    rig_cx = transpile(rig, basis_gates=['cx', 'u'], optimization_level=3).count_ops().get('cx', 0)
    assert rig_cx < qiskit_cx
