"""QRMA scaling benchmark utilities."""

from qseb.audio.qrma_benchmark import (
    qrma_qubit_cost,
    frqa_multichannel_cost,
)


def evaluate_scaling(
    channels_list=(2, 4, 8, 16, 32),
    samples_list=(16, 32, 64),
    amplitude_bits=8,
):
    """Evaluate QRMA scaling against independent FRQA channels."""

    results = []

    for channels in channels_list:
        for samples in samples_list:
            qrma = qrma_qubit_cost(
                channels=channels,
                samples=samples,
                amplitude_bits=amplitude_bits,
            )

            frqa = frqa_multichannel_cost(
                channels=channels,
                samples=samples,
                amplitude_bits=amplitude_bits,
            )

            saving = (
                (frqa - qrma["total_qubits"])
                / frqa
                * 100
            )

            results.append(
                {
                    "channels": channels,
                    "samples": samples,
                    "frqa_qubits": frqa,
                    "qrma_qubits": qrma["total_qubits"],
                    "saving_percent": round(saving, 2),
                }
            )

    return results