"""
Compatibility layer so existing ``import dash_aggrid`` statements continue to
work after the project was renamed to ``dash-aggrid-js`` / ``dash_aggrid_js``.
"""
from importlib import import_module as _import_module
import sys as _sys

_new_package = _import_module("dash_aggrid_js")

# Re-export everything from the new namespace.
from dash_aggrid_js import *  # noqa: F401,F403

__all__ = getattr(_new_package, "__all__", [])
__version__ = getattr(_new_package, "__version__", None)
__dash_components__ = getattr(_new_package, "__dash_components__", None)

# Make sure both module names resolve to the same underlying objects.
_sys.modules.setdefault("dash_aggrid_js", _new_package)


def __getattr__(name):
    return getattr(_new_package, name)


def __dir__():
    return sorted(set(globals()) | set(dir(_new_package)))
