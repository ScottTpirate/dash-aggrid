SHELL := /bin/bash

.PHONY: help install-dev js-build sync-version lint test dist clean-dist

help:
	@echo "Common targets:"
	@echo "  make install-dev    # pip install -e . with dev+test extras"
	@echo "  make js-build       # npm ci && npm run build"
	@echo "  make sync-version   # sync __about__.py -> package.json, package-info.json (use VERSION=X.Y.Z)"
	@echo "  make test           # run pytest"
	@echo "  make dist           # build wheel+sdist (runs js-build first)"

install-dev:
	python -m pip install -e .[dev,test]

js-build:
	npm ci
	npm run build

sync-version:
	python scripts/sync_version.py $(VERSION)

lint:
	pre-commit run --all-files

test:
	python -m pip install -e .[test]
	pytest

clean-dist:
	rm -rf build/ dist/ *.egg-info

dist: clean-dist js-build
	python -m build
