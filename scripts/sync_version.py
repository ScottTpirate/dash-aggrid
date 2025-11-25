"""
Sync the single source of truth version across Python and JS metadata files.

Usage:
    python scripts/sync_version.py               # sync package.json + package-info.json to __about__.__version__
    python scripts/sync_version.py 0.3.1         # set new version everywhere
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ABOUT_FILE = ROOT / "dash_aggrid_js" / "__about__.py"
VERSION_FILE = ROOT / "dash_aggrid_js" / "VERSION"
PACKAGE_JSON = ROOT / "package.json"
PACKAGE_INFO = ROOT / "dash_aggrid_js" / "package-info.json"
PACKAGE_LOCK = ROOT / "package-lock.json"
DESCRIPTION_FILE = ROOT / "DESCRIPTION"
PROJECT_TOML = ROOT / "Project.toml"
JULIA_PACKAGES = [ROOT / "src" / "DashAggridJs.jl", ROOT / "src" / "DashAggrid.jl"]
R_INTERNAL = ROOT / "R" / "internal.R"
DEPS_VERSION = ROOT / "deps" / "VERSION"
INST_DEPS_VERSION = ROOT / "inst" / "deps" / "VERSION"

VERSION_PATTERN = re.compile(r'__version__\s*=\s*"(.*?)"')


def read_version() -> str:
    text = ABOUT_FILE.read_text()
    match = VERSION_PATTERN.search(text)
    if not match:
        raise RuntimeError("Unable to find __version__ in __about__.py")
    return match.group(1)


def write_version(version: str) -> None:
    text = ABOUT_FILE.read_text()
    new = VERSION_PATTERN.sub(f'__version__ = "{version}"', text)
    ABOUT_FILE.write_text(new)
    for path in (VERSION_FILE, DEPS_VERSION, INST_DEPS_VERSION):
        path.write_text(f"{version}\n")


def update_json_version(path: Path, version: str) -> None:
    data = json.loads(path.read_text())
    data["version"] = version
    path.write_text(json.dumps(data, indent=2) + "\n")


def update_package_lock(version: str) -> None:
    data = json.loads(PACKAGE_LOCK.read_text())
    data["version"] = version
    packages = data.get("packages")
    if isinstance(packages, dict) and "" in packages:
        packages[""]["version"] = version
    PACKAGE_LOCK.write_text(json.dumps(data, indent=2) + "\n")


def replace_line(path: Path, pattern: str, replacement: str) -> None:
    text = path.read_text()
    new_text, count = re.subn(pattern, replacement, text, flags=re.MULTILINE)
    if count == 0:
        raise RuntimeError(f"Unable to update version in {path}")
    path.write_text(new_text)


def main() -> int:
    target_version = sys.argv[1] if len(sys.argv) > 1 else None
    if target_version:
        write_version(target_version)
        version = target_version
    else:
        version = read_version()

    for json_file in (PACKAGE_JSON, PACKAGE_INFO):
        update_json_version(json_file, version)
    update_package_lock(version)
    replace_line(DESCRIPTION_FILE, r"^Version:\s*.*", f"Version: {version}")
    replace_line(PROJECT_TOML, r'^version\s*=\s*".*"', f'version = "{version}"')
    replace_line(R_INTERNAL, r'version = ".*?"', f'version = "{version}"')
    for jl_file in JULIA_PACKAGES:
        replace_line(jl_file, r'^const version = ".*"', f'const version = "{version}"')

    print(
        f"Synced version to {version} in __about__.py, VERSION files, package manifests (JS/R/Julia), and lockfiles"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
