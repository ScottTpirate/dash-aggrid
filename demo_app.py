import json
from pathlib import Path

import duckdb
from dash import Dash, Input, Output, dcc, html

from aggrid_js import AgChartsJS, AgGridJS
from sample_data import ANALYTICS_ROWS, INVENTORY_ROWS, SALES_ROWS, SSRM_ROWS


DATA_DIR = Path(__file__).parent
DUCKDB_FILE = DATA_DIR / "ssrm_demo.duckdb"
SSRM_TABLE = "ssrm_demo"


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
                        ),
                        html.Small(
                            "Theme: Alpine (custom accent & rounded corners)",
                            style={"display": "block", "marginTop": "0.5rem"},
                        ),
                        html.Pre(
                            id="inventory-log",
                            style={"whiteSpace": "pre-wrap", "marginTop": "0.75rem", "fontSize": "0.85rem"},
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
    Input("inventory-grid", "editedCells"),
)
def show_inventory_events(selected_rows, filter_model, sort_model, edited_cells):
    payload = {
        "selectedRows": selected_rows or [],
        "filterModel": filter_model or {},
        "sortModel": sort_model or [],
        "editedCells": edited_cells or [],
    }
    return json.dumps(payload, indent=2)


@app.callback(Output("sales-log", "children"), Input("sales-grid", "selectedRows"))
def show_sales_selection(selected_rows):
    rows = selected_rows or []
    return json.dumps({"selectedRows": rows, "count": len(rows)}, indent=2)


if __name__ == "__main__":
    app.run(debug=True)
