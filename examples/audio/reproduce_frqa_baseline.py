"""Reproduce the minimal FRQA baseline from Fig. 1 of Yan et al. (2018)."""

from __future__ import annotations

from math import isclose

from qseb.audio import (
    build_frqa_circuit,
    exact_frqa_probabilities,
    reconstruct_frqa_signal,
    signed_to_twos_complement,
    simulate_frqa_counts,
)

PAPER_EXAMPLE = [0, 1, 0, -1, 0, 2, 3, 1, -1, -2, -1, 0, 0]


def main() -> None:
    circuit, spec = build_frqa_circuit(PAPER_EXAMPLE, amplitude_bits=3)
    probabilities = exact_frqa_probabilities(circuit, spec)

    expected_support = {
        (time_index, amplitude): 1 / spec.box_size
        for time_index, amplitude in enumerate(PAPER_EXAMPLE)
    }
    for time_index in range(spec.num_samples, spec.box_size):
        expected_support[(time_index, 0)] = 1 / spec.box_size

    exact_match = set(probabilities) == set(expected_support) and all(
        isclose(probabilities[key], probability, abs_tol=1e-12)
        for key, probability in expected_support.items()
    )

    counts = simulate_frqa_counts(circuit, shots=4096, seed_simulator=42)
    reconstructed = reconstruct_frqa_signal(counts, spec)

    codes = [signed_to_twos_complement(value, spec.amplitude_bits) for value in PAPER_EXAMPLE]
    bitstrings = [format(code, f"0{spec.amplitude_bits}b") for code in codes]

    print("FRQA primary-paper Fig. 1 minimal reproduction")
    print("------------------------------------------------")
    print(f"Signed samples:        {PAPER_EXAMPLE}")
    print(f"Two's-complement:      {bitstrings}")
    print(f"Effective samples:     {spec.num_samples}")
    print(f"Amplitude qubits (q):  {spec.amplitude_bits}")
    print(f"Time qubits (l):       {spec.time_bits}")
    print(f"Total data qubits:     {spec.total_qubits}")
    print(f"FRQA box size:         {spec.box_size}")
    print(f"Redundant positions:   {spec.padding_count}")
    print(f"Support probability:   {1 / spec.box_size:.6f}")
    print(f"Exact support match:   {exact_match}")
    print(f"Shot reconstruction:   {reconstructed}")
    print(f"Round-trip exact:      {reconstructed == PAPER_EXAMPLE}")

    if not exact_match:
        raise RuntimeError("FRQA exact-state validation failed")
    if reconstructed != PAPER_EXAMPLE:
        raise RuntimeError("FRQA shot reconstruction failed")


if __name__ == "__main__":
    main()
