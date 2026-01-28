# LLM Flight Recorder — Techtonic Shift (Automate26 Hackathon)

LLM Flight Recorder is an observability + replay system for Large Language Model (LLM) interactions.

This prototype provides a backend service that:

- Accepts chat prompts
- Generates responses (Mock mode or Gemini API)
- Stores interaction traces in MongoDB
- Supports semantic caching
- Exposes monitoring APIs for dashboards

Built as part of the **Automate26 Hackathon — Techtonic Shift Track**.

---

## ✅ Hackathon Deliverables Checklist

This repository provides:

- ✅ Runnable working prototype (FastAPI backend + Streamlit frontend scaffold)
- ✅ Public GitHub repository
- ✅ Open-source license (MIT)
- ✅ Setup + usage instructions
- ✅ Clean modular backend structure
- ✅ Trace + monitoring APIs

---

## 🧠 What We Are Building

The goal is to build an **LLM Observability Platform** similar to a "flight recorder":

- Every LLM request is logged
- Latency + metadata are captured
- Responses can be replayed later
- Monitoring endpoints allow dashboards to visualize usage

---

## ✨ Key Features Implemented

### Backend (FastAPI)

- `/chat` endpoint for LLM interaction
- Mock mode for demos
- Gemini LLM provider integration
- MongoDB trace persistence
- Semantic cache (exact-match)
- Rate limiting middleware
- Monitoring endpoints (`/traces`)

### Frontend (Streamlit)

- Dashboard structure in progress
- Charts utilities prepared
- Connects to backend APIs

---

## 📂 Project Structure

```
llm-flight-recorder/
│
├── backend/
│   ├── main.py                 # FastAPI app entrypoint
│   ├── config.py               # Environment + settings loader
│   ├── routes/
│   │   ├── chat.py             # POST /chat
│   │   └── monitor.py          # GET /traces endpoints
│   ├── services/
│   │   ├── llm_provider.py     # Gemini wrapper
│   │   └── semantic_cache.py   # Mongo semantic cache
│   ├── repositories/
│   │   └── trace_repo.py       # Mongo trace repository
│   ├── core/
│   │   └── database.py         # Mongo connection (Motor)
│   └── middleware/
│       └── rate_limit.py       # In-memory limiter
│
├── frontend/                   # Streamlit UI scaffold
│
├── requirements.txt
├── .env.example                # Environment template
└── README.md
```

---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/Veins19/Techtonic_Shift_Automate26.git
cd Techtonic_Shift_Automate26
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
```

Activate:

**Windows PowerShell**

```powershell
.venv\Scripts\Activate
```

**Mac/Linux**

```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Configuration

Create a `.env` file in the project root.

Example:

```env
API_ENV=development
LOG_LEVEL=INFO

USE_MOCK_LLM=True

# Gemini (only required if USE_MOCK_LLM=False)
GOOGLE_API_KEY=your_key_here
GEMINI_MODEL_NAME=models/gemini-2.5-flash

# MongoDB (optional, enables persistence)
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=llm_flight_recorder

MAX_RPM=25
MAX_RPD=14000
```

---

## ▶️ Running the Backend

Start FastAPI server:

```bash
uvicorn backend.main:app --reload
```

Backend runs at:

```
http://127.0.0.1:8000
```

---

## ✅ API Endpoints

### Health Check

```http
GET /health
```

Response:

```json
{
  "status": "ok",
  "mock": true,
  "mongo_enabled": false
}
```

### Chat Endpoint

```http
POST /chat
```

Body:

```json
{
  "message": "Hello!"
}
```

Returns:

- reply text
- trace_id
- latency

### Monitoring

#### List Traces

```http
GET /traces
```

#### Trace Detail

```http
GET /traces/{trace_id}
```

---

## ▶️ Running the Frontend (Streamlit)

Frontend is under development.

To start:

```bash
cd frontend
streamlit run app.py
```

Runs at:

```
http://localhost:8501
```

---

## 🧪 Demo Mode vs Real LLM Mode

### Mock Mode (default)

```env
USE_MOCK_LLM=True
```

No API key required.

### Gemini Mode

```env
USE_MOCK_LLM=False
GOOGLE_API_KEY=your_real_key
MONGODB_URI=your_real_mongo_uri
```

Enables:

- Gemini generation
- Semantic caching
- Mongo persistence

---

## 📝 Getting Started

To get started with LLM Flight Recorder:

1. Follow the **Setup Instructions** above to clone and configure the project
2. Set `USE_MOCK_LLM=True` to test with mock responses (no API keys required)
3. Start the backend with `uvicorn backend.main:app --reload`
4. Make requests to the `/chat` endpoint to see traces being logged
5. Access the `/traces` monitoring endpoint to view your interaction history
6. Optionally configure MongoDB for persistent trace storage
7. When ready, switch to Gemini mode with your API key for real LLM interactions

---

## 🔮 Future Enhancements

This project is actively being developed. Planned features include:

- Enhanced Streamlit dashboard with real-time trace visualization
- Advanced semantic caching with vector embeddings
- Distributed tracing support
- Export and replay functionality for detailed analysis
- Performance metrics and analytics
- Multi-LLM provider support

---
