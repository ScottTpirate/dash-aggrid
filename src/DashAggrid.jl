
module DashAggrid
using Dash

const resources_path = realpath(joinpath( @__DIR__, "..", "deps"))
const version = "0.2.2"

include("jl/agjs_agchartsjs.jl")
include("jl/agjs_aggridjs.jl")

function __init__()
    DashBase.register_package(
        DashBase.ResourcePkg(
            "dash_aggrid_js",
            resources_path,
            version = version,
            [
                DashBase.Resource(
    relative_package_path = "dash_aggrid.min.js",
    external_url = nothing,
    dynamic = nothing,
    async = nothing,
    type = :js
),
DashBase.Resource(
    relative_package_path = "dash_aggrid.min.js.map",
    external_url = nothing,
    dynamic = true,
    async = nothing,
    type = :js
)
            ]
        )

    )
end
end
