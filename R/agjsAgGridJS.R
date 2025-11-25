# AUTO GENERATED FILE - DO NOT EDIT

#' @export
agjsAgGridJS <- function(id=NULL, className=NULL, configArgs=NULL, configKey=NULL, filterModel=NULL, registerProps=NULL, rowData=NULL, selectedRows=NULL, sortModel=NULL, style=NULL) {
    
    props <- list(id=id, className=className, configArgs=configArgs, configKey=configKey, filterModel=filterModel, registerProps=registerProps, rowData=rowData, selectedRows=selectedRows, sortModel=sortModel, style=style)
    if (length(props) > 0) {
        props <- props[!vapply(props, is.null, logical(1))]
    }
    component <- list(
        props = props,
        type = 'AgGridJS',
        namespace = 'dash_aggrid_js',
        propNames = c('id', 'className', 'configArgs', 'configKey', 'filterModel', 'registerProps', 'rowData', 'selectedRows', 'sortModel', 'style'),
        package = 'dashAggridJs'
        )

    structure(component, class = c('dash_component', 'list'))
}
