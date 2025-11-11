# AUTO GENERATED FILE - DO NOT EDIT

export agjs_aggridjs

"""
    agjs_aggridjs(;kwargs...)

An AgGridJS component.
AgGridJS mounts AgGridReact using configurations stored on window.AGGRID_CONFIGS.
The component relays selection, filter, sort, and edit events back to Dash via setProps.
Keyword arguments:
- `id` (String; optional): The ID used to identify this component in Dash callbacks.
- `className` (String; optional): Optional CSS class to apply to the outer grid container.
- `configArgs` (Dict | Array | String | Real | Bool | a value equal to: null; optional): Optional JSON-serialisable payload passed to config factory functions.
- `configKey` (String; required): Key used to look up a configuration object in window.AGGRID_CONFIGS.
- `editedCells` (optional): Details of the most recent cell edit (rowId, colId, oldValue, newValue).. editedCells has the following type: Array of lists containing elements 'rowId', 'colId', 'oldValue', 'newValue'.
Those elements have the following types:
  - `rowId` (String | Real; optional)
  - `colId` (String; optional)
  - `oldValue` (Bool | Real | String | Dict | Array; optional)
  - `newValue` (Bool | Real | String | Dict | Array; optional)s
- `filterModel` (Dict; optional): Current AG Grid filter model. Populated by the component.
- `rowData` (Array of Dicts; optional): Row data provided directly from Dash. Overrides rowData defined in the JS config.
- `selectedRows` (Array of Dicts; optional): Array of row objects selected in the grid. Populated by the component.
- `sortModel` (optional): Current AG Grid sort model (colId, sort, sortIndex). Populated by the component.. sortModel has the following type: Array of lists containing elements 'colId', 'sort', 'sortIndex'.
Those elements have the following types:
  - `colId` (String; optional)
  - `sort` (a value equal to: 'asc', 'desc'; optional)
  - `sortIndex` (Real; optional)s
- `style` (Dict; optional): Inline style object applied to the grid container.
"""
function agjs_aggridjs(; kwargs...)
        available_props = Symbol[:id, :className, :configArgs, :configKey, :editedCells, :filterModel, :rowData, :selectedRows, :sortModel, :style]
        wild_props = Symbol[]
        return Component("agjs_aggridjs", "AgGridJS", "dash_aggrid_js", available_props, wild_props; kwargs...)
end

