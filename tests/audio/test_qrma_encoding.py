from qseb.audio.qrma_encoding import (
    encode_twos, decode_twos, build_qrma_circuit
)


def test_twos():
    assert encode_twos(-1, 3) == 7
    assert decode_twos(7, 3) == -1


def test_qrma_registers():
    audio = [[1, -2], [-1, 2]]
    circuit, spec = build_qrma_circuit(audio)

    assert spec.channels == 2
    assert spec.samples_per_channel == 2
    assert circuit.num_qubits == spec.total_qubits
