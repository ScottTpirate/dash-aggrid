% Auto-generated: do not edit by hand
\name{agjsAgChartsJS}

\alias{agjsAgChartsJS}

\title{AgChartsJS component}

\description{
AgChartsJS renders AG Charts using options stored in window.AGCHART_CONFIGS. Supply inline `options` or reference an `optionsKey`; the component resolves dynamic configs and keeps the chart instance updated for Dash layouts.
}

\usage{
agjsAgChartsJS(id=NULL, className=NULL, configArgs=NULL, options=NULL,
optionsKey=NULL, style=NULL)
}

\arguments{
\item{id}{Character. The ID used to identify this component in Dash callbacks.}

\item{className}{Character. Optional CSS class applied to the chart container.}

\item{configArgs}{Named list | unnamed list | character | numeric | logical | a value equal to: null. Optional JSON-serialisable payload passed to config factory functions.}

\item{options}{Named list. Chart options object to render. If provided, overrides optionsKey lookup.}

\item{optionsKey}{Character. Key used to look up chart options from window.AGCHART_CONFIGS.}

\item{style}{Named list. Inline styles for sizing/positioning the chart container.}
}

\value{named list of JSON elements corresponding to React.js properties and their values}

