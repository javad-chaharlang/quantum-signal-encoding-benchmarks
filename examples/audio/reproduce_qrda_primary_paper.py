"""Reproduce the primary QRDA paper's 15-sample worked example.

Primary reference:
    Wang, J. (2016). QRDA: Quantum Representation of Digital Audio.
    International Journal of Theoretical Physics, 55, 1622-1641.
    https://doi.org/10.1007/s10773-015-2800-2

The paper starts from the signed 4-bit signal

    [0, 3, 5, 7, 7, 5, 3, 0, -3, -5, -7, -7, -5, -3, 0]

and translates it by +8 to the unsigned QRDA amplitudes

    [8, 11, 13, 15, 15, 13, 11, 8, 5, 3, 1, 1, 3, 5, 8].

For L=15 samples and q=4 amplitude bits, the QRDA paper uses l=4 time
qubits. The resulting 2^l box has 16 time positions, so T=15 is a redundant
padding state with zero amplitude.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from qiskit.quantum_info import Statevector

from qseb.audio import (
    build_qrda_circuit,
    exact_qrda_probabilities,
    reconstruct_qrda_signal,
    signed_to_unsigned_samples,
    simulate_qrda_counts,
    unsigned_to_signed_samples,
)

PAPER_SIGNED_SAMPLES = (
    0,
    3,
    5,
    7,
    7,
    5,
    3,
    0,
    -3,
    -5,
    -7,
    -7,
    -5,
    -3,
    0,
)

PAPER_UNSIGNED_SAMPLES = (
    8,
    11,
    13,
    15,
    15,
    13,
    11,
    8,
    5,
    3,
    1,
    1,
    3,
    5,
    8,
)

AMPLITUDE_BITS = 4
SHOTS = 16384
SEED_SIMULATOR = 42


def _expected_support() -> dict[tuple[int, int], float]:
    """Return the exact QRDA support expected from the paper example."""

    support = {
        (time_index, amplitude): 1 / 16
        for time_index, amplitude in enumerate(PAPER_UNSIGNED_SAMPLES)
    }
    support[(15, 0)] = 1 / 16
    return support


def _count_amplitude_write_bits(samples: tuple[int, ...]) -> int:
    """Count the number of set amplitude bits loaded by the paper protocol."""

    return sum(sample.bit_count() for sample in samples)


def _write_support_csv(
    output_path: Path,
    probabilities: dict[tuple[int, int], float],
) -> None:
    """Write exact state support to CSV."""

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "time_index",
                "time_bits",
                "amplitude",
                "amplitude_bits",
                "probability",
            ],
        )
        writer.writeheader()

        for (time_index, amplitude), probability in sorted(probabilities.items()):
            writer.writerow(
                {
                    "time_index": time_index,
                    "time_bits": format(time_index, "04b"),
                    "amplitude": amplitude,
                    "amplitude_bits": format(amplitude, "04b"),
                    "probability": probability,
                }
            )


def main() -> None:
    unsigned = signed_to_unsigned_samples(
        PAPER_SIGNED_SAMPLES,
        amplitude_bits=AMPLITUDE_BITS,
    )

    if unsigned != PAPER_UNSIGNED_SAMPLES:
        raise RuntimeError("signed-to-unsigned conversion does not match the paper")

    circuit, spec = build_qrda_circuit(
        unsigned,
        amplitude_bits=AMPLITUDE_BITS,
    )

    probabilities = exact_qrda_probabilities(circuit, spec)
    expected_probabilities = _expected_support()

    if set(probabilities) != set(expected_probabilities):
        raise RuntimeError("QRDA state support does not match the paper example")

    for key, expected_probability in expected_probabilities.items():
        actual_probability = probabilities[key]
        if abs(actual_probability - expected_probability) > 1e-12:
            raise RuntimeError(
                f"probability mismatch for {key}: {actual_probability} != {expected_probability}"
            )

    statevector = Statevector.from_instruction(circuit)
    nonzero_amplitudes = [
        complex(amplitude) for amplitude in statevector.data if abs(amplitude) > 1e-12
    ]

    counts = simulate_qrda_counts(
        circuit,
        shots=SHOTS,
        seed_simulator=SEED_SIMULATOR,
    )
    reconstructed_unsigned = tuple(reconstruct_qrda_signal(counts, spec))
    reconstructed_signed = unsigned_to_signed_samples(
        reconstructed_unsigned,
        amplitude_bits=AMPLITUDE_BITS,
    )

    controlled_write_count = _count_amplitude_write_bits(PAPER_UNSIGNED_SAMPLES)

    report = {
        "reference": {
            "title": "QRDA: Quantum Representation of Digital Audio",
            "author": "Jian Wang",
            "journal": "International Journal of Theoretical Physics",
            "year": 2016,
            "doi": "10.1007/s10773-015-2800-2",
        },
        "paper_example": {
            "signed_samples": list(PAPER_SIGNED_SAMPLES),
            "unsigned_samples": list(PAPER_UNSIGNED_SAMPLES),
            "amplitude_bits": AMPLITUDE_BITS,
            "num_samples": spec.num_samples,
            "time_bits": spec.time_bits,
            "box_size": spec.box_size,
            "padding_count": spec.padding_count,
            "padding_time_indices": list(range(spec.num_samples, spec.box_size)),
            "total_qubits": spec.total_qubits,
        },
        "statevector_validation": {
            "nonzero_basis_states": len(probabilities),
            "nonzero_amplitudes": len(nonzero_amplitudes),
            "expected_probability_per_state": 1 / 16,
            "padding_state": {
                "time_index": 15,
                "amplitude": 0,
                "probability": probabilities[(15, 0)],
            },
            "support_matches_paper": set(probabilities) == set(expected_probabilities),
        },
        "preparation_protocol": {
            "set_amplitude_bits": controlled_write_count,
            "paper_reported_controlled_writes": 33,
            "matches_paper_count": controlled_write_count == 33,
            "raw_operation_counts": dict(circuit.count_ops()),
            "raw_depth": circuit.depth(),
            "raw_size": circuit.size(),
        },
        "shot_validation": {
            "shots": SHOTS,
            "seed_simulator": SEED_SIMULATOR,
            "unsigned_reconstruction": list(reconstructed_unsigned),
            "signed_reconstruction": list(reconstructed_signed),
            "unsigned_exact": reconstructed_unsigned == PAPER_UNSIGNED_SAMPLES,
            "signed_exact": reconstructed_signed == PAPER_SIGNED_SAMPLES,
        },
    }

    output_dir = Path("results/audio/qrda_primary_paper")
    output_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "validation_report.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )
    _write_support_csv(
        output_dir / "statevector_support.csv",
        probabilities,
    )

    print("QRDA primary-paper reproduction")
    print("--------------------------------")
    print(f"Signed samples:        {PAPER_SIGNED_SAMPLES}")
    print(f"Unsigned samples:      {PAPER_UNSIGNED_SAMPLES}")
    print(f"Amplitude qubits:      {spec.amplitude_bits}")
    print(f"Time qubits:           {spec.time_bits}")
    print(f"Total qubits:          {spec.total_qubits}")
    print(f"Effective samples:     {spec.num_samples}")
    print(f"QRDA box size:         {spec.box_size}")
    print(f"Padding states:        {spec.padding_count}")
    print(f"Nonzero basis states:  {len(probabilities)}")
    print(f"Probability per state: {1 / 16}")
    print(f"Controlled writes:     {controlled_write_count}")
    print(f"Unsigned exact:        {reconstructed_unsigned == PAPER_UNSIGNED_SAMPLES}")
    print(f"Signed exact:          {reconstructed_signed == PAPER_SIGNED_SAMPLES}")
    print()
    print(f"Results written to:    {output_dir}")


if __name__ == "__main__":
    main()
