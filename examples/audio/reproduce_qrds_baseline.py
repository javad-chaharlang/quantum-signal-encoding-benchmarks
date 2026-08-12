"""Reproduce the minimal validated QRDS fixed-point baseline."""

from __future__ import annotations

from fractions import Fraction
from math import isclose
from pathlib import Path

from qseb.audio import (
    build_qrds_circuit,
    exact_qrds_probabilities,
    fixed_point_to_twos_complement,
    qrds_resource_metrics,
    reconstruct_qrds_signal,
    simulate_qrds_counts,
)

PAPER_COMPACT_SIGNAL = [
    2.25,
    0.75,
    -1.25,
    1.50,
    2.50,
    -1.00,
]


def main() -> None:
    circuit, spec = build_qrds_circuit(
        PAPER_COMPACT_SIGNAL,
        integer_bits=2,
        fractional_bits=2,
    )

    probabilities = exact_qrds_probabilities(
        circuit,
        spec,
    )

    expected_signal = [Fraction(str(value)) for value in PAPER_COMPACT_SIGNAL]

    expected_support = {
        (position, amplitude): 1 / spec.box_size
        for position, amplitude in enumerate(expected_signal)
    }

    for position in range(spec.num_samples, spec.box_size):
        expected_support[(position, Fraction(0, 1))] = 1 / spec.box_size

    exact_match = set(probabilities) == set(expected_support) and all(
        isclose(
            probabilities[key],
            probability,
            abs_tol=1e-12,
        )
        for key, probability in expected_support.items()
    )

    counts = simulate_qrds_counts(
        circuit,
        shots=8192,
        seed_simulator=42,
    )

    reconstructed = reconstruct_qrds_signal(
        counts,
        spec,
    )

    codes = [
        fixed_point_to_twos_complement(
            value,
            integer_bits=spec.integer_bits,
            fractional_bits=spec.fractional_bits,
        )
        for value in PAPER_COMPACT_SIGNAL
    ]

    bitstrings = [format(code, f"0{spec.amplitude_bits}b") for code in codes]

    metrics = qrds_resource_metrics(circuit)

    print("QRDS minimal fixed-point reproduction")
    print("-------------------------------------")
    print(f"Signal:                 {PAPER_COMPACT_SIGNAL}")
    print(f"Fixed-point codes:      {bitstrings}")
    print(f"Effective samples:      {spec.num_samples}")
    print(f"Integer bits (m):       {spec.integer_bits}")
    print(f"Fractional bits:        {spec.fractional_bits}")
    print(f"Amplitude qubits:       {spec.amplitude_bits}")
    print(f"Position qubits (k):    {spec.position_bits}")
    print(f"Total data qubits:      {spec.total_qubits}")
    print(f"QRDS box size:          {spec.box_size}")
    print(f"Redundant positions:    {spec.padding_count}")
    print(f"Amplitude quantum:      {spec.quantum}")
    print(f"Support probability:    {1 / spec.box_size:.6f}")
    print(f"Exact support match:    {exact_match}")
    print(f"Shot reconstruction:    {reconstructed}")
    print(f"Round-trip exact:       {reconstructed == expected_signal}")
    print()
    print("Logical circuit resources")
    print("-------------------------")
    print(f"Raw depth:              {metrics['raw_depth']}")
    print(f"Raw size:               {metrics['raw_size']}")
    print(f"Raw operations:         {metrics['raw_operations']}")
    print(f"Transpiled depth:       {metrics['transpiled_depth']}")
    print(f"Transpiled size:        {metrics['transpiled_size']}")
    print(f"Transpiled operations:  {metrics['transpiled_operations']}")

    output_dir = Path("figures/audio/qrds")
    output_dir.mkdir(parents=True, exist_ok=True)

    figure = circuit.draw(
        output="mpl",
        fold=120,
        idle_wires=True,
    )

    figure.savefig(
        output_dir / "qrds_logical_circuit.png",
        dpi=220,
        bbox_inches="tight",
    )

    figure.savefig(
        output_dir / "qrds_logical_circuit.pdf",
        bbox_inches="tight",
    )

    print()
    print("Saved logical circuit:")
    print("  figures/audio/qrds/qrds_logical_circuit.png")
    print("  figures/audio/qrds/qrds_logical_circuit.pdf")

    if not exact_match:
        raise RuntimeError("QRDS exact-state validation failed")

    if reconstructed != expected_signal:
        raise RuntimeError("QRDS shot reconstruction failed")


if __name__ == "__main__":
    main()
