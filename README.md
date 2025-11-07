# dash_aggrid

dash_aggrid is a deliberately thin Dash wrapper around **AgGridReact**. It mounts the AG Grid React component directly, so you can copy examples from the AG Grid docs, drop them into a browser-side config registry, and the grid just works inside Dash.

> ⚠️ **Pick one wrapper per app.** AgGridJS is not meant to run alongside `dash-ag-grid`; loading both introduces duplicate CSS, overlapping themes, and conflicting event glue. Choose one approach per Dash project.

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
- [Migration checklist (dash-ag-grid → AgGridJS)](#migration-checklist-dash-ag-grid--aggridjs)
- [AI assistant playbook](#ai-assistant-playbook)
- [Packaging & distribution](#packaging--distribution)
- [Future enhancements](#future-enhancements)
- [FAQ](#faq)

---

## Why this wrapper?

Dash ships with Python-to-JS property mappings for many components. AG Grid already provides a rich React interface; we wanted a wrapper that stays out of the way:

- **No prop translation.** The exact object you pass to `AgGridReact` in the docs is what the wrapper forwards.
- **Pure JavaScript configs.** Keep complex row models, value formatters, renderers, and callbacks in JavaScript without serialising through Python.
- **Minimal Dash glue.** Only a handful of grid events (selection, filters, sorting, edits) are mirrored back to Dash for callbacks.
- **AG Grid v34.x** compatible (Community + optional Enterprise).

---

## Quick start

Clone the repo and run the sample app:

```bash
git clone https://github.com/ScottTpirate/dash-aggrid.git
cd dash-aggrid
npm install
npm run build
python -m pip install -e .
python app.py
```

Visit http://127.0.0.1:8050 for the sample app. `demo_app.py` renders three grids (including an integrated chart) and a standalone AG Charts example powered by `AgChartsJS`. The configs live in `assets/aggrid-configs.js` and `assets/agcharts-configs.js`.

> Reusing in another project? Install the package into that Dash app, copy the asset, and you’re ready to go.

---

## Installation

### In an existing Dash project

1. Install the Python package (local path shown; swap in the PyPI name `dash_aggrid` when using the published wheel):

   ```bash
   python -m pip install /path/to/dash_aggrid
   ```

2. If working from source, build the JS bundle once:

   ```bash
   cd /path/to/dash-aggrid
   npm install
   npm run build
   ```

3. Copy `assets/aggrid-configs.js` into your Dash app’s `assets/` folder (or create your own registry script).

4. Import and use the component:

   ```python
   from dash_aggrid import AgGridJS
   ```

Dash will serve the JS bundle automatically when the component is requested.

---

## Creating the config registry

`AgGridJS` looks up options from `window.AGGRID_CONFIGS`. Keep `assets/aggrid-configs.js` as your registry file: each key represents a grid and returns either a plain object or a factory function that the wrapper will call.

```javascript
// assets/aggrid-configs.js
(function registerAgGridConfigs() {
  const { themeQuartz } = window.AgGridJsThemes || {};

  const configs = {
    // Static config
    'feature-grid': {
      columnDefs: [
        { field: 'make' },
        { field: 'model' },
        { field: 'price', valueFormatter: (p) => Intl.NumberFormat().format(p.value) },
      ],
      defaultColDef: { sortable: true, filter: true, resizable: true },
      rowData: window.FEATURE_GRID_ROWS || [],
      theme: themeQuartz?.withParams?.({ borderRadius: 12 }),
    },

    // Factory config – reads configArgs/dashProps
    'sales-grid': ({ configArgs }) => ({
      columnDefs: getSalesColumns(configArgs),
      defaultColDef: { sortable: true, filter: true, resizable: true },
      rowData: configArgs?.rowData ?? [],
    }),

    // SSRM grid – demonstrates server-side datasource wiring
    'ssrm-grid': function ssrmGrid(context) {
      const gridId = context?.id || 'ssrm-grid';
      const ssrmArgs = context?.configArgs?.ssrm || {};
      const baseEndpoint = String(ssrmArgs.endpoint || '/_aggrid/ssrm').replace(/\/$/, '');

      const datasource = {
        getRows(params) {
          fetch(`${baseEndpoint}/${encodeURIComponent(gridId)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params.request || {}),
          })
            .then(async (response) => {
              const payload = await response.json().catch(() => null);
              if (!response.ok || !payload || typeof payload !== 'object') {
                throw new Error(payload?.error || `HTTP ${response.status}`);
              }
              const rows = Array.isArray(payload.rows) ? payload.rows : [];
              const rowCount = typeof payload.rowCount === 'number' ? payload.rowCount : undefined;
              params.success({ rowData: rows, rowCount });
            })
            .catch((err) => {
              console.error('AgGridJS SSRM request failed', err);
              params.fail();
            });
        },
      };

      return {
        columnDefs: buildSsrMColumns(),
        defaultColDef: baseColumnDefaults(),
        autoGroupColumnDef: { minWidth: 220 },
        rowModelType: 'serverSide',
        cacheBlockSize: 100,
        sideBar: ['columns', 'filters'],
        rowGroupPanelShow: 'always',
        serverSideDatasource: datasource,
        theme: themeQuartz,
      };
    },
  };

  window.AGGRID_CONFIGS = { ...(window.AGGRID_CONFIGS || {}), ...configs };
}());
```

Registry entries can be either:

- **Static** – an object literal (useful for simple read-only grids).
- **Factory** – a function receiving `{ id, configKey, configArgs, dashProps }`. Use factories when you need runtime arguments (locale toggles, SSRM metadata, chart options) or when wiring server-side datasources.

The demo app follows this structure for every grid (`feature-grid`, `sales-grid`, `analytics-grid`, `ssrm-grid`) and does the same for charts via `assets/agcharts-configs.js`. Keeping everything in these registries keeps the asset declarative and makes it simple to share helpers across grids.

---

## Using `AgGridJS` in Dash

```python
from dash import Dash, html, Output, Input
from dash_aggrid import AgGridJS

app = Dash(__name__)  # serves ./assets/aggrid-configs.js automatically

app.layout = html.Div(
    [
        AgGridJS(id="sales", configKey="sales-grid", style={"height": 420}),
        html.Pre(id="debug", style={"marginTop": "1rem"}),
    ]
)


@app.callback(Output("debug", "children"), Input("sales", "selectedRows"))
def display_selected(rows):
    if not rows:
        return "No selection"
    return f"Selected rows ({len(rows)}):\n{rows}"


if __name__ == "__main__":
    app.run(debug=True)
```

`configKey` is the only required prop. The wrapper will fetch the config, mount `AgGridReact`, and mirror key events back to Dash.

---

## Dash props & event bridge

| Prop            | Direction | Description |
|-----------------|-----------|-------------|
| `configKey`     | Dash → JS | Required. Looks up `window.AGGRID_CONFIGS[configKey]`. |
| `configArgs`    | Dash → JS | Optional JSON-serialisable payload passed to config factory functions. |
| `className`     | Dash → JS | Container class (defaults to `ag-theme-quartz`). |
| `style`         | Dash → JS | Inline styles for sizing/positioning. |
| `rowData`       | Dash → JS | Optional row data array supplied directly from Dash; overrides `rowData` defined in the JS config. |
| `selectedRows`  | JS → Dash | Array of selected rows (`api.getSelectedRows()`). |
| `filterModel`   | JS → Dash | Current filter model (`api.getFilterModel()`). |
| `sortModel`     | JS → Dash | Simplified array of columns with active sorting (`colId`, `sort`, `sortIndex`). |
| `editedCells`   | JS → Dash | Single-element array describing the most recent cell edit (`rowId`, `colId`, `oldValue`, `newValue`). |

The wrapper:

- Runs user-defined AG Grid handlers first, then calls `setProps`.
- Stores `gridApi` on `onGridReady` so other events can read selection/filter/sort state.
- Emits initial `selectedRows`, `filterModel`, and `sortModel` after the grid becomes ready.

Need more events? Add them to your config and call `setProps` manually.

---

## Passing arguments (`configArgs`)

Use `configArgs` when Dash needs to parameterise the grid:

```python
@app.callback(Output("sales", "configArgs"), Input("region-dropdown", "value"))
def choose_region(region):
    return {"region": region}
```

In JS:

```javascript
window.AGGRID_CONFIGS['sales-grid'] = ({ configArgs }) => ({
  columnDefs: getColumnsFor(configArgs?.region),
  rowData: [],
});
```

`configArgs` must be JSON-serialisable. For functions or class instances, keep them inside the registry instead.

---

## Styling & theming

AG Grid v34 defaults to the **Theming API**. The wrapper exposes common themes on `window.AgGridJsThemes` so your asset can pick them up on a per-grid basis:

```javascript
const { themeQuartz, themeAlpine } = window.AgGridJsThemes || {};

window.AGGRID_CONFIGS['sales-grid'] = {
  rowData: [...],
  columnDefs: [...],
  theme: themeQuartz.withParams({
    accentColor: '#2563eb',
    headerBackgroundColor: '#0f172a',
    headerTextColor: '#e2e8f0'
  })
};

window.AGGRID_CONFIGS['inventory-grid'] = ({ configArgs }) => ({
  rowData: [...],
  columnDefs: [...],
  theme: themeAlpine.withParams({
    accentColor: configArgs?.locale === 'ja-JP' ? '#f97316' : '#14b8a6',
    borderRadius: 10
  })
});
```

- `style` still controls the container height/width. Set the height explicitly so the grid has room to render.
- `className` is optional and can be used for extra layout styling. Theme classes are no longer required when using the theming API.
- If you want to keep the legacy CSS themes instead, set `theme: 'legacy'` in your registry entry and include the old CSS manually.
- Integrated charts rely on AG Grid Enterprise. If the module is not present, the grid will skip chart creation automatically.

## Standalone AG Charts

`AgChartsJS` wraps the charting engine from `ag-charts-community` without the React helper. Define chart options in `window.AGCHART_CONFIGS` and point the component at a key:

```javascript
// assets/agcharts-configs.js
window.AGCHART_CONFIGS = window.AGCHART_CONFIGS || {};

window.AGCHART_CONFIGS['revenue-chart'] = ({ configArgs }) => ({
  data: [...],
  title: { text: 'Quarterly Revenue' },
  series: [
    { type: 'bar', direction: 'vertical', xKey: 'quarter', yKey: 'north' },
    { type: 'bar', direction: 'vertical', xKey: 'quarter', yKey: 'emea' },
  ],
  theme: {
    baseTheme: 'ag-default',
    palette: {
      fills: [configArgs?.accentColor || '#2563eb', '#f97316'],
      strokes: ['#1e3a8a', '#9a3412'],
    },
  },
});
```

In Dash:

```python
from dash_aggrid import AgChartsJS

AgChartsJS(id="revenue", optionsKey="revenue-chart", style={"height": 360})
```

The wrapper takes either `options` (inline chart definition) or an `optionsKey` that resolves to `window.AGCHART_CONFIGS[key]`. Options factories receive `{ optionsKey, configArgs, dashProps }` just like grid configs.

---

## Enterprise support

Enterprise features are fully supported. To enable:

1. Ensure `ag-grid-enterprise` is installed (this package already includes it).
2. Expose the license key on the window before configs load:

   ```javascript
   window.AGGRID_LICENSE_KEY = "<YOUR KEY>";
   ```

   The sample asset calls `LicenseManager.setLicenseKey` if the key exists. Remember: the key is visible client-side. Inject it dynamically if you prefer not to store it in source control.

---

## Advanced patterns

- **Server-side row model:** See the [dedicated SSRM walkthrough](#server-side-row-model-ssrm) for the SQL helper, distinct endpoints, and asset patch.
- **Multiple variants:** Store each variant under its own key (`window.AGGRID_CONFIGS['sales/daily']`, `['sales/monthly']`), or return different objects inside a single factory.
- **Custom Dash outputs:** Pass `context` or other callbacks through the config and call `setProps` yourself for bespoke events (row drag, clipboard, etc.).
- **Sharing state between grids:** Keep shared data on `window` or a dedicated JS module; use Dash callbacks on `selectedRows`/`filterModel` to sync across components.

---

## Server-side row model (SSRM)

AgGridJS pairs a DuckDB-aware SQL builder with Dash hooks so server-side row-model grids work without manual Flask routes. Any grid that declares `configArgs={"ssrm": ...}` automatically registers JSON endpoints for data blocks and Set Filter values.

### 1. Configure the grid in Dash

```python
from pathlib import Path

from dash_aggrid import AgGridJS

AgGridJS(
    id="orders-grid",
    configKey="orders-ssrm",
    style={"height": 420},
    configArgs={
        "ssrm": {
            "duckdb_path": str(Path("data/orders.duckdb")),
            "table": "public.orders",        # or provide `builder` for custom SQL
            # "builder": lambda req: sql_for(req, "(SELECT * FROM ... ) AS src"),
            # "endpoint": "/_aggrid/ssrm"    # optional route prefix override
        }
    },
)
```

- `duckdb_path` is required and is opened read-only for each request.
- Supply either a `table`/sub-query string or a custom `builder(request) -> SQL` callable (advanced scenarios).
- Optional `endpoint` lets you change the HTTP prefix (defaults to `/_aggrid/ssrm`).

### 2. Wire the asset config

The JS registry just needs to opt the grid into SSRM so the datasource can post to the generated endpoint; the component takes care of Set Filter values automatically.

```javascript
// assets/aggrid-configs.js
(function () {
  const { themeQuartz } = window.AgGridJsThemes || {};

  window.AGGRID_CONFIGS['orders-ssrm'] = (context) => {
    const gridId = context?.id || 'orders-grid';
    const ssrmArgs = context?.configArgs?.ssrm || {};
    const baseEndpoint = (ssrmArgs.endpoint || '/_aggrid/ssrm').replace(/\/$/, '');

    return {
      columnDefs: [
        { field: 'order_id', headerName: 'Order ID', maxWidth: 130 },
        { field: 'region', filter: 'agSetColumnFilter', rowGroup: true },
        { field: 'product', minWidth: 160, filter: 'agSetColumnFilter' },
        { field: 'category', minWidth: 150, filter: 'agSetColumnFilter' },
        { field: 'quarter', maxWidth: 140, filter: 'agSetColumnFilter' },
        { field: 'units', type: 'numericColumn', aggFunc: 'sum' },
        {
          field: 'revenue',
          type: 'numericColumn',
          aggFunc: 'sum',
          valueFormatter: (params) => Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            maximumFractionDigits: 0,
          }).format(params.value || 0),
        },
      ],
      defaultColDef: {
        flex: 1,
        sortable: true,
        filter: true,
        resizable: true,
        enableRowGroup: true,
        enablePivot: true,
        enableValue: true,
      },
      autoGroupColumnDef: { minWidth: 220 },
      rowModelType: 'serverSide',
      cacheBlockSize: 100,
      sideBar: ['columns', 'filters'],
      rowGroupPanelShow: 'always',
      serverSideDatasource: {
        getRows(params) {
          fetch(`${baseEndpoint}/${encodeURIComponent(gridId)}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(params.request || {}),
          })
            .then(async (response) => {
              const payload = await response.json().catch(() => null);
              if (!response.ok || !payload || typeof payload !== 'object') {
                throw new Error(payload?.error || `HTTP ${response.status}`);
              }
              const rows = Array.isArray(payload.rows) ? payload.rows : [];
              const rowCount = typeof payload.rowCount === 'number' ? payload.rowCount : undefined;
              params.success({ rowData: rows, rowCount });
            })
            .catch((err) => {
              console.error('AgGridJS SSRM request failed', err);
              params.fail();
            });
        },
      },
      theme: themeQuartz,
    };
  };
}());
```

### 3. Notes

- Multiple SSRM grids can coexist; give each a unique `id` and `configKey`. Routes are registered automatically per grid/table pair via Dash hooks—no manual Flask code required.
- Set Filters pick up values via `/distinct` only for columns using `agSetColumnFilter` (or a Multi Filter that includes it). Add that filter type to any columns where you want distinct lookups.
- Pivot mode currently falls back to basic SQL; if you need pivoted results you’ll need to extend `sql_for` (grouping and aggregation are supported today).
- Custom builders receive the raw AG Grid request payload. Use `sql_for` inside the builder if you need to compose additional joins or filters.
- You can still call `sql_for`/`distinct_sql` manually (for exports, reports, etc.) — they mirror the autogenerated queries.

---
## Managing asset size

`assets/aggrid-configs.js` ships as a single registry for ease of onboarding. Browser caching and HTTP/2 keep it efficient, but for very large apps you can:

- Split configs across multiple asset files (one per page/feature) and guard them with early returns (`if (window.location.pathname !== '/reports') return;`).
- Lazily attach large `rowData` arrays by fetching from the server (`fetch('/api/data').then(...)`) instead of embedding huge literals.
- Minify/treeshake custom helpers via your build pipeline if you generate assets programmatically.

The sample file stays small—only configuration objects and lightweight factories—so no additional bundling is required by default.

---

## Developing the component

```bash
npm install                # install JS dependencies (React, AG Grid, tooling)
npm run build              # build the production bundle + regenerate Dash bindings
python -m pip install -e . # expose the component as an editable install
python app.py              # run the demo Dash app
```

- Component source lives in `src/lib/components/AgGridJS.jsx`.
- Webpack output goes to `dash_aggrid/dash_aggrid.min.js`.
- Python/R/Julia wrappers are regenerated via `dash-generate-components` during `npm run build`.

Need to tweak bundling? Edit `webpack.config.js`.

---

## Testing

Current repo ships with a simple smoke test:

```bash
python -m pytest tests/test_usage.py
```

For end-to-end tests, reintroduce a `dash_duo` Selenium test—just make sure Chrome/Chromedriver (or another WebDriver) is available.

---

## Known quirks

- Chrome will log "Added non-passive event listener" when AG Charts attaches wheel handlers. The library has not yet marked them as passive; there is no functional impact.
- React 18 warns about deprecated `componentWillMount`/`componentWillReceiveProps` lifecycles inside AG Grid Enterprise. They are harmless and scheduled for removal upstream.

---

## Migration checklist (dash-ag-grid → AgGridJS)

- Install the new wrapper (`pip install dash_aggrid`) and rebuild once (`npm install && npm run build`) so Dash can serve the bundled assets.
- Move grid definitions out of Dash props and into `assets/aggrid-configs.js`. Copy each grid’s `columnDefs`, default column settings, and event handlers into a registry entry (object or factory) so the asset controls configuration, not Python.
- Mirror the same approach for charts (`assets/agcharts-configs.js`) so chart options live alongside grid configs and can react to `configArgs`.
- Swap Python `gridOptions`/`columnState` assignments for `configKey`/`configArgs`. Any runtime values (locale, SSRM metadata, user selections) travel through `configArgs` and the JS factory can honour them.
- Use the component’s `rowData` prop when you truly need to push data from Dash; otherwise keep data fetching in JS (e.g., SSRM datasource, fetches).
- Port Python-defined renderers/formatters/value parsers to JavaScript functions—AgGridJS does not serialise functions across the bridge.
- Re-implement dash-ag-grid conveniences (persistence, context menus, quick filters) using native AG Grid APIs in the asset, calling `setProps` only when you need to notify Dash.
- Replace theme classes with the theming API: grab `themeQuartz`/`themeAlpine` from `window.AgGridJsThemes` and call `.withParams(...)` where needed.
- Continue handling Enterprise licensing by setting `window.AGGRID_LICENSE_KEY` before configs execute; the sample helper still applies it automatically.

---

## AI assistant playbook

- **Understand the registry**: Every grid/chart lives in `assets/aggrid-configs.js` (and `agcharts-configs.js`). Each exported key should be a self-contained config or factory.
- **When adding a grid**: Duplicate a pattern, update the key, tweak `columnDefs`, defaults, and any custom logic. Keep everything serialisable and let the registry own datasource setup (e.g., SSRM).
- **Migrations**: Move Python `gridOptions`/callbacks into JS; pass runtime values via `configArgs`. Use the component’s `rowData` only when Dash truly needs to push data.
- **SSRM**: Provide `configArgs={ ssrm: { duckdb_path, table | builder, endpoint? } }`. The helper auto-registers routes and set-filter values.
- **Charts**: Follow the same registry pattern in `agcharts-configs.js`; use factories when you need options derived from `configArgs`.
- **Bundle hygiene**: Run `npm run build` after editing component source or assets so Dash serves the latest bundle.

---

## Packaging & distribution

1. Run `npm run build` to guarantee the JS bundle matches the source.
2. Build Python artefacts (requires network access to fetch build-system deps):

   ```bash
   python -m build  # creates dist/*.tar.gz and dist/*.whl
   ```

3. Publish:
   - PyPI: `twine upload dist/*`
   - npm (optional): `npm publish`

`MANIFEST.in` already lists the built bundles so Dash can serve them when installed from a wheel/sdist.

For large apps you can drop page-specific config scripts into `assets/` and guard them by pathname (e.g., `if (window.location.pathname === '/reports') { ... }`). Each script is still global, but the early-return keeps unrelated pages lightweight.

---

## Future enhancements

- Add pytest coverage for `sql_for` and `distinct_sql` across filter combinations, grouping hierarchies, and pagination paths.
- Provide extension hooks so callers can override identifier quoting or literal casting without monkeypatching the helper.
- Document or automate SSRM export row-count strategies once production usage surfaces common patterns.
- Extend `sql_for` to generate pivot SQL so the SSRM demo supports AG Grid pivot mode end-to-end.

---

## FAQ

**How do I load configs from TypeScript?**  
Compile them to JS (e.g., via `tsc`) and expose the resulting objects/functions on `window.AGGRID_CONFIGS`.

**Can I update data from Dash callbacks?**  
Yes. Return new data through `configArgs` or store it in a registry the config reads from. You can also hit custom HTTP endpoints from within the config (server-side row model).

**What if I need more events back in Dash?**  
Add the AG Grid handler in the registry and call `setProps` manually. Example:

```javascript
window.AGGRID_CONFIGS['editable-grid'] = {
  onRowDragEnd: (params) => {
    params.api.refreshCells();
    params.context?.setProps?.({ lastDragged: params.node.data });
  },
  context: { setProps: window.dash_clientside.set_props }, // optional helper
};
```

**Does this conflict with dash-ag-grid?**  
No; they serve different audiences. This package is intentionally thin and expects you to manage grid options in JS. `dash-ag-grid` provides Python prop mapping and many Dash-first conveniences.

---

Questions or ideas? Open an issue or PR—this wrapper aims to stay lightweight while keeping the AG Grid React API fully accessible in Dash.
