"""Protocol-level regression tests for the primary QRDA paper example."""

from __future__ import annotations

import math

from qiskit import transpile
from qiskit.quantum_info import Statevector, state_fidelity

from qseb.audio import build_qrda_circuit, signed_to_unsigned_samples

PAPER_SIGNED_SAMPLES = (0, 3, 5, 7, 7, 5, 3, 0, -3, -5, -7, -7, -5, -3, 0)

PAPER_UNSIGNED_SAMPLES = (8, 11, 13, 15, 15, 13, 11, 8, 5, 3, 1, 1, 3, 5, 8)


def _paper_circuit():
    samples = signed_to_unsigned_samples(PAPER_SIGNED_SAMPLES, amplitude_bits=4)
    return build_qrda_circuit(samples, amplitude_bits=4, add_barriers=False)


def _reference_statevector() -> Statevector:
    data = [0j] * (1 << 8)
    for time_index, sample in enumerate(PAPER_UNSIGNED_SAMPLES):
        data[sample + (time_index << 4)] = 1 / 4
    data[15 << 4] = 1 / 4
    return Statevector(data)


def test_primary_paper_logical_operation_counts() -> None:
    circuit, _ = _paper_circuit()
    operations = circuit.count_ops()
    assert operations.get("h", 0) == 4
    assert operations.get("mcx", 0) == 33
    assert operations.get("x", 0) == 64


def test_primary_paper_state_fidelity_is_unity() -> None:
    circuit, _ = _paper_circuit()
    actual = Statevector.from_instruction(circuit)
    expected = _reference_statevector()
    assert math.isclose(
        float(state_fidelity(actual, expected)),
        1.0,
        abs_tol=1e-12,
    )


def test_primary_paper_identity_gates_need_not_be_emitted() -> None:
    circuit, _ = _paper_circuit()
    assert circuit.count_ops().get("id", 0) == 0


def test_primary_paper_transpiles_to_selected_basis() -> None:
    circuit, _ = _paper_circuit()
    compiled = transpile(
        circuit,
        basis_gates=["rz", "sx", "x", "cx"],
        optimization_level=1,
        seed_transpiler=42,
    )
    allowed = {"rz", "sx", "x", "cx", "barrier"}
    assert set(compiled.count_ops()).issubset(allowed)
    assert compiled.count_ops().get("mcx", 0) == 0
    assert compiled.num_qubits == 8
