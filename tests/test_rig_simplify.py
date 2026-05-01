import numpy as np

from rig_engine import RigControlEngine, ControlledGateSpec, PlacedControlledOp


def test_shared_control_chain_auto_cancels():
    eng = RigControlEngine()
    X = eng.get_gate("X")
    I2 = eng.register_gate("I2", np.eye(4, dtype=complex))
    ctrl = (1, 1)

    # disjoint targets with inverse pairs around them
    ops = [
        PlacedControlledOp(ControlledGateSpec(X, controls_top=ctrl), target_offset=0),
        PlacedControlledOp(ControlledGateSpec(I2, controls_top=ctrl), target_offset=1),
        PlacedControlledOp(ControlledGateSpec(X, controls_top=ctrl), target_offset=0),
        PlacedControlledOp(ControlledGateSpec(I2, controls_top=ctrl), target_offset=1),
    ]
    simp = eng.simplify_controlled_chain(ops)
    assert simp == []
