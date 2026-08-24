"""QRMA v0.2 state preparation baseline.

Backward compatible version:
- keeps build_qrma_circuit() from v0.1
- adds state preparation helpers from v0.2
"""

from dataclasses import dataclass
from math import ceil, log2

from qiskit import QuantumCircuit, QuantumRegister
from qiskit.quantum_info import Statevector


@dataclass(frozen=True)
class QRMAEncodingSpec:
    channels: int
    samples_per_channel: int
    amplitude_bits: int

    @property
    def channel_bits(self):
        return max(1, ceil(log2(self.channels)))

    @property
    def time_bits(self):
        return max(1, ceil(log2(self.samples_per_channel)))

    @property
    def total_qubits(self):
        return self.amplitude_bits + self.channel_bits + self.time_bits


def encode_twos(value, bits):
    return (1 << bits) + value if value < 0 else value


def decode_twos(code, bits):
    return code - (1 << bits) if code & (1 << (bits - 1)) else code


def prepare_qrma_state(audio, amplitude_bits=3):
    spec = QRMAEncodingSpec(
        len(audio),
        len(audio[0]),
        amplitude_bits
    )

    amp = QuantumRegister(spec.amplitude_bits, "amplitude")
    ch = QuantumRegister(spec.channel_bits, "channel")
    tm = QuantumRegister(spec.time_bits, "time")

    circuit = QuantumCircuit(amp, ch, tm, name="QRMA")

    circuit.h(ch)
    circuit.h(tm)

    encoded = {
        (c, t): encode_twos(audio[c][t], amplitude_bits)
        for c in range(spec.channels)
        for t in range(spec.samples_per_channel)
    }

    return circuit, spec, encoded


def build_qrma_circuit(audio, amplitude_bits=3):
    """
    Backward-compatible API from QRMA v0.1.
    """
    circuit, spec, _ = prepare_qrma_state(
        audio,
        amplitude_bits
    )
    return circuit, spec


def decode_qrma_samples(audio_map, spec):
    result = [
        [0 for _ in range(spec.samples_per_channel)]
        for _ in range(spec.channels)
    ]

    for (c, t), value in audio_map.items():
        result[c][t] = decode_twos(
            value,
            spec.amplitude_bits
        )

    return result


def modify_qrma_sample(audio_map, channel, time, value, bits=3):
    updated = dict(audio_map)
    updated[(channel, time)] = encode_twos(value, bits)
    return updated


def validate_state(circuit):
    return Statevector.from_instruction(circuit)
