from __future__ import annotations

from pathlib import Path

FILES = [
    "README.md",
    "benchmark_blind_phase1.py",
    "benchmark_qiskit.py",
    "benchmark_shared_control_trap.py",
    "benchmark_strict_phase1.py",
    "discopy_bridge.py",
    "rig_ast.py",
    "rig_engine.py",
    "rig_qiskit_phase1.py",
    "tests/conftest.py",
    "tests/test_rig_ast.py",
    "tests/test_rig_engine.py",
    "tests/test_rig_simplify.py",
    "tests/test_strict_phase1.py",
    "tests/test_strict_phase1_nontrivial.py",
]


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    out = root / "REVIEW_SNAPSHOT.txt"

    parts = []
    for rel in FILES:
        p = root / rel
        if not p.exists():
            parts.append(f"===== FILE: {rel} =====\n[MISSING]\n")
            continue
        content = p.read_text(encoding="utf-8")
        parts.append(f"===== FILE: {rel} =====\n{content}\n")

    out.write_text("\n".join(parts), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
