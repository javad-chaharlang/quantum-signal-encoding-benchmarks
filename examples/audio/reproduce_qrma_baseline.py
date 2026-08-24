from qseb.audio.qrma_encoding import build_qrma_circuit

audio = [
    [1, -2, 3, 0],
    [-1, 2, -3, 1],
]

circuit, spec = build_qrma_circuit(audio)

print(spec)
print(circuit.draw())
