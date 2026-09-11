# 🌾 Kannada Agricultural Conversational RAG Assistant

> **UG Major Engineering Project** — AI-Powered Multilingual Agricultural Intelligence Backend

---

## 📌 Overview

This is a **scalable conversational AI backend** built for Kannada-speaking farmers. It combines:

- **Retrieval-Augmented Generation (RAG)** — grounded answers from agricultural datasets
- **Conversational Memory** — multi-turn dialogue continuity
- **Semantic Retrieval** — FAISS + Sentence Transformers
- **Local LLM Support** — Ollama-compatible (Llama, Mistral, etc.)
- **Voice Pipeline** — Faster-Whisper STT + Coqui/Piper TTS
- **FastAPI + WebSockets** — real-time streaming communication

The assistant behaves like a **real agricultural advisor** — asking follow-up questions, reasoning over retrieved knowledge, and communicating naturally in Kannada.

---

## 🏗️ Architecture Overview

```
User (Voice/Text)
      │
      ▼
FastAPI WebSocket / REST API
      │
      ├── Speech-to-Text (Faster-Whisper)
      ▼
Conversation Memory Manager
      │
      ▼
Missing Info Detector → Follow-Up Question Generator
      │
      ▼
Semantic Retrieval (FAISS + Sentence Transformers)
      │
      ▼
Context Builder + Prompt Engineer
      │
      ▼
LLM Response Generator (Ollama / Gemini Fallback)
      │
      ▼
Text-to-Speech (Coqui / Piper)
      │
      ▼
User Response (Voice/Text)
```

---

## 📁 Project Structure

```
major-project/
├── app/
│   ├── main.py                    # FastAPI entry point
│   ├── config.py                  # All configuration settings
│   │
│   ├── api/
│   │   ├── routes/
│   │   │   ├── chat.py            # REST chat endpoint
│   │   │   ├── voice.py           # Voice upload endpoint
│   │   │   └── health.py          # Health check endpoint
│   │   └── websocket/
│   │       └── ws_handler.py      # WebSocket real-time handler
│   │
│   ├── rag/
│   │   ├── dataset_loader.py      # Load + validate agricultural JSON datasets
│   │   ├── preprocessor.py        # Clean and prepare dataset entries
│   │   ├── embedder.py            # Generate Sentence Transformer embeddings
│   │   ├── faiss_index.py         # Build and query FAISS vector index
│   │   ├── retriever.py           # Semantic retrieval engine
│   │   ├── context_builder.py     # Build RAG context from retrieved chunks
│   │   └── metadata_filter.py     # Filter by crop, season, region, etc.
│   │
│   ├── conversation/
│   │   ├── memory_manager.py      # Per-session conversation memory
│   │   ├── session_manager.py     # Session lifecycle management
│   │   ├── follow_up.py           # Follow-up question detection + generation
│   │   └── dialogue_state.py      # Track dialogue state (crop, symptoms, etc.)
│   │
│   ├── llm/
│   │   ├── ollama_client.py       # Ollama local LLM integration
│   │   ├── gemini_client.py       # Optional Gemini API fallback
│   │   ├── prompt_builder.py      # Agricultural prompt engineering
│   │   └── response_generator.py  # Unified LLM response generation
│   │
│   ├── voice/
│   │   ├── stt.py                 # Faster-Whisper speech-to-text
│   │   └── tts.py                 # Coqui/Piper text-to-speech
│   │
│   ├── training/
│   │   ├── fine_tune_embeddings.py  # Lightweight Sentence Transformer fine-tuning
│   │   └── training_data_builder.py # Build training pairs from dataset
│   │
│   ├── evaluation/
│   │   ├── retrieval_eval.py      # Precision@k, cosine similarity metrics
│   │   └── response_eval.py       # Response quality evaluation
│   │
│   └── utils/
│       ├── logger.py              # Structured logging
│       ├── text_utils.py          # Text cleaning, language detection
│       └── exceptions.py          # Custom exception classes
│
├── data/
│   ├── raw/                       # Raw JSON agricultural datasets
│   ├── processed/                 # Preprocessed data
│   └── sample_dataset.json        # Sample 5-entry dataset for testing
│
├── models/
│   ├── faiss_index/               # Saved FAISS index files
│   └── fine_tuned/                # Fine-tuned Sentence Transformer checkpoints
│
├── scripts/
│   ├── ingest_data.py             # Run dataset ingestion + index building
│   ├── evaluate.py                # Run retrieval evaluation
│   └── test_conversation.py       # Test conversational pipeline
│
├── requirements.txt               # All Python dependencies
├── .env.example                   # Environment variable template
└── README.md                      # This file
```

---

## ⚙️ Setup Instructions

### 1. Clone and Navigate
```bash
cd major-project
```

### 2. Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Linux/Mac
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
copy .env.example .env
# Edit .env with your settings
```

### 5. Install Ollama (Local LLM)
Download from https://ollama.com and pull a model:
```bash
ollama pull llama3.2
# or for multilingual support:
ollama pull aya
```

### 6. Ingest Agricultural Dataset
```bash
python scripts/ingest_data.py
```

### 7. Start the Backend Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 8. Access API Documentation
Open: http://localhost:8000/docs

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | System health check |
| POST | `/api/chat` | Text-based chat |
| POST | `/api/voice/transcribe` | Audio → Text (STT) |
| POST | `/api/voice/synthesize` | Text → Audio (TTS) |
| WS | `/ws/chat/{session_id}` | Real-time conversational WebSocket |

---

## 🧠 Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend Framework | FastAPI + Uvicorn |
| Embeddings | Sentence Transformers (multilingual) |
| Vector Search | FAISS |
| Local LLM | Ollama (Llama3, Mistral, Aya) |
| LLM Fallback | Google Gemini API |
| Speech-to-Text | Faster-Whisper |
| Text-to-Speech | Coqui TTS / Piper TTS |
| Conversation Memory | In-memory (Redis-ready) |
| Data Format | JSON (MongoDB/PostgreSQL-ready) |

---

## 📋 Example Conversation Flow

```
Farmer: "ನನ್ನ ಬೆಳೆ ಒಣಗುತ್ತಿದೆ"
AI:     "ಯಾವ ಬೆಳೆ ಬಗ್ಗೆ ಮಾತನಾಡುತ್ತಿದ್ದೀರಿ?"
Farmer: "ಟೊಮ್ಯಾಟೊ"
AI:     "ಎಲೆಗಳಲ್ಲಿ ಹಳದಿ ಬಣ್ಣ ಅಥವಾ ಕಲೆಗಳಿವೆಯೇ?"
Farmer: "ಹೌದು, ಹಳದಿ ಬಣ್ಣ ಇದೆ"
AI:     "ಇದು ಎಲೆ ರೋಲ್ ವೈರಸ್ ಆಗಿರಬಹುದು. ..."
```

---

## 👨‍🎓 Academic Note

This project is designed as a **UG Major Engineering Project** demonstrating:
- Conversational AI Architecture
- Retrieval-Augmented Generation (RAG)
- Multilingual NLP for low-resource languages
- Production-oriented Python backend engineering
- Agricultural domain adaptation
