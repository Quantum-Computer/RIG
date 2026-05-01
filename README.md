# RIG Engine (Rig-to-Control)

This repository implements a generalized practical control engine inspired by *One rig to control them all*.

## Features
- Register arbitrary base gates (unitary/permutation matrices of size `2^n`).
- Build generalized mixed-sign controlled gates `C_w'^w(f)`.
- Export directly to Qiskit circuits with `ctrl_state`.
- Verify matrix-level equivalence between engine semantics and Qiskit semantics.
- Minimal DisCoPy bridge for diagram-level expression of controlled operations.
- Qiskit benchmark script.

## Install
```bash
python -m pip install qiskit discopy pytest numpy
```

## Test
```bash
pytest -q
```

## Benchmark
```bash
python benchmark_qiskit.py
```

## Shared-Control Trap benchmark (Rig Phase 1 vs Qiskit DAG)
```bash
python benchmark_shared_control_trap.py
```
This script runs a real transpilation comparison between direct Qiskit composition and a rig-factored structural form.
