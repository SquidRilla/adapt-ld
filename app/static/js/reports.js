// Store chart instances
const _reportCharts = {};

function destroyChart(id) {
  try {
    if (_reportCharts[id]) {
      _reportCharts[id].destroy();
      delete _reportCharts[id];
    }
  } catch (e) {
    console.warn('Destroy chart failed', id, e);
  }
}

function updateChart(canvasId, data, label = "Score") {
  const canvas = document.getElementById(canvasId);
  if (!canvas) {
    console.warn(`Canvas ${canvasId} not found`);
    return;
  }

  destroyChart(canvasId);
  const ctx = canvas.getContext('2d');
  
  const labels = data.map((_, i) => `Item ${i + 1}`);
  const colors = data.map(v => v > 70 ? '#22c55e' : v > 40 ? '#eab308' : '#ef4444');

  _reportCharts[canvasId] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label,
        data,
        backgroundColor: colors
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          suggestedMax: 100
        }
      }
    }
  });
}

async function loadReport() {
    try {
        const res = await fetch("/adapt-ld/reports/report");
        if (!res.ok) {
            throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }
        const data = await res.json();

        if (!data || !data.overall_accuracy || !data.overall_avg_time || !data.batch_performance || !data.difficulty_analysis) {
            console.error("Invalid report data structure:", data);
            document.getElementById("accuracy").innerText = "No data";
            document.getElementById("avgTime").innerText = "No data";
            return;
        }

        // Overall stats
        document.getElementById("accuracy").innerText =
            (data.overall_accuracy * 100).toFixed(1) + "%";

        document.getElementById("avgTime").innerText =
            data.overall_avg_time.toFixed(2) + " sec";

        // Batch performance (every 10 tests)
        const batchScores = data.batch_performance.map(b => b.score * 100);
        const batchTimes = data.batch_performance.map(b => b.avg_time);

        updateChart("scoreChart", batchScores, "Score %");
        if (batchTimes.length > 0) {
          updateChart("timeChart", batchTimes, "Avg Time (sec)");
        }

        // Difficulty analysis
        const diff = data.difficulty_analysis;

        let reportText = "";

        for (let level in diff) {
            reportText += `
                <div class="p-4 bg-gray-100 rounded-xl mb-3">
                    <h3 class="font-bold">${level.toUpperCase()}</h3>
                    <p>Accuracy: ${(diff[level].accuracy * 100).toFixed(1)}%</p>
                    <p>Avg Time: ${diff[level].avg_time.toFixed(2)} sec</p>
                </div>
            `;
        }

        document.getElementById("difficultyReport").innerHTML = reportText;

        // Load ML prediction
        await loadMLPrediction();
    } catch (err) {
        console.error("Error loading report:", err);
        document.getElementById("accuracy").innerText = "Error";
        document.getElementById("avgTime").innerText = "Error";
    }
}

loadReport();

async function loadMLPrediction() {
  try {
    const res = await fetch("/adapt-ld/ml/predict-summary");
    if (!res.ok) {
      console.warn("ML prediction not available:", res.status);
      document.getElementById("riskLevel").innerText = "N/A";
      document.getElementById("riskConfidence").innerText = "Confidence: Not available";
      return;
    }

    const data = await res.json();
    const pred = data.prediction;

    // Display risk level with color coding
    const riskLevelEl = document.getElementById("riskLevel");
    const riskConfidenceEl = document.getElementById("riskConfidence");

    const riskLabel = pred.risk_label || "Unknown";
    const confidence = (pred.confidence * 100).toFixed(1);

    riskLevelEl.innerText = riskLabel;

    // Color code by risk level
    if (pred.risk_level === 0) {
      riskLevelEl.className = "text-3xl font-bold text-green-600";
    } else if (pred.risk_level === 1) {
      riskLevelEl.className = "text-3xl font-bold text-yellow-600";
    } else if (pred.risk_level === 2) {
      riskLevelEl.className = "text-3xl font-bold text-orange-600";
    } else {
      riskLevelEl.className = "text-3xl font-bold text-red-600";
    }

    riskConfidenceEl.innerText = `Confidence: ${confidence}%`;
    riskConfidenceEl.innerHTML += `<br/><span class="text-xs text-gray-500 mt-1 block">${pred.interpretation}</span>`;

    console.log("ML Prediction loaded:", pred);
  } catch (err) {
    console.error("Error loading ML prediction:", err);
    document.getElementById("riskLevel").innerText = "Error";
    document.getElementById("riskConfidence").innerText = "Could not load prediction";
  }
}