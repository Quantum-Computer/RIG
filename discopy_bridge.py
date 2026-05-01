from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np
from discopy.monoidal import Ty, Diagram, Box

from rig_engine import RigControlEngine, ControlledGateSpec


@dataclass
class ControlledBox(Box):
    spec: ControlledGateSpec

    def __init__(self, spec: ControlledGateSpec):
        dom = Ty(*(["bit"] * spec.total_arity))
        cod = dom
        name = f"C[{spec.controls_top}|{spec.controls_bottom}]({spec.gate.name})"
        super().__init__(name, dom, cod)
        self.spec = spec


def controlled_box(spec: ControlledGateSpec) -> ControlledBox:
    return ControlledBox(spec)


def as_diagram(spec: ControlledGateSpec) -> Diagram:
    return controlled_box(spec)


def as_unitary(engine: RigControlEngine, spec: ControlledGateSpec) -> np.ndarray:
    return engine.controlled_unitary(spec)
