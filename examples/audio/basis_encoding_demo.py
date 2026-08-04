"""Run a complete basis-encoded quantum audio demonstration."""

from __future__ import annotations

from pprint import pprint

from qseb.audio import (
    build_basis_encoded_audio_circuit,
    circuit_resource_metrics,
    exact_basis_probabilities,
    reconstruct_from_counts,
    simulate_counts,
)


def main() -> None:
    samples = [3, 6, 2, 5]
    circuit, spec = build_basis_encoded_audio_circuit(samples, amplitude_bits=3)

    print("Original samples:", samples)
    print("Encoding specification:", spec)
    print("\nCircuit:\n")
    print(circuit.draw(output="text", fold=120))

    print("\nExact non-zero basis probabilities:")
    pprint(exact_basis_probabilities(circuit, spec))

    counts = simulate_counts(circuit, shots=4096, seed_simulator=42)
    reconstructed = reconstruct_from_counts(counts, spec)

    print("\nReconstructed samples:", reconstructed)
    print("Exact reconstruction:", reconstructed == samples)

    print("\nResource metrics:")
    pprint(circuit_resource_metrics(circuit))


if __name__ == "__main__":
    main()
