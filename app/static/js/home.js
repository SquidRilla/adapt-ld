const AUTH_BASE_URL = '/adapt-ld/auth';

console.log('home.js loaded');

(function() {
  console.log('Initializing...');

  const openLoginBtn = document.getElementById('open-login');
  console.log('openLoginBtn found:', !!openLoginBtn);

  if (openLoginBtn) {
    openLoginBtn.addEventListener('click', function() {
      console.log('Login button clicked!');
      openLoginModal();
    });
    console.log('Event listener attached to login button');
  }

  const demoStart = document.getElementById('demo-start');
  if (demoStart) {
    console.log('Demo elements found, initializing demo functionality');

    let mediaRecorder;
    let audioChunks = [];
    let theta = 0;
    let currentItem = null;

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

    // Demo functions
    async function demoStartHandler() {
      demoArea.classList.remove('hidden');
      demoStart.classList.add('hidden');
      // initialize theta and get an item
      const res = await fetch('/assessment/start', { method: 'POST' });
      const data = await res.json();
      theta = data.theta;
      await loadDemoItem();
    }

    async function loadDemoItem() {
      demoStatus.textContent = 'Loading word...';
      const res = await fetch('/assessment/next-item', {
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

    async function sendDemoAudio() {
      const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
      const formData = new FormData();
      formData.append('audio', audioBlob);
      formData.append('item_id', currentItem.id);

      demoStatus.textContent = 'Processing...';
      try {
        const res = await fetch('/speech/score', {
          method: 'POST',
          body: formData
        });
        const data = await res.json();
        demoResult.textContent = `WPM: ${data.wpm}, Accuracy: ${data.accuracy}`;
        demoPrediction.textContent = `Prediction: ${data.prediction}`;
        demoStatus.textContent = 'Complete';
      } catch (e) {
        demoStatus.textContent = 'Error processing audio';
      }
    }

    // Attach event listeners
    demoStart.addEventListener('click', demoStartHandler);
    if (demoRecord) demoRecord.addEventListener('click', startRecording);
    if (demoStop) demoStop.addEventListener('click', () => {
      if (mediaRecorder) mediaRecorder.stop();
    });
    if (demoReset) demoReset.addEventListener('click', () => {
      demoArea.classList.add('hidden');
      demoStart.classList.remove('hidden');
      demoStatus.textContent = '';
      demoResult.textContent = '';
      demoPrediction.textContent = '';
    });
  }
})();

function setupTabSwitching() {
  const loginTab = document.getElementById('tab-login');
  const registerTab = document.getElementById('tab-register');
  const loginContent = document.getElementById('login-tab');
  const registerContent = document.getElementById('register-tab');

  loginTab.addEventListener('click', () => {
    loginTab.className = 'px-4 py-2 text-blue-600 border-b-2 border-blue-600 font-medium';
    registerTab.className = 'px-4 py-2 text-slate-500 border-b-2 border-transparent';
    loginContent.classList.remove('hidden');
    registerContent.classList.add('hidden');
  });

  registerTab.addEventListener('click', () => {
    registerTab.className = 'px-4 py-2 text-blue-600 border-b-2 border-blue-600 font-medium';
    loginTab.className = 'px-4 py-2 text-slate-500 border-b-2 border-transparent';
    registerContent.classList.remove('hidden');
    loginContent.classList.add('hidden');
  });
}

function showLoading() {
  document.getElementById('loading-spinner').classList.remove('hidden');
}

function hideLoading() {
  document.getElementById('loading-spinner').classList.add('hidden');
}

function showError(message) {
  const errorDiv = document.getElementById('error-message');
  errorDiv.querySelector('p').textContent = message;
  errorDiv.classList.remove('hidden');
}

function showSuccess(message) {
  const successDiv = document.getElementById('success-message');
  successDiv.querySelector('p').textContent = message;
  successDiv.classList.remove('hidden');
}

function createLoginModal() {
  // Build modal HTML and append to body if not present
  if (document.getElementById('login-modal')) return;
  const modal = document.createElement('div');
  modal.id = 'login-modal';
  modal.className = 'fixed inset-0 z-50 flex items-center justify-center bg-black/40';
  modal.innerHTML = `
    <div class="bg-white rounded-xl shadow-lg w-full max-w-md mx-4">
      <div class="p-6">
        <div class="flex justify-center mb-4">
          <button id="tab-login" class="px-4 py-2 text-blue-600 border-b-2 border-blue-600 font-medium">Sign In</button>
          <button id="tab-register" class="px-4 py-2 text-slate-500 border-b-2 border-transparent">Sign Up</button>
        </div>
        
        <div id="login-tab" class="tab-content">
          <h3 class="text-xl font-semibold mb-2">Sign in</h3>
          <p class="text-slate-500 text-sm mb-4">Sign in to access saved assessments and reports.</p>
          <form id="login-form" class="space-y-4">
            <input id="login-email" type="email" placeholder="Email" required class="w-full px-4 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
            <input id="login-password" type="password" placeholder="Password" required class="w-full px-4 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
            <div class="flex items-center justify-between">
              <label class="flex items-center">
                <input type="checkbox" id="remember-me" class="mr-2">
                <span class="text-sm text-slate-600">Remember me</span>
              </label>
              <a href="#" class="text-sm text-blue-600 hover:underline">Forgot password?</a>
            </div>
            <div class="flex justify-end gap-2">
              <button type="button" id="login-cancel" class="px-4 py-2 bg-slate-200 rounded-md hover:bg-slate-300">Cancel</button>
              <button type="submit" id="login-submit" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50">Sign in</button>
            </div>
          </form>
        </div>
        
        <div id="register-tab" class="tab-content hidden">
          <h3 class="text-xl font-semibold mb-2">Create Account</h3>
          <p class="text-slate-500 text-sm mb-4">Create a new account to save your progress.</p>
          <form id="register-form" class="space-y-4">
            <input id="register-name" type="text" placeholder="Full Name" required class="w-full px-4 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
            <input id="register-email" type="email" placeholder="Email" required class="w-full px-4 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
            <input id="register-password" type="password" placeholder="Password" required class="w-full px-4 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
            <div class="text-xs text-slate-500">Password must be at least 6 characters</div>
            <input id="register-confirm" type="password" placeholder="Confirm Password" required class="w-full px-4 py-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
            <div class="flex justify-end gap-2">
              <button type="button" id="register-cancel" class="px-4 py-2 bg-slate-200 rounded-md hover:bg-slate-300">Cancel</button>
              <button type="submit" id="register-submit" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50">Create Account</button>
            </div>
          </form>
        </div>
        
        <div id="loading-spinner" class="hidden flex justify-center items-center py-4">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span class="ml-2 text-slate-600">Processing...</span>
        </div>

        <div id="error-message" class="hidden mt-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <p class="text-red-700 text-sm"></p>
        </div>

        <div id="success-message" class="hidden mt-4 p-3 bg-green-50 border border-green-200 rounded-md">
          <p class="text-green-700 text-sm"></p>
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(modal);

  // Attach handlers
  setupTabSwitching();
  document.getElementById('login-cancel').addEventListener('click', closeLoginModal);
  document.getElementById('register-cancel').addEventListener('click', closeLoginModal);
  document.getElementById('login-form').addEventListener('submit', submitLoginForm);
  document.getElementById('register-form').addEventListener('submit', submitRegisterForm);
}

function openLoginModal() {
  createLoginModal();
  const modal = document.getElementById('login-modal');
  if (modal) {
    modal.style.display = 'flex';
    document.addEventListener('keydown', handleEscapeKey);
  } else {
    alert('Modal not found!'); // Debug
  }
}

function closeLoginModal() {
  const m = document.getElementById('login-modal');
  if (m) {
    m.style.display = 'none';
    document.removeEventListener('keydown', handleEscapeKey);
  }
}

function handleEscapeKey(e) {
  if (e.key === 'Escape') {
    closeLoginModal();
  }
}

async function submitRegisterForm(e) {
  e.preventDefault();
  const name = document.getElementById('register-name').value;
  const email = document.getElementById('register-email').value;
  const password = document.getElementById('register-password').value;
  const confirmPassword = document.getElementById('register-confirm').value;


  if (password !== confirmPassword) {
    showError('Passwords do not match');
    return;
  }

  if (password.length < 6) {
    showError('Password must be at least 6 characters long');
    return;
  }

  showLoading();
  const submitBtn = document.getElementById('register-submit');
  submitBtn.disabled = true;

  try {
    const res = await fetch(`${AUTH_BASE_URL}/register`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password })
    });

    if (res.ok) {
      showSuccess('Account created successfully! You are now signed in.');
      setTimeout(() => {
        closeLoginModal();
        window.location.reload();
      }, 2000);
    } else {
      const errorData = await res.json().catch(() => ({ detail: 'Registration failed' }));
      showError(errorData.detail || 'Registration failed');
    }
  } catch (err) {
    showError('Network error. Please try again.');
  } finally {
    hideLoading();
    submitBtn.disabled = false;
  }
}

async function submitLoginForm(e) {
  e.preventDefault();
  const email = document.getElementById('login-email').value;
  const password = document.getElementById('login-password').value;

  showLoading();
  const submitBtn = document.getElementById('login-submit');
  submitBtn.disabled = true;

  try {
    const res = await fetch(`${AUTH_BASE_URL}/login`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    if (res.ok) {
      closeLoginModal();
      window.location.reload();
    } else {
      const errorData = await res.json().catch(() => ({ detail: 'Login failed' }));
      showError(errorData.detail || 'Login failed');
    }
  } catch (err) {
    showError('Network error. Please try again.');
  } finally {
    hideLoading();
    submitBtn.disabled = false;
  }
}

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
