# AUTO GENERATED FILE - DO NOT EDIT

export agjs_agchartsjs

"""
    agjs_agchartsjs(;kwargs...)

An AgChartsJS component.
AgChartsJS renders AG Charts using options stored in window.AGCHART_CONFIGS.
Supply inline `options` or reference an `optionsKey`; the component resolves
dynamic configs and keeps the chart instance updated for Dash layouts.
Keyword arguments:
- `id` (String; optional): The ID used to identify this component in Dash callbacks.
- `className` (String; optional): Optional CSS class applied to the chart container.
- `configArgs` (Dict | Array | String | Real | Bool | a value equal to: null; optional): Optional JSON-serialisable payload passed to config factory functions.
- `options` (Dict; optional): Chart options object to render. If provided, overrides optionsKey lookup.
- `optionsKey` (String; optional): Key used to look up chart options from window.AGCHART_CONFIGS.
- `style` (Dict; optional): Inline styles for sizing/positioning the chart container.
"""
function agjs_agchartsjs(; kwargs...)
        available_props = Symbol[:id, :className, :configArgs, :options, :optionsKey, :style]
        wild_props = Symbol[]
        return Component("agjs_agchartsjs", "AgChartsJS", "dash_aggrid", available_props, wild_props; kwargs...)
end

