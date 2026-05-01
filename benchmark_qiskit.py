from __future__ import annotations

import time
from statistics import mean

from qiskit.quantum_info import Operator

from rig_engine import RigControlEngine, ControlledGateSpec


def bench(spec, rounds=200):
    eng = RigControlEngine()
    t0 = time.perf_counter()
    for _ in range(rounds):
        eng.controlled_unitary(spec)
    t1 = time.perf_counter()

    t2 = time.perf_counter()
    for _ in range(rounds):
        qc = eng.controlled_qiskit_circuit(spec)
        Operator(qc).data
    t3 = time.perf_counter()

    return {
        "engine_avg_ms": (t1 - t0) * 1000 / rounds,
        "qiskit_avg_ms": (t3 - t2) * 1000 / rounds,
    }


def main():
    eng = RigControlEngine()
    x = eng.get_gate("X")
    specs = [
        ControlledGateSpec(gate=x, controls_top=(1,)),
        ControlledGateSpec(gate=x, controls_top=(1, 0, 1)),
        ControlledGateSpec(gate=x, controls_top=(1, 1, 0, 1, 0)),
    ]

    for s in specs:
        res = bench(s)
        print(f"controls={s.total_controls}, arity={s.total_arity}: {res}")


if __name__ == "__main__":
    main()
