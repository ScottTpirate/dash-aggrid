import json
from pathlib import Path

import duckdb
from dash import Dash, Input, Output, State, dcc, html
from dash.exceptions import PreventUpdate

from dash_aggrid_js import AgChartsJS, AgGridJS
from sample_data import ANALYTICS_ROWS, INVENTORY_ROWS, SALES_ROWS, SSRM_ROWS


DATA_DIR = Path(__file__).parent
DUCKDB_FILE = DATA_DIR / "ssrm_demo.duckdb"
SSRM_TABLE = "ssrm_demo"

ROW_DRAG_BACKLOG = [
    {"id": 101, "color": "Red", "value1": 64, "value2": 18},
    {"id": 102, "color": "Green", "value1": 14, "value2": 83},
    {"id": 103, "color": "Blue", "value1": 76, "value2": 11},
    {"id": 104, "color": "Red", "value1": 54, "value2": 22},
    {"id": 105, "color": "Green", "value1": 67, "value2": 65},
    {"id": 106, "color": "Blue", "value1": 21, "value2": 90},
]

ROW_DRAG_ACTIVE = [
    {"id": 201, "color": "Red", "value1": 45, "value2": 15},
    {"id": 202, "color": "Green", "value1": 88, "value2": 42},
    {"id": 203, "color": "Blue", "value1": 39, "value2": 77},
]


def ensure_demo_duckdb():
    if DUCKDB_FILE.exists():
        return

    DUCKDB_FILE.unlink(missing_ok=True)

    with duckdb.connect(str(DUCKDB_FILE)) as con:
        con.execute(
            f"""
            CREATE TABLE {SSRM_TABLE} (
                order_id TEXT,
                region TEXT,
                product TEXT,
                category TEXT,
                quarter TEXT,
                units INTEGER,
                revenue DOUBLE
            )
            """
        )
        con.executemany(
            f"""
            INSERT INTO {SSRM_TABLE}
                (order_id, region, product, category, quarter, units, revenue)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    row["order_id"],
                    row["region"],
                    row["product"],
                    row["category"],
                    row["quarter"],
                    row["units"],
                    row["revenue"],
                )
                for row in SSRM_ROWS
            ],
        )


ensure_demo_duckdb()

app = Dash(__name__)
app.title = "AgGridJS Feature Demo"

app.layout = html.Div(
    [
        dcc.Store(id="inventory-click-store"),
        html.H2("AgGridJS Demo"),
        html.P(
            "Two independent grids sharing the same wrapper. The feature grid uses AG Grid's "
            "new theming API, while the sales grid shows a different accent style."
        ),
        html.Div(
            [
                html.Label("Currency locale"),
                dcc.Dropdown(
                    id="locale-select",
                    value="en-US",
                    clearable=False,
                    options=[
                        {"label": "English (United States)", "value": "en-US"},
                        {"label": "German (Germany)", "value": "de-DE"},
                        {"label": "Japanese (Japan)", "value": "ja-JP"},
                    ],
                    style={"width": 260},
                ),
            ],
            style={"marginBottom": "1.5rem"},
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.H3("Inventory grid"),
                        AgGridJS(
                            id="inventory-grid",
                            configKey="feature-grid",
                            rowData=INVENTORY_ROWS,
                            style={"height": "420px"},
                            registerProps=["cellClicked"],
                        ),
                        html.Small(
                            "Theme: Alpine (custom accent & rounded corners)",
                            style={"display": "block", "marginTop": "0.5rem"},
                        ),
                        html.Pre(
                            id="inventory-log",
                            style={"whiteSpace": "pre-wrap", "marginTop": "0.75rem", "fontSize": "0.85rem"},
                        ),
                        html.Div(
                            [
                                html.Strong("Cell clicks"),
                                html.Pre(
                                    id="inventory-click-display",
                                    style={
                                        "whiteSpace": "pre-wrap",
                                        "marginTop": "0.5rem",
                                        "fontSize": "0.85rem",
                                    },
                                ),
                            ],
                            style={"marginTop": "0.5rem"},
                        ),
                    ],
                    style={"flex": 1, "minWidth": "320px"},
                ),
                html.Div(
                    [
                        html.H3("Sales grid"),
                        AgGridJS(
                            id="sales-grid",
                            configKey="sales-grid",
                            configArgs={"rowData": SALES_ROWS},
                            style={"height": "420px"},
                        ),
                        html.Small(
                            "Theme: Quartz with deep blue header",
                            style={"display": "block", "marginTop": "0.5rem"},
                        ),
                        html.Pre(
                            id="sales-log",
                            style={"whiteSpace": "pre-wrap", "marginTop": "0.75rem", "fontSize": "0.85rem"},
                        ),
                    ],
                    style={"flex": 1, "minWidth": "320px"},
                ),
            ],
            style={"display": "flex", "flexWrap": "wrap", "gap": "1.5rem"},
        ),
        html.Div(
            [
                html.H3("Row dragging between grids + delete bin"),
                html.P(
                    "Drag rows left/right or drop them on the bin to delete. Buttons spawn new rows on either side; "
                    "row IDs stay unique so duplicates are skipped automatically."
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Button(
                                            "Add Red",
                                            className="row-drag-factory row-drag-factory-red",
                                            **{"data-color": "Red", "data-side": "left"},
                                        ),
                                        html.Button(
                                            "Add Green",
                                            className="row-drag-factory row-drag-factory-green",
                                            **{"data-color": "Green", "data-side": "left"},
                                        ),
                                        html.Button(
                                            "Add Blue",
                                            className="row-drag-factory row-drag-factory-blue",
                                            **{"data-color": "Blue", "data-side": "left"},
                                        ),
                                    ],
                                    className="row-drag-toolbar",
                                ),
                                AgGridJS(
                                    id="row-drag-left",
                                    configKey="row-drag-grid",
                                    configArgs={"bucket": "left", "rowData": ROW_DRAG_BACKLOG},
                                    style={"height": "360px"},
                                    registerProps=["rowDragEvent"],
                                ),
                                html.Small(
                                    "Left grid (row drag managed, suppressMoveWhenRowDragging=true)",
                                    style={"display": "block"},
                                ),
                            ],
                            className="row-drag-column",
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div("🗑️", className="bin-icon"),
                                        html.Div("Drop here to delete rows", className="bin-label"),
                                    ],
                                    id="row-drag-bin",
                                    className="row-drag-bin",
                                ),
                            ],
                            className="row-drag-bin-wrapper",
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Button(
                                            "Add Red",
                                            className="row-drag-factory row-drag-factory-red",
                                            **{"data-color": "Red", "data-side": "right"},
                                        ),
                                        html.Button(
                                            "Add Green",
                                            className="row-drag-factory row-drag-factory-green",
                                            **{"data-color": "Green", "data-side": "right"},
                                        ),
                                        html.Button(
                                            "Add Blue",
                                            className="row-drag-factory row-drag-factory-blue",
                                            **{"data-color": "Blue", "data-side": "right"},
                                        ),
                                    ],
                                    className="row-drag-toolbar",
                                ),
                                AgGridJS(
                                    id="row-drag-right",
                                    configKey="row-drag-grid",
                                    configArgs={"bucket": "right", "rowData": ROW_DRAG_ACTIVE},
                                    style={"height": "360px"},
                                    registerProps=["rowDragEvent"],
                                ),
                                html.Small(
                                    "Right grid; drop rows here from the left or send them to the bin.",
                                    style={"display": "block"},
                                ),
                            ],
                            className="row-drag-column",
                        ),
                    ],
                    className="row-drag-shell",
                ),
                html.Div(
                    [
                        html.Strong("Event console"),
                        html.Pre(
                            id="row-drag-console",
                            className="row-drag-console",
                            children="Drag rows or click a factory button to see events.",
                        ),
                    ],
                    style={"marginTop": "0.75rem"},
                ),
            ],
            style={"marginTop": "2rem"},
        ),
        html.Div(
            [
                html.H3("Analytics grid with integrated chart"),
                AgGridJS(
                    id="analytics-grid",
                    configKey="analytics-grid",
                    configArgs={"rowData": ANALYTICS_ROWS},
                    style={"height": "420px"},
                ),
                html.Small(
                    "Integrated stacked column chart rendered into the container below",
                    style={"display": "block", "marginTop": "0.5rem"},
                ),
                html.Div(
                    id="analytics-chart",
                    style={
                        "height": "320px",
                        "marginTop": "1rem",
                        "background": "#0f172a",
                        "borderRadius": "12px",
                        "padding": "4px",
                    },
                ),
            ],
            style={"marginTop": "2rem"},
        ),
        html.Div(
            [
                html.H3("Server-side row model"),
                AgGridJS(
                    id="ssrm-grid",
                    configKey="ssrm-grid",
                    configArgs={
                        "ssrm": {
                            "duckdb_path": str(DUCKDB_FILE),
                            "table": SSRM_TABLE,
                        }
                    },
                    style={"height": "420px"},
                ),
                html.Small(
                    "Rows stream from Dash via a server-side datasource",
                    style={"display": "block", "marginTop": "0.5rem"},
                ),
            ],
            style={"marginTop": "2rem"},
        ),
        html.Div(
            [
                html.H3("Standalone AG Chart (AgChartsJS)"),
                AgChartsJS(
                    id="revenue-chart",
                    optionsKey="revenue-chart",
                    style={"height": "360px"},
                ),
            ],
            style={"marginTop": "2.5rem"},
        ),
    ],
    style={"maxWidth": "1200px", "margin": "0 auto", "padding": "1.5rem"},
)


@app.callback(
    Output("inventory-grid", "configArgs"),
    Output("inventory-grid", "rowData"),
    Input("locale-select", "value"),
)
def set_locale(locale):
    region_by_locale = {
        "en-US": "NA",
        "de-DE": "EU",
        "ja-JP": "APAC",
    }
    target_region = region_by_locale.get(locale)
    if target_region:
        rows = [row for row in INVENTORY_ROWS if row["region"] == target_region]
        if not rows:
            rows = INVENTORY_ROWS
    else:
        rows = INVENTORY_ROWS
    return {"locale": locale}, rows


@app.callback(
    Output("inventory-log", "children"),
    Input("inventory-grid", "selectedRows"),
    Input("inventory-grid", "filterModel"),
    Input("inventory-grid", "sortModel"),
)
def show_inventory_events(selected_rows, filter_model, sort_model):
    payload = {
        "selectedRows": selected_rows or [],
        "filterModel": filter_model or {},
        "sortModel": sort_model or [],
    }
    return json.dumps(payload, indent=2)


@app.callback(
    Output("inventory-click-store", "data"),
    Input("inventory-grid", "cellClicked"),
    State("inventory-click-store", "data"),
    prevent_initial_call=True,
)
def track_inventory_clicks(cell_clicked, stored):
    if not cell_clicked:
        raise PreventUpdate
    stored = stored or {}
    count = int(stored.get("count") or 0) + 1
    per_cell = stored.get("perCell") or {}
    row_id = cell_clicked.get("rowId") or cell_clicked.get("rowIndex")
    col_id = cell_clicked.get("field") or cell_clicked.get("colId")
    key = f"{row_id}::{col_id}"
    per_cell[key] = int(per_cell.get(key) or 0) + 1
    return {"count": count, "last": cell_clicked, "perCell": per_cell, "lastKey": key, "lastKeyCount": per_cell[key]}


@app.callback(Output("inventory-click-display", "children"), Input("inventory-click-store", "data"))
def show_inventory_clicks(data):
    if not data:
        return "Click any cell to see details."
    return json.dumps(
        {
            "clicks_total": data.get("count", 0),
            "clicks_for_last_cell": data.get("lastKeyCount", 0),
            "last": data.get("last"),
        },
        indent=2,
    )


@app.callback(Output("sales-log", "children"), Input("sales-grid", "selectedRows"))
def show_sales_selection(selected_rows):
    rows = selected_rows or []
    return json.dumps({"selectedRows": rows, "count": len(rows)}, indent=2)


@app.callback(
    Output("row-drag-console", "children"),
    Input("row-drag-left", "rowDragEvent"),
    Input("row-drag-right", "rowDragEvent"),
)
def show_row_dragging_console(left_event, right_event):
    events = [e for e in (left_event, right_event) if e]
    if not events:
        return "Drag rows between grids or drop them on the bin to see event payloads."

    latest = max(events, key=lambda evt: evt.get("timestamp", 0))
    return json.dumps(latest, indent=2)


if __name__ == "__main__":
    app.run(debug=True)
