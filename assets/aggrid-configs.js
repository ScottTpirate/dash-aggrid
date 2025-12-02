/* eslint-disable no-console */
(function initialiseAgGridConfigs() {
  if (typeof window === 'undefined') {
    return;
  }

  const enterprise = window.agGrid && window.agGrid.LicenseManager;
  if (enterprise && window.AGGRID_LICENSE_KEY) {
    try {
      enterprise.setLicenseKey(window.AGGRID_LICENSE_KEY);
    } catch (err) {
      console.error('Failed to apply AG Grid Enterprise license', err);
    }
  }

  const configs = {
    'sales-grid': function salesGrid(context) {
      const themes = window.AgGridJsThemes || {};
      const quartzTheme = themes.themeQuartz;
      const rows = context?.configArgs?.rowData || [];

      return {
        columnDefs: [
          { field: 'make' },
          { field: 'model' },
          {
            field: 'price',
            valueFormatter: (p) => Intl.NumberFormat().format(p.value),
          },
        ],
        defaultColDef: { sortable: true, filter: true, resizable: true },
        rowData: rows,
        theme: quartzTheme
          ? quartzTheme.withParams({
              accentColor: '#2563eb',
              fontFamily: 'Inter, system-ui, sans-serif',
              headerBackgroundColor: '#0f172a',
              headerTextColor: '#e2e8f0',
            })
          : undefined,
        onGridReady: (params) => {
          if (params?.api?.sizeColumnsToFit) {
            params.api.sizeColumnsToFit();
          }
        },
      };
    },
    'feature-grid': function featureGrid(context) {
      const themes = window.AgGridJsThemes || {};
      const alpineTheme = themes.themeAlpine;
      const cfgArgs = context && context.configArgs ? context.configArgs : null;
      const locale = cfgArgs && cfgArgs.locale ? cfgArgs.locale : 'en-US';
      const currency = new Intl.NumberFormat(locale, {
        style: 'currency',
        currency: 'USD',
        maximumFractionDigits: 0,
      });
      const inventory = context?.dashProps?.rowData || [];
      const setProps = context?.setProps;

      const resolveRollup = (node) => {
        if (!node) {
          return null;
        }
        if (node.aggData && typeof node.aggData === 'object') {
          return node.aggData;
        }
        if (node.data && typeof node.data === 'object') {
          return node.data;
        }
        return null;
      };

      return {
        rowData: inventory,
        columnDefs: [
          {
            headerName: 'Category',
            field: 'category',
            rowGroup: true,
            hide: true,
          },
          { headerName: 'Product', field: 'product', minWidth: 160 },
          {
            headerName: 'Region',
            field: 'region',
            filter: 'agSetColumnFilter',
            minWidth: 140,
          },
          {
            headerName: 'Units Sold',
            field: 'units',
            editable: true,
            type: 'numericColumn',
            aggFunc: 'sum',
            valueParser: (params) => Number(params.newValue) || 0,
            cellStyle: function cellStyle(params) {
              return params.value > 50 ? { fontWeight: 'bold' } : null;
            },
          },
          {
            headerName: 'Revenue',
            field: 'revenue',
            valueFormatter: function valueFormatter(params) {
              var value = params.value;
              return currency.format(value || 0);
            },
            type: 'numericColumn',
            aggFunc: 'sum',
            minWidth: 140,
          },
          {
            headerName: 'Stock',
            field: 'stock',
            editable: true,
            type: 'numericColumn',
            valueParser: (params) => Number(params.newValue) || 0,
          },
          {
            headerName: 'Backorder',
            field: 'backorder',
            cellRenderer: function cellRenderer(params) {
              return params.value ? '⚠️ Yes' : '✅ No';
            },
            filter: 'agSetColumnFilter',
          },
        ],
        defaultColDef: {
          flex: 1,
          sortable: true,
          filter: true,
          resizable: true,
        },
        animateRows: true,
        rowSelection: {
          mode: 'multiRow',
          checkboxes: true,
          headerCheckbox: true,
          checkboxLocation: 'selectionColumn',
          groupSelects: 'descendants',
        },
        theme: alpineTheme
          ? alpineTheme.withParams({
              accentColor: cfgArgs && cfgArgs.locale === 'ja-JP' ? '#f97316' : '#14b8a6',
              borderRadius: 10,
              headerFontSize: 14,
            })
          : undefined,
        sideBar: {
          toolPanels: [
            {
              id: 'columns',
              labelDefault: 'Columns',
              iconKey: 'columns',
              toolPanel: 'agColumnsToolPanel',
            },
            {
              id: 'filters',
              labelDefault: 'Filters',
              iconKey: 'filter',
              toolPanel: 'agFiltersToolPanel',
            },
          ],
          defaultToolPanel: 'filters',
        },
        statusBar: {
          statusPanels: [
            { statusPanel: 'agTotalRowCountComponent', align: 'left' },
            { statusPanel: 'agFilteredRowCountComponent' },
            { statusPanel: 'agAggregationComponent' },
          ],
        },
        autoGroupColumnDef: {
          headerName: 'Category',
          minWidth: 180,
          cellRendererParams: {
            suppressCount: false,
          },
        },
        groupDefaultExpanded: -1,
        selectionColumnDef: {
          maxWidth: 60,
          resizable: false,
          pinned: 'left',
          suppressHeaderMenuButton: true,
        },
        onCellClicked: function onCellClicked(event) {
          // Users must include "cellClicked" (or any custom prop) in registerProps on the Dash side
          // before wiring callbacks to it. This handler only emits; Dash validation is opt-in.
          if (!setProps) {
            return;
          }
          const isGroup = !!event?.node?.group;
          const rollupData = isGroup ? resolveRollup(event?.node) || null : null;
          const column =
            (event?.column && typeof event.column.getColId === 'function' && event.column.getColId()) ||
            event?.colDef?.field ||
            null;
          const payload = {
            colId: column,
            value: event?.value,
            data: isGroup ? rollupData : event?.data || null,
            groupData: rollupData || event?.node?.groupData || null,
            nodeIsGroup: isGroup,
            rowIndex: typeof event?.rowIndex === 'number' ? event.rowIndex : null,
              timestamp: Date.now(),
          };
          try {
            setProps({ cellClicked: payload });
          } catch (err) {
            console.error('Failed to dispatch summary click event', err);
          }
        },
      };
    },
    'analytics-grid': function analyticsGrid(context) {
      const themes = window.AgGridJsThemes || {};
      const quartzTheme = themes.themeQuartz;

      const monthly = context?.configArgs?.rowData || [];

      const destroyExistingChart = () => {
        const container = document.getElementById('analytics-chart');
        if (container && container.__agGridChartRef) {
          try {
            container.__agGridChartRef.destroyChart();
          } catch (err) {
            console.error('Failed to destroy linked chart', err);
          }
          container.__agGridChartRef = null;
          container.innerHTML = '';
        }
      };

      return {
        rowData: monthly,
        columnDefs: [
          { field: 'month', chartDataType: 'category', sortable: false },
          { field: 'desktops', chartDataType: 'series' },
          { field: 'laptops', chartDataType: 'series' },
          { field: 'tablets', chartDataType: 'series' },
        ],
        defaultColDef: {
          flex: 1,
          sortable: true,
          resizable: true,
        },
        enableCharts: true,
        cellSelection: true,
        chartThemes: ['ag-material-dark', 'ag-pastel', 'ag-sheets'],
        theme: quartzTheme
          ? quartzTheme.withParams({
              accentColor: '#9333ea',
              headerBackgroundColor: '#111827',
              headerTextColor: '#e5e7eb',
              borderRadius: 12,
            })
          : undefined,
        statusBar: {
          statusPanels: [
            { statusPanel: 'agAggregationComponent', align: 'right' },
          ],
        },
        onFirstDataRendered: function onFirstDataRendered(params) {
          if (!params?.api?.createRangeChart || !monthly.length) {
            return;
          }
          window.setTimeout(() => {
            const container = document.getElementById('analytics-chart');
            if (!container) {
              return;
            }
            destroyExistingChart();
            const chartRef = params.api.createRangeChart({
              chartType: 'stackedColumn',
              chartContainer: container,
              cellRange: {
                rowStartIndex: 0,
                rowEndIndex: monthly.length - 1,
                columns: ['month', 'desktops', 'laptops', 'tablets'],
              },
            });
            container.__agGridChartRef = chartRef;
          }, 0);
        },
        onGridPreDestroyed: destroyExistingChart,
      };
    },
    'ssrm-grid': function ssrmGrid(context) {
      const gridId = context?.id || 'ssrm-grid';
      const ssrmArgs = context?.configArgs?.ssrm || {};
      const baseEndpoint = String(ssrmArgs.endpoint || '_aggrid/ssrm').replace(/\/$/, '');
      const themes = window.AgGridJsThemes || {};
      const alpineTheme = themes.themeAlpine;

      const createDatasource = () => ({
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
        }
      });

      return {
        columnDefs: [
          { field: 'region', rowGroup: true },
          { field: 'units', type: 'numericColumn', aggFunc: 'sum', maxWidth: 140 },
          {
            field: 'revenue',
            type: 'numericColumn',
            aggFunc: 'sum',
            minWidth: 150,
            valueFormatter: (params) =>
              Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(params.value || 0)
          },
          { field: 'product', minWidth: 150 },
          { field: 'category', minWidth: 140 },
          { field: 'quarter', maxWidth: 120 },
          { field: 'order_id', headerName: 'Order ID', maxWidth: 130 },
        ],
        defaultColDef: {
          flex: 1,
          sortable: true,
          filter: false,
          resizable: true,
          enableRowGroup: true,
          enablePivot: true,
          enableValue: true,
          minWidth: 110,
          menuTabs: ['generalMenuTab', 'columnsMenuTab'],
        },
        autoGroupColumnDef: {
          minWidth: 220,
        },
        theme: alpineTheme
          ? alpineTheme.withParams({
              accentColor: '#2563eb',
              borderRadius: 10,
            })
          : undefined,
        rowModelType: 'serverSide',
        cacheBlockSize: 100,
        maxBlocksInCache: 10,
        suppressAggFuncInHeader: true,
        animateRows: true,
        rowGroupPanelShow: 'always',
        sideBar: ['columns'],
        serverSideDatasource: createDatasource(),
        onFirstDataRendered: (params) => {
          if (params?.api && params.columnApi?.autoSizeAllColumns) {
            params.columnApi.autoSizeAllColumns();
          }
        },
      };
    },
    'row-drag-grid': function rowDragGrid(context) {
      const themes = window.AgGridJsThemes || {};
      const alpineTheme = themes.themeAlpine;
      const bucket = context?.configArgs?.bucket || 'left';
      const initialRows = (context?.configArgs?.rowData || []).map((row) => ({ ...row }));
      const setProps = context?.setProps;

      const state = (window.__rowDragBinState = window.__rowDragBinState || {
        grids: {},
        apiToBucket: new WeakMap(),
        linked: false,
        seq: 100,
        binAttached: new WeakSet(),
        factoriesBound: false,
      });

      const maxId = initialRows.reduce((max, row) => Math.max(max, Number(row.id) || 0), 0);
      state.seq = Math.max(state.seq, maxId + 1);

      const emit = (payload) => {
        if (typeof setProps !== 'function') {
          return;
        }
        try {
          setProps({ rowDragEvent: { ...payload, timestamp: Date.now() } });
        } catch (err) {
          console.error('Failed to emit row drag event', err);
        }
      };

      const createDataItem = (color) => ({
        id: state.seq++,
        color: color || 'Red',
        value1: Math.floor(Math.random() * 100),
        value2: Math.floor(Math.random() * 100),
      });

      const addRecordToGrid = (side, data, source) => {
        if (!data || data.id == null) {
          return;
        }
        const api = state.grids[side];
        if (!api) {
          return;
        }
        const idStr = String(data.id);
        if (api.getRowNode(idStr)) {
          return;
        }
        api.applyTransaction({ add: [data] });
        emit({ type: source || 'factory-add', target: side, ids: [data.id] });
      };

      const handleFactoryButton = (btn) => {
        const color = btn?.dataset?.color;
        const side = (btn?.dataset?.side || 'left').toLowerCase();
        const data = createDataItem(color);
        addRecordToGrid(side, data, 'factory-add');
      };

      const ensureFactories = () => {
        if (state.factoriesBound) {
          return;
        }
        const buttons = document.querySelectorAll('.row-drag-factory');
        buttons.forEach((btn) => {
          btn.addEventListener('click', () => handleFactoryButton(btn));
        });
        if (buttons.length) {
          state.factoriesBound = true;
        }
      };

      const handleTransfer = (targetBucket, params) => {
        const targetApi = state.grids[targetBucket];
        const sourceBucket = targetBucket === 'left' ? 'right' : 'left';
        const sourceApi = state.grids[sourceBucket];
        if (!targetApi || !sourceApi) {
          return;
        }

        const nodes = Array.isArray(params?.nodes) && params.nodes.length ? params.nodes : params?.node ? [params.node] : [];
        if (!nodes.length) {
          return;
        }

        const rows = nodes.map((node) => node?.data).filter(Boolean);
        const toAdd = rows.filter((row) => !targetApi.getRowNode(String(row.id)));

        if (!toAdd.length) {
          return;
        }

        targetApi.applyTransaction({ add: toAdd });
        sourceApi.applyTransaction({ remove: toAdd });

        emit({ type: 'grid-drop', source: sourceBucket, target: targetBucket, ids: toAdd.map((r) => r.id) });
      };

      const handleBinDrop = (params) => {
        const nodes = Array.isArray(params?.nodes) && params.nodes.length ? params.nodes : params?.node ? [params.node] : [];
        const rows = nodes.map((node) => node?.data).filter(Boolean);
        if (!rows.length) {
          return;
        }

        ['left', 'right'].forEach((side) => {
          const api = state.grids[side];
          if (!api) {
            return;
          }
          const existing = rows.filter((row) => api.getRowNode(String(row.id)));
          if (existing.length) {
            api.applyTransaction({ remove: existing });
          }
        });

        emit({ type: 'bin-drop', target: 'bin', ids: rows.map((r) => r.id) });
      };

      const ensureBinDropZone = (api) => {
        if (!api || state.binAttached.has(api)) {
          return;
        }
        const bin = document.getElementById('row-drag-bin');
        if (!bin) {
          return;
        }
        const icon = bin.querySelector('.bin-icon');
        const setActive = (active) => {
          bin.classList.toggle('bin-active', !!active);
          if (icon) {
            icon.classList.toggle('bin-icon-active', !!active);
          }
        };

        const dropZone = {
          getContainer: () => bin,
          onDragEnter: () => setActive(true),
          onDragLeave: () => setActive(false),
          onDragStop: (params) => {
            handleBinDrop(params);
            setActive(false);
          },
          onDragCancel: () => setActive(false),
        };

        api.addRowDropZone(dropZone);
        state.binAttached.add(api);
      };

      const linkGrids = () => {
        if (state.linked || !state.grids.left || !state.grids.right) {
          return;
        }

        const leftDropZone = state.grids.left.getRowDropZoneParams({
          onDragStop: (params) => handleTransfer('left', params),
        });
        const rightDropZone = state.grids.right.getRowDropZoneParams({
          onDragStop: (params) => handleTransfer('right', params),
        });

        state.grids.left.addRowDropZone(rightDropZone);
        state.grids.right.addRowDropZone(leftDropZone);

        state.linked = true;
      };

      const onGridReady = (params) => {
        state.grids[bucket] = params.api;
        state.apiToBucket.set(params.api, bucket);

        if (params?.api?.setGridOption) {
          params.api.setGridOption('rowData', initialRows);
        }

        linkGrids();
        ensureBinDropZone(params.api);
        ensureFactories();

        if (params?.api?.sizeColumnsToFit) {
          params.api.sizeColumnsToFit();
        }
      };

      return {
        columnDefs: [
          { field: 'id', rowDrag: true, maxWidth: 120 },
          { field: 'color', minWidth: 120 },
          { field: 'value1' },
          { field: 'value2' },
        ],
        defaultColDef: {
          flex: 1,
          minWidth: 110,
          sortable: true,
          filter: true,
          resizable: true,
        },
        rowClassRules: {
          'red-row': "data.color === 'Red'",
          'green-row': "data.color === 'Green'",
          'blue-row': "data.color === 'Blue'",
        },
        rowData: initialRows,
        getRowId: (params) => String(params?.data?.id || ''),
        rowSelection: { mode: 'multiRow', rowMultiSelectWithClick: true },
        rowDragManaged: true,
        rowDragMultiRow: true,
        suppressMoveWhenRowDragging: true,
        animateRows: true,
        theme: alpineTheme
          ? alpineTheme.withParams({
              accentColor: bucket === 'right' ? '#2563eb' : '#22c55e',
              borderRadius: 10,
            })
          : undefined,
        onGridReady,
      };
    },
  };

  window.AGGRID_CONFIGS = {
    ...(window.AGGRID_CONFIGS || {}),
    ...configs,
  };
}());
