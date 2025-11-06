import React, { useEffect, useMemo, useRef, useState } from 'react';
import PropTypes from 'prop-types';
import { AgCharts, setupCommunityModules } from 'ag-charts-community';

let setupEnterpriseModules;
try {
  // eslint-disable-next-line global-require, import/no-extraneous-dependencies
  ({ setupEnterpriseModules } = require('ag-charts-enterprise'));
} catch (err) {
  setupEnterpriseModules = null;
}

let chartsRegistered = false;
const ensureChartsModules = () => {
  if (chartsRegistered) {
    return;
  }

  try {
    setupCommunityModules?.();
    setupEnterpriseModules?.();
    chartsRegistered = true;
  } catch (err) {
    // eslint-disable-next-line no-console
    console.error('AgChartsJS module registration failed', err);
  }
};

const getChartConfig = (key, context) => {
  if (typeof window === 'undefined') {
    return null;
  }
  const map = window.AGCHART_CONFIGS || {};
  const candidate = map[key];
  if (!candidate) {
    return null;
  }
  if (typeof candidate === 'function') {
    try {
      return candidate(context);
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error('AgChartsJS config resolver failed', err);
      return null;
    }
  }
  return candidate;
};

/**
 * AgChartsJS renders AG Charts using options stored in window.AGCHART_CONFIGS.
 * Supply inline `options` or reference an `optionsKey`; the component resolves
 * dynamic configs and keeps the chart instance updated for Dash layouts.
 */
const AgChartsJS = (props) => {
  ensureChartsModules();

  const {
    id,
    className,
    style,
    options,
    optionsKey,
    configArgs = null,
    setProps, // eslint-disable-line no-unused-vars
  } = props;

  const containerRef = useRef(null);
  const chartRef = useRef(null);

  const configArgsKey = useMemo(() => {
    try {
      return JSON.stringify(configArgs ?? null);
    } catch (err) {
      console.error('AgChartsJS failed to serialise configArgs', err);
      return '__error__';
    }
  }, [configArgs]);

  const dashPropsRef = useRef(props);
  useEffect(() => {
    dashPropsRef.current = props;
  });

  const [resolvedOptions, setResolvedOptions] = useState(() => {
    if (options && typeof options === 'object') {
      return options;
    }
    if (!optionsKey) {
      return null;
    }
    return getChartConfig(optionsKey, {
      optionsKey,
      configArgs,
      dashProps: props,
    });
  });

  useEffect(() => {
    if (options && typeof options === 'object') {
      setResolvedOptions(options);
      return;
    }

    if (!optionsKey) {
      setResolvedOptions(null);
      return;
    }

    let cancelled = false;
    const resolveAndSet = () => {
      const config = getChartConfig(optionsKey, {
        optionsKey,
        configArgs,
        dashProps: dashPropsRef.current,
      });
      if (!cancelled) {
        setResolvedOptions(config || null);
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
  }, [options, optionsKey, configArgsKey]);

  useEffect(() => {
    if (!resolvedOptions || !containerRef.current) {
      if (chartRef.current) {
        try {
          chartRef.current.destroy();
        } catch (err) {
          console.error('AgChartsJS destroy failed', err);
        }
        chartRef.current = null;
      }
      return;
    }

    const chartOptions = {
      ...resolvedOptions,
      container: containerRef.current,
    };

    if (chartRef.current) {
      try {
        const { container, ...rest } = chartOptions;
        chartRef.current.update(rest);
      } catch (err) {
        console.error('AgChartsJS update failed, recreating chart', err);
        try {
          chartRef.current.destroy();
        } catch (destroyErr) {
          console.error('AgChartsJS destroy during recreate failed', destroyErr);
        }
        chartRef.current = AgCharts.create(chartOptions);
      }
    } else {
      chartRef.current = AgCharts.create(chartOptions);
    }
  }, [resolvedOptions]);

  useEffect(() => () => {
    if (chartRef.current) {
      try {
        chartRef.current.destroy();
      } catch (err) {
        console.error('AgChartsJS destroy on unmount failed', err);
      }
      chartRef.current = null;
    }
  }, []);

  if (!resolvedOptions) {
    return (
      <div
        id={id}
        className={className}
        style={{ ...(style || {}), padding: 12, border: '1px dashed #ccc' }}
      >
        Missing AG Charts config for key: <code>{String(optionsKey)}</code>
      </div>
    );
  }

  return (
    <div
      id={id}
      className={className}
      style={style}
      ref={containerRef}
    />
  );
};

AgChartsJS.propTypes = {
  /**
   * The ID used to identify this component in Dash callbacks.
   */
  id: PropTypes.string,
  /**
   * Optional CSS class applied to the chart container.
   */
  className: PropTypes.string,
  /**
   * Inline styles for sizing/positioning the chart container.
   */
  style: PropTypes.object,
  /**
   * Chart options object to render. If provided, overrides optionsKey lookup.
   */
  options: PropTypes.object,
  /**
   * Key used to look up chart options from window.AGCHART_CONFIGS.
   */
  optionsKey: PropTypes.string,
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
   * Dash-assigned callback for reporting property changes (unused for charts).
   */
  setProps: PropTypes.func,
};

export default AgChartsJS;
