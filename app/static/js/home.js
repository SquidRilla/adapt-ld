let mediaRecorder;
let audioChunks = [];
let theta = 0;
//let currentItem = null;

const demoStart = document.getElementById('demo-start');
const demoArea = document.getElementById('demo-area');
const demoWord = document.getElementById('demo-word');
const demoRecord = document.getElementById('demo-record');
const demoStop = document.getElementById('demo-stop');
const demoReset = document.getElementById('demo-reset');
const demoStatus = document.getElementById('demo-status');
const demoResult = document.getElementById('demo-result');
const demoPrediction = document.getElementById('demo-prediction');
const demoSim = document.getElementById('demo-sim');
const demoWpm = document.getElementById('demo-wpm');

async function demoStartHandler() {
  demoArea.classList.remove('hidden');
  demoStart.classList.add('hidden');
  // initialize theta and get an item
  const res = await fetch('/adapt-ld/assessment/start', { method: 'POST' });
  const data = await res.json();
  theta = data.theta;
  await loadDemoItem();
}

async function loadDemoItem() {
  demoStatus.textContent = 'Loading word...';
  const res = await fetch('/adapt-ld/assessment/next-item', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ theta, used_items: [] })
  });
  currentItem = await res.json();
  demoWord.textContent = currentItem.text;
  demoStatus.textContent = 'Ready to record';
}

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = [];
    mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
    mediaRecorder.onstop = sendDemoAudio;
    mediaRecorder.start();
    demoStatus.textContent = 'Recording...';
  } catch (e) {
    demoStatus.textContent = 'Microphone access denied';
  }
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') mediaRecorder.stop();
}

async function sendDemoAudio() {
  demoStatus.textContent = 'Scoring...';
  const blob = new Blob(audioChunks, { type: 'audio/webm' });
  const formData = new FormData();
  formData.append('student_id', 'demo_user');
  formData.append('theta', theta);
  formData.append('expected_text', currentItem.text);
  formData.append('audio', blob, 'demo.webm');

  const res = await fetch('/adapt-ld/speech/score', { method: 'POST', body: formData, credentials: 'include' });
  const data = await res.json();

  // show result
  demoPrediction.textContent = data.prediction;
  demoSim.textContent = (data.metrics.similarity || 0).toFixed(2);
  demoWpm.textContent = (data.metrics.wpm || 0).toFixed(0);
  demoResult.classList.remove('hidden');
  demoStatus.textContent = 'Done';
}

function resetDemo() {
  demoArea.classList.add('hidden');
  demoStart.classList.remove('hidden');
  demoResult.classList.add('hidden');
  demoStatus.textContent = 'idle';
  demoWord.textContent = '—';
}

demoStart && demoStart.addEventListener('click', demoStartHandler);
demoRecord && demoRecord.addEventListener('click', startRecording);
demoStop && demoStop.addEventListener('click', stopRecording);
demoReset && demoReset.addEventListener('click', resetDemo);

// --- Login modal behavior ---
const openLoginBtn = document.getElementById('open-login');
const openLoginBtnMobile = document.getElementById('open-login-mobile');

function createLoginModal() {
  // Build modal HTML and append to body if not present
  if (document.getElementById('login-modal')) return;
  const modal = document.createElement('div');
  modal.id = 'login-modal';
  modal.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black/40';
  modal.innerHTML = `
    <div class="bg-white rounded-xl shadow-lg w-full max-w-md mx-4">
      <div class="p-6">
        <h3 class="text-xl font-semibold mb-2">Sign in</h3>
        <p class="text-slate-500 text-sm mb-4">Sign in to access saved assessments and reports.</p>
        <form id="login-form" class="space-y-4">
          <input id="login-email" type="email" placeholder="Email" required class="w-full px-4 py-2 border rounded-md" />
          <input id="login-password" type="password" placeholder="Password" required class="w-full px-4 py-2 border rounded-md" />
          <div class="flex justify-end gap-2">
            <button type="button" id="login-cancel" class="px-4 py-2 bg-slate-200 rounded-md">Cancel</button>
            <button type="submit" class="px-4 py-2 bg-blue-600 text-white rounded-md">Sign in</button>
          </div>
        </form>
      </div>
    </div>
  `;
  document.body.appendChild(modal);

  // Attach handlers
  document.getElementById('login-cancel').addEventListener('click', closeLoginModal);
  document.getElementById('login-form').addEventListener('submit', submitLoginForm);
}

function openLoginModal() {
  createLoginModal();
  document.getElementById('login-modal').style.display = 'flex';
}

function closeLoginModal() {
  const m = document.getElementById('login-modal');
  if (m) m.style.display = 'none';
}

async function submitLoginForm(e) {
  e.preventDefault();
  const email = document.getElementById('login-email').value;
  const password = document.getElementById('login-password').value;

  // Basic UI feedback
  const submitBtn = e.submitter || null;
  if (submitBtn) submitBtn.disabled = true;

  // Try to POST to /auth/login if available, otherwise simulate success
  try {
    const res = await fetch('/auth/login', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    if (res.ok) {
      // server sets HttpOnly cookie; no token stored in JS
      // If a redirect target was provided, go there
      if (window.__login_next_path) {
        window.location = window.__login_next_path;
        return;
      }
      closeLoginModal();
      // refresh page so navbar updates to show user profile
      window.location.reload();
    } else {
      // fallback simulation
      const text = await res.text();
      alert('Login failed: ' + (text || res.status));
    }
  } catch (err) {
    // Simulate successful sign in for demo
    if (window.__login_next_path) {
      window.location = window.__login_next_path;
      return;
    }
    closeLoginModal();
    alert('Signed in (demo) — no auth endpoint configured');
  } finally {
    if (submitBtn) submitBtn.disabled = false;
  }
}

openLoginBtn && openLoginBtn.addEventListener('click', openLoginModal);
openLoginBtnMobile && openLoginBtnMobile.addEventListener('click', openLoginModal);

// Auto-open login modal if redirected here with ?signin=1
(function checkAutoSignin() {
  try {
    const params = new URLSearchParams(window.location.search);
    const signin = params.get('signin');
    const next = params.get('next');
    if (next) window.__login_next_path = next;
    if (signin === '1') {
      openLoginModal();
    }
  } catch (e) {
    // ignore
  }
})();
