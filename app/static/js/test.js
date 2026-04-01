
// Load previous test scores and display on cards
async function loadTestScores() {
  try {
    const res = await fetch('/adapt-ld/reports/test-scores');
    if (!res.ok) {
      console.warn('Could not load test scores:', res.status);
      return;
    }
    
    const testScores = await res.json();
    console.log('Test scores loaded:', testScores);
    
    // Map test types to card IDs and display names
    const testTypeMap = {
      'grammar': 'grammar-card',
      'attention': 'attention-card',
      'numeracy': 'math-card',
      'reading': 'reading-card'
    };
    
    // Update each card if scores exist
    for (const [testType, cardId] of Object.entries(testTypeMap)) {
      if (testScores[testType]) {
        const score = testScores[testType];
        const card = document.getElementById(cardId);
        if (card) {
          // Update status badge
          const badge = card.querySelector('.status-badge');
          if (badge) {
            const scoreValue = Math.round(score.score);
            badge.textContent = `Score: ${scoreValue}%`;
            
            // Color code the badge
            if (scoreValue >= 70) {
              badge.className = 'status-badge text-xs bg-green-100/20 text-green-400 px-2 py-1 rounded-full';
            } else if (scoreValue >= 50) {
              badge.className = 'status-badge text-xs bg-yellow-100/20 text-yellow-400 px-2 py-1 rounded-full';
            } else {
              badge.className = 'status-badge text-xs bg-red-100/20 text-red-400 px-2 py-1 rounded-full';
            }
          }
        }
      }
    }
  } catch (err) {
    console.error('Error loading test scores:', err);
  }
}

// Load scores when page loads
document.addEventListener('DOMContentLoaded', loadTestScores);

let mediaRecorder;
let audioChunks = [];
let theta = 0;
let usedItems = [];
let testCount = 0;
let currentItem = null;
const MAX_ITEMS = 3; // Number of items to assess before scoring

async function startTest() {
  const res = await fetch("/adapt-ld/reading/start", { method: "POST" });
  const data = await res.json();
  theta = data.theta;
  usedItems = [];
  testCount = 0;
  loadNextItem();
}

async function loadNextItem() {
  const res = await fetch("/adapt-ld/reading/next-item", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({ theta, used_items: usedItems })
  });
  currentItem = await res.json();
  usedItems.push(currentItem.text);
  
  // Only update DOM if elements exist (not all pages have these)
  const wordEl = document.getElementById("word");
  const statusEl = document.getElementById("status");
  if (wordEl) wordEl.textContent = currentItem.text;
  if (statusEl) statusEl.textContent = `Item ${testCount + 1} of ${MAX_ITEMS}`;
}

async function startRecording() {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream);
  mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
  mediaRecorder.onstop = sendAudio;
  mediaRecorder.start();
  const statusEl = document.getElementById("status");
  if (statusEl) statusEl.textContent = "Listening...";
}

function stopRecording() { mediaRecorder.stop(); }

async function sendAudio() {
  const blob = new Blob(audioChunks, { type: "audio/webm" });
  audioChunks = [];
  const formData = new FormData();
  formData.append("student_id", "demo_student");
  formData.append("theta", theta);
  formData.append("expected_text", currentItem.text);
  formData.append("audio", blob);
  const res = await fetch("/adapt-ld/speech/score", { method: "POST", body: formData });
  const data = await res.json();
  
  // Update theta based on response
  const updateRes = await fetch("/adapt-ld/reading/submit-response", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({ 
      theta: theta, 
      is_correct: data.fluency_score > 0.7 // Adjust threshold as needed
    })
  });
  const updateData = await updateRes.json();
  theta = updateData.theta;
  testCount++;
  
  // Continue with more items or finish
  if (testCount < MAX_ITEMS) {
    const statusEl = document.getElementById("status");
    if (statusEl) statusEl.textContent = "Loading next word...";
    setTimeout(loadNextItem, 1000);
  } else {
    // All items complete, go to result
    window.location = "/result?prediction=" + data.prediction;
  }
}

startTest();
