# Contributing

Thanks for helping improve `dash-aggrid-js`! This project is a thin Dash wrapper over AG Grid React. The guidance below keeps builds reproducible, releases predictable, and collaboration friendly.

## Local setup

```bash
git clone https://github.com/ScottTpirate/dash-aggrid.git
cd dash-aggrid
python -m venv .venv && source .venv/bin/activate
python -m pip install -U pip
make install-dev
npm ci
```

## Common tasks

- Build JS + backends: `make js-build`
- Run tests: `make test` (uses `dash[testing]`; requires Chrome/Chromedriver for the browser test)
- Lint/format: `make lint` (pre-commit with ruff + black)
- Sync versions: `make sync-version VERSION=0.3.1` (updates `__about__.py`, `package.json`, `dash_aggrid_js/package-info.json`)
- Build distributables: `make dist` (runs JS build first, then `python -m build`)

## Branch/PR expectations

- Keep PRs small and scoped. Include a short summary of behavior changes.
- Add/refresh tests when changing behavior.
- Run `make js-build`, `make lint`, and `make test` before opening a PR. CI will run the same checks.
- If you add new props or assets, ensure they are included in `MANIFEST.in`.

## Release process

1. Choose the next semver version.
2. `make sync-version VERSION=X.Y.Z`
3. Update `CHANGELOG.md` with the new entry (Added/Changed/Fixed).
4. Commit and tag `vX.Y.Z`.
5. Push tag to GitHub. The release workflow builds fresh assets, creates sdist/wheel, and publishes to PyPI using `PYPI_API_TOKEN` (configured in repo secrets).

## Reporting issues

Please include:
- What you expected vs what happened.
- Minimal reproduction (code/config) and Dash/AG Grid versions.
- Browser/OS if UI related.
