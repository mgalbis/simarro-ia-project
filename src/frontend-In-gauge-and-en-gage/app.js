const API_BASE = window.API_BASE || "http://localhost:8000";
const fallbackMetadata = {
  model_name: "LogisticRegression",
  input_ranges: {
    IndoorTemperature: { label: "Temperatura interior", unit: "°C", min: 15, max: 35, default: 22, step: 0.1, acceptable: "18–28 °C", description: "Temperatura medida dentro del aula." },
    IndoorHumidity: { label: "Humedad interior", unit: "%", min: 20, max: 90, default: 45, step: 0.5, acceptable: "30–70 %", description: "Humedad relativa interior." },
    IndoorCO2: { label: "CO₂ interior", unit: "ppm", min: 350, max: 2000, default: 700, step: 10, acceptable: "400–1000 ppm", description: "Concentración de CO₂ en el aula." },
    IndoorNoise: { label: "Ruido interior", unit: "dB", min: 25, max: 85, default: 45, step: 1, acceptable: "30–65 dB", description: "Nivel sonoro interior." }
  }
};

let metadata = fallbackMetadata;
const statusEl = document.getElementById("api-status");
const inputsEl = document.getElementById("inputs");
const form = document.getElementById("predict-form");
const predictionBox = document.getElementById("prediction-box");
const room = document.getElementById("room");

function renderInputs() {
  inputsEl.innerHTML = "";
  Object.entries(metadata.input_ranges).forEach(([key, cfg]) => {
    const card = document.createElement("div");
    card.className = "input-card";
    card.innerHTML = `
      <div class="input-head">
        <strong>${cfg.label}</strong>
        <span class="value" id="value-${key}">${cfg.default} ${cfg.unit}</span>
      </div>
      <input name="${key}" type="range" min="${cfg.min}" max="${cfg.max}" step="${cfg.step}" value="${cfg.default}" />
      <small>${cfg.description}</small>
      <small class="acceptable">Rango aceptable orientativo: ${cfg.acceptable}</small>
    `;
    const input = card.querySelector("input");
    input.addEventListener("input", () => {
      document.getElementById(`value-${key}`).textContent = `${input.value} ${cfg.unit}`;
    });
    inputsEl.appendChild(card);
  });
}

async function loadMetadata() {
  try {
    const res = await fetch(`${API_BASE}/metadata`);
    if (!res.ok) throw new Error("metadata no disponible");
    metadata = await res.json();
    statusEl.textContent = `API conectada · ${metadata.model_name}`;
    statusEl.className = "status ok";
  } catch (err) {
    statusEl.textContent = "API no disponible · usando formulario local";
    statusEl.className = "status error";
  }
  renderInputs();
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = form.querySelector("button");
  button.disabled = true;
  button.textContent = "Prediciendo...";

  const payload = {};
  new FormData(form).forEach((value, key) => payload[key] = Number(value));

  try {
    const res = await fetch(`${API_BASE}/predict`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Error en predicción");
    }
    const data = await res.json();
    const pct = data.probability_occupied !== null ? `${(data.probability_occupied * 100).toFixed(1)}%` : "no disponible";
    predictionBox.innerHTML = `
      <h2>${data.prediction_label}</h2>
      <p>${data.interpretation}</p>
      <p><strong>Probabilidad de ocupación:</strong> ${pct}</p>
    `;
    room.classList.toggle("occupied", data.prediction === 1);
  } catch (err) {
    predictionBox.innerHTML = `<h2>Error</h2><p>${err.message}</p>`;
  } finally {
    button.disabled = false;
    button.textContent = "Predecir ocupación";
  }
});

loadMetadata();
