from qseb.audio.multichannel import create_stereo_example
from qseb.audio.qrma_benchmark import qrma_qubit_cost

audio = create_stereo_example()

cost = qrma_qubit_cost(
    channels=audio.channels,
    samples=audio.samples_per_channel,
    amplitude_bits=3,
)

print("Multichannel Audio Benchmark")
print("----------------------------")
print("Channels:", audio.channels)
print("Samples/channel:", audio.samples_per_channel)
print("QRMA cost:", cost)