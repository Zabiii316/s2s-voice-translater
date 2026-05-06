const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const speakBtn = document.getElementById("speakBtn");
const translateBtn = document.getElementById("translateBtn");
const clearBtn = document.getElementById("clearBtn");

const pathwayABtn = document.getElementById("pathwayABtn");
const pathwayBBtn = document.getElementById("pathwayBBtn");
const activePathwayLabel = document.getElementById("activePathwayLabel");

const originalText = document.getElementById("originalText");
const translatedText = document.getElementById("translatedText");
const statusText = document.getElementById("status");

const sourceLanguage = document.getElementById("sourceLanguage");
const targetLanguage = document.getElementById("targetLanguage");
const subtitle = document.getElementById("subtitle");

const conversationHistory = document.getElementById("conversationHistory");
const turnCount = document.getElementById("turnCount");

const sourceMetric = document.getElementById("sourceMetric");
const targetMetric = document.getElementById("targetMetric");
const pathwayMetric = document.getElementById("pathwayMetric");
const totalTurnsMetric = document.getElementById("totalTurnsMetric");

const statusPill = document.getElementById("statusPill");
const voiceOrb = document.getElementById("voiceOrb");
const orbLabel = document.getElementById("orbLabel");

const inputPanelTag = document.getElementById("inputPanelTag");
const inputPanelTitle = document.getElementById("inputPanelTitle");
const outputPanelTag = document.getElementById("outputPanelTag");
const outputPanelTitle = document.getElementById("outputPanelTitle");

const callTimer = document.getElementById("callTimer");
const translationLatency = document.getElementById("translationLatency");
const ttsLatency = document.getElementById("ttsLatency");
const totalLatency = document.getElementById("totalLatency");
const confidenceScore = document.getElementById("confidenceScore");
const confidenceFill = document.getElementById("confidenceFill");

let recognition;
let totalTurns = 0;
let activePathway = "A";

let callStartTime = null;
let callTimerInterval = null;

const SpeechRecognition =
  window.SpeechRecognition || window.webkitSpeechRecognition;

const pathwayConfig = {
  A: {
    label: "Pathway A Active",
    metric: "A",
    subtitle: "Pathway A: Client → Representative | Arabic → Urdu",
    speaker: "Client",
    destination: "Representative",
    source: "Arabic",
    target: "Urdu",
    inputTag: "Client Input Stream",
    inputTitle: "Client Speech",
    outputTag: "Representative Output Stream",
    outputTitle: "Translation for Representative"
  },
  B: {
    label: "Pathway B Active",
    metric: "B",
    subtitle: "Pathway B: Representative → Client | English/Urdu → Arabic",
    speaker: "Representative",
    destination: "Client",
    source: "English",
    target: "Arabic",
    inputTag: "Representative Input Stream",
    inputTitle: "Representative Speech",
    outputTag: "Client Output Stream",
    outputTitle: "Translation for Client"
  }
};

function setPathway(pathway) {
  activePathway = pathway;
  const config = pathwayConfig[pathway];

  sourceLanguage.value = config.source;
  targetLanguage.value = config.target;

  pathwayABtn.classList.toggle("active", pathway === "A");
  pathwayBBtn.classList.toggle("active", pathway === "B");

  activePathwayLabel.innerText = config.label;
  pathwayMetric.innerText = config.metric;

  inputPanelTag.innerText = config.inputTag;
  inputPanelTitle.innerText = config.inputTitle;
  outputPanelTag.innerText = config.outputTag;
  outputPanelTitle.innerText = config.outputTitle;

  originalText.value = "";
  translatedText.value = "";

  updateSubtitle();
  setSystemStatus(`${config.label} selected`, "ready");
}

function updateSubtitle() {
  const config = pathwayConfig[activePathway];

  subtitle.innerText = `${config.subtitle} | Current: ${sourceLanguage.value} → ${targetLanguage.value}`;
  sourceMetric.innerText = sourceLanguage.value;
  targetMetric.innerText = targetLanguage.value;
}

function setSystemStatus(message, type = "ready") {
  statusText.innerText = message;

  statusPill.className = "status-pill";
  statusPill.classList.add(`status-${type}`);

  if (type === "listening" || type === "translating" || type === "speaking") {
    voiceOrb.classList.add("active");
  } else {
    voiceOrb.classList.remove("active");
  }

  if (type === "listening") {
    orbLabel.innerText = "Listening for speech...";
  } else if (type === "translating") {
    orbLabel.innerText = "Translating in real time...";
  } else if (type === "speaking") {
    orbLabel.innerText = "Playing translated audio...";
  } else if (type === "error") {
    orbLabel.innerText = "System encountered an error";
  } else {
    orbLabel.innerText = "System Ready";
  }
}

function startCallTimer() {
  if (callTimerInterval) return;

  callStartTime = Date.now();

  callTimerInterval = setInterval(() => {
    const elapsedSeconds = Math.floor((Date.now() - callStartTime) / 1000);
    const minutes = String(Math.floor(elapsedSeconds / 60)).padStart(2, "0");
    const seconds = String(elapsedSeconds % 60).padStart(2, "0");

    callTimer.innerText = `${minutes}:${seconds}`;
  }, 1000);
}

function stopCallTimer() {
  if (callTimerInterval) {
    clearInterval(callTimerInterval);
    callTimerInterval = null;
  }
}

function resetPerformanceMetrics() {
  translationLatency.innerText = "0 ms";
  ttsLatency.innerText = "0 ms";
  totalLatency.innerText = "0 ms";
  confidenceScore.innerText = "0%";
  confidenceFill.style.width = "0%";
}

function updatePerformanceMetrics(metrics) {
  translationLatency.innerText = `${metrics.translationLatencyMs} ms`;
  ttsLatency.innerText = `${metrics.ttsLatencyMs} ms`;
  totalLatency.innerText = `${metrics.totalLatencyMs} ms`;
  confidenceScore.innerText = `${metrics.confidence}%`;
  confidenceFill.style.width = `${metrics.confidence}%`;
}

function calculateConfidence(original, translation, sourceLang, targetLang) {
  if (!translation || translation.trim() === "") return 0;

  const lowerTranslation = translation.toLowerCase();

  if (
    lowerTranslation.includes("[demo") ||
    lowerTranslation.includes("[mock") ||
    lowerTranslation.includes("translation]")
  ) {
    return 58;
  }

  let score = 94;

  if (sourceLang === "Arabic" || sourceLang === "Urdu") {
    score -= 4;
  }

  if (original.length < 6) {
    score -= 6;
  }

  if (translation.length < 4) {
    score -= 8;
  }

  return Math.max(65, Math.min(score, 97));
}

sourceLanguage.onchange = updateSubtitle;
targetLanguage.onchange = updateSubtitle;

pathwayABtn.onclick = () => setPathway("A");
pathwayBBtn.onclick = () => setPathway("B");

function escapeHtml(text) {
  const div = document.createElement("div");
  div.innerText = text;
  return div.innerHTML;
}

function addConversationEntry(original, translation, sourceLang, targetLang, metrics) {
  const config = pathwayConfig[activePathway];

  const emptyHistory = document.querySelector(".empty-history");
  if (emptyHistory) {
    emptyHistory.remove();
  }

  totalTurns += 1;
  turnCount.innerText = `${totalTurns} turn${totalTurns > 1 ? "s" : ""}`;
  totalTurnsMetric.innerText = totalTurns;

  const item = document.createElement("div");
  item.className = "history-item";

  const time = new Date().toLocaleTimeString();

  item.innerHTML = `
    <div class="history-top">
      <div class="history-meta-row">
        <span>Turn ${totalTurns} • ${time}</span>
        <span class="language-badge">Pathway ${activePathway}</span>
        <span class="language-badge">${sourceLang} → ${targetLang}</span>
      </div>

      <div class="history-meta-row">
        <span class="speaker-badge">${config.speaker} Said</span>
        <span class="destination-badge">For ${config.destination}</span>
        <span class="latency-badge">Total ${metrics.totalLatencyMs} ms</span>
        <span class="confidence-badge">Confidence ${metrics.confidence}%</span>
      </div>
    </div>

    <div class="history-label">${config.speaker} Original</div>
    <div class="history-original">${escapeHtml(original)}</div>

    <div class="history-label">AI Translation for ${config.destination}</div>
    <div class="history-translation">${escapeHtml(translation)}</div>
  `;

  conversationHistory.prepend(item);
}

async function speakTranslation(text) {
  if (!text || text.trim() === "") {
    alert("No translation available to speak.");
    return { ttsLatencyMs: 0 };
  }

  const ttsStart = performance.now();

  try {
    setSystemStatus("Generating voice...", "speaking");

    const response = await fetch("http://127.0.0.1:8000/tts", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text: text,
        language: targetLanguage.value,
      }),
    });

    if (!response.ok) {
      throw new Error("TTS backend error: " + response.status);
    }

    const audioBlob = await response.blob();
    const ttsLatencyMs = Math.round(performance.now() - ttsStart);

    const audioUrl = URL.createObjectURL(audioBlob);
    const audio = new Audio(audioUrl);

    audio.onplay = () => {
      setSystemStatus("Playing translated voice...", "speaking");
    };

    audio.onended = () => {
      setSystemStatus("Finished speaking", "ready");
      URL.revokeObjectURL(audioUrl);
    };

    audio.onerror = () => {
      setSystemStatus("Audio playback error", "error");
    };

    await audio.play();

    return { ttsLatencyMs };
  } catch (error) {
    console.error("TTS error:", error);
    setSystemStatus("TTS error", "error");
    alert("TTS error. Check backend terminal.");
    return { ttsLatencyMs: Math.round(performance.now() - ttsStart) };
  }
}

async function translateText(text, autoSpeak = false) {
  startCallTimer();

  const turnStart = performance.now();

  setSystemStatus("Translating...", "translating");

  try {
    const translationStart = performance.now();

    const response = await fetch("http://127.0.0.1:8000/translate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text: text,
        source_language: sourceLanguage.value,
        target_language: targetLanguage.value,
      }),
    });

    const translationLatencyMs = Math.round(performance.now() - translationStart);

    if (!response.ok) {
      throw new Error("Backend error: " + response.status);
    }

    const data = await response.json();

    translatedText.value = data.translated_text;
    setSystemStatus("Translation complete", "ready");

    let ttsResult = { ttsLatencyMs: 0 };

    if (autoSpeak) {
      ttsResult = await speakTranslation(data.translated_text);
    }

    const totalLatencyMs = Math.round(performance.now() - turnStart);

    const confidence = calculateConfidence(
      data.original_text,
      data.translated_text,
      data.source_language,
      data.target_language
    );

    const metrics = {
      translationLatencyMs,
      ttsLatencyMs: ttsResult.ttsLatencyMs,
      totalLatencyMs,
      confidence
    };

    updatePerformanceMetrics(metrics);

    addConversationEntry(
      data.original_text,
      data.translated_text,
      data.source_language,
      data.target_language,
      metrics
    );
  } catch (error) {
    console.error("Translation error:", error);
    setSystemStatus("Translation error", "error");
    alert("Translation error. Check backend server.");
  }
}

if (!SpeechRecognition) {
  setSystemStatus("Speech Recognition not supported. Use Chrome.", "error");
} else {
  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = true;
  recognition.lang = "ar-SA";

  recognition.onstart = () => {
    startCallTimer();
    setSystemStatus("Listening...", "listening");
  };

  recognition.onresult = async (event) => {
    let finalTranscript = "";
    let interimTranscript = "";

    for (let i = event.resultIndex; i < event.results.length; i++) {
      const transcript = event.results[i][0].transcript;

      if (event.results[i].isFinal) {
        finalTranscript += transcript;
      } else {
        interimTranscript += transcript;
      }
    }

    originalText.value = finalTranscript || interimTranscript;

    if (finalTranscript) {
      await translateText(finalTranscript, true);
    }
  };

  recognition.onerror = (event) => {
    console.error("Recognition error:", event);
    setSystemStatus(`Recognition error - ${event.error}`, "error");
  };

  recognition.onend = () => {
    if (
      !statusText.innerText.includes("Translating") &&
      !statusText.innerText.includes("Generating") &&
      !statusText.innerText.includes("Playing")
    ) {
      setSystemStatus("Stopped", "ready");
    }
  };
}

function setRecognitionLanguage() {
  if (!recognition) return;

  if (sourceLanguage.value === "English") {
    recognition.lang = "en-US";
  } else if (sourceLanguage.value === "Arabic") {
    recognition.lang = "ar-SA";
  } else if (sourceLanguage.value === "Urdu") {
    recognition.lang = "ur-PK";
  }
}

startBtn.onclick = () => {
  if (!recognition) {
    alert("Speech recognition not supported. Please use Google Chrome.");
    return;
  }

  startCallTimer();
  setRecognitionLanguage();

  originalText.value = "";
  translatedText.value = "";
  setSystemStatus("Starting microphone...", "listening");

  recognition.start();
};

stopBtn.onclick = () => {
  if (recognition) {
    recognition.stop();
  }

  stopCallTimer();
  setSystemStatus("Stopped", "ready");
};

translateBtn.onclick = async () => {
  const text = originalText.value.trim();

  if (!text) {
    alert("Please type or speak text first.");
    return;
  }

  await translateText(text, true);
};

speakBtn.onclick = async () => {
  const text = translatedText.value.trim();

  if (!text) {
    alert("No translated text found.");
    return;
  }

  const result = await speakTranslation(text);

  ttsLatency.innerText = `${result.ttsLatencyMs} ms`;
};

clearBtn.onclick = () => {
  totalTurns = 0;
  turnCount.innerText = "0 turns";
  totalTurnsMetric.innerText = "0";

  stopCallTimer();
  callStartTime = null;
  callTimer.innerText = "00:00";

  resetPerformanceMetrics();

  conversationHistory.innerHTML = `
    <div class="empty-history">
      <div class="empty-icon">◌</div>
      <p>No conversation yet. Start speaking to populate the live transcript history.</p>
    </div>
  `;

  originalText.value = "";
  translatedText.value = "";
  setSystemStatus("History cleared", "ready");
};

setPathway("A");
setSystemStatus("Ready", "ready");
resetPerformanceMetrics();