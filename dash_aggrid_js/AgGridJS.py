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


class AgGridJS(Component):
    """An AgGridJS component.
AgGridJS mounts AgGridReact using configurations stored on window.AGGRID_CONFIGS.
The component relays selection, filter, sort, and edit events back to Dash via setProps.

Keyword arguments:

- id (string; optional):
    The ID used to identify this component in Dash callbacks.

- className (string; optional):
    Optional CSS class to apply to the outer grid container.

- configArgs (dict | list | string | number | boolean | a value equal to: null; optional):
    Optional JSON-serialisable payload passed to config factory
    functions.

- configKey (string; required):
    Key used to look up a configuration object in
    window.AGGRID_CONFIGS.

- filterModel (dict; optional):
    Current AG Grid filter model. Populated by the component.

- registerProps (list of strings | string | a value equal to: null; optional):
    Optional list of extra Dash props this grid is allowed to emit
    (e.g. [\"cellDoubleClicked\"]). These are appended to the
    component's available_properties on the Python side.

- rowData (list of dicts; optional):
    Row data provided directly from Dash. Overrides rowData defined in
    the JS config.

- selectedRows (list of dicts; optional):
    Array of row objects selected in the grid. Populated by the
    component.

- sortModel (list of dicts; optional):
    Current AG Grid sort model (colId, sort, sortIndex). Populated by
    the component.

    `sortModel` is a list of dicts with keys:

    - colId (string; optional)

    - sort (a value equal to: 'asc', 'desc'; optional)

    - sortIndex (number; optional)"""
    _children_props: typing.List[str] = []
    _base_nodes = ['children']
    _namespace = 'dash_aggrid_js'
    _type = 'AgGridJS'
    SortModel = TypedDict(
        "SortModel",
            {
            "colId": NotRequired[str],
            "sort": NotRequired[Literal["asc", "desc"]],
            "sortIndex": NotRequired[NumberType]
        }
    )


    def __init__(
        self,
        id: typing.Optional[typing.Union[str, dict]] = None,
        configKey: typing.Optional[str] = None,
        className: typing.Optional[str] = None,
        style: typing.Optional[typing.Any] = None,
        configArgs: typing.Optional[typing.Union[dict, typing.Sequence, str, NumberType, bool, Literal[None]]] = None,
        registerProps: typing.Optional[typing.Union[typing.Sequence[str], str, Literal[None]]] = None,
        selectedRows: typing.Optional[typing.Sequence[dict]] = None,
        filterModel: typing.Optional[dict] = None,
        sortModel: typing.Optional[typing.Sequence["SortModel"]] = None,
        rowData: typing.Optional[typing.Sequence[dict]] = None,
        **kwargs
    ):
        self._prop_names = ['id', 'className', 'configArgs', 'configKey', 'filterModel', 'registerProps', 'rowData', 'selectedRows', 'sortModel', 'style']
        self._valid_wildcard_attributes =            []
        self.available_properties = ['id', 'className', 'configArgs', 'configKey', 'filterModel', 'registerProps', 'rowData', 'selectedRows', 'sortModel', 'style']
        self.available_wildcard_properties =            []
        _explicit_args = kwargs.pop('_explicit_args')
        _locals = locals()
        _locals.update(kwargs)  # For wildcard attrs and excess named props
        args = {k: _locals[k] for k in _explicit_args}

        for k in ['configKey']:
            if k not in args:
                raise TypeError(
                    'Required argument `' + k + '` was not specified.')

        super(AgGridJS, self).__init__(**args)

setattr(AgGridJS, "__init__", _explicitize_args(AgGridJS.__init__))
