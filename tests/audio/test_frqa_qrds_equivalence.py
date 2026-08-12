"""Controlled equivalence tests for FRQA and QRDS basis preparation."""

from fractions import Fraction

from qseb.audio import (
    build_frqa_circuit,
    build_qrds_circuit,
    exact_frqa_probabilities,
    exact_qrds_probabilities,
    fixed_point_to_twos_complement,
    qrds_resource_metrics,
    signed_to_twos_complement,
)

QRDS_SIGNAL = [
    2.25,
    0.75,
    -1.25,
    1.50,
    2.50,
    -1.00,
]

FRACTIONAL_BITS = 2
SCALE = 1 << FRACTIONAL_BITS

FRQA_SCALED_SIGNAL = [int(Fraction(str(value)) * SCALE) for value in QRDS_SIGNAL]


def test_qrds_and_scaled_frqa_codes_are_identical() -> None:
    qrds_circuit, qrds_spec = build_qrds_circuit(
        QRDS_SIGNAL,
        integer_bits=2,
        fractional_bits=FRACTIONAL_BITS,
    )

    _, frqa_spec = build_frqa_circuit(
        FRQA_SCALED_SIGNAL,
        amplitude_bits=5,
    )

    qrds_codes = [
        fixed_point_to_twos_complement(
            value,
            integer_bits=qrds_spec.integer_bits,
            fractional_bits=qrds_spec.fractional_bits,
        )
        for value in QRDS_SIGNAL
    ]

    frqa_codes = [
        signed_to_twos_complement(
            value,
            frqa_spec.amplitude_bits,
        )
        for value in FRQA_SCALED_SIGNAL
    ]

    assert qrds_codes == frqa_codes
    assert qrds_circuit.num_qubits == frqa_spec.total_qubits


def test_qrds_and_scaled_frqa_state_support_are_equivalent() -> None:
    qrds_circuit, qrds_spec = build_qrds_circuit(
        QRDS_SIGNAL,
        integer_bits=2,
        fractional_bits=FRACTIONAL_BITS,
    )

    frqa_circuit, frqa_spec = build_frqa_circuit(
        FRQA_SCALED_SIGNAL,
        amplitude_bits=5,
    )

    qrds_probabilities = exact_qrds_probabilities(
        qrds_circuit,
        qrds_spec,
    )

    frqa_probabilities = exact_frqa_probabilities(
        frqa_circuit,
        frqa_spec,
    )

    qrds_scaled_support = {
        (position, int(amplitude * SCALE)): probability
        for (position, amplitude), probability in qrds_probabilities.items()
    }

    assert qrds_scaled_support == frqa_probabilities


def test_qrds_and_scaled_frqa_register_widths_match() -> None:
    _, qrds_spec = build_qrds_circuit(
        QRDS_SIGNAL,
        integer_bits=2,
        fractional_bits=FRACTIONAL_BITS,
    )

    _, frqa_spec = build_frqa_circuit(
        FRQA_SCALED_SIGNAL,
        amplitude_bits=5,
    )

    assert qrds_spec.amplitude_bits == frqa_spec.amplitude_bits
    assert qrds_spec.position_bits == frqa_spec.time_bits
    assert qrds_spec.total_qubits == frqa_spec.total_qubits


def test_qrds_and_scaled_frqa_logical_resources_match() -> None:
    qrds_circuit, _ = build_qrds_circuit(
        QRDS_SIGNAL,
        integer_bits=2,
        fractional_bits=FRACTIONAL_BITS,
    )

    frqa_circuit, _ = build_frqa_circuit(
        FRQA_SCALED_SIGNAL,
        amplitude_bits=5,
    )

    qrds_metrics = qrds_resource_metrics(qrds_circuit)
    frqa_metrics = qrds_resource_metrics(frqa_circuit)

    assert qrds_metrics["num_qubits"] == frqa_metrics["num_qubits"]
    assert qrds_metrics["raw_depth"] == frqa_metrics["raw_depth"]
    assert qrds_metrics["raw_size"] == frqa_metrics["raw_size"]
    assert qrds_metrics["raw_operations"] == frqa_metrics["raw_operations"]


def test_qrds_and_scaled_frqa_transpiled_resources_match() -> None:
    qrds_circuit, _ = build_qrds_circuit(
        QRDS_SIGNAL,
        integer_bits=2,
        fractional_bits=FRACTIONAL_BITS,
    )

    frqa_circuit, _ = build_frqa_circuit(
        FRQA_SCALED_SIGNAL,
        amplitude_bits=5,
    )

    qrds_metrics = qrds_resource_metrics(qrds_circuit)
    frqa_metrics = qrds_resource_metrics(frqa_circuit)

    assert qrds_metrics["transpiled_depth"] == frqa_metrics["transpiled_depth"]

    assert qrds_metrics["transpiled_size"] == frqa_metrics["transpiled_size"]

    assert qrds_metrics["transpiled_operations"] == frqa_metrics["transpiled_operations"]
