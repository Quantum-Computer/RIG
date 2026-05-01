import numpy as np
from qiskit.quantum_info import Operator

from rig_engine import RigControlEngine, ControlledGateSpec


def test_positive_control_x_builds_qiskit_unitary():
    eng = RigControlEngine()
    spec = ControlledGateSpec(gate=eng.get_gate("X"), controls_top=(1,))
    qc = eng.controlled_qiskit_circuit(spec)
    u = Operator(qc).data
    assert u.shape == (4, 4)


def test_mixed_controls_x_engine_unitary():
    eng = RigControlEngine()
    spec = ControlledGateSpec(gate=eng.get_gate("X"), controls_top=(1, 0), controls_bottom=(1,))
    u = eng.controlled_unitary(spec)
    ident = np.eye(u.shape[0], dtype=complex)
    assert np.allclose(u.conj().T @ u, ident)


def test_controlled_identity_is_identity():
    eng = RigControlEngine()
    I = np.eye(2, dtype=complex)
    ig = eng.register_gate("I", I)
    spec = ControlledGateSpec(gate=ig, controls_top=(1, 0, 1))
    u = eng.controlled_unitary(spec)
    assert np.allclose(u, np.eye(2 ** spec.total_arity))


def test_controlled_swap_multi_qubit_target_supported():
    from qiskit.quantum_info import Operator

    eng = RigControlEngine()
    SWAP = np.array([
        [1, 0, 0, 0],
        [0, 0, 1, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
    ], dtype=complex)
    sg = eng.register_gate("SWAP2", SWAP)
    spec = ControlledGateSpec(gate=sg, controls_top=(1,))

    u = eng.controlled_unitary(spec)
    assert u.shape == (8, 8)
    assert np.allclose(u.conj().T @ u, np.eye(8))

    qc = eng.controlled_qiskit_circuit(spec)
    uq = Operator(qc).data
    assert uq.shape == (8, 8)
