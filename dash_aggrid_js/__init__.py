from __future__ import print_function as _

import os as _os
import sys as _sys
import json
from collections.abc import Mapping as _Mapping

import dash as _dash

# noinspection PyUnresolvedReferences
from ._imports_ import *
from ._imports_ import __all__

try:
    from ._imports_ import __dash_components__
except ImportError:  # dash-generate-components < 2.x
    __dash_components__ = [name for name in __all__ if name in globals()]

from .ssrm import distinct_sql, quote_identifier, register_duckdb_ssrm, sql_for

for _extra in ("sql_for", "distinct_sql", "quote_identifier", "register_duckdb_ssrm"):
    if _extra not in __all__:
        __all__.append(_extra)

if not hasattr(_dash, '__plotly_dash') and not hasattr(_dash, 'development'):
    print('Dash was not successfully imported. '
          'Make sure you don\'t have a file '
          'named \n"dash.py" in your current directory.', file=_sys.stderr)
    _sys.exit(1)

_basepath = _os.path.dirname(__file__)
_filepath = _os.path.abspath(_os.path.join(_basepath, 'package-info.json'))
with open(_filepath) as f:
    package = json.load(f)

package_name = package['name'].replace(' ', '_').replace('-', '_')
__version__ = package['version']

_current_path = _os.path.dirname(_os.path.abspath(__file__))

_this_module = _sys.modules[__name__]

async_resources = []

_js_dist = []

_js_dist.extend(
    [
        {
            "relative_package_path": "async-{}.js".format(async_resource),
            "external_url": (
                "https://unpkg.com/{0}@{2}"
                "/{1}/async-{3}.js"
            ).format(package_name, __name__, __version__, async_resource),
            "namespace": package_name,
            "async": True,
        }
        for async_resource in async_resources
    ]
)

_js_dist.extend(
    [
        {
            "relative_package_path": "async-{}.js.map".format(async_resource),
            "external_url": (
                "https://unpkg.com/{0}@{2}"
                "/{1}/async-{3}.js.map"
            ).format(package_name, __name__, __version__, async_resource),
            "namespace": package_name,
            "dynamic": True,
        }
        for async_resource in async_resources
    ]
)

_js_dist.extend(
    [
        {
            'relative_package_path': 'dash_aggrid_js.min.js',
    
            'namespace': package_name
        },
        {
            'relative_package_path': 'dash_aggrid_js.min.js.map',
    
            'namespace': package_name,
            'dynamic': True
        }
    ]
)

_css_dist = []


for _component in __dash_components__:
    setattr(locals()[_component], '_js_dist', _js_dist)
    setattr(locals()[_component], '_css_dist', _css_dist)


if "AgGridJS" in globals():
    _aggrid_original_init = AgGridJS.__init__

    def _aggrid_ssrm_init(self, *args, **kwargs):
        result = _aggrid_original_init(self, *args, **kwargs)

        grid_id = getattr(self, "id", None)
        config_args = getattr(self, "configArgs", None)

        if isinstance(grid_id, (str, int)) and isinstance(config_args, _Mapping):
            if not isinstance(config_args, dict):
                config_args = dict(config_args)
                setattr(self, "configArgs", config_args)

            ssrm_cfg = config_args.get("ssrm")
            if isinstance(ssrm_cfg, _Mapping):
                if not isinstance(ssrm_cfg, dict):
                    ssrm_cfg = dict(ssrm_cfg)
                    config_args["ssrm"] = ssrm_cfg

                target_grid_id = ssrm_cfg.get("gridId")
                target_grid_id = (
                    str(target_grid_id)
                    if isinstance(target_grid_id, (str, int)) and str(target_grid_id)
                    else None
                )
                registry_grid_id = target_grid_id or str(grid_id)

                endpoint = register_duckdb_ssrm(registry_grid_id, ssrm_cfg)
                ssrm_cfg.setdefault("gridId", registry_grid_id)
                ssrm_cfg.setdefault("endpoint", endpoint)
                ssrm_cfg.setdefault("distinctEndpoint", f"{endpoint.rstrip('/')}/distinct")

        return result

    AgGridJS.__init__ = _aggrid_ssrm_init
