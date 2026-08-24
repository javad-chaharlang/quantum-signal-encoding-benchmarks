from qseb.audio.qrma_scaling import evaluate_scaling


results = evaluate_scaling()

print("QRMA Scaling Benchmark")
print("---------------------")

for item in results:
    print(
        f"Channels={item['channels']}, "
        f"Samples={item['samples']}, "
        f"FRQA={item['frqa_qubits']} qubits, "
        f"QRMA={item['qrma_qubits']} qubits, "
        f"Saving={item['saving_percent']}%"
    )