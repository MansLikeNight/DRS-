(function() {
  function parseJSON(id) {
    const el = document.getElementById(id);
    if (!el) return null;
    try { return JSON.parse(el.textContent); } catch(e) { console.warn('Failed parsing', id, e); return null; }
  }

  // Data from embedded JSON tags (template provides rig_labels, rig_values, downtime_labels, downtime_values)
  const rigLabels = parseJSON('rig-labels-json');
  const rigValues = parseJSON('rig-values-json');
  const downtimeLabels = parseJSON('downtime-labels-json');
  const downtimeValues = parseJSON('downtime-values-json');

  if (!window.Chart) return;

  function buildPalette(count, baseColors) {
    const colors = [];
    for (let i = 0; i < count; i++) {
      colors.push(baseColors[i % baseColors.length]);
    }
    return colors;
  }

  // Rig performance donut chart
  const rigCtx = document.getElementById('rigPerformanceChart');
  if (rigCtx && rigLabels && rigValues) {
    new Chart(rigCtx.getContext('2d'), {
      type: 'doughnut',
      data: {
        labels: rigLabels,
        datasets: [{
          label: 'Meters Drilled (24h)',
          data: rigValues,
          backgroundColor: buildPalette(rigValues.length, [
            '#0d6efd','#6610f2','#6f42c1','#d63384','#dc3545',
            '#fd7e14','#ffc107','#198754','#20c997','#0dcaf0'
          ])
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom' }
        }
      }
    });
  }

  // Downtime donut chart
  const downtimeCtx = document.getElementById('downtimeChart');
  if (downtimeCtx && downtimeLabels && downtimeValues) {
    // Explicit color coding by activity type
    const downtimeColorMap = {
      'maintenance': '#ffc107',       // yellow
      'safety': '#198754',            // green
      'meeting': '#fd7e14',           // orange
      'drilling': '#0d6efd',          // blue (operational time if included)
      'other': '#6c757d'              // gray fallback
    };
    const downtimeColors = downtimeLabels.map(l => downtimeColorMap[l] || '#6c757d');
    new Chart(downtimeCtx.getContext('2d'), {
      type: 'doughnut',
      data: {
        labels: downtimeLabels,
        datasets: [{
          label: 'Downtime (hrs)',
          data: downtimeValues,
          backgroundColor: downtimeColors
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom' }
        }
      }
    });
  }
})();