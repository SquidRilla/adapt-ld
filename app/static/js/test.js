
let mediaRecorder;
let audioChunks = [];
let theta = 0;
let usedItems = [];
let testCount = 0;
const MAX_ITEMS = 3; // Number of items to assess before scoring

async function startTest() {
  const res = await fetch("/adapt-ld/assessment/start", { method: "POST" });
  const data = await res.json();
  theta = data.theta;
  usedItems = [];
  testCount = 0;
  loadNextItem();
}

async function loadNextItem() {
  const res = await fetch("/adapt-ld/assessment/next-item", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({ theta, used_items: usedItems })
  });
  currentItem = await res.json();
  usedItems.push(currentItem.text);
  document.getElementById("word").textContent = currentItem.text;
  document.getElementById("status").textContent = `Item ${testCount + 1} of ${MAX_ITEMS}`;
}

async function startRecording() {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream);
  mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
  mediaRecorder.onstop = sendAudio;
  mediaRecorder.start();
  document.getElementById("status").textContent = "Listening...";
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
  const updateRes = await fetch("/adapt-ld/assessment/submit-response", {
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
    document.getElementById("status").textContent = "Loading next word...";
    setTimeout(loadNextItem, 1000);
  } else {
    // All items complete, go to result
    window.location = "/result?prediction=" + data.prediction;
  }
}

startTest();
