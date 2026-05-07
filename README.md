# Nova Voice AI Console  
## Real-Time Speech-to-Speech Translation Dashboard

Nova Voice AI Console is a real-time Speech-to-Speech translation prototype designed for multilingual call-center and customer-support environments.

The system supports bidirectional voice interpretation between clients and representatives using speech recognition, translation, text-to-speech, Arabic dialect handling, latency tracking, PII masking, and session export.

---

## Project Overview

This project demonstrates a production-style Voice AI workflow:

```text
Speech Input → ASR → PII Masking → Translation → TTS → Dashboard Output


Tech Stack

Frontend

.HTML
.CSS
.JavaScript
.Browser SpeechRecognition API
.Browser Audio API

Backend

.Python
.FastAPI
.Uvicorn
.gTTS
.Regex-based PII masking



Key Features

.Real-time browser speech recognition
.Bidirectional call flow dashboard
.Pathway A: Client → Representative
.Pathway B: Representative → Client
.English → Urdu translation
.English → Arabic translation
.Arabic → Urdu translation
.Urdu → Arabic translation
.Arabic dialect selector
.MSA
.Gulf Arabic
.Egyptian Arabic
.Levantine Arabic
.Backend text-to-speech audio generation
.Urdu and Arabic audio playback
.Conversation history
.Speaker role control
.Call timer
.Translation latency tracking
.TTS latency tracking
.Total response latency tracking
.Confidence score display
.PII masking before translation
.TXT transcript export
.JSON structured session export
.Futuristic glassmorphism UI


s2s-voice-translater/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   └── services/
│   │       ├── translation_service.py
│   │       └── pii_service.py
│   │
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
│
├── .gitignore
└── README.md