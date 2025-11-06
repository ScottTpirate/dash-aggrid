from dash import Dash, html, Output, Input
from aggrid_js import AgGridJS

from sample_data import SALES_ROWS

app = Dash(__name__)  # auto-serves ./assets/aggrid-configs.js

app.layout = html.Div([
    AgGridJS(id="sales", configKey="sales-grid", rowData=SALES_ROWS, style={"height": 420}),
    html.Div(id="debug")
])


@app.callback(Output("debug", "children"), Input("sales", "selectedRows"))
def show_selected(rows):
    return f"Selected: {len(rows)} rows" if rows else "No selection"


if __name__ == "__main__":
    app.run(debug=True)
