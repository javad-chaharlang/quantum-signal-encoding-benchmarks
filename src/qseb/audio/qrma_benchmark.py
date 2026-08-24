"""Basic QRMA multichannel benchmark utilities."""

from math import ceil, log2


def required_bits(value):
    return max(1, ceil(log2(value)))


def qrma_qubit_cost(channels, samples, amplitude_bits):
    """Qubit cost for QRMA representation."""
    channel_bits = required_bits(channels)
    time_bits = required_bits(samples)

    return {
        "amplitude_qubits": amplitude_bits,
        "channel_qubits": channel_bits,
        "time_qubits": time_bits,
        "total_qubits": amplitude_bits + channel_bits + time_bits,
    }


def frqa_multichannel_cost(channels, samples, amplitude_bits):
    """Reference cost if each channel is encoded independently."""
    time_bits = required_bits(samples)

    return channels * (amplitude_bits + time_bits)