from qseb.audio.qrma_scaling import evaluate_scaling


def test_qrma_scaling_output():
    results = evaluate_scaling(
        channels_list=(2, 4),
        samples_list=(16,),
        amplitude_bits=8,
    )

    assert len(results) == 2
    assert results[0]["qrma_qubits"] < results[0]["frqa_qubits"]


def test_scaling_contains_metrics():
    results = evaluate_scaling(
        channels_list=(8,),
        samples_list=(32,),
    )

    item = results[0]

    assert "saving_percent" in item
    assert item["saving_percent"] > 0