/* ═══════════════════════════════════════════════════════════════════════════
   PPM Data Quality Dashboard — JavaScript
   Loads data_quality_exceptions.csv, computes KPIs, and renders charts + table
   ═══════════════════════════════════════════════════════════════════════════ */

// ── CSV Parser (lightweight, no dependencies) ──────────────────────────────
function parseCSV(text) {
  const lines = text.trim().split('\n');
  const headers = parseCSVLine(lines[0]);
  return lines.slice(1).map(line => {
    const values = parseCSVLine(line);
    const obj = {};
    headers.forEach((h, i) => {
      obj[h.trim()] = (values[i] || '').trim();
    });
    return obj;
  });
}

function parseCSVLine(line) {
  const result = [];
  let current = '';
  let inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"') {
      if (inQuotes && line[i + 1] === '"') {
        current += '"';
        i++;
      } else {
        inQuotes = !inQuotes;
      }
    } else if (ch === ',' && !inQuotes) {
      result.push(current);
      current = '';
    } else {
      current += ch;
    }
  }
  result.push(current);
  return result;
}

// ── Globals ────────────────────────────────────────────────────────────────
let rawData = [];
let chartIssue = null;
let chartSeverity = null;
let chartTrend = null;

const CHART_COLORS = {
  indigo: '#6366f1',
  violet: '#a78bfa',
  emerald: '#34d399',
  amber: '#fbbf24',
  rose: '#fb7185',
  sky: '#38bdf8',
  teal: '#2dd4bf',
  fuchsia: '#d946ef',
};

// ── Chart.js global defaults ───────────────────────────────────────────────
Chart.defaults.color = '#9ca3bf';
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.pointStyleWidth = 10;
Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(11,14,26,0.92)';
Chart.defaults.plugins.tooltip.borderColor = 'rgba(99,102,241,0.25)';
Chart.defaults.plugins.tooltip.borderWidth = 1;
Chart.defaults.plugins.tooltip.cornerRadius = 10;
Chart.defaults.plugins.tooltip.padding = 12;
Chart.defaults.plugins.tooltip.titleFont = { weight: '600', size: 13 };
Chart.defaults.plugins.tooltip.bodyFont = { size: 12 };
Chart.defaults.scale.grid = { color: 'rgba(99,102,241,0.07)' };

// ── Load & render ──────────────────────────────────────────────────────────
async function loadData() {
  try {
    let text;
    if (typeof EXCEPTIONS_CSV !== 'undefined') {
      // Works even when the file is opened directly (file://), no server needed.
      text = EXCEPTIONS_CSV;
    } else {
      // Fallback: fetch fresh data if served over http:// (e.g. after re-running validate_data.py).
      const resp = await fetch('data_quality_exceptions.csv');
      text = await resp.text();
    }
    rawData = parseCSV(text);

    document.getElementById('last-scan-badge').textContent =
      `Last scan: ${new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`;

    renderKPIs();
    renderCharts();
    renderTable();
  } catch (err) {
    console.error('Failed to load data:', err);
  }
}

// ── KPIs ───────────────────────────────────────────────────────────────────
function renderKPIs() {
  const total = rawData.length;
  const open = rawData.filter(r => r.status === 'Open').length;
  const inProgress = rawData.filter(r => r.status === 'In Progress').length;
  const closed = rawData.filter(r => r.status === 'Closed').length;

  // Average resolution time for Closed tickets
  let totalDays = 0;
  let closedWithDates = 0;
  rawData.forEach(r => {
    if (r.status === 'Closed' && r.date_raised && r.date_resolved) {
      const raised = new Date(r.date_raised);
      const resolved = new Date(r.date_resolved);
      const diff = (resolved - raised) / (1000 * 60 * 60 * 24);
      if (!isNaN(diff) && diff >= 0) {
        totalDays += diff;
        closedWithDates++;
      }
    }
  });
  const avgRes = closedWithDates > 0 ? (totalDays / closedWithDates).toFixed(1) : '—';

  animateCounter('kpi-total-val', total);
  animateCounter('kpi-open-val', open);
  animateCounter('kpi-inprogress-val', inProgress);
  animateCounter('kpi-closed-val', closed);
  animateCounter('kpi-avgres-val', parseFloat(avgRes) || 0, true);
}

function animateCounter(elementId, target, isFloat = false) {
  const el = document.getElementById(elementId);
  const duration = 800;
  const start = performance.now();

  function step(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
    const current = eased * target;
    el.textContent = isFloat ? current.toFixed(1) : Math.round(current);
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

// ── Charts ─────────────────────────────────────────────────────────────────
function renderCharts() {
  renderIssueTypeChart();
  renderSeverityChart();
  renderTrendChart();
}

function renderIssueTypeChart() {
  const counts = {};
  rawData.forEach(r => {
    counts[r.issue_type] = (counts[r.issue_type] || 0) + 1;
  });

  // Sort by count descending for visual clarity
  const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  // Split multi-word labels into arrays so Chart.js wraps them
  const labels = sorted.map(([k]) => k.split(' '));
  const values = sorted.map(([, v]) => v);
  const colors = [CHART_COLORS.rose, CHART_COLORS.indigo, CHART_COLORS.amber, CHART_COLORS.emerald, CHART_COLORS.sky];
  const bgColors = [
    'rgba(251,113,133,0.85)',
    'rgba(99,102,241,0.85)',
    'rgba(251,191,36,0.85)',
    'rgba(52,211,153,0.85)',
    'rgba(56,189,248,0.85)',
  ];

  if (chartIssue) chartIssue.destroy();

  chartIssue = new Chart(document.getElementById('chartIssueType'), {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Exceptions',
        data: values,
        backgroundColor: bgColors,
        borderColor: colors,
        borderWidth: 2,
        borderRadius: 8,
        borderSkipped: false,
        barPercentage: 0.6,
        categoryPercentage: 0.75,
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: (items) => items[0].label.replace(/,/g, ' '),
          }
        }
      },
      scales: {
        y: {
          ticks: { font: { size: 11, weight: '500' }, autoSkip: false },
          grid: { display: false },
        },
        x: {
          beginAtZero: true,
          ticks: { stepSize: 2, font: { size: 11 } },
        },
      },
      animation: { duration: 1000, easing: 'easeOutQuart' },
    },
  });
}

function renderSeverityChart() {
  const counts = {};
  rawData.forEach(r => {
    counts[r.severity] = (counts[r.severity] || 0) + 1;
  });

  const order = ['High', 'Medium', 'Low'];
  const labels = order.filter(s => counts[s]);
  const values = labels.map(s => counts[s]);
  const colorMap = { High: CHART_COLORS.rose, Medium: CHART_COLORS.amber, Low: CHART_COLORS.sky };
  const colors = labels.map(s => colorMap[s]);
  const bgColors = colors.map(c => c + 'cc');

  if (chartSeverity) chartSeverity.destroy();

  chartSeverity = new Chart(document.getElementById('chartSeverity'), {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: bgColors,
        borderColor: 'rgba(11,14,26,0.8)',
        borderWidth: 3,
        hoverOffset: 10,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '62%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: { padding: 18, font: { size: 12 } },
        },
      },
      animation: { animateRotate: true, duration: 1200 },
    },
  });
}

function renderTrendChart() {
  // Aggregate by date_raised
  const dateCounts = {};
  rawData.forEach(r => {
    if (r.date_raised) {
      dateCounts[r.date_raised] = (dateCounts[r.date_raised] || 0) + 1;
    }
  });

  const sortedDates = Object.keys(dateCounts).sort();
  const values = sortedDates.map(d => dateCounts[d]);

  // Cumulative
  const cumulative = [];
  values.reduce((acc, v, i) => { cumulative[i] = acc + v; return cumulative[i]; }, 0);

  if (chartTrend) chartTrend.destroy();

  chartTrend = new Chart(document.getElementById('chartTrend'), {
    type: 'line',
    data: {
      labels: sortedDates,
      datasets: [
        {
          label: 'Exceptions Raised',
          data: values,
          borderColor: CHART_COLORS.indigo,
          backgroundColor: CHART_COLORS.indigo + '18',
          fill: true,
          tension: 0.35,
          pointRadius: 4,
          pointBackgroundColor: CHART_COLORS.indigo,
          pointBorderColor: '#0b0e1a',
          pointBorderWidth: 2,
          pointHoverRadius: 7,
        },
        {
          label: 'Cumulative',
          data: cumulative,
          borderColor: CHART_COLORS.violet,
          backgroundColor: 'transparent',
          borderDash: [6, 4],
          tension: 0.3,
          pointRadius: 0,
          pointHoverRadius: 5,
        },
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          position: 'top',
          align: 'end',
          labels: { padding: 16, font: { size: 11 } },
        },
      },
      scales: {
        x: {
          type: 'time',
          time: { unit: 'week', tooltipFormat: 'MMM d, yyyy' },
          ticks: { font: { size: 10 }, maxRotation: 0 },
          grid: { display: false },
        },
        y: {
          beginAtZero: true,
          ticks: { stepSize: 2, font: { size: 11 } },
        },
      },
      animation: { duration: 1200, easing: 'easeOutQuart' },
    },
  });
}

// ── Table ──────────────────────────────────────────────────────────────────
function renderTable(filterStatus = 'All', filterSeverity = 'All') {
  const tbody = document.getElementById('exception-tbody');
  tbody.innerHTML = '';

  let filtered = rawData;
  if (filterStatus !== 'All') {
    filtered = filtered.filter(r => r.status === filterStatus);
  }
  if (filterSeverity !== 'All') {
    filtered = filtered.filter(r => r.severity === filterSeverity);
  }

  // Sort: Open first, then In Progress, then Closed
  const statusOrder = { 'Open': 0, 'In Progress': 1, 'Closed': 2 };
  filtered.sort((a, b) => (statusOrder[a.status] ?? 9) - (statusOrder[b.status] ?? 9));

  filtered.forEach((row, i) => {
    const tr = document.createElement('tr');
    tr.style.animationDelay = `${i * 20}ms`;

    const statusClass = row.status === 'Closed' ? 'pill-closed'
      : row.status === 'In Progress' ? 'pill-inprogress' : 'pill-open';
    const sevClass = row.severity === 'High' ? 'pill-high'
      : row.severity === 'Medium' ? 'pill-medium' : 'pill-low';

    tr.innerHTML = `
      <td style="font-weight:600;color:var(--text-primary)">${row.exception_id}</td>
      <td>${row.project_id}</td>
      <td>${row.issue_type}</td>
      <td><span class="pill ${sevClass}">${row.severity}</span></td>
      <td><span class="pill ${statusClass}">${row.status}</span></td>
      <td>${row.date_raised || '—'}</td>
      <td>${row.date_resolved || '—'}</td>
      <td style="font-size:0.75rem">${row.detail || ''}</td>
    `;
    tbody.appendChild(tr);
  });
}

// ── Event listeners ────────────────────────────────────────────────────────
document.getElementById('filter-status').addEventListener('change', function () {
  const sevFilter = document.getElementById('filter-severity').value;
  renderTable(this.value, sevFilter);
});

document.getElementById('filter-severity').addEventListener('change', function () {
  const statusFilter = document.getElementById('filter-status').value;
  renderTable(statusFilter, this.value);
});

document.getElementById('btn-refresh').addEventListener('click', () => {
  loadData();
});

// ── Init ───────────────────────────────────────────────────────────────────
loadData();
