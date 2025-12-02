import React, { useEffect, useMemo, useRef, useState } from 'react';
import PropTypes from 'prop-types';
import { AgGridReact } from 'ag-grid-react';
import {
  ModuleRegistry,
  AllCommunityModule,
  TextFilterModule,
  ColumnAutoSizeModule,
  ValidationModule,
  themeQuartz,
  themeAlpine,
  BeanStub,
} from 'ag-grid-community';
import * as EnterpriseModules from 'ag-grid-enterprise';
import componentMetadata from '../../../dash_aggrid_js/metadata.json';

const isDevEnv = typeof process !== 'undefined'
  ? process?.env?.NODE_ENV !== 'production'
  : false;

const VALID_MENU_TABS = new Set(['generalMenuTab', 'filterMenuTab', 'columnsMenuTab']);
const warnedMenuConfigs = new Set();
const warnOnceRegistry = new Set();

const warnOnce = (key, logger, ...args) => {
  if (warnOnceRegistry.has(key)) {
    return;
  }
  warnOnceRegistry.add(key);
  try {
    logger(...args);
  } catch (err) {
    // eslint-disable-next-line no-console
    console.warn('[AgGridJS] failed to emit warning', err);
  }
};

const describeColumn = (colDef, index) => (
  colDef?.field
    || colDef?.colId
    || colDef?.headerName
    || `column[${index}]`
);

const validateMenuTabs = (label, tabs) => {
  if (!Array.isArray(tabs) || !tabs.length) {
    return;
  }
  const invalid = tabs.filter((tab) => typeof tab !== 'string' || !VALID_MENU_TABS.has(tab));
  if (!invalid.length) {
    return;
  }
  warnOnce(
    `aggridjs-invalid-menu-tabs-${label}`,
    // eslint-disable-next-line no-console
    console.error,
    `AgGridJS config "${label}" defines unsupported menuTabs: ${invalid.join(', ')}. `
      + 'Valid values are generalMenuTab, filterMenuTab, columnsMenuTab.'
  );
};

const validateGridMenuConfig = (configKey, gridOptions) => {
  if (!isDevEnv || !gridOptions || warnedMenuConfigs.has(configKey)) {
    return;
  }

  const columnDefs = gridOptions.columnDefs;
  const runValidation = () => {
    if (Array.isArray(gridOptions?.defaultColDef)) {
      gridOptions.defaultColDef.forEach((def, index) => {
        validateMenuTabs(`${configKey}:defaultColDef[${index}]`, def?.menuTabs);
      });
    } else if (gridOptions?.defaultColDef) {
      validateMenuTabs(`${configKey}:defaultColDef`, gridOptions.defaultColDef.menuTabs);
    }

    const walk = (defs, lineage = []) => {
      if (!Array.isArray(defs)) {
        return;
      }
      defs.forEach((def, index) => {
        if (!def || typeof def !== 'object') {
          return;
        }
        const labelParts = [...lineage, describeColumn(def, index)];
        const label = `${configKey}:${labelParts.join('>')}`;
        validateMenuTabs(label, def.menuTabs);
        if (Array.isArray(def.children) && def.children.length) {
          walk(def.children, labelParts);
        }
      });
    };
    walk(columnDefs);
  };

  runValidation();
  warnedMenuConfigs.add(configKey);
};

class ColumnMenuGuard extends BeanStub {
  constructor(...args) {
    super(...args);
    this.beanName = 'agGridJsColumnMenuGuard';
    this.hasLoggedInvalidGroup = false;
  }

  postConstruct() {
    const factory = this?.beans?.colMenuFactory ?? null;
    if (!factory || factory.__agGridJsGuardApplied) {
      if (!factory && isDevEnv) {
        warnOnce(
          'aggridjs-colmenu-guard-missing-factory',
          // eslint-disable-next-line no-console
          console.warn,
          'AgGridJS: ColumnMenuGuard could not locate colMenuFactory; header menus may break if menuTabs are used.'
        );
      }
      return;
    }

    const original = typeof factory.getMenuItems === 'function'
      ? factory.getMenuItems.bind(factory)
      : null;

    if (!original) {
      return;
    }

    factory.getMenuItems = (column = null, columnGroup = null) => {
      if (columnGroup && typeof columnGroup.getColGroupDef !== 'function') {
        if (!this.hasLoggedInvalidGroup && isDevEnv) {
          this.hasLoggedInvalidGroup = true;
          warnOnce(
            'aggridjs-invalid-column-group',
            // eslint-disable-next-line no-console
            console.error,
            '[AgGridJS] Column menu received a columnGroup without getColGroupDef(). '
              + 'This usually means the column definition is a plain object or enterprise modules failed to register.',
            columnGroup
          );
        }
        columnGroup = null;
      }
      return original(column, columnGroup);
    };

    factory.__agGridJsGuardApplied = true;
  }
}

const registeredModuleNames = new Set();
let menuGuardRegistered = false;

let cachedAgVersion = typeof AllCommunityModule?.version === 'string'
  ? AllCommunityModule.version
  : null;
const getAgGridVersion = () => {
  if (cachedAgVersion) {
    return cachedAgVersion;
  }

  try {
    // eslint-disable-next-line global-require, import/no-extraneous-dependencies
    const enterprise = require('ag-grid-enterprise');
    cachedAgVersion = enterprise?.AllEnterpriseModule?.version
      || enterprise?.ColumnMenuModule?.version
      || null;
  } catch (err) {
    cachedAgVersion = null;
  }

  return cachedAgVersion;
};

const registerColumnMenuGuard = (enterprise) => {
  if (menuGuardRegistered) {
    return;
  }

  const moduleDef = {
    moduleName: 'AgGridJsColumnMenuGuard',
    version: getAgGridVersion() || '0.0.0-aggridjs',
    beans: [ColumnMenuGuard],
  };

  if (enterprise?.ColumnMenuModule) {
    moduleDef.dependsOn = [enterprise.ColumnMenuModule];
  }

  try {
    ModuleRegistry.registerModules([moduleDef]);
    menuGuardRegistered = true;
  } catch (err) {
    warnOnce(
      'aggridjs-column-menu-guard-register-error',
      // eslint-disable-next-line no-console
      console.warn,
      'AgGridJS failed to register column menu guard',
      err
    );
  }
};

const registerModulesSafely = (modules) => {
  const toRegister = [];
  (modules || []).forEach((module) => {
    const name = module?.moduleName || module?.name || null;
    if (name && registeredModuleNames.has(name)) {
      return;
    }
    if (name) {
      registeredModuleNames.add(name);
    }
    if (module) {
      toRegister.push(module);
    }
  });

  if (!toRegister.length) {
    return;
  }

  try {
    ModuleRegistry.registerModules(toRegister);
  } catch (err) {
    // eslint-disable-next-line no-console
    console.error('AgGridJS failed to register modules', err);
  }
};

const ensureModulesRegistered = () => {
  registerModulesSafely([AllCommunityModule, TextFilterModule, ColumnAutoSizeModule, ValidationModule]);

  try {
    const enterprise = EnterpriseModules;

    const missingModules = [];
    const flagModule = (key) => {
      if (!enterprise[key]) {
        missingModules.push(key);
      }
    };
    flagModule('AllEnterpriseModule');
    flagModule('RowGroupingModule');
    flagModule('PivotModule');

    const additional = [];
    const addIfPresent = (module) => {
      if (module) {
        additional.push(module);
      }
    };

    addIfPresent(enterprise.MenuModule);
    addIfPresent(enterprise.ColumnMenuModule);
    addIfPresent(enterprise.ContextMenuModule);
    addIfPresent(enterprise.SideBarModule);
    addIfPresent(enterprise.StatusBarModule);
    addIfPresent(enterprise.ColumnsToolPanelModule);
    addIfPresent(enterprise.FiltersToolPanelModule);
    addIfPresent(enterprise.NewFiltersToolPanelModule);
    addIfPresent(enterprise.RowGroupingModule);
    addIfPresent(enterprise.PivotModule);
    addIfPresent(enterprise.RowGroupingPanelModule);
    addIfPresent(enterprise.GroupFilterModule);
    addIfPresent(enterprise.RowSelectionModule);
    addIfPresent(enterprise.ServerSideRowModelModule);
    addIfPresent(enterprise.ServerSideRowModelApiModule);

    let chartsModule = null;
    try {
      // eslint-disable-next-line global-require, import/no-extraneous-dependencies
      const chartsEnterprise = require('ag-charts-enterprise');
      chartsModule = chartsEnterprise?.AgChartsEnterpriseModule || chartsEnterprise?.AgChartsCommunityModule || null;
    } catch (err) {
      chartsModule = null;
    }

    if (!chartsModule) {
      try {
        // eslint-disable-next-line global-require, import/no-extraneous-dependencies
        const chartsCommunity = require('ag-charts-community');
        chartsModule = chartsCommunity?.AgChartsCommunityModule || null;
      } catch (err) {
        chartsModule = null;
      }
    }

    if (enterprise.IntegratedChartsModule && chartsModule) {
      additional.push(enterprise.IntegratedChartsModule.with(chartsModule));
    } else if (enterprise.IntegratedChartsModule && !chartsModule) {
      // eslint-disable-next-line no-console
      console.warn('AgGridJS integrated charts requested but no ag-charts module is installed');
    }

    registerModulesSafely(additional);

    if (isDevEnv) {
      const names = additional.map((module) => module?.moduleName).filter(Boolean);
      if (names.length) {
        console.info('[AgGridJS] Registered enterprise modules:', names);
      }
      if (missingModules.length) {
        console.warn('[AgGridJS] Missing enterprise modules from bundle:', missingModules);
      }
    }

    registerColumnMenuGuard(enterprise);
  } catch (err) {
    // eslint-disable-next-line no-console
    console.warn('AgGridJS enterprise modules unavailable', err);
    registerColumnMenuGuard(null);
  }

};

const createDeferred = () => {
  let resolve;
  const promise = new Promise((res) => {
    resolve = res;
  });
  return { promise, resolve };
};

const ensureApiRegistry = () => {
  if (typeof window === 'undefined') {
    return null;
  }
  if (!window.AgGridJsRegistry) {
    window.AgGridJsRegistry = {};
  }
  const registry = window.AgGridJsRegistry;
  registry._records = registry._records || {};
  registry.getApiAsync = (gridId) => {
    if (!gridId) {
      return Promise.resolve(null);
    }
    if (!registry._records[gridId]) {
      registry._records[gridId] = createDeferred();
    }
    return registry._records[gridId].promise;
  };
  return registry;
};

ensureModulesRegistered();
ensureApiRegistry();

if (typeof window !== 'undefined') {
  window.AgGridJsThemes = window.AgGridJsThemes || {};
  if (!window.AgGridJsThemes.themeQuartz) {
    window.AgGridJsThemes.themeQuartz = themeQuartz;
  }
  if (!window.AgGridJsThemes.themeAlpine) {
    window.AgGridJsThemes.themeAlpine = themeAlpine;
  }
}

const setApiInstance = (gridId, api) => {
  const registry = ensureApiRegistry();
  if (!registry || !gridId) {
    return;
  }
  const resolved = Promise.resolve(api);
  registry._records[gridId] = {
    promise: resolved,
    resolve: () => {},
  };
};

// Keep registerProps normaliser for future event opt-ins; Dash-side validation already handles
// available_properties, but retaining this avoids accidental agent additions elsewhere.
const normaliseRegisterProps = (raw) => {
  if (!raw) {
    return new Set();
  }
  if (Array.isArray(raw)) {
    return new Set(
      raw
        .map((v) => (typeof v === 'string' ? v.trim() : ''))
        .filter((v) => !!v)
    );
  }
  if (typeof raw === 'string') {
    const trimmed = raw.trim();
    return trimmed ? new Set([trimmed]) : new Set();
  }
  return new Set();
};

const ensureMetadataObject = () => {
  if (typeof window === 'undefined') return null;
  let meta =
    window.__dash_component_metadata__
    || window.__dash_component_metadata
    || window.dash_component_metadata
    || window._dashprivate_componentMetadata;

  if (!meta && componentMetadata) {
    meta = JSON.parse(JSON.stringify(componentMetadata));
    window.__dash_component_metadata__ = meta;
  }
  return meta;
};

const extendDashMetadata = (extraPropsSet) => {
  if (typeof window === 'undefined') return;
  const meta = ensureMetadataObject();
  if (!meta) return;

  const extendPropsObject = (comp) => {
    if (!comp || typeof comp !== 'object' || !comp.props) return;
    extraPropsSet.forEach((prop) => {
      if (!prop || comp.props[prop]) {
        return;
      }
      comp.props[prop] = {
        type: { name: 'any' },
        required: false,
        description: 'Dynamic prop registered via registerProps',
      };
    });
  };

  if (meta.AgGridJS) {
    extendPropsObject(meta.AgGridJS);
  }
  Object.values(meta).forEach((entry) => {
    if (entry && entry.displayName === 'AgGridJS') {
      extendPropsObject(entry);
    }
  });

  let registryMeta =
    window?.dash_component_api?.componentRegistry?.metadata
    || window?.dash_component_api?._componentMetadata
    || window?.dash_renderer?.componentMetadata;

  if (!registryMeta && window?.dash_component_api?.componentRegistry) {
    window.dash_component_api.componentRegistry.metadata = JSON.parse(JSON.stringify(meta));
    registryMeta = window.dash_component_api.componentRegistry.metadata;
  }
  if (registryMeta) {
    extendPropsObject(registryMeta.AgGridJS);
    Object.values(registryMeta).forEach((entry) => {
      if (entry && entry.displayName === 'AgGridJS') {
        extendPropsObject(entry);
      }
    });
  }
};

const collectRegisterPropsFromLayout = () => {
  if (typeof window === 'undefined') return new Set();
  const layout = window._dash_layout || window.__dash_layout;
  if (!layout) return new Set();
  const propsSet = new Set();

  const walk = (node) => {
    if (!node) return;
    if (Array.isArray(node)) {
      node.forEach(walk);
      return;
    }
    if (node && typeof node === 'object') {
      const isAgGrid =
        node.type === 'AgGridJS' ||
        node.component === 'AgGridJS' ||
        (node.namespace === 'dash_aggrid_js' && node.type);
      if (isAgGrid && node.props && node.props.registerProps) {
        normaliseRegisterProps(node.props.registerProps).forEach((p) => propsSet.add(p));
      }
      if (node.props) {
        walk(node.props.children || node.props._dashprivate_children);
        Object.values(node.props).forEach((v) => {
          if (v && typeof v === 'object') {
            walk(v);
          }
        });
      }
      if (node.children) {
        walk(node.children);
      }
    }
  };

  walk(layout);
  return propsSet;
};

const ensureRegistryMetadata = () => {
  if (typeof window === 'undefined') return;
  const registry = window?.dash_component_api?.componentRegistry;
  if (!registry) return;
  if (!registry.metadata) {
    const meta = ensureMetadataObject();
    if (meta) {
      registry.metadata = JSON.parse(JSON.stringify(meta));
    }
  }
};

const bootstrapMetadata = () => {
  try {
    ensureMetadataObject();
    ensureRegistryMetadata();
    const layoutProps = collectRegisterPropsFromLayout();
    extendDashMetadata(layoutProps);
  } catch (err) {
    // eslint-disable-next-line no-console
    console.warn('AgGridJS metadata bootstrap failed', err);
  }
};

// Bootstrap immediately and schedule a short retry to catch late layout availability
bootstrapMetadata();
if (typeof window !== 'undefined') {
  let retries = 50;
  const retry = () => {
    retries -= 1;
    bootstrapMetadata();
    if (retries > 0) {
      window.setTimeout(retry, 100);
    }
  };
  window.setTimeout(retry, 100);
}

const withSsrmFilterValues = (options, gridId, configArgs) => {
  if (!gridId || !configArgs || !configArgs.ssrm || !options) {
    return options;
  }

  const ssrmArgs = configArgs.ssrm || {};
  const baseEndpointRaw = ssrmArgs.endpoint || ssrmArgs.base || '_aggrid/ssrm';
  const distinctEndpointRaw = ssrmArgs.distinctEndpoint || `${baseEndpointRaw}/distinct`;
  const baseEndpoint = String(baseEndpointRaw).replace(/\/$/, '');
  const distinctEndpoint = String(distinctEndpointRaw).replace(/\/$/, '');

  const patchColumns = (cols) => {
    if (!Array.isArray(cols)) {
      return cols;
    }
    return cols.map((colDef) => {
      if (!colDef || typeof colDef !== 'object') {
        return colDef;
      }

      const next = { ...colDef };
      if (Array.isArray(next.children) && next.children.length) {
        next.children = patchColumns(next.children);
      }

      if (next.filter === 'agSetColumnFilter') {
        const params = { ...(next.filterParams || {}) };
        const hasCustom =
          typeof params.values === 'function' ||
          (typeof params.values === 'object' && params.values !== null);

        if (!hasCustom) {
          params.values = async (paramsObj) => {
            const colId = paramsObj?.column?.getColId?.() || next.field;
            if (!colId) {
              paramsObj.success([]);
              return;
            }
            const url = `${distinctEndpoint}/${encodeURIComponent(gridId)}/${encodeURIComponent(colId)}`;
            try {
              const response = await fetch(url, { credentials: 'same-origin' });
              const ok =
                response.ok &&
                String(response.headers.get('content-type') || '').startsWith('application/json');
              const payload = ok ? await response.json() : [];
              paramsObj.success(Array.isArray(payload) ? payload : []);
            } catch (err) {
              console.error(`[AgGridJS:ssrm] distinct fetch failed`, err);
              paramsObj.success([]);
            }
          };
        }

        next.filterParams = params;
      }

      return next;
    });
  };

  const patched = { ...options };
  if (Array.isArray(options.columnDefs)) {
    patched.columnDefs = patchColumns(options.columnDefs);
  }
  if (Array.isArray(options.autoGroupColumnDef?.children)) {
    patched.autoGroupColumnDef = {
      ...options.autoGroupColumnDef,
      children: patchColumns(options.autoGroupColumnDef.children),
    };
  }

  if (patched.serverSideDatasource && typeof patched.serverSideDatasource.getRows === 'function') {
    const originalGetRows = patched.serverSideDatasource.getRows;
    patched.serverSideDatasource = {
      ...patched.serverSideDatasource,
      getRows: (params, ...rest) => {
        const requestPayload = params?.request || {};
        if (!requestPayload.gridId) {
          requestPayload.gridId = gridId;
        }
        const nextParams = { ...params, request: requestPayload };
        return originalGetRows(nextParams, ...rest);
      },
    };
  }

  return patched;
};

const getConfig = (key) => {
  if (typeof window === 'undefined') {
    return null;
  }
  const map = window.AGGRID_CONFIGS || {};
  return map[key] || null;
};

const resolveConfig = (context) => {
  const { configKey } = context;
  const candidate = getConfig(configKey);
  if (!candidate) {
    return null;
  }

  if (typeof candidate === 'function') {
    try {
      return candidate(context);
    } catch (err) {
      console.error('AgGridJS config resolver failed', err);
      return null;
    }
  }

  return candidate;
};

const withDash = (userHandler, dashFn) => {
  if (typeof userHandler !== 'function' && typeof dashFn !== 'function') {
    return undefined;
  }

  return (...args) => {
    try {
      if (typeof userHandler === 'function') {
        userHandler(...args);
      }
    } catch (err) {
      console.error('AgGridJS user handler threw', err);
    }

    try {
      if (typeof dashFn === 'function') {
        dashFn(...args);
      }
    } catch (err) {
      console.error('AgGridJS dash bridge failed', err);
    }
  };
};

const buildSortModel = (api) => {
  if (!api || typeof api.getColumnState !== 'function') {
    return [];
  }

  return (api.getColumnState() || [])
    .filter((col) => !!col.sort)
    .map((col) => ({
      colId: col.colId,
      sort: col.sort,
      sortIndex: col.sortIndex,
    }));
};

const normaliseFilterModel = (model) => {
  if (!model || typeof model !== 'object') {
    return {};
  }

  const copy = {};
  Object.entries(model).forEach(([key, node]) => {
    if (!node || typeof node !== 'object') {
      return;
    }
    if (node.filterType === 'set' && Array.isArray(node.values) && node.values.length === 0) {
      return;
    }
    copy[key] = node;
  });
  return copy;
};

/**
 * AgGridJS mounts AgGridReact using configurations stored on window.AGGRID_CONFIGS.
 * The component relays selection, filter, sort, and edit events back to Dash via setProps.
 */
const AgGridJS = (props) => {
  const {
    id,
    configKey,
    className,
    style,
    configArgs = null,
    rowData: rowDataProp = null,
    setProps,            // injected by Dash
    registerProps = null,
  } = props;

  const apiRef = useRef(null);
  const awaitingRowDataConfigRef = useRef(!(Array.isArray(rowDataProp) && rowDataProp.length > 0));

  const configArgsKey = useMemo(() => {
    try {
      return JSON.stringify(configArgs ?? null);
    } catch (err) {
      console.error('AgGridJS failed to serialise configArgs', err);
      return '__error__';
    }
  }, [configArgs]);

  const dashPropsRef = useRef(props);
  useEffect(() => {
    dashPropsRef.current = props;
  });

  const filterModelProp = props.filterModel;
  const filterModelKey = useMemo(() => {
    try {
      return JSON.stringify(filterModelProp ?? null);
    } catch (err) {
      console.error('AgGridJS failed to serialise filterModel prop', err);
      return '__error__';
    }
  }, [filterModelProp]);

  const [resolvedConfig, setResolvedConfig] = useState(() => resolveConfig({
    configKey,
    id,
    configArgs,
    dashProps: props,
    setProps,
  }));

  useEffect(() => {
    awaitingRowDataConfigRef.current = !(Array.isArray(rowDataProp) && rowDataProp.length > 0);
    let cancelled = false;
    const resolveAndSet = () => {
      const config = resolveConfig({
        configKey,
        id,
        configArgs,
        dashProps: dashPropsRef.current,
        setProps: dashPropsRef.current?.setProps,
      });
      if (!cancelled) {
        setResolvedConfig(config);
      }
      return !!config;
    };

    if (resolveAndSet()) {
      return () => {
        cancelled = true;
      };
    }

    let attempts = 0;
    const maxAttempts = 50;
    const interval = typeof window !== 'undefined'
      ? window.setInterval(() => {
        attempts += 1;
        if (resolveAndSet() || attempts >= maxAttempts) {
          window.clearInterval(interval);
        }
      }, 100)
      : null;

    return () => {
      cancelled = true;
      if (interval) {
        window.clearInterval(interval);
      }
    };
  }, [configKey, id, configArgsKey]);

  useEffect(() => {
    if (!awaitingRowDataConfigRef.current) {
      return;
    }
    if (!Array.isArray(rowDataProp) || rowDataProp.length === 0) {
      return;
    }
    const config = resolveConfig({
      configKey,
      id,
      configArgs,
      dashProps: dashPropsRef.current,
      setProps: dashPropsRef.current?.setProps,
    });
    if (config && typeof config === 'object') {
      awaitingRowDataConfigRef.current = false;
      setResolvedConfig(config);
    }
  }, [rowDataProp, configArgsKey, configKey, id]);

  if (!resolvedConfig || typeof resolvedConfig !== 'object') {
    return (
      <div id={id} className={className} style={{ ...(style || {}), padding: 8, border: '1px dashed #ccc' }}>
        Missing AG Grid config for key: <code>{String(configKey)}</code>
      </div>
    );
  }

  const {
    onGridReady: userReady,
    onSelectionChanged: userSelection,
    onFilterChanged: userFilter,
    onSortChanged: userSort,
    theme: userTheme,
    ...gridOptions
  } = resolvedConfig;

  const finalGridOptions = Array.isArray(rowDataProp)
    ? { ...gridOptions, rowData: rowDataProp }
    : { ...gridOptions };
  const derivedTheme = typeof userTheme === 'undefined' ? 'legacy' : userTheme;
  finalGridOptions.theme = derivedTheme;

  if (isDevEnv) {
    const validationKey = configKey || id || 'aggrid-js-grid';
    validateGridMenuConfig(validationKey, finalGridOptions);
  }

  const gridOptionsWithSsrm = withSsrmFilterValues(finalGridOptions, id, configArgs);

  const registerPropsSet = useMemo(() => normaliseRegisterProps(registerProps), [registerProps]);
  useEffect(() => {
    ensureRegistryMetadata();
    extendDashMetadata(registerPropsSet);
  }, [registerPropsSet]);

  const gridUsesSetFilter = () => {
    const defs = [
      ...(Array.isArray(gridOptionsWithSsrm?.columnDefs) ? gridOptionsWithSsrm.columnDefs : []),
      ...(Array.isArray(gridOptionsWithSsrm?.autoGroupColumnDef?.children)
        ? gridOptionsWithSsrm.autoGroupColumnDef.children
        : []),
    ];
    const filters = defs
      .map((def) => def?.filter || gridOptionsWithSsrm?.defaultColDef?.filter || null)
      .filter(Boolean);
    return filters.some((f) => f === true || String(f) === 'agSetColumnFilter');
  };

  const resolveConfigModules = () => {
    const requested = [];
    const raw = gridOptionsWithSsrm?.modules;
    if (Array.isArray(raw)) {
      raw.forEach((item) => {
        if (item && typeof item === 'object') {
          requested.push(item);
          return;
        }
        if (typeof item === 'string' && EnterpriseModules[item]) {
          requested.push(EnterpriseModules[item]);
        }
      });
    }
    if (gridUsesSetFilter() && EnterpriseModules.SetFilterModule) {
      requested.push(EnterpriseModules.SetFilterModule);
    }
    return requested;
  };

  const extraModules = useMemo(resolveConfigModules, [configArgsKey, configKey, id]);
  if (extraModules.length) {
    registerModulesSafely(extraModules);
  }

  const syncSelectedRows = () => {
    if (!setProps || !apiRef.current) {
      return;
    }
    setProps({ selectedRows: apiRef.current.getSelectedRows() || [] });
  };

  const syncFilterModel = () => {
    if (!setProps || !apiRef.current) {
      return;
    }
    setProps({ filterModel: apiRef.current.getFilterModel() || null });
  };

  const syncSortModel = () => {
    if (!setProps || !apiRef.current) {
      return;
    }
    setProps({ sortModel: buildSortModel(apiRef.current) });
  };

  const onGridReady = withDash(userReady, (params) => {
    apiRef.current = params?.api || null;
    if (apiRef.current && id) {
      setApiInstance(id, apiRef.current);
    }
    if (!setProps || !apiRef.current) {
      return;
    }
    syncSelectedRows();
    syncFilterModel();
    syncSortModel();
  });

  const onSelectionChanged = withDash(userSelection, syncSelectedRows);
  const onFilterChanged = withDash(userFilter, syncFilterModel);
  const onSortChanged = withDash(userSort, syncSortModel);

  useEffect(() => {
    if (!apiRef.current) {
      return;
    }
    if (typeof filterModelProp === 'undefined') {
      return;
    }
    let currentKey = null;
    try {
      currentKey = JSON.stringify(apiRef.current.getFilterModel() || null);
    } catch (err) {
      currentKey = null;
    }
    if (currentKey === filterModelKey) {
      return;
    }
    try {
      const nextModel = filterModelProp || null;
      apiRef.current.setFilterModel(nextModel);
      if (typeof apiRef.current.onFilterChanged === 'function') {
        apiRef.current.onFilterChanged();
      } else if (apiRef.current.dispatchEvent) {
        apiRef.current.dispatchEvent({ type: 'filterChanged' });
      }
    } catch (err) {
      console.error('AgGridJS failed to apply filterModel prop', err);
    }
  }, [filterModelKey, filterModelProp]);

  return (
    <div id={id} className={className} style={style}>
      <div style={{ width: '100%', height: '100%' }}>
        <AgGridReact
          {...gridOptionsWithSsrm}
          onGridReady={onGridReady}
          onSelectionChanged={onSelectionChanged}
          onFilterChanged={onFilterChanged}
          onSortChanged={onSortChanged}
        />
      </div>
    </div>
  );
};

// AI/agents: keep this propTypes list minimal. Do NOT add custom/event props here.
// Users opt into extra Dash props via registerProps + their asset handlers.
AgGridJS.propTypes = {
  /**
   * The ID used to identify this component in Dash callbacks.
   */
  id: PropTypes.string,
  /**
   * Key used to look up a configuration object in window.AGGRID_CONFIGS.
   */
  configKey: PropTypes.string.isRequired,
  /**
   * Optional CSS class to apply to the outer grid container.
   */
  className: PropTypes.string,
  /**
   * Inline style object applied to the grid container.
   */
  style: PropTypes.object,
  /**
   * Optional JSON-serialisable payload passed to config factory functions.
   */
  configArgs: PropTypes.oneOfType([
    PropTypes.object,
    PropTypes.array,
    PropTypes.string,
    PropTypes.number,
    PropTypes.bool,
    PropTypes.oneOf([null]),
  ]),
  /**
   * Optional list of extra Dash props this grid is allowed to emit (e.g. ["cellDoubleClicked"]).
   * These are appended to the component's available_properties on the Python side.
   */
  registerProps: PropTypes.oneOfType([
    PropTypes.arrayOf(PropTypes.string),
    PropTypes.string,
    PropTypes.oneOf([null]),
  ]),
  /**
   * Dash-assigned callback for reporting property changes to Dash.
   */
  setProps: PropTypes.func,
  /**
   * Array of row objects selected in the grid. Populated by the component.
   */
  selectedRows: PropTypes.arrayOf(PropTypes.object),
  /**
   * Current AG Grid filter model. Populated by the component.
   */
  filterModel: PropTypes.object,
  /**
   * Current AG Grid sort model (colId, sort, sortIndex). Populated by the component.
   */
  sortModel: PropTypes.arrayOf(PropTypes.shape({
    colId: PropTypes.string,
    sort: PropTypes.oneOf(['asc', 'desc']),
    sortIndex: PropTypes.number
  })),
  /**
   * Row data provided directly from Dash. Overrides rowData defined in the JS config.
   */
  rowData: PropTypes.arrayOf(PropTypes.object)
};

AgGridJS._dashprivate_isDummyProperty = false;
export default AgGridJS;
