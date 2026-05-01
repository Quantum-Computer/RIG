from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from qiskit.circuit.library import UnitaryGate

Bit = int
Word = Tuple[Bit, ...]


@dataclass(frozen=True)
class Gate:
    name: str
    arity: int
    matrix: np.ndarray

    def __post_init__(self):
        n = 2 ** self.arity
        if self.matrix.shape != (n, n):
            raise ValueError(f"{self.name}: matrix must be {(n, n)}")


@dataclass(frozen=True)
class ControlledGateSpec:
    gate: Gate
    controls_top: Word = ()
    controls_bottom: Word = ()

    @property
    def total_controls(self) -> int:
        return len(self.controls_top) + len(self.controls_bottom)

    @property
    def total_arity(self) -> int:
        return self.total_controls + self.gate.arity


@dataclass(frozen=True)
class PlacedControlledOp:
    spec: ControlledGateSpec
    target_offset: int  # offset in target register (post-controls)

    @property
    def target_interval(self) -> Tuple[int, int]:
        return (self.target_offset, self.target_offset + self.spec.gate.arity)


class RigControlEngine:
    def __init__(self):
        self.base_gates: Dict[str, Gate] = {}
        self.register_not_gate()

    def register_gate(self, name: str, matrix: np.ndarray) -> Gate:
        matrix = np.array(matrix, dtype=complex)
        log2n = np.log2(matrix.shape[0])
        if matrix.shape[0] != matrix.shape[1] or abs(log2n - round(log2n)) > 1e-10:
            raise ValueError("gate matrix must be square of dimension 2^n")
        arity = int(round(log2n))
        gate = Gate(name=name, arity=arity, matrix=matrix)
        self.base_gates[name] = gate
        return gate

    def register_not_gate(self) -> Gate:
        x = np.array([[0, 1], [1, 0]], dtype=complex)
        return self.register_gate("X", x)

    def get_gate(self, name: str) -> Gate:
        return self.base_gates[name]

    def controlled_unitary(self, spec: ControlledGateSpec) -> np.ndarray:
        n = spec.total_arity
        d = 2 ** n
        out = np.zeros((d, d), dtype=complex)
        ctrl_pattern = spec.controls_top + spec.controls_bottom
        ctrl_n = len(ctrl_pattern)
        tgt_n = spec.gate.arity

        for idx in range(d):
            bits = self._index_to_bits(idx, n)
            if bits[:ctrl_n] == ctrl_pattern:
                src_t = self._bits_to_index(bits[ctrl_n: ctrl_n + tgt_n])
                for dst_t in range(2 ** tgt_n):
                    amp = spec.gate.matrix[dst_t, src_t]
                    if abs(amp) > 0:
                        dst_bits = bits[:ctrl_n] + self._index_to_bits(dst_t, tgt_n)
                        out[self._bits_to_index(dst_bits), idx] = amp
            else:
                out[idx, idx] = 1
        return out

    def controlled_qiskit_circuit(self, spec: ControlledGateSpec) -> QuantumCircuit:
        n = spec.total_arity
        qc = QuantumCircuit(n)
        gate = UnitaryGate(spec.gate.matrix, label=spec.gate.name)
        ctrl_pattern = spec.controls_top + spec.controls_bottom
        ctrl_n = len(ctrl_pattern)
        ctrl_state = int(''.join(str(b) for b in ctrl_pattern[::-1]), 2) if ctrl_n else None
        cgate = gate.control(ctrl_n, ctrl_state=ctrl_state) if ctrl_n else gate
        qc.append(cgate, list(range(n)))
        return qc

    def simplify_controlled_chain(self, ops: List[PlacedControlledOp]) -> List[PlacedControlledOp]:
        """Automatic Phase-1 structural simplification.

        Rules used (general, not benchmark-specific):
        1) Same-control ops on disjoint targets commute.
        2) Adjacent inverse pairs on same controls+target cancel.
        Repeats to fixed point.
        """
        out = list(ops)
        changed = True
        while changed:
            changed = False
            # bubble-sort commuting disjoint operations into canonical target order
            for i in range(len(out) - 1):
                a, b = out[i], out[i + 1]
                if self._same_controls(a, b) and self._disjoint(a.target_interval, b.target_interval):
                    if a.target_offset > b.target_offset:
                        out[i], out[i + 1] = out[i + 1], out[i]
                        changed = True
            # cancel adjacent inverses
            i = 0
            collapsed: List[PlacedControlledOp] = []
            while i < len(out):
                if i + 1 < len(out) and self._can_cancel(out[i], out[i + 1]):
                    changed = True
                    i += 2
                else:
                    collapsed.append(out[i])
                    i += 1
            out = collapsed
        return out

    def verify_qiskit_equivalence(self, spec: ControlledGateSpec, atol: float = 1e-9) -> bool:
        return np.allclose(self.controlled_unitary(spec), Operator(self.controlled_qiskit_circuit(spec)).data, atol=atol)

    def _same_controls(self, a: PlacedControlledOp, b: PlacedControlledOp) -> bool:
        return (a.spec.controls_top, a.spec.controls_bottom) == (b.spec.controls_top, b.spec.controls_bottom)

    @staticmethod
    def _disjoint(x: Tuple[int, int], y: Tuple[int, int]) -> bool:
        return x[1] <= y[0] or y[1] <= x[0]

    def _can_cancel(self, a: PlacedControlledOp, b: PlacedControlledOp, atol: float = 1e-9) -> bool:
        same_slot = a.target_interval == b.target_interval
        same_ctrl = self._same_controls(a, b)
        inv = np.allclose(a.spec.gate.matrix @ b.spec.gate.matrix, np.eye(2 ** a.spec.gate.arity), atol=atol)
        return same_slot and same_ctrl and inv

    @staticmethod
    def _index_to_bits(i: int, n: int) -> Word:
        return tuple((i >> (n - 1 - k)) & 1 for k in range(n))

    @staticmethod
    def _bits_to_index(bits: Word) -> int:
        x = 0
        for b in bits:
            x = (x << 1) | b
        return x
