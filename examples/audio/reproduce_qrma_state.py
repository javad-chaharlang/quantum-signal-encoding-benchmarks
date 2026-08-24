from qseb.audio.qrma_encoding import (
    prepare_qrma_state,
    decode_qrma_samples,
    modify_qrma_sample,
)

audio = [
    [1, -2, 3, 0],
    [-1, 2, -3, 1],
]

circuit, spec, mapping = prepare_qrma_state(audio)

print("Channels:", spec.channels)
print("Samples/channel:", spec.samples_per_channel)
print("Amplitude qubits:", spec.amplitude_bits)
print("Channel qubits:", spec.channel_bits)
print("Time qubits:", spec.time_bits)
print("Total qubits:", spec.total_qubits)

print("Reconstruction:")
print(decode_qrma_samples(mapping, spec))

modified = modify_qrma_sample(mapping, 1, 2, 1)

print("Modified:")
print(decode_qrma_samples(modified, spec))
