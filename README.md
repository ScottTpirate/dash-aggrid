# dash-aggrid-js

`dash-aggrid-js` (Python import: `dash_aggrid_js`) is a deliberately thin Dash wrapper around **AgGridReact**. It mounts the AG Grid React component directly, so you can copy examples from the AG Grid docs, drop them into a browser-side config registry, and the grid just works inside Dash.

> Warning: **Pick one wrapper per app.** AgGridJS is not meant to run alongside `dash-ag-grid`; loading both introduces duplicate CSS, overlapping themes, and conflicting event glue. Choose one approach per Dash project.

---

## Table of contents

- [Why this wrapper?](#why-this-wrapper)
- [Quick start](#quick-start)
- [Installation](#installation)
- [Creating the config registry](#creating-the-config-registry)
- [Using `AgGridJS` in Dash](#using-aggridjs-in-dash)
- [Dash props & event bridge](#dash-props--event-bridge)
- [Passing arguments (`configArgs`)](#passing-arguments-configargs)
- [Styling & theming](#styling--theming)
- [Enterprise support](#enterprise-support)
- [Advanced patterns](#advanced-patterns)
- [Server-side row model (SSRM)](#server-side-row-model-ssrm)
- [Managing asset size](#managing-asset-size)
- [Developing the component](#developing-the-component)
- [Testing](#testing)
- [Known quirks](#known-quirks)
- [Migration checklist (dash-ag-grid -> AgGridJS)](#migration-checklist-dash-ag-grid--aggridjs)
- [AI assistant playbook](#ai-assistant-playbook)
- [Packaging & distribution](#packaging--distribution)
- [FAQ](#faq)

---

## Why this wrapper?

- **No prop translation.** The exact object you pass to `AgGridReact` in the docs is what the wrapper forwards.
- **Pure JavaScript configs.** Keep row models, value formatters, renderers, and callbacks in JavaScript without serialising through Python.
- **Minimal Dash glue.** Only selection, filters, sorting, edits, and cell clicks are mirrored back to Dash for callbacks.
- **AG Grid v34.x** compatible (Community + optional Enterprise).

---

## Quick start

Clone the repo and run the sample app:

```bash
git clone https://github.com/ScottTpirate/dash-aggrid.git
cd dash-aggrid
npm install
python -m pip install -e .
npm run build
python app.py
```

Visit http://127.0.0.1:8050 for the sample app. `demo_app.py` renders three grids (including an integrated chart) and a standalone AG Charts example powered by `AgChartsJS`. The configs live in `assets/aggrid-configs.js` and `assets/agcharts-configs.js`.

> Reusing in another project? Install the package into that Dash app, copy the asset registry, and you're ready to go.

---

## Installation

### From PyPI (when published)

```bash
pip install dash-aggrid-js
```

### From source

```bash
cd dash-aggrid
npm install
npm run build          # builds JS bundle + backends
pip install -e .
```

---

## Creating the config registry

AgGridJS looks for configs on `window.AGGRID_CONFIGS`. Each entry can be an object or a `(context) => config` factory. Recommended layout (no bundler required):

**1) Shared bootstrap** (`assets/aggrid/00-aggrid-shared.js`)
- Applies the AG Grid Enterprise license if `window.AGGRID_LICENSE_KEY` is present.
- Exposes `window.agGridShared` with helpers (formatters, renderers, themes) and `ensureConfigs()` to create `window.AGGRID_CONFIGS`.

```javascript
/* eslint-disable no-console */
(function initAgGridShared() {
  if (typeof window === "undefined") return;

  // License (optional)
  const key = window.AGGRID_LICENSE_KEY;
  if (key && window.agGrid?.LicenseManager) {
    try {
      window.agGrid.LicenseManager.setLicenseKey(key);
    } catch (err) {
      console.error("License apply failed", err);
    }
  }

  const shared = (window.agGridShared = window.agGridShared || {});
  Object.assign(shared, {
    themes: window.AgGridJsThemes || {},
    formatInteger(value) {
      const fmt = new Intl.NumberFormat("en-US");
      return typeof value === "number" && Number.isFinite(value) ? fmt.format(value) : "";
    },
    ensureConfigs() {
      window.AGGRID_CONFIGS = window.AGGRID_CONFIGS || {};
      return window.AGGRID_CONFIGS;
    },
  });
})();
```

**2) One file per page** (`assets/aggrid/01-<page_name>.js`)
- Register all grids for that page in one file; use helpers from `agGridShared`.

```javascript
/* eslint-disable no-console */
(function registerExamplePageGrids() {
  if (typeof window === "undefined") return;
  const shared = window.agGridShared || {};
  const configs =
    shared.ensureConfigs?.() || (window.AGGRID_CONFIGS = window.AGGRID_CONFIGS || {});

  configs["example-grid"] = function exampleGrid(context = {}) {
    const quartzTheme = shared.themes?.themeQuartz;
    const rowData =
      Array.isArray(context?.dashProps?.rowData) ? context.dashProps.rowData : context?.rowData || [];
    return {
      rowData,
      columnDefs: [
        { headerName: "Name", field: "name" },
        { headerName: "Value", field: "value" },
      ],
      defaultColDef: { sortable: true, resizable: true, filter: false },
      theme: quartzTheme,
    };
  };
})();
```

Load order is alphabetical, so `00-*` runs before any `01-*` page bundles.

---

## Using `AgGridJS` in Dash

```python
from dash import Dash, html, Output, Input
from dash_aggrid_js import AgGridJS

app = Dash(__name__)  # serves ./assets automatically

app.layout = html.Div(
    [
        AgGridJS(
            id="inventory-grid",
            configKey="example-grid",        # must match the JS registry entry
            style={"height": 420},
            configArgs={"locale": "en-US"},  # available to the JS factory
        ),
        html.Pre(id="selection"),
    ]
)

@app.callback(Output("selection", "children"), Input("inventory-grid", "selectedRows"))
def show_selection(rows):
    return f"Selected rows: {rows or []}"

if __name__ == "__main__":
    app.run(debug=True)
```

`rowData` passed from Dash overrides any `rowData` set in the JS config.

---

## Dash props & event bridge

AgGridJS relays key events to Dash via `setProps` (only when explicitly allowed):

- Always: `selectedRows`, `filterModel`, `sortModel`.
- Opt-in (set `registerProps=["cellClicked","editedCells"]` or pass the prop): `cellClicked`, `editedCells`.
- Custom: add any prop name to `registerProps` (e.g., `["cellDoubleClicked"]`) and call `setProps` from your asset.

Example: keep filters/selection in sync with the URL or callbacks:

```python
@app.callback(
    Output("summary", "children"),
    Input("inventory-grid", "selectedRows"),
    Input("inventory-grid", "filterModel"),
    Input("inventory-grid", "sortModel"),
)
def summarize(rows, filters, sorts):
    return {
        "selected": len(rows or []),
        "filters": filters,
        "sorts": sorts,
    }
```

To push a filter model from Dash into the grid, set the `filterModel` prop; the component will apply it and fire the usual `filterChanged` events.

---

## Passing arguments (`configArgs`)

`configArgs` is JSON-serialisable and passed to your registry factory as `context.configArgs`. The factory also receives `{ id, dashProps, setProps }`.

Example: reuse one config for multiple locales and default row sets:

```javascript
configs["sales-grid"] = function salesGrid(context = {}) {
  const locale = context.configArgs?.locale || "en-US";
  const theme = window.agGridShared?.themes?.themeQuartz;
  const rowData = context.configArgs?.rows || context?.dashProps?.rowData || [];

  return {
    rowData,
    columnDefs: [
      { field: "region", rowGroup: true },
      {
        field: "revenue",
        valueFormatter: (p) => Intl.NumberFormat(locale, { style: "currency", currency: "USD" }).format(p.value || 0),
      },
    ],
    defaultColDef: { sortable: true, resizable: true, filter: true },
    theme,
  };
};
```

---

## Registering extra Dash props (`registerProps`)

Dash only accepts callbacks for props declared on the component. Use `registerProps` to opt into event props you plan to emit from your assets (e.g., `cellDoubleClicked`), and gate the built-in click/edit emissions:

```python
AgGridJS(
    id="orders-grid",
    configKey="orders",
    registerProps=["cellClicked", "cellDoubleClicked", "editedCells"],
)
```

Then in your asset:

```javascript
onCellDoubleClicked(event) {
  setProps?.({
    cellDoubleClicked: {
      colId: event?.column?.getColId(),
      value: event?.value,
      data: event?.data || event?.node?.aggData || null,
    },
  });
}
```

If you don't register a prop, AgGridJS won't emit it.

To avoid repeating the same list everywhere, set defaults once at app bootstrap:

```python
from dash_aggrid_js import set_default_props

set_default_props(["cellDoubleClicked"])
```

Defaults are merged into each grid's `registerProps` unless you explicitly pass your own list.

---

## Styling & theming

- AgGridJS registers `window.AgGridJsThemes.themeQuartz` and `themeAlpine` (from AG Grid v34). Set `theme` on your config to use them.
- Include AG Grid CSS separately in your Dash app (e.g., add `ag-grid.css` + a theme CSS to `assets/` or link from a CDN).
- Use your own CSS by applying `className`/`style` on the Dash component and custom cell renderers in the registry.

---

## Enterprise support

- Enterprise modules are registered automatically when available. Provide `window.AGGRID_LICENSE_KEY` before the registry loads to avoid watermarks:

```javascript
// assets/license.js
window.AGGRID_LICENSE_KEY = "<YOUR LICENSE KEY>";
```

- Keep enterprise-only props in the registry (row grouping, pivoting, charts, etc.); the wrapper doesn't block them.

---

## Advanced patterns

- **Shared access to grid API:** `window.AgGridJsRegistry.getApiAsync(<gridId>)` resolves the grid API once ready.
- **User + Dash handlers:** Registry callbacks still run; AgGridJS wraps them and then mirrors events back to Dash.
- **Config factories:** Because configs are functions, you can branch on `configArgs`, feature flags, or `dashProps`.
- **Charts:** Use `params.api.createRangeChart` in registry callbacks (`onFirstDataRendered`) to mount AG Charts into a provided container.

---

## Server-side row model (SSRM)

AgGridJS ships helpers to register DuckDB-backed SSRM endpoints automatically.

1) **Dash usage**

```python
AgGridJS(
    id="orders-grid",
    configKey="ssrm-grid",
    style={"height": 520},
    configArgs={
        "ssrm": {
            "duckdb_path": "ssrm_demo.duckdb",  # required
            "table": "orders",                  # table/view or subquery
            # optional: "endpoint": "/custom/ssrm/orders"
        }
    },
)
```

2) **Registry entry** (simplified from `assets/aggrid-configs.js`)

```javascript
configs["ssrm-grid"] = function ssrmGrid(context = {}) {
  const gridId = context.id || "ssrm-grid";
  const ssrmArgs = context.configArgs?.ssrm || {};
  const baseEndpoint = String(ssrmArgs.endpoint || "_aggrid/ssrm").replace(/\/$/, "");

  const datasource = {
    getRows(params) {
      fetch(`${baseEndpoint}/${encodeURIComponent(gridId)}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params.request || {}),
      })
        .then((r) => r.json())
        .then((payload) =>
          params.success({
            rowData: Array.isArray(payload.rows) ? payload.rows : [],
            rowCount: typeof payload.rowCount === "number" ? payload.rowCount : undefined,
          })
        )
        .catch((err) => {
          console.error("AgGridJS SSRM request failed", err);
          params.fail();
        });
    },
  };

  return {
    rowModelType: "serverSide",
    serverSideDatasource: datasource,
    columnDefs: [
      { field: "region", filter: "agSetColumnFilter", rowGroup: true },
      { field: "product", filter: "agSetColumnFilter" },
      { field: "units", type: "numericColumn", aggFunc: "sum" },
    ],
    defaultColDef: { sortable: true, filter: true, resizable: true, enableRowGroup: true, enablePivot: true },
  };
};
```

3) **What the backend does**
- `configArgs["ssrm"]` triggers `register_duckdb_ssrm` (Python) to expose routes under `_aggrid/ssrm/<gridId>` plus `/distinct/<col>` for set filters. Use relative paths so app prefixes (e.g., Dash Enterprise) are preserved.
- Incoming SSRM datasource requests are translated into DuckDB SQL via `dash_aggrid_js.ssrm.sql_for`.
- Requires `duckdb` installed in your Dash environment.

Notes:
- `configArgs.ssrm.endpoint` lets you customise the base path and avoid collisions.
- Set filters automatically fetch distinct values from `/distinct` when you use `filter: 'agSetColumnFilter'`.
- You can supply a `builder` callable instead of `table` if you need dynamic SQL.

---

## Managing asset size

- `npm run build` produces a minified bundle; ship the built assets, not `npm start` output.
- Avoid loading both `dash-ag-grid` and `dash-aggrid-js`; duplicate CSS/JS bloats downloads.
- Keep registry files focused (one per page) to minimise parse/exec time.

---

## Developing the component

- Common commands (see `Makefile`):
  - `make install-dev` - install Python dev+test extras
  - `make js-build` - `npm ci` + bundle + backend stubs
  - `make lint` - pre-commit (ruff + black)
  - `make test` - pytest (requires Chrome/Chromedriver for the UI test)
  - `make dist` - rebuild JS then build wheel/sdist
- Version source of truth: `dash_aggrid_js/__about__.py` (sync to `package.json` and `dash_aggrid_js/package-info.json` via `make sync-version VERSION=X.Y.Z`).

---

## Testing

- `pytest dash-aggrid/tests` runs a headless browser smoke test that ensures demo grids render rows. It skips if Chrome/Chromedriver is unavailable.
- Add Dash callback-level tests by following the pattern in `tests/test_usage.py` (ThreadedRunner + Browser).

---

## Known quirks

- If `configKey` is missing, the component renders a dashed placeholder instead of crashing.
- Load order matters: keep shared helpers in `00-*`, page registries in `01-*`.
- Avoid mixing with `dash-ag-grid`; CSS and event bridges will conflict.
- Set filters with SSRM need a `gridId` in requests (automatically injected); don't override `serverSideDatasource.getRows` without preserving `request.gridId`.
- Menu `menuTabs` validation only runs in dev mode; invalid tabs log warnings.

---

## Migration checklist (dash-ag-grid -> AgGridJS)

1. Move columnDefs/gridOptions into `assets/aggrid/01-*.js` under `window.AGGRID_CONFIGS`.
2. Replace `dash_ag_grid.AgGrid` usages with `dash_aggrid_js.AgGridJS(configKey=..., configArgs=...)`.
3. Keep `rowData` in Dash only if you truly need Python-sourced data; otherwise move data fetching to the registry/DuckDB.
4. Map callbacks:
   - `selectedRows` -> same
   - `filterModel`/`sortModel` -> same shape as AG Grid JS
   - Edits -> `editedCells[0]`
   - Cell clicks -> `cellClicked`
5. Remove the `dash-ag-grid` CSS/JS bundles from `assets/`.

---

## AI assistant playbook

- Do not invent props; use AG Grid docs (v34) and the registry pattern shown above.
- Keep complex logic in JS assets; pass only JSON-friendly state through Dash props.
- Prefer set filters, row grouping, and SSRM examples from AG Grid's official guides; adapt minimally.
- When editing docs or code, avoid mixing this wrapper with `dash-ag-grid`.

---

## Packaging & distribution

- Version lives in `dash_aggrid_js/__about__.py`; keep `package.json` and `dash_aggrid_js/package-info.json` in sync via `make sync-version VERSION=X.Y.Z`.
- Build assets + wheels locally with `make dist` (runs `npm run build` then `python -m build`).
- Git tags of the form `vX.Y.Z` trigger the `Publish` workflow, which verifies the tag matches the version, rebuilds assets, runs tests, and publishes to PyPI using `PYPI_API_TOKEN`.
- CI (`CI` workflow) runs lint/build/tests on PRs and pushes to `main`/`master`.
- Keep `CHANGELOG.md` updated for anything user-facing.

---

## FAQ

**Is this the same as `dash-ag-grid`?**  
No. `dash-aggrid-js` mounts `AgGridReact` directly and keeps complex logic in JavaScript assets; `dash-ag-grid` translates props in Python. Use one per Dash app to avoid CSS/event conflicts.

**Do I need a bundler?**  
No. Drop the generated bundle plus your config registry into `assets/` and Dash will serve them. Use `npm run build` only when developing the component itself or updating bundled assets.

**How do I access the grid API from elsewhere?**  
Use `window.AgGridJsRegistry.getApiAsync("<gridId>")` in your own scripts to get the API once the grid is ready.

**Can I use SSRM without DuckDB?**  
You can, but the built-in helpers expect DuckDB. Provide your own `serverSideDatasource.getRows` in the registry and omit `configArgs.ssrm` if you're targeting another backend.
