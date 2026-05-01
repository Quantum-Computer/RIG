import warnings
from qiskit import QuantumCircuit, transpile

from rig_qiskit_phase1 import factor_shared_controls_phase1, equivalent

warnings.filterwarnings('ignore')


def build_blind_sequence():
    num_controls = 3
    num_targets = 4
    num_qubits = num_controls + num_targets
    c = [0, 1, 2]
    t = [3, 4, 5, 6]

    qc = QuantumCircuit(num_qubits)
    qc.mcx(c + [t[0]], t[1])
    qc.mcx(c + [t[1]], t[2])
    qc.mcx(c + [t[1]], t[2])
    qc.mcx(c + [t[2]], t[3])
    qc.mcx(c + [t[2]], t[3])
    qc.mcx(c + [t[0]], t[1])
    qc.mcx(c + [t[0]], t[3])
    return qc


def run():
    raw = build_blind_sequence()
    qiskit_opt = transpile(raw, basis_gates=['cx', 'u'], optimization_level=3)

    rig = factor_shared_controls_phase1(raw)
    rig_opt = transpile(rig, basis_gates=['cx', 'u'], optimization_level=3)

    print('qiskit_cx', qiskit_opt.count_ops().get('cx', 0))
    print('rig_cx', rig_opt.count_ops().get('cx', 0))
    print('equiv', equivalent(raw, rig))


if __name__ == '__main__':
    run()
