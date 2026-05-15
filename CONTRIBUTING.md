# Contributing

Thanks for your interest in contributing! This project adapts
[`k8s-agent-sandbox`](https://pypi.org/project/k8s-agent-sandbox/) to the
[`deepagents`](https://github.com/langchain-ai/deepagents) sandbox protocol.

## Development setup

Requires Python 3.12+ and [`uv`](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/irwinding/langchain-kubernetes-agent-sandbox.git
cd langchain-kubernetes-agent-sandbox
make install   # uv sync
```

Husky installs git hooks via `npm install` (used to enforce commit messages —
see below). If you don't have Node installed, the hooks won't run locally but
CI will still enforce the same rules.

## Running tests

```bash
make unit                 # fast, no cluster needed
make lint                 # ruff check
make format               # ruff format (writes)
make integration-local    # requires a local Kubernetes cluster with the
                          # agent-sandbox operator installed
```

Override the integration template/namespace if needed:

```bash
make integration-local K8S_SANDBOX_TEMPLATE=python K8S_SANDBOX_NAMESPACE=default
```

CI runs `ruff check`, `ruff format --check`, and the unit tests on every PR.
Integration tests are not run in CI — please run them locally for any change
that touches sandbox interaction.

## Commit messages

This repo uses [Conventional Commits](https://www.conventionalcommits.org/) and
[python-semantic-release](https://python-semantic-release.readthedocs.io/) to
automate versioning and the changelog. Commit messages are linted by commitlint
via a husky `commit-msg` hook.

Allowed prefixes (from `pyproject.toml`):

`feat`, `fix`, `perf`, `refactor`, `docs`, `chore`, `test`, `ci`, `build`, `style`

Version bump rules:

- `feat:` → minor
- `fix:` / `perf:` → patch
- `BREAKING CHANGE:` in the body or `!` after the type → major

Examples:

```
feat: add streaming execute response
fix: handle timeout cause chain on older requests versions
docs: document tool-mode usage
```

**Do not bump the version in `pyproject.toml`.** semantic-release does that on
merge to `main`.

## Pull requests

1. Fork the repo and create a branch off `main`.
2. Make your changes; keep PRs focused — one logical change per PR.
3. Run `make lint` and `make unit` locally before pushing.
4. Open a PR against `main`. Fill in the PR template (summary + test plan).
5. CI must be green and at least one approval is required before merge.
6. Use **Squash and merge** so the squash commit message is your Conventional
   Commit (semantic-release reads commit messages on `main`).

## Reporting issues

Use the issue templates under "New issue" — bug reports and feature requests.
For security issues, please open a private security advisory rather than a
public issue.

## License

By contributing, you agree that your contributions are licensed under the MIT
License (see [LICENSE](LICENSE)).
