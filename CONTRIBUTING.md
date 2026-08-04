# Contributing

Thank you for helping improve the scientific quality of this project.

## Contribution priorities

Contributions are especially welcome when they improve:

1. Mathematical correctness
2. Reproducibility
3. Decoding and reconstruction validation
4. Resource accounting
5. Noise-aware experiments
6. Documentation and primary-source attribution
7. Tests and continuous integration

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev,notebook]"
```

Run the checks:

```bash
ruff check .
ruff format --check .
pytest
```

## Scientific requirements for a new encoding method

A new method should include:

- A primary-source citation
- A mathematical state definition
- Explicit register and endianness conventions
- State-preparation code
- Decoding or reconstruction code
- At least one correctness test
- Resource metrics
- A clear distinction between simulator and hardware results
- A limitations section

Do not label a simplified or modified implementation with the exact name of a published method unless it reproduces the defining state and protocol.

## Pull requests

- Keep each pull request focused.
- Explain the scientific purpose and expected behavior.
- Include tests for new behavior.
- Do not commit large datasets, generated environments, credentials, or private client material.
