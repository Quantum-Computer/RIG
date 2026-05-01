from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Operator

from rig_qiskit_phase1 import factor_shared_controls_phase1


def build_nontrivial_sequence():
    # 3 shared controls, 5 targets; rich non-cancelling pattern
    c = [0, 1, 2]
    t = [3, 4, 5, 6, 7]
    qc = QuantumCircuit(8)
    seq = [
        (t[0], t[1]), (t[1], t[3]), (t[3], t[4]),
        (t[4], t[2]), (t[2], t[0]), (t[1], t[2]),
        (t[0], t[4]), (t[3], t[1]), (t[2], t[3]),
        (t[4], t[0]), (t[1], t[4]),
    ]
    for a, b in seq:
        qc.mcx(c + [a], b)
    return qc


def test_strict_nontrivial_equivalence_and_reduction():
    raw = build_nontrivial_sequence()
    rig = factor_shared_controls_phase1(raw)

    assert Operator(raw).equiv(Operator(rig))

    qiskit_cx = transpile(raw, basis_gates=['cx', 'u'], optimization_level=3).count_ops().get('cx', 0)
    rig_cx = transpile(rig, basis_gates=['cx', 'u'], optimization_level=3).count_ops().get('cx', 0)

    # Must not regress; in these structured cases rig should improve.
    assert rig_cx <= qiskit_cx
