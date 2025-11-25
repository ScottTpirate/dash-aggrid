# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased
### Added
- `set_default_props([...])` helper to apply a default registerProps list across all grids.

## 0.4.0 - 2025-11-25
### Added
- CI workflows for lint/tests and tag-based PyPI publishing.
- Single-source version file with sync script for Python/JS metadata.
- Contributor guide, code of conduct, and make targets for common tasks.
- `registerProps` support to opt-in to custom Dash props (e.g., `cellDoubleClicked`).
- VERSION file for builds that avoid importing the package.

### Changed
- Packaging metadata moved to `pyproject.toml` (PEP 621) with optional dev/test extras.
- `cellClicked`/`editedCells` emission now gated by `registerProps` to avoid unintended props; register them for backward compatibility.
