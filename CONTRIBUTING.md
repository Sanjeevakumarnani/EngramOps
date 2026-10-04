# Contributing to EngramOps

## Development workflow

1. Create a focused change on a feature or documentation branch.
2. Keep engineering-memory records structured and traceable.
3. Add or update tests when behavior changes.
4. Run local validation before opening a pull request.
5. Explain the user-visible or engineering impact in the pull request.

## Memory records

New records should preserve enough context to make future recall useful:

- incident or decision context
- affected component or dependency
- observed failure or successful outcome
- attempted mitigation
- final outcome
- durable lesson
- source and timestamp where applicable

Avoid storing secrets, credentials, personal data, or unverifiable claims.

## Safety boundary

EngramOps is decision support. It does not autonomously modify production systems or replace human approval for high-impact engineering changes.

## Local validation

At minimum, contributors should run:

```bash
python -m compileall app
pytest
```

For changes that affect the HTTP layer, also perform a local smoke test against the running application.

## Pull requests

Keep pull requests focused. Include:

- what changed
- why it changed
- how it was validated
- any limitations or follow-up work

Documentation-only changes are welcome when they improve onboarding or explain important architecture decisions.
