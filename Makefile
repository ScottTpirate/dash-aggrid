SHELL := /bin/bash
PYTHON ?= python3

.PHONY: help install-dev js-build sync-version lint test dist clean-dist

help:
	@echo "Common targets:"
	@echo "  make install-dev    # pip install -e . with dev+test extras"
	@echo "  make js-build       # npm ci && npm run build"
	@echo "  make sync-version   # sync __about__.py -> package.json, package-info.json (use VERSION=X.Y.Z)"
	@echo "  make test           # run pytest"
	@echo "  make dist           # build wheel+sdist (runs js-build first)"

install-dev:
	$(PYTHON) -m pip install -e .[dev,test]

js-build:
	npm ci
	./node_modules/.bin/webpack --mode production
	node scripts/run_python.js -m dash.development.component_generator ./src/lib/components dash_aggrid_js -p package-info.json --r-prefix 'agjs' --jl-prefix 'agjs' --ignore '\\.test\\.'

sync-version:
	$(PYTHON) scripts/sync_version.py $(VERSION)

lint:
	pre-commit run --all-files

test:
	$(PYTHON) -m pip install -e .[test]
	$(PYTHON) -m pytest

clean-dist:
	rm -rf build/ dist/ *.egg-info

dist: clean-dist js-build
	$(PYTHON) -m build
