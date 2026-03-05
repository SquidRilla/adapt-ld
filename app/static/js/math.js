(function () {
// Presents questions from a built-in bank, times responses, and submits to server

const BANK = [
  {q: "What is 7 + 6?", a: 13, difficulty: 'easy'},
  {q: "What is 12 - 4?", a: 8, difficulty: 'easy'},
  {q: "What is 9 × 3?", a: 27, difficulty: 'easy'},
  {q: "What is 48 ÷ 6?", a: 8, difficulty: 'easy'},
  {q: "What is 15 + 27?", a: 42, difficulty: 'easy'},
  {q: "What is 100 - 37?", a: 63, difficulty: 'easy'},
  {q: "What is 6 × 7?", a: 42, difficulty: 'easy'},
  {q: "What is 81 ÷ 9?", a: 9, difficulty: 'easy'},
  {q: "What is 14 + 5?", a: 19, difficulty: 'easy'},
  {q: "What is 20 - 13?", a: 7, difficulty: 'easy'},
  {q: "What is 25 + 17?", a: 42, difficulty: 'easy'},
  {q: "What is 8 × 5?", a: 40, difficulty: 'easy'},
  {q: "What is 45 ÷ 5?", a: 9, difficulty: 'easy'},
  {q: "What is 11 + 13?", a: 24, difficulty: 'easy'},
  {q: "What is 30 - 18?", a: 12, difficulty: 'easy'},
  {q: "What is 7 × 8?", a: 56, difficulty: 'easy'},
  {q: "What is 72 ÷ 8?", a: 9, difficulty: 'easy'},
  {q: "What is 3 + 4 × 2? (order of operations)", a: 11, difficulty: 'medium'},
  {q: "If x + 5 = 12, what is x?", a: 7, difficulty: 'medium'},
  {q: "What is 2^3 (2 to the power 3)?", a: 8, difficulty: 'easy'},
  {q: "What is -5 + 12?", a: 7, difficulty: 'easy'},
  {q: "What is 0.5 + 0.25?", a: 0.75, difficulty: 'medium'},
  {q: "What is 10% of 80?", a: 8, difficulty: 'medium'},
  {q: "If a pack has 12 pencils and you have 4 packs, how many pencils?", a: 48, difficulty: 'easy'},
  {q: "What is 3.5 + 2.1?", a: 5.6, difficulty: 'medium'},
  {q: "What is 14 × 0.5?", a: 7, difficulty: 'medium'},
  {q: "If you divide 90 into 9 equal groups, how many in each?", a: 10, difficulty: 'easy'},
  {q: "A shirt costs 40 and is 25% off. What is the sale price?", a: 30, difficulty: 'medium'},
  {q: "If y - 4 = 9, what is y?", a: 13, difficulty: 'medium'}
];

let startedAt = null;
let results = [];
let testStart = null;
let timerInterval = null;
let questionTimer = null;
let questionTimeLeft = 0;

const QUIZ_LENGTH = 10; // fixed number of items per run

// adaptive state
let currentDifficulty = 'easy';
let easyPool = [];
let mediumPool = [];
let currentItem = null;
let questionCount = 0;
let streak = 0; // positive = correct streak, negative = incorrect streak

function shuffle(a){
  for(let i=a.length-1;i>0;i--){
    const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];
  }
}

function init(){
  // build difficulty pools
  easyPool = BANK.filter(b => b.difficulty === 'easy').slice();
  mediumPool = BANK.filter(b => b.difficulty === 'medium').slice();
  shuffle(easyPool); shuffle(mediumPool);
  document.getElementById('q-total').textContent = QUIZ_LENGTH;
  bindButtons();
  questionCount = 0; streak = 0; currentDifficulty = 'easy'; results = [];
  testStart = performance.now();
  // timer for UI
  if(timerInterval) clearInterval(timerInterval);
  timerInterval = setInterval(()=>{
    const elapsed = (performance.now() - testStart)/1000.0;
    const el = document.getElementById('num-timer');
    if(el) el.textContent = elapsed.toFixed(2) + 's';
  }, 100);
  showNext();
}

function bindButtons(){
  document.getElementById('q-next').addEventListener('click', onNext);
  document.getElementById('q-skip').addEventListener('click', onSkip);
  document.getElementById('q-answer').addEventListener('keydown', (e)=>{
    if(e.key === 'Enter') onNext();
  });
}

function pickFromPool(diff){
  let pool = diff === 'easy' ? easyPool : mediumPool;
  if(pool.length > 0) return pool.shift();
  // fallback to other pool
  pool = diff === 'easy' ? mediumPool : easyPool;
  if(pool.length > 0) return pool.shift();
  return null;
}

function showNext(){
  if(questionCount >= QUIZ_LENGTH){
    submitResults();
    return;
  }
  currentItem = pickFromPool(currentDifficulty);
  if(!currentItem){
    // no items left at all
    submitResults();
    return;
  }
  document.getElementById('q-index').textContent = questionCount+1;
  document.getElementById('q-text').textContent = currentItem.q;
  document.getElementById('q-answer').value = '';
  document.getElementById('q-answer').focus();
  startedAt = performance.now();
  // clear any existing question timer
  if(questionTimer) clearInterval(questionTimer);
  // set time limits by difficulty (seconds)
  const limits = { easy: 15, medium: 25 };
  const limit = limits[currentItem.difficulty] || 20;
  questionTimeLeft = limit;
  const bar = document.getElementById('num-countdown-bar');
  if(bar) bar.style.width = '100%';
  questionTimer = setInterval(()=>{
    questionTimeLeft -= 0.1;
    questionTimeLeft = Math.max(0, questionTimeLeft);
    const pct = (questionTimeLeft / limit) * 100;
    if(bar) {
      bar.style.width = (pct>0?pct.toFixed(2):'0.00') + '%';
      // smooth transitions
      bar.style.transition = 'width 0.1s linear, background-color 0.25s linear';
      // color change: green (>50), yellow (20-50), red (<20)
      if(pct > 50) bar.style.backgroundColor = '#10B981'; // emerald-500
      else if(pct > 20) bar.style.backgroundColor = '#F59E0B'; // amber-500
      else bar.style.backgroundColor = '#EF4444'; // red-500
    }
    if(questionTimeLeft <= 0){
      clearInterval(questionTimer); questionTimer = null;
      // time up: record as skipped (NaN) and move on
      recordAnswer(NaN);
      showNext();
    }
  }, 100);
}

function recordAnswer(given){
  const rt = (performance.now() - startedAt)/1000.0;
  const numeric = Number(given);
  const correct = !isNaN(numeric) && numeric === currentItem.a ? 1 : 0;
  results.push({question: currentItem.q, answer: isNaN(numeric) ? null : numeric, correct, rt, difficulty: currentItem.difficulty});
  // update adaptive streak
  if(correct){
    streak = Math.max(0, streak) + 1;
  } else {
    streak = Math.min(0, streak) - 1;
  }
  // simple rule: two correct in a row -> escalate; two incorrect in a row -> de-escalate
  if(streak >= 2 && currentDifficulty === 'easy'){
    currentDifficulty = 'medium'; streak = 0;
  } else if(streak <= -2 && currentDifficulty === 'medium'){
    currentDifficulty = 'easy'; streak = 0;
  }
  questionCount += 1;
  // update live accuracy display
  const correctCount = results.reduce((s,r)=>s+(r.correct?1:0),0);
  const accEl = document.getElementById('num-accuracy');
  if(accEl){
    const acc = results.length ? (correctCount / results.length) : 0;
    accEl.textContent = results.length ? (acc*100).toFixed(1)+'%' : '-';
  }
  // clear question timer when answer recorded
  if(questionTimer){ clearInterval(questionTimer); questionTimer = null; }
  const bar = document.getElementById('num-countdown-bar'); if(bar) { bar.style.width = '0%'; bar.style.backgroundColor = '#10B981'; }
}

async function onNext(){
  const val = document.getElementById('q-answer').value;
  recordAnswer(val === '' ? NaN : Number(val));
  showNext();
}

function onSkip(){
  recordAnswer(NaN);
  showNext();
}

async function submitResults(){
  // Prepare payload compatible with server: answers, correct flags, response_times
  const answers = results.map(r => r.answer === null ? null : r.answer);
  const correct = results.map(r => r.correct);
  const rts = results.map(r => r.rt);
  const total_time = testStart ? ((performance.now() - testStart)/1000.0) : 0;
  const correctCount = results.reduce((s,r)=>s+(r.correct?1:0),0);
  const accuracy = results.length ? (correctCount / results.length) : 0;
  const payload = { answers, correct, response_times: rts, total_time, accuracy };

  try{
    const resp = await fetch('/adapt-ld/math/score', {
      method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload), credentials: 'include'
    });
    const data = await resp.json();
    showResult(data);
    // persist a summary run to localStorage for dashboard charts
    try{
      const run = {
        ts: new Date().toISOString(),
        total: data.total,
        correct: data.correct,
        accuracy: data.accuracy,
        total_time: data.total_time ?? payload.total_time,
        number_sense_score: data.number_sense_score ?? null
      };
      const key = 'adapt_numeracy_runs';
      const arr = JSON.parse(localStorage.getItem(key) || '[]');
      arr.push(run);
      // keep last 500
      localStorage.setItem(key, JSON.stringify(arr.slice(-500)));
    }catch(e){ console.warn('Failed to save numeracy run', e); }
  }catch(err){
    console.error('Numeracy submit failed', err);
    alert('Failed to submit numeracy results.');
  }
}

function showResult(data){
  document.getElementById('num-total').textContent = data.total;
  document.getElementById('num-correct').textContent = data.correct;
  document.getElementById('num-acc').textContent = (data.accuracy*100).toFixed(1) + '%';
  document.getElementById('num-total-time').textContent = (data.total_time ?? 0).toFixed(2);
  document.getElementById('num-rt').textContent = (data.avg_response_time ?? 0).toFixed(2);
  document.getElementById('num-score').textContent = (data.number_sense_score ?? 0).toFixed(1);
  document.getElementById('numeracy-result').classList.remove('hidden');
  // hide question card
  document.getElementById('question-card').style.display = 'none';
  document.getElementById('q-next').style.display = 'none';
  document.getElementById('q-skip').style.display = 'none';
  if(timerInterval) clearInterval(timerInterval);

  // Charts (Chart.js required)
  try{
    // Correct vs Incorrect
    const correctCount = results.reduce((s,r)=>s+(r.correct?1:0),0);
    const incorrectCount = results.length - correctCount;
    const skippedCount = results.filter(r=>r.answer===null).length;
    // render counts using centralized chart helper
    const maxCount = Math.max(correctCount, incorrectCount, skippedCount, 1);
    const suggestedMax = Math.max(QUIZ_LENGTH, Math.ceil(maxCount * 1));
    window.renderBarChart('num-correct-chart', ['Correct','Incorrect','Skipped'], [correctCount, incorrectCount, skippedCount], ['#10B981','#EF4444','#94A3B8'], { label: 'Count', suggestedMax });

    // RT histogram (simple binning)
    const rts = results.map(r=>r.rt).filter(x=>typeof x==='number' && !isNaN(x));
    const bins = [0,0.5,1,1.5,2,3,5];
    const labels = bins.slice(0,-1).map((b,i)=>`${bins[i]}-${bins[i+1]}s`);
    const counts = labels.map((_,i)=>0);
    rts.forEach(rt=>{
      for(let i=0;i<bins.length-1;i++){
        if(rt >= bins[i] && rt < bins[i+1]){ counts[i]+=1; break; }
      }
    });
    const rtMax = counts.length ? Math.max(...counts) : 1;
    const suggestedRtMax = Math.max(1, Math.ceil(rtMax * 1.2));
    window.renderHistogram('num-rt-chart', labels, counts, '#3B82F6', { label: 'Responses', suggestedMax: suggestedRtMax });
  }catch(e){ console.warn('Chart rendering failed', e); }
}

window.addEventListener('DOMContentLoaded', init);
})();
