# AUTO GENERATED FILE - DO NOT EDIT

#' @export
agjsAgChartsJS <- function(id=NULL, className=NULL, configArgs=NULL, options=NULL, optionsKey=NULL, style=NULL) {
    
    props <- list(id=id, className=className, configArgs=configArgs, options=options, optionsKey=optionsKey, style=style)
    if (length(props) > 0) {
        props <- props[!vapply(props, is.null, logical(1))]
    }
    component <- list(
        props = props,
        type = 'AgChartsJS',
        namespace = 'aggrid_js',
        propNames = c('id', 'className', 'configArgs', 'options', 'optionsKey', 'style'),
        package = 'aggridJs'
        )

    structure(component, class = c('dash_component', 'list'))
}
