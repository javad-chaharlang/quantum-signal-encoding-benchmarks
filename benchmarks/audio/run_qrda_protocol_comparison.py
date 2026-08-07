"""Compare the repository QRDA preparation with the primary-paper protocol."""

from __future__ import annotations

import csv
import json
import platform
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from qiskit import transpile
from qiskit.quantum_info import Statevector, state_fidelity

from qseb.audio import (
    build_qrda_circuit,
    exact_qrda_probabilities,
    signed_to_unsigned_samples,
)

PAPER_SIGNED_SAMPLES = (0, 3, 5, 7, 7, 5, 3, 0, -3, -5, -7, -7, -5, -3, 0)
PAPER_UNSIGNED_SAMPLES = (8, 11, 13, 15, 15, 13, 11, 8, 5, 3, 1, 1, 3, 5, 8)

AMPLITUDE_BITS = 4
EXPECTED_TIME_BITS = 4
EXPECTED_BOX_SIZE = 16
EXPECTED_PADDING_COUNT = 1
EXPECTED_CONTROLLED_WRITES = 33
EXPECTED_X_WRAPPERS = 64
BASIS_GATES = ("rz", "sx", "x", "cx")
OPTIMIZATION_LEVELS = (0, 1)
SEED_TRANSPILER = 42
RESULT_DIR = Path("results/audio/qrda_primary_paper")


def _package_version(package_name: str) -> str:
    try:
        return version(package_name)
    except PackageNotFoundError:
        return "unknown"


def _environment_metadata() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "qiskit": _package_version("qiskit"),
        "qiskit_aer": _package_version("qiskit-aer"),
    }


def _reference_statevector() -> Statevector:
    data = [0j] * (1 << 8)
    for time_index, sample in enumerate(PAPER_UNSIGNED_SAMPLES):
        data[sample + (time_index << AMPLITUDE_BITS)] = 1 / 4
    data[15 << AMPLITUDE_BITS] = 1 / 4
    return Statevector(data)


def _protocol_rows() -> list[dict[str, object]]:
    return [
        {
            "stage": "Step 1",
            "paper_definition": "I^q on amplitude register",
            "paper_count": AMPLITUDE_BITS,
            "qiskit_operation": "identity omitted",
            "qiskit_count": 0,
            "interpretation": "Equivalent no-op on the initialized amplitude register.",
        },
        {
            "stage": "Step 1",
            "paper_definition": "H^l on time register",
            "paper_count": EXPECTED_TIME_BITS,
            "qiskit_operation": "h",
            "qiskit_count": EXPECTED_TIME_BITS,
            "interpretation": "Direct logical match.",
        },
        {
            "stage": "Step 2",
            "paper_definition": "l-CNOT for each set amplitude bit",
            "paper_count": EXPECTED_CONTROLLED_WRITES,
            "qiskit_operation": "mcx",
            "qiskit_count": EXPECTED_CONTROLLED_WRITES,
            "interpretation": "Direct logical controlled-write count match.",
        },
        {
            "stage": "Step 2",
            "paper_definition": "open/closed time controls",
            "paper_count": "diagrammatic",
            "qiskit_operation": "x wrappers around mcx",
            "qiskit_count": EXPECTED_X_WRAPPERS,
            "interpretation": "Zero-controls are converted to all-one controls by X conjugation.",
        },
    ]


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    unsigned = signed_to_unsigned_samples(
        PAPER_SIGNED_SAMPLES,
        amplitude_bits=AMPLITUDE_BITS,
    )
    if unsigned != PAPER_UNSIGNED_SAMPLES:
        raise RuntimeError("paper quantization translation mismatch")

    circuit, spec = build_qrda_circuit(
        unsigned,
        amplitude_bits=AMPLITUDE_BITS,
        add_barriers=False,
    )

    actual_state = Statevector.from_instruction(circuit)
    expected_state = _reference_statevector()
    fidelity = float(state_fidelity(actual_state, expected_state))
    probabilities = exact_qrda_probabilities(circuit, spec)
    raw_ops = dict(circuit.count_ops())

    if spec.time_bits != EXPECTED_TIME_BITS:
        raise RuntimeError("unexpected time-register width")
    if spec.box_size != EXPECTED_BOX_SIZE:
        raise RuntimeError("unexpected QRDA box size")
    if spec.padding_count != EXPECTED_PADDING_COUNT:
        raise RuntimeError("unexpected padding count")
    if raw_ops.get("h", 0) != EXPECTED_TIME_BITS:
        raise RuntimeError("Hadamard count does not match the paper")
    if raw_ops.get("mcx", 0) != EXPECTED_CONTROLLED_WRITES:
        raise RuntimeError("controlled-write count does not match the paper")
    if raw_ops.get("x", 0) != EXPECTED_X_WRAPPERS:
        raise RuntimeError("zero-control X-wrapper count changed unexpectedly")
    if abs(fidelity - 1.0) > 1e-12:
        raise RuntimeError(f"state fidelity is not unity: {fidelity}")

    metric_rows: list[dict[str, object]] = [
        {
            "representation": "logical_qrda",
            "optimization_level": "raw",
            "num_qubits": circuit.num_qubits,
            "depth": circuit.depth(),
            "size": circuit.size(),
            "h": raw_ops.get("h", 0),
            "x": raw_ops.get("x", 0),
            "mcx": raw_ops.get("mcx", 0),
            "cx": raw_ops.get("cx", 0),
            "rz": raw_ops.get("rz", 0),
            "sx": raw_ops.get("sx", 0),
        }
    ]

    transpiled_reports: list[dict[str, object]] = []
    for optimization_level in OPTIMIZATION_LEVELS:
        compiled = transpile(
            circuit,
            basis_gates=list(BASIS_GATES),
            optimization_level=optimization_level,
            seed_transpiler=SEED_TRANSPILER,
        )
        operations = dict(compiled.count_ops())
        metric_rows.append(
            {
                "representation": "basis_transpiled",
                "optimization_level": optimization_level,
                "num_qubits": compiled.num_qubits,
                "depth": compiled.depth(),
                "size": compiled.size(),
                "h": operations.get("h", 0),
                "x": operations.get("x", 0),
                "mcx": operations.get("mcx", 0),
                "cx": operations.get("cx", 0),
                "rz": operations.get("rz", 0),
                "sx": operations.get("sx", 0),
            }
        )
        transpiled_reports.append(
            {
                "optimization_level": optimization_level,
                "basis_gates": list(BASIS_GATES),
                "seed_transpiler": SEED_TRANSPILER,
                "depth": compiled.depth(),
                "size": compiled.size(),
                "operations": operations,
            }
        )

    protocol_rows = _protocol_rows()
    protocol_csv = RESULT_DIR / "protocol_mapping.csv"
    metrics_csv = RESULT_DIR / "circuit_metrics.csv"
    _write_csv(protocol_csv, protocol_rows)
    _write_csv(metrics_csv, metric_rows)

    report = {
        "benchmark": "qrda_primary_paper_protocol_comparison",
        "environment": _environment_metadata(),
        "reference": {
            "author": "Jian Wang",
            "title": "QRDA: Quantum Representation of Digital Audio",
            "journal": "International Journal of Theoretical Physics",
            "year": 2016,
            "doi": "10.1007/s10773-015-2800-2",
            "validated_sections": {
                "representation": "Section 3.1, Eqs. (5)-(7)",
                "preparation": "Section 3.2, Eqs. (8)-(18), Figs. 3-4",
                "controlled_write_count": "Section 5.2.3 comparison of Figs. 4 and 11",
            },
        },
        "paper_example": {
            "num_samples": spec.num_samples,
            "amplitude_bits": spec.amplitude_bits,
            "time_bits": spec.time_bits,
            "total_qubits": spec.total_qubits,
            "box_size": spec.box_size,
            "padding_count": spec.padding_count,
            "controlled_amplitude_writes": EXPECTED_CONTROLLED_WRITES,
        },
        "state_equivalence": {
            "state_fidelity": fidelity,
            "exact_support_size": len(probabilities),
            "padding_state_probability": probabilities[(15, 0)],
            "passes": abs(fidelity - 1.0) <= 1e-12,
        },
        "logical_protocol": {
            "paper_h_count": EXPECTED_TIME_BITS,
            "qiskit_h_count": raw_ops.get("h", 0),
            "paper_controlled_write_count": EXPECTED_CONTROLLED_WRITES,
            "qiskit_mcx_count": raw_ops.get("mcx", 0),
            "qiskit_zero_control_x_wrappers": raw_ops.get("x", 0),
            "identity_gates_emitted": 0,
        },
        "raw_circuit": {
            "depth": circuit.depth(),
            "size": circuit.size(),
            "operations": raw_ops,
        },
        "transpiled_circuits": transpiled_reports,
        "interpretation": {
            "state_level": "Exact match.",
            "logical_write_level": "33 controlled amplitude writes match the paper.",
            "gate_for_gate_level": (
                "Not identical: the paper uses symbolic open/closed l-CNOT controls, "
                "whereas Qiskit realizes zero-controls with X conjugation around MCX "
                "and then decomposes MCX into the selected basis."
            ),
            "physical_resource_claim": (
                "Transpiled CX counts are implementation-dependent and are not "
                "identified with the paper's symbolic 4-CNOT count."
            ),
        },
    }

    output_path = RESULT_DIR / "protocol_comparison.json"
    output_path.write_text(
        json.dumps(report, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    print("QRDA primary-paper protocol comparison")
    print("--------------------------------------")
    print(f"State fidelity:             {fidelity:.12f}")
    print(f"Paper H count:              {EXPECTED_TIME_BITS}")
    print(f"Qiskit H count:             {raw_ops.get('h', 0)}")
    print(f"Paper controlled writes:    {EXPECTED_CONTROLLED_WRITES}")
    print(f"Qiskit MCX writes:          {raw_ops.get('mcx', 0)}")
    print(f"Qiskit X wrappers:          {raw_ops.get('x', 0)}")
    print(f"QRDA support states:        {len(probabilities)}")
    print(f"Padding probability:        {probabilities[(15, 0)]:.12f}")
    for item in transpiled_reports:
        print(
            f"O{item['optimization_level']}: "
            f"depth={item['depth']}, size={item['size']}, "
            f"CX={item['operations'].get('cx', 0)}"
        )
    print()
    print(f"Wrote: {output_path}")
    print(f"Wrote: {protocol_csv}")
    print(f"Wrote: {metrics_csv}")


if __name__ == "__main__":
    main()
