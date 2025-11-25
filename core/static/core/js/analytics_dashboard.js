(function() {
  function parseJSON(id) {
    const el = document.getElementById(id);
    if (!el) return null;
    try { return JSON.parse(el.textContent); } catch (e) { console.warn('Failed parsing', id, e); return null; }
  }

  if (!window.Chart) return;

  // Parse datasets
  const metersDates = parseJSON('meters-dates-json');
  const metersValues = parseJSON('meters-values-json');
  const ropDates = parseJSON('rop-dates-json');
  const ropValues = parseJSON('rop-values-json');
  const recoveryDates = parseJSON('recovery-dates-json');
  const recoveryValues = parseJSON('recovery-values-json');
  const downtimeActivityLabels = parseJSON('downtime-activity-labels-json');
  const downtimeActivityValues = parseJSON('downtime-activity-values-json');
  const materialLabels = parseJSON('material-labels-json');
  const materialValues = parseJSON('material-values-json');
  const bitLabels = parseJSON('bit-labels-json');
  const bitMeters = parseJSON('bit-meters-json');
  const bitRecovery = parseJSON('bit-recovery-json');
  const rigMonthLabels = parseJSON('rig-month-labels-json');
  const rigMonthMeters = parseJSON('rig-month-meters-json');
  const rigMonthRecovery = parseJSON('rig-month-recovery-json');
  const rigMonthRop = parseJSON('rig-month-rop-json');

  // Helper to safely create chart
  function createChart(ctxId, config) {
    const el = document.getElementById(ctxId);
    if (!el) return;
    new Chart(el.getContext('2d'), config);
  }

  // Daily Meters Chart
  if (metersDates && metersValues) {
    createChart('metersChart', {
      type: 'line',
      data: { labels: metersDates, datasets: [{ label: 'Meters Drilled', data: metersValues, backgroundColor: 'rgba(13,110,253,0.2)', borderColor: 'rgba(13,110,253,1)', borderWidth: 2, fill: true, tension: 0.3 }] },
      options: { responsive: true, maintainAspectRatio: true, scales: { y: { beginAtZero: true, title: { display: true, text: 'Meters' } }, x: { title: { display: true, text: 'Date' } } } }
    });
  }

  // ROP Chart
  if (ropDates && ropValues) {
    createChart('ropChart', {
      type: 'line',
      data: { labels: ropDates, datasets: [{ label: 'Average ROP', data: ropValues, backgroundColor: 'rgba(13,202,240,0.2)', borderColor: 'rgba(13,202,240,1)', borderWidth: 2, fill: true, tension: 0.3 }] },
      options: { responsive: true, maintainAspectRatio: true, scales: { y: { beginAtZero: true, title: { display: true, text: 'ROP (m/hr)' } } } }
    });
  }

  // Recovery Chart with 90% threshold line
  if (recoveryDates && recoveryValues) {
    createChart('recoveryChart', {
      type: 'line',
      data: { labels: recoveryDates, datasets: [{ label: 'Average Recovery', data: recoveryValues, backgroundColor: 'rgba(255,193,7,0.2)', borderColor: 'rgba(255,193,7,1)', borderWidth: 2, fill: true, tension: 0.3 }] },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        scales: { y: { beginAtZero: true, max: 100, title: { display: true, text: 'Recovery (%)' } } },
        plugins: {
          annotation: {
            annotations: {
              threshold90: {
                type: 'line',
                yMin: 90,
                yMax: 90,
                borderColor: 'rgb(255,99,132)',
                borderWidth: 2,
                borderDash: [5, 5],
                label: {
                  content: '90% Threshold',
                  enabled: true,
                  position: 'start',
                  backgroundColor: 'rgba(255,99,132,0.8)',
                  color: 'white'
                }
              }
            }
          }
        }
      }
    });
  }

  // Downtime Pie Chart
  if (downtimeActivityLabels && downtimeActivityValues) {
    const colorMap = {
      'maintenance': '#ffc107',
      'safety': '#198754',
      'meeting': '#fd7e14',
      'other': '#6c757d'
    };
    const pieColors = downtimeActivityLabels.map(l => colorMap[l] || '#0d6efd');
    const el = document.getElementById('downtimePieChart');
    if (el) {
      new Chart(el.getContext('2d'), {
        type: 'doughnut',
        data: {
          labels: downtimeActivityLabels,
          datasets: [{
            label: 'Downtime (hrs)',
            data: downtimeActivityValues,
            backgroundColor: pieColors
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { position: 'bottom' } }
        }
      });
    }
  }

  // Materials Chart
  if (materialLabels && materialValues) {
    createChart('materialsChart', {
      type: 'bar',
      data: { labels: materialLabels, datasets: [{ label: 'Quantity Used', data: materialValues, backgroundColor: 'rgba(25,135,84,0.7)', borderColor: 'rgba(25,135,84,1)', borderWidth: 1 }] },
      options: { responsive: true, maintainAspectRatio: true, indexAxis: 'y', scales: { x: { beginAtZero: true } }, plugins: { legend: { display: false } } }
    });
  }

  // Bit Performance Chart (Dual Axis)
  if (bitLabels && bitMeters && bitRecovery) {
    createChart('bitChart', {
      type: 'bar',
      data: { labels: bitLabels, datasets: [ { label: 'Total Meters', data: bitMeters, backgroundColor: 'rgba(108,117,125,0.7)', borderColor: 'rgba(108,117,125,1)', borderWidth: 1, yAxisID: 'y' }, { label: 'Avg Recovery %', data: bitRecovery, type: 'line', borderColor: 'rgba(255,193,7,1)', backgroundColor: 'rgba(255,193,7,0.2)', borderWidth: 2, yAxisID: 'y1', tension: 0.3 } ] },
      options: { responsive: true, maintainAspectRatio: true, scales: { y: { type: 'linear', display: true, position: 'left', beginAtZero: true, title: { display: true, text: 'Meters' } }, y1: { type: 'linear', display: true, position: 'right', beginAtZero: true, max: 100, title: { display: true, text: 'Recovery (%)' }, grid: { drawOnChartArea: false } } } }
    });
  }

  // Monthly Rig Performance Chart (meters + recovery overlay)
  if (rigMonthLabels && rigMonthMeters) {
    const el = document.getElementById('rigMonthChart');
    if (el) {
      new Chart(el.getContext('2d'), {
        type: 'bar',
        data: {
          labels: rigMonthLabels,
          datasets: [
            {
              label: 'Meters (Month)',
              data: rigMonthMeters,
              backgroundColor: rigMonthMeters.map(v => 'rgba(13,110,253,0.7)'),
              borderColor: 'rgba(13,110,253,1)',
              borderWidth: 1,
              yAxisID: 'y'
            },
            rigMonthRecovery ? {
              label: 'Avg Recovery %',
              data: rigMonthRecovery,
              type: 'line',
              borderColor: 'rgba(25,135,84,1)',
              backgroundColor: 'rgba(25,135,84,0.2)',
              tension: 0.3,
              yAxisID: 'y1'
            } : null,
            rigMonthRop ? {
              label: 'Avg ROP (m/hr)',
              data: rigMonthRop,
              type: 'line',
              borderColor: 'rgba(255,193,7,1)',
              backgroundColor: 'rgba(255,193,7,0.2)',
              tension: 0.3,
              yAxisID: 'y2'
            } : null
          ].filter(Boolean)
        },
        options: {
          responsive: true,
          maintainAspectRatio: true,
          scales: {
            y: { beginAtZero: true, title: { display: true, text: 'Meters' } },
            y1: { position: 'right', beginAtZero: true, max: 100, grid: { drawOnChartArea: false }, title: { display: true, text: 'Recovery (%)' } },
            y2: { position: 'right', beginAtZero: true, grid: { drawOnChartArea: false }, title: { display: true, text: 'Avg ROP (m/hr)' } }
          },
          plugins: { legend: { position: 'bottom' } }
        }
      });
    }
  }
})();