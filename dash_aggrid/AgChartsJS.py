# AUTO GENERATED FILE - DO NOT EDIT

import typing  # noqa: F401
from typing_extensions import TypedDict, NotRequired, Literal # noqa: F401
from dash.development.base_component import Component, _explicitize_args

ComponentType = typing.Union[
    str,
    int,
    float,
    Component,
    None,
    typing.Sequence[typing.Union[str, int, float, Component, None]],
]

NumberType = typing.Union[
    typing.SupportsFloat, typing.SupportsInt, typing.SupportsComplex
]


class AgChartsJS(Component):
    """An AgChartsJS component.
AgChartsJS renders AG Charts using options stored in window.AGCHART_CONFIGS.
Supply inline `options` or reference an `optionsKey`; the component resolves
dynamic configs and keeps the chart instance updated for Dash layouts.

Keyword arguments:

- id (string; optional):
    The ID used to identify this component in Dash callbacks.

- className (string; optional):
    Optional CSS class applied to the chart container.

- configArgs (dict | list | string | number | boolean | a value equal to: null; optional):
    Optional JSON-serialisable payload passed to config factory
    functions.

- options (dict; optional):
    Chart options object to render. If provided, overrides optionsKey
    lookup.

- optionsKey (string; optional):
    Key used to look up chart options from window.AGCHART_CONFIGS."""
    _children_props = []
    _base_nodes = ['children']
    _namespace = 'dash_aggrid'
    _type = 'AgChartsJS'


    def __init__(
        self,
        id: typing.Optional[typing.Union[str, dict]] = None,
        className: typing.Optional[str] = None,
        style: typing.Optional[typing.Any] = None,
        options: typing.Optional[dict] = None,
        optionsKey: typing.Optional[str] = None,
        configArgs: typing.Optional[typing.Union[dict, typing.Sequence, str, NumberType, bool, Literal[None]]] = None,
        **kwargs
    ):
        self._prop_names = ['id', 'className', 'configArgs', 'options', 'optionsKey', 'style']
        self._valid_wildcard_attributes =            []
        self.available_properties = ['id', 'className', 'configArgs', 'options', 'optionsKey', 'style']
        self.available_wildcard_properties =            []
        _explicit_args = kwargs.pop('_explicit_args')
        _locals = locals()
        _locals.update(kwargs)  # For wildcard attrs and excess named props
        args = {k: _locals[k] for k in _explicit_args}

        super(AgChartsJS, self).__init__(**args)

setattr(AgChartsJS, "__init__", _explicitize_args(AgChartsJS.__init__))
