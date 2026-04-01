// Centralized Chart helpers for ADAPT-LD
(function () {

  const canvas1 = document.getElementById('num-correct-chart');
  if (!canvas1) return;

  window._charts = window._charts || {};

  function destroyChart(id){
    try{
      if(window._charts && window._charts[id]){
        window._charts[id].destroy();
        delete window._charts[id];
      }
    }catch(e){ 
      console.warn('Destroy chart failed', id, e); 
    }
  }

  function renderBarChart(canvasId, labels, data, bgColors, opts={}){
    const el = document.getElementById(canvasId);
    if(!el) return null;

    destroyChart(canvasId);
    const ctx = el.getContext('2d');

    const background = Array.isArray(bgColors)
      ? bgColors
      : labels.map(()=>bgColors || '#3B82F6');

    const cfg = {
      type: 'bar',
      data: {
        labels,
        datasets:[{
          label: opts.label || 'Count',
          data,
          backgroundColor: background
        }]
      },
      options:{
        responsive: opts.responsive ?? true,
        maintainAspectRatio: opts.maintainAspectRatio ?? false,
        scales:{ y:{ beginAtZero:true, suggestedMax: opts.suggestedMax }}
      }
    };

    window._charts[canvasId] = new Chart(ctx, cfg);
    return window._charts[canvasId];
  }

  function renderHistogram(canvasId, labels, data, color, opts={}){
    return renderBarChart(canvasId, labels, data, color, opts);
  }

  function renderLineChart(canvasId, labels, data, strokeColor, fillColor, opts={}){
    const el = document.getElementById(canvasId);
    if(!el) return null;

    destroyChart(canvasId);
    const ctx = el.getContext('2d');

    const cfg = {
      type:'line',
      data:{
        labels,
        datasets:[{
          label: opts.label || '',
          data,
          borderColor: strokeColor || '#3B82F6',
          backgroundColor: fillColor || 'rgba(59,130,246,0.12)',
          tension: opts.tension || 0.2,
          fill: opts.fill ?? true
        }]
      },
      options:{
        responsive: opts.responsive ?? true,
        maintainAspectRatio: opts.maintainAspectRatio ?? false,
        scales:{
          x:{ display:true },
          y:{ beginAtZero: opts.beginAtZero ?? true, max: opts.max }
        }
      }
    };

    window._charts[canvasId] = new Chart(ctx, cfg);
    return window._charts[canvasId];
  }

  window.renderBarChart = function(canvasId, labels, data, colors, options = {}) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: options.label || 'Data',
        data: data,
        backgroundColor: colors
      }]
    },
    options: {
      responsive: true,
      scales: {
        y: {
          beginAtZero: true,
          suggestedMax: options.suggestedMax || undefined
        }
      }
    }
  });
};

window.renderHistogram = function(canvasId, labels, data, color, options = {}) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: options.label || 'Frequency',
        data: data,
        backgroundColor: color
      }]
    },
    options: {
      responsive: true,
      scales: {
        y: {
          beginAtZero: true,
          suggestedMax: options.suggestedMax || undefined
        }
      }
    }
  });
};

window.renderBarChart = renderBarChart;
window.renderHistogram = renderHistogram;
window.renderLineChart = renderLineChart;

})();