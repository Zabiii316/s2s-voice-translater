"use strict";

const API_BASE_URL = "http://127.0.0.1:8000";

const SILENCE_TIMEOUT_MS = 2200;
const RESTART_DELAY_MS = 450;
const REQUEST_TIMEOUT_MS = 45000;
const MIN_TRANSLATE_CHARS = 2;

const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const speakBtn = document.getElementById("speakBtn");
const translateBtn = document.getElementById("translateBtn");
const clearBtn = document.getElementById("clearBtn");
const exportTxtBtn = document.getElementById("exportTxtBtn");
const exportJsonBtn = document.getElementById("exportJsonBtn");

const pathwayABtn = document.getElementById("pathwayABtn");
const pathwayBBtn = document.getElementById("pathwayBBtn");
const activePathwayLabel = document.getElementById(
  "activePathwayLabel"
);

const originalText = document.getElementById("originalText");
const translatedText = document.getElementById(
  "translatedText"
);

const statusText = document.getElementById("status");

const sourceLanguage = document.getElementById(
  "sourceLanguage"
);

const targetLanguage = document.getElementById(
  "targetLanguage"
);

const arabicDialect = document.getElementById(
  "arabicDialect"
);

const speakerRole = document.getElementById(
  "speakerRole"
);

const subtitle = document.getElementById("subtitle");

const conversationHistory = document.getElementById(
  "conversationHistory"
);

const turnCount = document.getElementById("turnCount");

const sourceMetric = document.getElementById(
  "sourceMetric"
);

const targetMetric = document.getElementById(
  "targetMetric"
);

const pathwayMetric = document.getElementById(
  "pathwayMetric"
);

const dialectMetric = document.getElementById(
  "dialectMetric"
);

const statusPill = document.getElementById(
  "statusPill"
);

const voiceOrb = document.getElementById("voiceOrb");
const orbLabel = document.getElementById("orbLabel");

const inputPanelTag = document.getElementById(
  "inputPanelTag"
);

const inputPanelTitle = document.getElementById(
  "inputPanelTitle"
);

const outputPanelTag = document.getElementById(
  "outputPanelTag"
);

const outputPanelTitle = document.getElementById(
  "outputPanelTitle"
);

const callTimer = document.getElementById("callTimer");

const translationLatency = document.getElementById(
  "translationLatency"
);

const ttsLatency = document.getElementById(
  "ttsLatency"
);

const totalLatency = document.getElementById(
  "totalLatency"
);

const confidenceScore = document.getElementById(
  "confidenceScore"
);

const confidenceFill = document.getElementById(
  "confidenceFill"
);

const piiStatus = document.getElementById(
  "piiStatus"
);

const piiTypes = document.getElementById("piiTypes");


const SpeechRecognition =
  window.SpeechRecognition ||
  window.webkitSpeechRecognition;


let recognition = null;

let sessionActive = false;
let recognitionRunning = false;
let manualStopRequested = false;
let pendingUtteranceFlush = false;
let busy = false;

let silenceTimer = null;
let restartTimer = null;

let finalBuffer = "";
let interimBuffer = "";
let lastTranslatedText = "";

let currentAudio = null;

let totalTurns = 0;
let activePathway = "A";
let sessionEntries = [];

let callStartTime = null;
let callTimerInterval = null;


const sessionId =
  `s2s-session-${
    new Date()
      .toISOString()
      .replace(/[:.]/g, "-")
  }`;


const pathwayConfig = {
  A: {
    label: "Pathway A Active",
    metric: "A",
    subtitle:
      "Pathway A: Client → Representative | Arabic → Urdu",
    speaker: "Client",
    destination: "Representative",
    source: "Arabic",
    target: "Urdu",
    dialect: "Gulf Arabic",
    inputTag: "Client Input Stream",
    inputTitle: "Client Speech",
    outputTag: "Representative Output Stream",
    outputTitle: "Translation for Representative"
  },

  B: {
    label: "Pathway B Active",
    metric: "B",
    subtitle:
      "Pathway B: Representative → Client | English/Urdu → Arabic",
    speaker: "Representative",
    destination: "Client",
    source: "English",
    target: "Arabic",
    dialect: "MSA",
    inputTag: "Representative Input Stream",
    inputTitle: "Representative Speech",
    outputTag: "Client Output Stream",
    outputTitle: "Translation for Client"
  }
};


function compactWhitespace(value) {
  return (value || "")
    .replace(/\s+/g, " ")
    .trim();
}


function appendTranscript(base, addition) {
  const cleanBase = compactWhitespace(base);
  const cleanAddition = compactWhitespace(addition);

  if (!cleanAddition) {
    return cleanBase;
  }

  if (!cleanBase) {
    return cleanAddition;
  }

  if (cleanBase.endsWith(cleanAddition)) {
    return cleanBase;
  }

  return `${cleanBase} ${cleanAddition}`;
}


function shortDialectName(value) {
  if (value === "Gulf Arabic") {
    return "Gulf";
  }

  if (value === "Egyptian Arabic") {
    return "Egyptian";
  }

  if (value === "Levantine Arabic") {
    return "Levantine";
  }

  return "MSA";
}


function isArabicInvolved() {
  return (
    sourceLanguage.value === "Arabic" ||
    targetLanguage.value === "Arabic"
  );
}


function updateDialectAvailability() {
  const enabled = isArabicInvolved();

  arabicDialect.disabled = !enabled;

  dialectMetric.innerText = enabled
    ? shortDialectName(arabicDialect.value)
    : "N/A";
}


function getCurrentSpeaker() {
  if (speakerRole.value === "Auto") {
    return pathwayConfig[
      activePathway
    ].speaker;
  }

  return speakerRole.value;
}


function getCurrentDestination() {
  const speaker = getCurrentSpeaker();

  if (speaker === "Client") {
    return "Representative";
  }

  if (speaker === "Representative") {
    return "Client";
  }

  return pathwayConfig[
    activePathway
  ].destination;
}


function setSystemStatus(
  message,
  type = "ready"
) {
  statusText.innerText = message;

  statusPill.className =
    `status-pill status-${type}`;

  if (
    type === "listening" ||
    type === "translating" ||
    type === "speaking"
  ) {
    voiceOrb.classList.add("active");
  } else {
    voiceOrb.classList.remove("active");
  }

  const orbMessages = {
    ready: "System Ready",

    listening:
      "Listening for the complete sentence...",

    translating:
      "Translating the complete utterance...",

    speaking:
      "Playing translated audio...",

    error:
      "System encountered an error"
  };

  orbLabel.innerText =
    orbMessages[type] || message;
}


function updateSubtitle() {
  const config =
    pathwayConfig[activePathway];

  subtitle.innerText =
    `${config.subtitle} | ` +
    `Current: ${sourceLanguage.value} → ` +
    `${targetLanguage.value} | ` +
    `Dialect: ${
      shortDialectName(
        arabicDialect.value
      )
    }`;

  sourceMetric.innerText =
    sourceLanguage.value;

  targetMetric.innerText =
    targetLanguage.value;

  updateDialectAvailability();
  setRecognitionLanguage();
}


function setPathway(pathway) {
  stopVoiceSession(false);

  activePathway = pathway;

  const config =
    pathwayConfig[pathway];

  sourceLanguage.value =
    config.source;

  targetLanguage.value =
    config.target;

  arabicDialect.value =
    config.dialect;

  speakerRole.value = "Auto";

  pathwayABtn.classList.toggle(
    "active",
    pathway === "A"
  );

  pathwayBBtn.classList.toggle(
    "active",
    pathway === "B"
  );

  activePathwayLabel.innerText =
    config.label;

  pathwayMetric.innerText =
    config.metric;

  inputPanelTag.innerText =
    config.inputTag;

  inputPanelTitle.innerText =
    config.inputTitle;

  outputPanelTag.innerText =
    config.outputTag;

  outputPanelTitle.innerText =
    config.outputTitle;

  resetUtteranceBuffers();

  originalText.value = "";
  translatedText.value = "";

  updateSubtitle();

  setSystemStatus(
    `${config.label} selected`,
    "ready"
  );
}


function startCallTimer() {
  if (callTimerInterval) {
    return;
  }

  callStartTime = Date.now();

  callTimerInterval =
    window.setInterval(() => {
      const elapsed =
        Math.floor(
          (
            Date.now() -
            callStartTime
          ) / 1000
        );

      const minutes =
        String(
          Math.floor(elapsed / 60)
        ).padStart(2, "0");

      const seconds =
        String(
          elapsed % 60
        ).padStart(2, "0");

      callTimer.innerText =
        `${minutes}:${seconds}`;
    }, 1000);
}


function stopCallTimer() {
  if (callTimerInterval) {
    window.clearInterval(
      callTimerInterval
    );
  }

  callTimerInterval = null;
}


function resetPerformanceMetrics() {
  translationLatency.innerText = "0 ms";
  ttsLatency.innerText = "0 ms";
  totalLatency.innerText = "0 ms";

  confidenceScore.innerText = "0%";
  confidenceFill.style.width = "0%";

  piiStatus.innerText = "Clear";

  piiStatus.className =
    "performance-value pii-safe";

  piiTypes.innerText =
    "No sensitive data detected";
}


function updatePIIStatus(
  found,
  detected
) {
  piiStatus.innerText =
    found ? "Detected" : "Clear";

  piiStatus.className =
    `performance-value ${
      found
        ? "pii-warning"
        : "pii-safe"
    }`;

  piiTypes.innerText =
    found
      ? (detected || []).join(", ")
      : "No sensitive data detected";
}


function updatePerformanceMetrics(
  metrics
) {
  translationLatency.innerText =
    `${metrics.translationLatencyMs} ms`;

  ttsLatency.innerText =
    `${metrics.ttsLatencyMs} ms`;

  totalLatency.innerText =
    `${metrics.totalLatencyMs} ms`;

  confidenceScore.innerText =
    `${metrics.confidence}%`;

  confidenceFill.style.width =
    `${metrics.confidence}%`;
}


function calculateConfidence(
  original,
  translation,
  provider,
  piiFound
) {
  if (!compactWhitespace(translation)) {
    return 0;
  }

  let score =
    provider === "openai"
      ? 95
      : 82;

  if (
    provider ===
    "offline_phrasebook_partial"
  ) {
    score = 45;
  }

  if (piiFound) {
    score -= 4;
  }

  if ((original || "").length < 5) {
    score -= 5;
  }

  return Math.max(
    35,
    Math.min(score, 98)
  );
}


function escapeHtml(value) {
  const div =
    document.createElement("div");

  div.innerText = value || "";

  return div.innerHTML;
}


function addConversationEntry(
  data,
  metrics
) {
  const emptyHistory =
    document.querySelector(
      ".empty-history"
    );

  if (emptyHistory) {
    emptyHistory.remove();
  }

  totalTurns += 1;

  turnCount.innerText =
    `${totalTurns} turn${
      totalTurns === 1
        ? ""
        : "s"
    }`;

  const speaker =
    getCurrentSpeaker();

  const destination =
    getCurrentDestination();

  const time =
    new Date().toLocaleTimeString();

  const entry = {
    session_id: sessionId,
    turn: totalTurns,
    timestamp:
      new Date().toISOString(),
    display_time: time,
    pathway: activePathway,
    speaker,
    destination,

    source_language:
      data.source_language,

    target_language:
      data.target_language,

    arabic_dialect:
      data.arabic_dialect,

    original_text:
      data.original_text,

    masked_text:
      data.masked_text,

    translated_text:
      data.translated_text,

    pii_found:
      data.pii_found,

    detected_pii:
      data.detected_pii || [],

    provider:
      data.provider,

    metrics
  };

  sessionEntries.push(entry);

  const item =
    document.createElement("div");

  item.className = "history-item";

  item.innerHTML = `
    <div class="history-top">

      <div class="history-meta-row">
        <span>
          Turn ${totalTurns} • ${time}
        </span>

        <span class="language-badge">
          Pathway ${activePathway}
        </span>

        <span class="language-badge">
          ${escapeHtml(data.source_language)}
          →
          ${escapeHtml(data.target_language)}
        </span>

        <span class="dialect-badge">
          ${escapeHtml(data.arabic_dialect)}
        </span>
      </div>

      <div class="history-meta-row">
        <span class="speaker-badge">
          ${escapeHtml(speaker)} Said
        </span>

        <span class="destination-badge">
          For ${escapeHtml(destination)}
        </span>

        <span class="latency-badge">
          ${metrics.totalLatencyMs} ms
        </span>

        <span class="confidence-badge">
          ${metrics.confidence}%
        </span>
      </div>
    </div>

    <div class="history-label">
      Original
    </div>

    <div class="history-original">
      ${escapeHtml(data.original_text)}
    </div>

    <div class="history-label">
      Translation
      (${escapeHtml(
        data.provider || "unknown"
      )})
    </div>

    <div class="history-translation">
      ${escapeHtml(data.translated_text)}
    </div>
  `;

  conversationHistory.prepend(item);
}


async function fetchWithTimeout(
  url,
  options,
  timeoutMs = REQUEST_TIMEOUT_MS
) {
  const controller =
    new AbortController();

  const timeoutId =
    window.setTimeout(
      () => controller.abort(),
      timeoutMs
    );

  try {
    return await fetch(
      url,
      {
        ...options,
        signal: controller.signal
      }
    );
  } finally {
    window.clearTimeout(timeoutId);
  }
}


async function readErrorResponse(
  response
) {
  try {
    const payload =
      await response.json();

    return (
      payload.detail ||
      JSON.stringify(payload)
    );
  } catch (_) {
    return await response.text();
  }
}


async function speakTranslation(text) {
  const cleanText =
    compactWhitespace(text);

  if (!cleanText) {
    return {
      ttsLatencyMs: 0
    };
  }

  if (
    cleanText.includes(
      "[Offline phrase not found"
    )
  ) {
    return {
      ttsLatencyMs: 0
    };
  }

  const started =
    performance.now();

  setSystemStatus(
    "Generating translated voice...",
    "speaking"
  );

  try {
    const response =
      await fetchWithTimeout(
        `${API_BASE_URL}/tts`,
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json"
          },

          body: JSON.stringify({
            text: cleanText,
            language:
              targetLanguage.value
          })
        }
      );

    if (!response.ok) {
      throw new Error(
        await readErrorResponse(
          response
        )
      );
    }

    const audioBlob =
      await response.blob();

    const audioUrl =
      URL.createObjectURL(
        audioBlob
      );

    if (currentAudio) {
      currentAudio.pause();
      currentAudio = null;
    }

    return await new Promise(
      (resolve, reject) => {
        const audio =
          new Audio(audioUrl);

        currentAudio = audio;

        let settled = false;

        const finish = (
          error = null
        ) => {
          if (settled) {
            return;
          }

          settled = true;

          URL.revokeObjectURL(
            audioUrl
          );

          currentAudio = null;

          const result = {
            ttsLatencyMs:
              Math.round(
                performance.now() -
                started
              )
          };

          if (error) {
            reject(error);
          } else {
            resolve(result);
          }
        };

        audio.onplay = () => {
          setSystemStatus(
            "Playing translated voice...",
            "speaking"
          );
        };

        audio.onended = () => {
          finish();
        };

        audio.onerror = () => {
          finish(
            new Error(
              "Audio playback failed"
            )
          );
        };

        audio
          .play()
          .catch(
            error => finish(error)
          );
      }
    );

  } catch (error) {
    console.error(
      "TTS error:",
      error
    );

    setSystemStatus(
      `TTS error: ${error.message}`,
      "error"
    );

    return {
      ttsLatencyMs:
        Math.round(
          performance.now() -
          started
        )
    };
  }
}


async function translateText(
  text,
  autoSpeak = false
) {
  const cleanText =
    compactWhitespace(text);

  if (
    cleanText.length <
    MIN_TRANSLATE_CHARS
  ) {
    return null;
  }

  if (busy) {
    return null;
  }

  if (
    cleanText ===
    lastTranslatedText
  ) {
    return null;
  }

  busy = true;

  lastTranslatedText =
    cleanText;

  const turnStarted =
    performance.now();

  setSystemStatus(
    "Translating complete sentence...",
    "translating"
  );

  try {
    const translationStarted =
      performance.now();

    const response =
      await fetchWithTimeout(
        `${API_BASE_URL}/translate`,
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json"
          },

          body: JSON.stringify({
            text: cleanText,

            source_language:
              sourceLanguage.value,

            target_language:
              targetLanguage.value,

            arabic_dialect:
              arabicDialect.value,

            speaker_role:
              getCurrentSpeaker(),

            pathway:
              activePathway
          })
        }
      );

    if (!response.ok) {
      throw new Error(
        await readErrorResponse(
          response
        )
      );
    }

    const data =
      await response.json();

    const translationLatencyMs =
      data.translation_latency_ms ??
      Math.round(
        performance.now() -
        translationStarted
      );

    translatedText.value =
      data.translated_text;

    updatePIIStatus(
      data.pii_found,
      data.detected_pii
    );

    let ttsResult = {
      ttsLatencyMs: 0
    };

    const isFullyTranslated =
      data.provider !==
      "offline_phrasebook_partial";

    if (
      autoSpeak &&
      isFullyTranslated
    ) {
      ttsResult =
        await speakTranslation(
          data.translated_text
        );
    }

    const metrics = {
      translationLatencyMs,

      ttsLatencyMs:
        ttsResult.ttsLatencyMs,

      totalLatencyMs:
        Math.round(
          performance.now() -
          turnStarted
        ),

      confidence:
        calculateConfidence(
          data.original_text,
          data.translated_text,
          data.provider,
          data.pii_found
        )
    };

    updatePerformanceMetrics(
      metrics
    );

    addConversationEntry(
      data,
      metrics
    );

    setSystemStatus(
      "Translation complete",
      "ready"
    );

    return data;

  } catch (error) {
    console.error(
      "Translation error:",
      error
    );

    lastTranslatedText = "";

    setSystemStatus(
      `Translation error: ${
        error.message
      }`,
      "error"
    );

    return null;

  } finally {
    busy = false;
  }
}


function clearTimers() {
  if (silenceTimer) {
    window.clearTimeout(
      silenceTimer
    );
  }

  if (restartTimer) {
    window.clearTimeout(
      restartTimer
    );
  }

  silenceTimer = null;
  restartTimer = null;
}


function resetUtteranceBuffers() {
  finalBuffer = "";
  interimBuffer = "";

  pendingUtteranceFlush = false;

  if (silenceTimer) {
    window.clearTimeout(
      silenceTimer
    );
  }

  silenceTimer = null;
}


function setRecognitionLanguage() {
  if (!recognition) {
    return;
  }

  const languageCodes = {
    English: "en-US",
    Urdu: "ur-PK",
    Arabic: "ar-SA"
  };

  recognition.lang =
    languageCodes[
      sourceLanguage.value
    ] || "en-US";
}


function scheduleSilenceFlush() {
  if (silenceTimer) {
    window.clearTimeout(
      silenceTimer
    );
  }

  silenceTimer =
    window.setTimeout(() => {
      if (
        !sessionActive ||
        busy
      ) {
        return;
      }

      pendingUtteranceFlush = true;

      setSystemStatus(
        "End of sentence detected...",
        "translating"
      );

      if (recognitionRunning) {
        try {
          recognition.stop();
        } catch (error) {
          console.warn(
            "Recognition stop warning:",
            error
          );

          recognitionRunning =
            false;

          void flushCurrentUtterance();
        }
      } else {
        void flushCurrentUtterance();
      }
    }, SILENCE_TIMEOUT_MS);
}


async function flushCurrentUtterance() {
  const utterance =
    compactWhitespace(
      finalBuffer ||
      interimBuffer ||
      originalText.value
    );

  resetUtteranceBuffers();

  if (
    utterance.length <
    MIN_TRANSLATE_CHARS
  ) {
    scheduleRecognitionRestart();
    return;
  }

  originalText.value =
    utterance;

  await translateText(
    utterance,
    true
  );

  scheduleRecognitionRestart();
}


function scheduleRecognitionRestart() {
  if (
    !sessionActive ||
    manualStopRequested ||
    busy ||
    currentAudio
  ) {
    return;
  }

  if (restartTimer) {
    window.clearTimeout(
      restartTimer
    );
  }

  restartTimer =
    window.setTimeout(() => {
      startRecognitionEngine();
    }, RESTART_DELAY_MS);
}


function startRecognitionEngine() {
  if (
    !recognition ||
    !sessionActive ||
    recognitionRunning ||
    busy ||
    currentAudio
  ) {
    return;
  }

  setRecognitionLanguage();

  try {
    recognition.start();
  } catch (error) {
    if (
      error.name !==
      "InvalidStateError"
    ) {
      console.error(
        "Could not start recognition:",
        error
      );

      setSystemStatus(
        "Could not start microphone",
        "error"
      );
    }
  }
}


function stopVoiceSession(
  updateStatus = true
) {
  sessionActive = false;
  manualStopRequested = true;

  clearTimers();

  if (
    recognitionRunning &&
    recognition
  ) {
    try {
      recognition.stop();
    } catch (_) {
      // Already stopped.
    }
  }

  if (currentAudio) {
    currentAudio.pause();
    currentAudio = null;
  }

  recognitionRunning = false;

  resetUtteranceBuffers();
  stopCallTimer();

  if (updateStatus) {
    setSystemStatus(
      "Stopped",
      "ready"
    );
  }
}


function initializeSpeechRecognition() {
  if (!SpeechRecognition) {
    setSystemStatus(
      "Speech Recognition is not supported. Use Google Chrome.",
      "error"
    );

    startBtn.disabled = true;
    return;
  }

  recognition =
    new SpeechRecognition();

  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.maxAlternatives = 1;

  setRecognitionLanguage();

  recognition.onstart = () => {
    recognitionRunning = true;

    if (sessionActive) {
      setSystemStatus(
        "Listening...",
        "listening"
      );
    }
  };


  recognition.onspeechstart = () => {
    if (silenceTimer) {
      window.clearTimeout(
        silenceTimer
      );
    }

    setSystemStatus(
      "Speech detected...",
      "listening"
    );
  };


  recognition.onresult = event => {
    let newFinalText = "";
    let latestInterim = "";

    for (
      let index =
        event.resultIndex;

      index <
        event.results.length;

      index += 1
    ) {
      const result =
        event.results[index];

      const transcript =
        compactWhitespace(
          result[0].transcript
        );

      if (!transcript) {
        continue;
      }

      if (result.isFinal) {
        newFinalText =
          appendTranscript(
            newFinalText,
            transcript
          );
      } else {
        latestInterim =
          appendTranscript(
            latestInterim,
            transcript
          );
      }
    }

    if (newFinalText) {
      finalBuffer =
        appendTranscript(
          finalBuffer,
          newFinalText
        );
    }

    interimBuffer =
      latestInterim;

    originalText.value =
      compactWhitespace(
        `${finalBuffer} ${interimBuffer}`
      );

    scheduleSilenceFlush();
  };


  recognition.onspeechend = () => {
    scheduleSilenceFlush();
  };


  recognition.onerror = event => {
    console.error(
      "Speech recognition error:",
      event.error
    );

    recognitionRunning = false;

    if (
      event.error ===
        "not-allowed" ||
      event.error ===
        "service-not-allowed"
    ) {
      sessionActive = false;

      setSystemStatus(
        "Microphone permission was denied",
        "error"
      );

      return;
    }

    if (
      event.error ===
      "no-speech"
    ) {
      setSystemStatus(
        "No speech detected. Listening again...",
        "listening"
      );

      scheduleRecognitionRestart();
      return;
    }

    if (
      event.error ===
        "aborted" &&
      manualStopRequested
    ) {
      return;
    }

    setSystemStatus(
      `Recognition error: ${
        event.error
      }`,
      "error"
    );

    scheduleRecognitionRestart();
  };


  recognition.onend = () => {
    recognitionRunning = false;

    if (pendingUtteranceFlush) {
      void flushCurrentUtterance();
      return;
    }

    if (
      sessionActive &&
      !manualStopRequested
    ) {
      scheduleRecognitionRestart();
    }
  };
}


function downloadFile(
  filename,
  content,
  mimeType
) {
  const blob =
    new Blob(
      [content],
      { type: mimeType }
    );

  const url =
    URL.createObjectURL(blob);

  const link =
    document.createElement("a");

  link.href = url;
  link.download = filename;

  document.body.appendChild(
    link
  );

  link.click();
  link.remove();

  URL.revokeObjectURL(url);
}


function exportSessionAsJSON() {
  if (!sessionEntries.length) {
    alert(
      "No session data to export."
    );

    return;
  }

  const data = {
    session_id: sessionId,

    exported_at:
      new Date().toISOString(),

    total_turns:
      sessionEntries.length,

    entries:
      sessionEntries
  };

  downloadFile(
    `${sessionId}.json`,
    JSON.stringify(
      data,
      null,
      2
    ),
    "application/json"
  );
}


function exportSessionAsTXT() {
  if (!sessionEntries.length) {
    alert(
      "No session data to export."
    );

    return;
  }

  const lines = [
    "Nova Voice AI Console - Session Transcript",
    "================================================",
    `Session ID: ${sessionId}`,
    `Exported At: ${
      new Date().toISOString()
    }`,
    ""
  ];

  for (
    const entry of sessionEntries
  ) {
    lines.push(
      `Turn ${entry.turn} - ${entry.display_time}`,

      `${entry.source_language} → ${entry.target_language}`,

      `Provider: ${entry.provider}`,

      `Original: ${entry.original_text}`,

      `Translation: ${entry.translated_text}`,

      "------------------------------------------------",

      ""
    );
  }

  downloadFile(
    `${sessionId}.txt`,
    lines.join("\n"),
    "text/plain"
  );
}


sourceLanguage.addEventListener(
  "change",
  () => {
    updateSubtitle();

    if (sessionActive) {
      stopVoiceSession(false);

      setSystemStatus(
        "Language changed. Press Start Listening.",
        "ready"
      );
    }
  }
);


targetLanguage.addEventListener(
  "change",
  updateSubtitle
);


arabicDialect.addEventListener(
  "change",
  updateSubtitle
);


speakerRole.addEventListener(
  "change",
  updateSubtitle
);


pathwayABtn.addEventListener(
  "click",
  () => setPathway("A")
);


pathwayBBtn.addEventListener(
  "click",
  () => setPathway("B")
);


startBtn.addEventListener(
  "click",
  () => {
    if (!recognition) {
      alert(
        "Speech recognition is unavailable. Use Google Chrome."
      );

      return;
    }

    if (sessionActive) {
      return;
    }

    manualStopRequested = false;
    sessionActive = true;

    lastTranslatedText = "";

    resetUtteranceBuffers();

    originalText.value = "";
    translatedText.value = "";

    startCallTimer();

    setSystemStatus(
      "Starting microphone...",
      "listening"
    );

    startRecognitionEngine();
  }
);


stopBtn.addEventListener(
  "click",
  () => {
    stopVoiceSession(true);
  }
);


translateBtn.addEventListener(
  "click",
  async () => {
    const text =
      compactWhitespace(
        originalText.value
      );

    if (!text) {
      alert(
        "Type or speak a sentence first."
      );

      return;
    }

    const resumeAfter =
      sessionActive;

    if (
      recognitionRunning &&
      recognition
    ) {
      try {
        recognition.stop();
      } catch (_) {
        // Already stopping.
      }
    }

    await translateText(
      text,
      true
    );

    if (resumeAfter) {
      scheduleRecognitionRestart();
    }
  }
);


speakBtn.addEventListener(
  "click",
  async () => {
    const text =
      compactWhitespace(
        translatedText.value
      );

    if (!text) {
      alert(
        "No translated text is available."
      );

      return;
    }

    const result =
      await speakTranslation(text);

    ttsLatency.innerText =
      `${result.ttsLatencyMs} ms`;

    scheduleRecognitionRestart();
  }
);


exportTxtBtn.addEventListener(
  "click",
  exportSessionAsTXT
);


exportJsonBtn.addEventListener(
  "click",
  exportSessionAsJSON
);


clearBtn.addEventListener(
  "click",
  () => {
    stopVoiceSession(false);

    totalTurns = 0;
    sessionEntries = [];
    lastTranslatedText = "";

    turnCount.innerText =
      "0 turns";

    callTimer.innerText =
      "00:00";

    resetPerformanceMetrics();

    originalText.value = "";
    translatedText.value = "";

    conversationHistory.innerHTML = `
      <div class="empty-history">
        <div class="empty-icon">
          ◌
        </div>

        <p>
          No conversation yet.
          Start speaking to populate
          the live transcript history.
        </p>
      </div>
    `;

    setSystemStatus(
      "History cleared",
      "ready"
    );
  }
);


window.addEventListener(
  "beforeunload",
  () => {
    stopVoiceSession(false);
  }
);


initializeSpeechRecognition();
setPathway("A");
resetPerformanceMetrics();
setSystemStatus("Ready", "ready");