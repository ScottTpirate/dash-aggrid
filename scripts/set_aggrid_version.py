#!/usr/bin/env python3
"""Update AG Grid/Charts dependency versions in package metadata."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_JSON = ROOT / "package.json"
PACKAGE_INFO = ROOT / "dash_aggrid_js" / "package-info.json"

GRID_DEPS = ("ag-grid-community", "ag-grid-enterprise", "ag-grid-react")
CHART_DEPS = ("ag-charts-community", "ag-charts-enterprise")


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
    changed = False
    deps_map = payload.get("dependencies") or {}
    for dep in deps:
        if dep in deps_map and deps_map[dep] != version:
            deps_map[dep] = version
            changed = True
    payload["dependencies"] = deps_map
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Update AG Grid/Charts dependency versions in package.json and package-info.json."
    )
    parser.add_argument(
        "--aggrid",
        dest="aggrid",
        default=None,
        help="Version for ag-grid-* packages (e.g. 34.3.5, ^34.3.1, latest).",
    )
    parser.add_argument(
        "--agcharts",
        dest="agcharts",
        default=None,
        help="Version for ag-charts-* packages (e.g. 12.3.5, ^12.3.1, latest).",
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        help="Set both ag-grid and ag-charts packages to 'latest'.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print changes without writing files.",
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
        print("No versions supplied. Use --aggrid/--agcharts or env vars.")
        return 0

    package_json = _load_json(PACKAGE_JSON)
    package_info = _load_json(PACKAGE_INFO)

    changed = False
    changed |= _update_deps(package_json, GRID_DEPS, aggrid_version)
    changed |= _update_deps(package_info, GRID_DEPS, aggrid_version)
    changed |= _update_deps(package_json, CHART_DEPS, agcharts_version)
    changed |= _update_deps(package_info, CHART_DEPS, agcharts_version)

    if not changed:
        print("No dependency updates needed.")
        return 0

    if args.dry_run:
        print("Dry run - changes not written.")
        return 0

    _write_json(PACKAGE_JSON, package_json)
    _write_json(PACKAGE_INFO, package_info)
    print("Updated dependency versions.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
