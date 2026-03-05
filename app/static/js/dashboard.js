// Dashboard cumulative charts from localStorage
(function(){
  function loadRuns(key){
    try{ return JSON.parse(localStorage.getItem(key) || '[]'); }catch(e){ return []; }
  }

  function renderNumeracy(){
    const runs = loadRuns('adapt_numeracy_runs');
    if(!runs.length) return;
    const labels = runs.map(r=>new Date(r.ts).toLocaleString());
    const scores = runs.map(r=>r.number_sense_score ?? null);
    const ctx = document.getElementById('dash-numeracy-score');
    if(!ctx) return;
    window.renderLineChart('dash-numeracy-score', labels, scores, '#10B981', 'rgba(16,185,129,0.15)', { label: 'Number Sense', max: 100 });
  }

  function renderAttention(){
    const runs = loadRuns('adapt_attention_runs');
    if(!runs.length) return;
    const labels = runs.map(r=>new Date(r.ts).toLocaleString());
    const scores = runs.map(r=>r.attention_score ?? null);
    const ctx = document.getElementById('dash-attention-score');
    if(!ctx) return;
    window.renderLineChart('dash-attention-score', labels, scores, '#3B82F6', 'rgba(59,130,246,0.12)', { label: 'Attention', max: 1 });
  }

  function init(){
    renderNumeracy(); renderAttention();
    // re-render when storage changes in other tabs
    window.addEventListener('storage', ()=>{ renderNumeracy(); renderAttention(); });
    const btn = document.getElementById('export-pdf');
    if(btn) btn.addEventListener('click', async ()=>{
      try{
        const numCanvas = document.getElementById('dash-numeracy-score');
        const attCanvas = document.getElementById('dash-attention-score');
        const images = {};
        if(numCanvas) images['Number Sense'] = numCanvas.toDataURL('image/png');
        if(attCanvas) images['Attention'] = attCanvas.toDataURL('image/png');
        const payload = { student_id: 'demo_student', images };
        const resp = await fetch('/adapt-ld/report/create', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
        const json = await resp.json();
        alert('Report created: ' + json.filename);
      }catch(e){ console.error('Export failed', e); alert('Export failed'); }
    });
  }

  window.addEventListener('DOMContentLoaded', init);
})();
