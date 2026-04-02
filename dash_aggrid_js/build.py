#!/usr/bin/env python3
"""CLI helpers for rebuilding dash-aggrid-js with custom AG Grid versions."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

GRID_DEPS = ("ag-grid-community", "ag-grid-enterprise", "ag-grid-react")
CHART_DEPS = ("ag-charts-community", "ag-charts-enterprise")


def _find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "package.json").exists() and (
            candidate / "webpack.config.js"
        ).exists():
            return candidate
    raise FileNotFoundError(
        "Unable to locate package.json/webpack.config.js. "
        "Run this command from a dash-aggrid-js source checkout."
    )


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: dict) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=False)
        handle.write("\n")


def _update_deps(payload: dict, deps: Iterable[str], version: str | None) -> bool:
    if not version:
        return False
    deps_map = payload.get("dependencies") or {}
    changed = False
    for dep in deps:
        if dep in deps_map and deps_map[dep] != version:
            deps_map[dep] = version
            changed = True
    payload["dependencies"] = deps_map
    return changed


def _ensure_npm() -> str:
    npm = shutil.which("npm")
    if not npm:
        raise RuntimeError("npm is required to rebuild the JS bundle.")
    return npm


def _run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=str(cwd), check=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rebuild dash-aggrid-js with custom AG Grid/Charts versions."
    )
    parser.add_argument(
        "--aggrid",
        dest="aggrid",
        default=None,
        help="Version for ag-grid-* packages (e.g. 35.2.0, ^35.2.0, latest).",
    )
    parser.add_argument(
        "--agcharts",
        dest="agcharts",
        default=None,
        help="Version for ag-charts-* packages (e.g. 13.2.0, ^13.2.0, latest).",
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Set both ag-grid and ag-charts packages to 'latest'.",
    )
    parser.add_argument(
        "--no-install",
        action="store_true",
        help="Skip npm install (assumes node_modules already up to date).",
    )
    parser.add_argument(
        "--skip-build",
        action="store_true",
        help="Skip rebuilding the JS bundle.",
    )
    args = parser.parse_args()

    env_grid = os.getenv("AGGRID_VERSION")
    env_charts = os.getenv("AGCHARTS_VERSION")

    if args.latest:
        aggrid_version = "latest"
        agcharts_version = "latest"
    else:
        aggrid_version = args.aggrid or env_grid
        agcharts_version = args.agcharts or env_charts

    if not aggrid_version and not agcharts_version:
        print(
            "No versions supplied. Use --aggrid/--agcharts, --latest, or env vars."
        )
        return 1

    repo_root = _find_repo_root(Path(__file__).resolve())
    package_json = repo_root / "package.json"
    package_info = repo_root / "dash_aggrid_js" / "package-info.json"

    package_payload = _load_json(package_json)
    package_info_payload = _load_json(package_info)

    changed = False
    changed |= _update_deps(package_payload, GRID_DEPS, aggrid_version)
    changed |= _update_deps(package_info_payload, GRID_DEPS, aggrid_version)
    changed |= _update_deps(package_payload, CHART_DEPS, agcharts_version)
    changed |= _update_deps(package_info_payload, CHART_DEPS, agcharts_version)

    if changed:
        _write_json(package_json, package_payload)
        _write_json(package_info, package_info_payload)
        print("Updated AG Grid/Charts dependency versions.")
    else:
        print("Dependency versions already match.")

    if args.skip_build:
        return 0

    npm = _ensure_npm()
    if not args.no_install:
        _run([npm, "install"], repo_root)
    _run([npm, "run", "build:js"], repo_root)
    print("Rebuilt dash-aggrid-js bundle.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
