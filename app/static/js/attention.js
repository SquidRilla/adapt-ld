// Simple Continuous Performance Test (CPT) harness
// Presents letters, target = 'X'. Records hits, misses, false alarms, and reaction times.

const TRIALS = 40;
const STIMULUS_MS = 600;
const ISI_MS = 400;
const TARGET_PROB = 0.25;

let trials = [];
let idx = 0;
let stimulusShownAt = 0;
let awaitingResponse = false;
let hitCount = 0;
let missCount = 0;
let falseAlarms = 0;
let reactionTimes = [];
let running = false;
let keyHandler = null;
let respondBtn = null;
let testStart = null;
let attTimerInterval = null;
let attStimCountdownInterval = null;
let stimTimeLeft = 0;

function randLetter(){
  const letters = 'ABCDEFGHIJKLMNOPQRSTUVWYZ'; // intentionally omit X so targets can be inserted
  return letters.charAt(Math.floor(Math.random()*letters.length));
}

function buildTrials(){
  trials = [];
  for(let i=0;i<TRIALS;i++){
    const isTarget = Math.random() < TARGET_PROB;
    const letter = isTarget ? 'X' : randLetter();
    trials.push({isTarget, letter});
  }
}

function showStimulus(letter){
  const el = document.getElementById('stimulus');
  el.textContent = letter;
  el.classList.add('text-6xl');
}

function clearStimulus(){
  const el = document.getElementById('stimulus');
  el.textContent = '-';
}

function startTest(){
  if(running) return;
  running = true;
  idx = 0;
  hitCount = 0; missCount = 0; falseAlarms = 0; reactionTimes = [];
  buildTrials();
  document.getElementById('attention-result').classList.add('hidden');
  attachHandlers();
  testStart = performance.now();
  if(attTimerInterval) clearInterval(attTimerInterval);
  attTimerInterval = setInterval(()=>{
    const elapsed = (performance.now() - testStart)/1000.0;
    const el = document.getElementById('att-timer'); if(el) el.textContent = elapsed.toFixed(2) + 's';
  }, 100);
  runNext();
}

function stopTest(){
  running = false;
  detachHandlers();
  clearStimulus();
  // show partial results if any trials executed
  if(idx>0) submitResults();
}

function attachHandlers(){
  keyHandler = (e)=>{
    if(e.code === 'Space') handleResponse();
  };
  document.addEventListener('keydown', keyHandler);
  respondBtn = document.getElementById('respond-btn');
  respondBtn.addEventListener('click', handleResponse);
}

function detachHandlers(){
  if(keyHandler) document.removeEventListener('keydown', keyHandler);
  if(respondBtn) respondBtn.removeEventListener('click', handleResponse);
}

function handleResponse(){
  if(!awaitingResponse) {
    // response outside stimulus window = false alarm
    falseAlarms += 1;
    return;
  }
  const rt = (performance.now() - stimulusShownAt)/1000.0;
  const trial = trials[idx];
  if(trial && trial.isTarget){
    hitCount += 1;
    reactionTimes.push(rt);
  } else {
    falseAlarms += 1;
  }
  // prevent double responses for same stimulus
  awaitingResponse = false;
}

function runNext(){
  if(!running) return;
  if(idx >= trials.length){
    running = false;
    detachHandlers();
    clearStimulus();
    submitResults();
    return;
  }
  const trial = trials[idx];
  // show stimulus
  showStimulus(trial.letter);
  stimulusShownAt = performance.now();
  awaitingResponse = true;
  // per-stimulus countdown (based on STIMULUS_MS) - update progress bar
  if(attStimCountdownInterval) clearInterval(attStimCountdownInterval);
  stimTimeLeft = STIMULUS_MS/1000.0;
  const limit = STIMULUS_MS/1000.0;
  const bar = document.getElementById('att-countdown-bar');
  if(bar) bar.style.width = '100%';
  attStimCountdownInterval = setInterval(()=>{
    stimTimeLeft -= 0.05;
    stimTimeLeft = Math.max(0, stimTimeLeft);
    const pct = (stimTimeLeft / limit) * 100;
    if(bar) {
      bar.style.width = (pct>0?pct.toFixed(2):'0.00') + '%';
      bar.style.transition = 'width 0.05s linear, background-color 0.15s linear';
      if(pct > 50) bar.style.backgroundColor = '#10B981'; // emerald-500
      else if(pct > 20) bar.style.backgroundColor = '#F59E0B'; // amber-500
      else bar.style.backgroundColor = '#EF4444'; // red-500
    }
  }, 50);
  // after stimulus duration
  setTimeout(()=>{
    if(attStimCountdownInterval){ clearInterval(attStimCountdownInterval); attStimCountdownInterval = null; }
    const bar = document.getElementById('att-countdown-bar'); if(bar) { bar.style.width = '0%'; bar.style.backgroundColor = '#10B981'; }
    // if it was a target and no response recorded -> miss
    if(trial.isTarget && awaitingResponse){
      missCount +=1;
      awaitingResponse = false;
    }
    clearStimulus();
    idx += 1;
    // inter-stimulus interval
    setTimeout(()=>{
      runNext();
    }, ISI_MS);
  }, STIMULUS_MS);
}

async function submitResults(){
  const total_time = testStart ? ((performance.now() - testStart)/1000.0) : 0;
  const accuracy = (hitCount + missCount) ? (hitCount / (hitCount + missCount)) : 0;
  const payload = {
    hits: hitCount,
    misses: missCount,
    false_alarms: falseAlarms,
    reaction_times: reactionTimes,
    total_time,
    accuracy
  };
  try{
    const resp = await fetch('/adapt-ld/attention/score', {
      method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload), credentials: 'include'
    });
    const data = await resp.json();
    showResults(data);
    // persist a summary run to localStorage for dashboard charts
    try{
      const run = {
        ts: new Date().toISOString(),
        hits: hitCount,
        misses: missCount,
        false_alarms: falseAlarms,
        total_time: payload.total_time,
        accuracy: payload.accuracy,
        attention_score: data.attention_score ?? null
      };
      const key = 'adapt_attention_runs';
      const arr = JSON.parse(localStorage.getItem(key) || '[]');
      arr.push(run);
      localStorage.setItem(key, JSON.stringify(arr.slice(-500)));
    }catch(e){ console.warn('Failed to save attention run', e); }
  }catch(err){
    console.error('Attention submit failed', err);
    alert('Failed to submit attention results.');
  }
}

function showResults(data){
  document.getElementById('att-hits').textContent = hitCount;
  document.getElementById('att-misses').textContent = missCount;
  document.getElementById('att-false').textContent = falseAlarms;
  document.getElementById('att-rt').textContent = reactionTimes.length ? (reactionTimes.reduce((a,b)=>a+b,0)/reactionTimes.length).toFixed(3) : '-';
  document.getElementById('att-score').textContent = data.attention_score ?? '-';
  const accEl = document.getElementById('att-accuracy');
  if(accEl) accEl.textContent = ((hitCount + missCount) ? (hitCount/(hitCount+missCount))*100 : 0).toFixed(1) + '%';
  if(attTimerInterval) clearInterval(attTimerInterval);
  document.getElementById('attention-result').classList.remove('hidden');

  // Charts
  try{
    const attMaxCount = Math.max(hitCount, missCount, falseAlarms, 1);
    const attSuggestedMax = Math.max(TRIALS, Math.ceil(attMaxCount * 1.2));
    window.renderBarChart('att-counts-chart', ['Hits','Misses','False Alarms'], [hitCount, missCount, falseAlarms], ['#10B981','#F59E0B','#EF4444'], { label: 'Count', suggestedMax: attSuggestedMax });

    const rts = reactionTimes.slice();
    const bins = [0,0.25,0.5,0.75,1,1.5,2,3];
    const labels = bins.slice(0,-1).map((b,i)=>`${bins[i]}-${bins[i+1]}s`);
    const counts = labels.map(()=>0);
    rts.forEach(rt=>{ for(let i=0;i<bins.length-1;i++){ if(rt>=bins[i] && rt<bins[i+1]){ counts[i]+=1; break; } }});
    const attRtMax = counts.length ? Math.max(...counts) : 1;
    const attSuggestedRtMax = Math.max(1, Math.ceil(attRtMax * 1.2));
    window.renderHistogram('att-rt-chart', labels, counts, '#3B82F6', { label: 'Responses', suggestedMax: attSuggestedRtMax });
  }catch(e){ console.warn('Attention chart error', e); }
}

window.addEventListener('DOMContentLoaded', ()=>{
  document.getElementById('start-btn').addEventListener('click', startTest);
  document.getElementById('stop-btn').addEventListener('click', stopTest);
});
