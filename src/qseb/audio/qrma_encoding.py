"""Minimal QRMA multichannel audio baseline."""

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


def build_qrma_circuit(audio, amplitude_bits=3):
    spec = QRMAEncodingSpec(
        len(audio),
        len(audio[0]),
        amplitude_bits,
    )

    amp = QuantumRegister(spec.amplitude_bits, "amplitude")
    ch = QuantumRegister(spec.channel_bits, "channel")
    tm = QuantumRegister(spec.time_bits, "time")

    circuit = QuantumCircuit(amp, ch, tm, name="QRMA")

    circuit.h(ch)
    circuit.h(tm)

    return circuit, spec


def validate_state(circuit):
    return Statevector.from_instruction(circuit)
