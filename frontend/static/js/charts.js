/**
 * NetSage AI - Analytics & Chart.js Visualizations
 */

let chartCategoryInstance = null;
let chartOsiInstance = null;
let chartSeverityInstance = null;
let chartVerdictsInstance = null;

const CYBER_COLORS = {
  cyan: '#00f0ff',
  blue: '#38bdf8',
  indigo: '#818cf8',
  purple: '#a855f7',
  green: '#22c55e',
  amber: '#f59e0b',
  red: '#ef4444',
  teal: '#14b8a6',
  gray: '#64748b'
};

function initAnalyticsCharts(statsData) {
  const isDark = true;
  const gridColor = 'rgba(56, 189, 248, 0.1)';
  const textColor = '#94a3b8';

  // 1. Categories Chart (Doughnut)
  const ctxCat = document.getElementById('chartCategory');
  if (ctxCat) {
    if (chartCategoryInstance) chartCategoryInstance.destroy();
    const catLabels = Object.keys(statsData.category_counts || {});
    const catValues = Object.values(statsData.category_counts || {});

    chartCategoryInstance = new Chart(ctxCat, {
      type: 'doughnut',
      data: {
        labels: catLabels,
        datasets: [{
          data: catValues,
          backgroundColor: [
            CYBER_COLORS.cyan,
            CYBER_COLORS.blue,
            CYBER_COLORS.purple,
            CYBER_COLORS.green,
            CYBER_COLORS.amber,
            CYBER_COLORS.red,
            CYBER_COLORS.indigo,
            CYBER_COLORS.teal
          ],
          borderColor: '#070b14',
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right',
            labels: { color: textColor, font: { family: 'Inter', size: 11 }, boxWidth: 12 }
          }
        },
        cutout: '65%'
      }
    });
  }

  // 2. OSI Layer Breakdown (Bar)
  const ctxOsi = document.getElementById('chartOsi');
  if (ctxOsi) {
    if (chartOsiInstance) chartOsiInstance.destroy();
    const osiLabels = ['Layer 1', 'Layer 2', 'Layer 3', 'Layer 4', 'Layer 7'];
    const osiValues = osiLabels.map(l => (statsData.osi_counts && statsData.osi_counts[l]) || 0);

    chartOsiInstance = new Chart(ctxOsi, {
      type: 'bar',
      data: {
        labels: ['L1 Physical', 'L2 Data Link', 'L3 Network', 'L4 Transport', 'L7 Application'],
        datasets: [{
          label: 'Fault Scenarios',
          data: osiValues,
          backgroundColor: [
            'rgba(148, 163, 184, 0.6)',
            'rgba(56, 189, 248, 0.6)',
            'rgba(0, 240, 255, 0.7)',
            'rgba(168, 85, 247, 0.6)',
            'rgba(34, 197, 94, 0.6)'
          ],
          borderColor: [
            CYBER_COLORS.gray,
            CYBER_COLORS.blue,
            CYBER_COLORS.cyan,
            CYBER_COLORS.purple,
            CYBER_COLORS.green
          ],
          borderWidth: 1,
          borderRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: textColor, font: { size: 10 } } },
          y: { grid: { color: gridColor }, ticks: { color: textColor, stepSize: 2 } }
        }
      }
    });
  }

  // 3. Severity Distribution (Polar Area / Doughnut)
  const ctxSev = document.getElementById('chartSeverity');
  if (ctxSev) {
    if (chartSeverityInstance) chartSeverityInstance.destroy();
    const sevLabels = ['Critical', 'High', 'Medium', 'Low'];
    const sevValues = sevLabels.map(s => (statsData.severity_counts && statsData.severity_counts[s]) || 0);

    chartSeverityInstance = new Chart(ctxSev, {
      type: 'pie',
      data: {
        labels: sevLabels,
        datasets: [{
          data: sevValues,
          backgroundColor: [
            'rgba(239, 68, 68, 0.8)',
            'rgba(245, 158, 11, 0.8)',
            'rgba(56, 189, 248, 0.8)',
            'rgba(34, 197, 94, 0.8)'
          ],
          borderColor: '#070b14',
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right',
            labels: { color: textColor, font: { family: 'Inter', size: 11 }, boxWidth: 12 }
          }
        }
      }
    });
  }

  // 4. Human Review Verdicts (Bar / Doughnut)
  const ctxVerd = document.getElementById('chartVerdicts');
  if (ctxVerd) {
    if (chartVerdictsInstance) chartVerdictsInstance.destroy();
    const vCounts = statsData.verdict_counts || { Accepted: 0, Edited: 0, Rejected: 0 };

    chartVerdictsInstance = new Chart(ctxVerd, {
      type: 'doughnut',
      data: {
        labels: ['Accepted', 'Edited (Corrected)', 'Rejected'],
        datasets: [{
          data: [vCounts.Accepted || 0, vCounts.Edited || 0, vCounts.Rejected || 0],
          backgroundColor: [
            CYBER_COLORS.green,
            CYBER_COLORS.amber,
            CYBER_COLORS.red
          ],
          borderColor: '#070b14',
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'right',
            labels: { color: textColor, font: { family: 'Inter', size: 11 }, boxWidth: 12 }
          }
        },
        cutout: '60%'
      }
    });
  }
}
