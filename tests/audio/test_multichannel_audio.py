from qseb.audio.multichannel import create_stereo_example
from qseb.audio.qrma_benchmark import qrma_qubit_cost


def test_multichannel_structure():
    audio = create_stereo_example()

    assert audio.channels == 2
    assert audio.samples_per_channel == 4


def test_qrma_cost():
    cost = qrma_qubit_cost(
        channels=2,
        samples=4,
        amplitude_bits=3,
    )

    assert cost["channel_qubits"] == 1
    assert cost["time_qubits"] == 2
    assert cost["total_qubits"] == 6