/* eslint-disable no-console */
(function initialiseAgChartsConfigs() {
  if (typeof window === 'undefined') {
    return;
  }

  const dataset = [
    { quarter: 'Q1', north: 18_200, emea: 12_450, apac: 9_870 },
    { quarter: 'Q2', north: 22_100, emea: 14_360, apac: 11_230 },
    { quarter: 'Q3', north: 25_840, emea: 16_540, apac: 12_980 },
    { quarter: 'Q4', north: 28_930, emea: 18_120, apac: 13_770 },
  ];

  const configs = {
    'revenue-chart': function revenueChart(context) {
      const accent = context?.configArgs?.accentColor || '#2563eb';
      return {
        title: {
          text: 'Quarterly Revenue',
          fontSize: 18,
        },
        subtitle: {
          text: 'FY24, in thousands USD',
        },
        data: dataset,
        theme: {
          baseTheme: 'ag-default',
          palette: {
            fills: [accent, '#f97316', '#facc15'],
            strokes: ['#1e3a8a', '#9a3412', '#854d0e'],
          },
        },
        series: [
          { type: 'bar', direction: 'vertical', xKey: 'quarter', yKey: 'north', yName: 'North America' },
          { type: 'bar', direction: 'vertical', xKey: 'quarter', yKey: 'emea', yName: 'EMEA' },
          { type: 'bar', direction: 'vertical', xKey: 'quarter', yKey: 'apac', yName: 'APAC' },
        ],
        axes: [
          {
            type: 'category',
            position: 'bottom',
            gridLine: { enabled: false },
          },
          {
            type: 'number',
            position: 'left',
            label: {
              formatter: (params) => `$${Math.round(params.value / 100) / 10}k`,
            },
          },
        ],
        legend: {
          position: 'bottom',
        },
      };
    },
  };

  window.AGCHART_CONFIGS = {
    ...(window.AGCHART_CONFIGS || {}),
    ...configs,
  };
}());
