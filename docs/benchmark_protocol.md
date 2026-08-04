# Benchmark Protocol

Every method comparison must use a predefined protocol so that conclusions are not driven by undocumented implementation choices.

## Required metadata

- Method name and version
- Primary reference
- Commit SHA
- Python, Qiskit, and simulator versions
- Operating system and hardware
- Input signal dimensions and quantization
- Random seeds
- Shots
- Transpiler backend and optimization level
- Noise model or hardware calibration timestamp

## Correctness checks

1. Verify register widths and ordering.
2. Verify exact state probabilities on the smallest examples.
3. Verify decoding independently from state preparation.
4. Reconstruct the classical signal.
5. Report failures and unsupported inputs explicitly.

## Resource metrics

Report both raw and transpiled values:

- Data qubits
- Ancilla qubits
- Circuit size
- Circuit depth
- One-qubit gates
- Two-qubit gates
- Multi-controlled operations before decomposition
- State-preparation runtime
- Simulation runtime and peak memory where practical

## Reconstruction metrics

Depending on the representation:

- Exact sample recovery rate
- Mean absolute error
- Mean squared error
- Signal-to-noise ratio
- Fidelity or probability-distribution distance
- Time-index coverage under finite shots

## Experimental design

- Use multiple seeds when stochastic effects are present.
- Report mean, standard deviation, and confidence intervals where appropriate.
- Keep preprocessing identical across compared methods.
- Separate ideal statevector, shot-based, noisy simulation, and hardware results.
- Do not infer scalability from only tiny examples.

## Reporting negative results

A method that fails to scale, reconstruct reliably, or survive noise still provides useful evidence. Record the failure boundary, probable cause, and reproducible configuration instead of omitting the experiment.
