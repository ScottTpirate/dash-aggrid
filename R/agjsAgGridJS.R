# AUTO GENERATED FILE - DO NOT EDIT

#' @export
agjsAgGridJS <- function(id=NULL, className=NULL, configArgs=NULL, configKey=NULL, editedCells=NULL, filterModel=NULL, rowData=NULL, selectedRows=NULL, sortModel=NULL, style=NULL) {
    
    props <- list(id=id, className=className, configArgs=configArgs, configKey=configKey, editedCells=editedCells, filterModel=filterModel, rowData=rowData, selectedRows=selectedRows, sortModel=sortModel, style=style)
    if (length(props) > 0) {
        props <- props[!vapply(props, is.null, logical(1))]
    }
    component <- list(
        props = props,
        type = 'AgGridJS',
        namespace = 'dash_aggrid',
        propNames = c('id', 'className', 'configArgs', 'configKey', 'editedCells', 'filterModel', 'rowData', 'selectedRows', 'sortModel', 'style'),
        package = 'dashAggrid'
        )

    structure(component, class = c('dash_component', 'list'))
}
