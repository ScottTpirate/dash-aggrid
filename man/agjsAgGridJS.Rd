% Auto-generated: do not edit by hand
\name{agjsAgGridJS}

\alias{agjsAgGridJS}

\title{AgGridJS component}

\description{
AgGridJS mounts AgGridReact using configurations stored on window.AGGRID_CONFIGS. The component relays selection, filter, sort, and edit events back to Dash via setProps.
}

\usage{
agjsAgGridJS(id=NULL, className=NULL, configArgs=NULL, configKey=NULL,
filterModel=NULL, registerProps=NULL, rowData=NULL,
selectedRows=NULL, sortModel=NULL, style=NULL)
}

\arguments{
\item{id}{Character. The ID used to identify this component in Dash callbacks.}

\item{className}{Character. Optional CSS class to apply to the outer grid container.}

\item{configArgs}{Named list | unnamed list | character | numeric | logical | a value equal to: null. Optional JSON-serialisable payload passed to config factory functions.}

\item{configKey}{Character. Key used to look up a configuration object in window.AGGRID_CONFIGS.}

\item{filterModel}{Named list. Current AG Grid filter model. Populated by the component.}

\item{registerProps}{List of characters | character | a value equal to: null. Optional list of extra Dash props this grid is allowed to emit (e.g. ["cellDoubleClicked"]).
These are appended to the component's available_properties on the Python side.}

\item{rowData}{List of named lists. Row data provided directly from Dash. Overrides rowData defined in the JS config.}

\item{selectedRows}{List of named lists. Array of row objects selected in the grid. Populated by the component.}

\item{sortModel}{List of lists containing elements 'colid', 'sort', 'sortindex'.
those elements have the following types:
  - colid (character; optional)
  - sort (a value equal to: 'asc', 'desc'; optional)
  - sortindex (numeric; optional)s. Current AG Grid sort model (colId, sort, sortIndex). Populated by the component.}

\item{style}{Named list. Inline style object applied to the grid container.}
}

\value{named list of JSON elements corresponding to React.js properties and their values}

