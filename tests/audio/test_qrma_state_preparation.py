from qseb.audio.qrma_encoding import (
    prepare_qrma_state,
    decode_qrma_samples,
    modify_qrma_sample,
)


def test_qrma_round_trip():
    audio = [
        [1, -2, 3, 0],
        [-1, 2, -3, 1],
    ]

    circuit, spec, mapping = prepare_qrma_state(audio)

    assert decode_qrma_samples(mapping, spec) == audio
    assert circuit.num_qubits == spec.total_qubits


def test_local_modification():
    audio = [
        [1, -2, 3, 0],
        [-1, 2, -3, 1],
    ]

    _, spec, mapping = prepare_qrma_state(audio)

    modified = modify_qrma_sample(mapping, 1, 2, 1)
    result = decode_qrma_samples(modified, spec)

    assert result[0] == audio[0]
    assert result[1] == [-1, 2, 1, 1]
