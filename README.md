# NEXUS EDU

### The AI Operating System for Modern Education

> **Empowering Educators. Elevating Learners. One Intelligent System.**

NEXUS EDU is an AI-powered educational platform that transforms course materials into intelligent, interactive academic resources.

Instead of treating uploaded documents as static files, NEXUS EDU leverages **Retrieval-Augmented Generation (RAG)**, **Large Language Models (Groq / Qwen / LLaMA)**, structured AI outputs, and persistent conversations to create an intelligent workspace for both students and educators.

---

## 🚀 Key Features

- **Document Ingestion & Hybrid RAG**: Upload `.pdf`, `.docx`, `.pptx`, `.txt`, and `.md` files. Documents are parsed into parent/child chunks and indexed into ChromaDB vector store with hybrid dense + sparse (BM25) retrieval.
- **Context-Aware AI Chat**: Converse with course materials through a persistent multi-turn chat orchestrator.
- **Automated Lecture Notes**: Generate structured, comprehensive lecture notes from course documents.
- **Smart Summarization**: Distill complex topics and reading materials into concise key summaries.
- **Question Paper & Quiz Generation**: Produce balanced exam question papers complete with answer schemes and difficulty breakdowns.
- **Interactive Presentation Builder**: Auto-generate slide decks and structured presentations from ingested academic content.
- **Previous Paper Analysis**: Identify recurring themes, question patterns, and core competencies across historical exams.
- **Role-Based Authentication**: Secure JWT-based authentication supporting students, professors, and administrators.

---

## 🏗️ System Architecture

```text
                 ┌────────────────────────────────────────────────────────┐
                 │                 NEXUS Frontend                         │
                 │     (React 19 + TanStack Start/Router + Tailwind)      │
                 └───────────────────────────┬────────────────────────────┘
                                             │ HTTP / REST (JWT)
                                             ▼
                 ┌────────────────────────────────────────────────────────┐
                 │                  NEXUS EDU Backend                     │
                 │                 (FastAPI + Uvicorn)                    │
                 ├───────────────────────────┬────────────────────────────┤
                 │  Auth & User Management   │   API Routing & CORS       │
                 │  Course & Doc Services    │   AI Orchestrator          │
                 └─────────────┬─────────────┴───────────────┬────────────┘
                               │                             │
               ┌───────────────┴───────────────┐             │
               ▼                               ▼             ▼
  ┌─────────────────────────┐     ┌───────────────────────┐ ┌───────────────┐
  │   PostgreSQL Database   │     │  ChromaDB Vector Store│ │   Groq LLM    │
  │   (Users, Courses,      │     │  (Dense Embeddings,   │ │ (qwen3.8-27b) │
  │    Docs, Chats, Logs)   │     │   Parent/Child Chunks)│ └───────────────┘
  └─────────────────────────┘     └───────────────────────┘
```

---

## 🛠️ Tech Stack

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11+)
- **Database**: PostgreSQL with [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html) & [asyncpg](https://github.com/MagicStack/asyncpg)
- **Vector DB / RAG**: [ChromaDB](https://www.trychroma.com/), BAAI `bge-small-en-v1.5` embeddings, Cross-Encoder reranker
- **LLM Provider**: [Groq](https://groq.com/) API (`qwen/qwen3.8-27b`)
- **Authentication**: OAuth2 with JWT (HMAC-SHA256) & bcrypt password hashing
- **Testing**: [pytest](https://docs.pytest.org/), `pytest-asyncio`, FastAPI `TestClient`

### Frontend
- **Framework**: [React 19](https://react.dev/), [TanStack Start](https://tanstack.com/start), [TanStack Router](https://tanstack.com/router)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/), Radix UI, Lucide icons
- **Build Tool**: [Vite](https://vitejs.dev/)

---

## ⚡ Quick Start

### 1. Prerequisites
- **Python**: 3.11+
- **Node.js**: 18+ and `npm`
- **PostgreSQL**: 15+ running locally or in Docker

---

### 2. Backend Setup

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # Linux/macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Create a `.env` file in `backend/` (see `backend/.env.example`):
   ```env
   APP_NAME=NEXUS_EDU
   APP_ENV=development
   DEBUG=true
   APP_HOST=0.0.0.0
   APP_PORT=8000

   # CORS
   CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000

   # Database
   DATABASE_URL=postgresql+asyncpg://postgres:12345@localhost:5432/nexus
   DATABASE_URL_SYNC=postgresql+psycopg2://postgres:12345@localhost:5432/nexus

   # Authentication
   JWT_SECRET_KEY=nexus-local-dev-secret-change-me
   JWT_ALGORITHM=HS256
   JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

   # LLM Provider
   GROQ_API_KEY=your_groq_api_key_here
   LLM_MODEL_METADATA=qwen/qwen3.8-27b
   LLM_MODEL_JSON=qwen/qwen3.8-27b
   LLM_MODEL_CONTENT=qwen/qwen3.8-27b
   ```

5. **Run database migrations / table creation**:
   The database schema is automatically verified on startup, or initialize via Alembic:
   ```bash
   alembic upgrade head
   ```

6. **Start the backend server**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   API Documentation is available at:
   - **Swagger UI**: `http://localhost:8000/docs`
   - **ReDoc**: `http://localhost:8000/redoc`

---

### 3. Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd nexus-learnforge-main
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure environment variables**:
   Create a `.env` file in `nexus-learnforge-main/`:
   ```env
   VITE_API_URL=http://localhost:8000
   ```

4. **Start the frontend development server**:
   ```bash
   npm run dev
   ```
   Open `http://localhost:5173` in your browser.

---

## 🧪 Running Tests

The test suite covers full CORS compliance, configuration coercion, auth edge cases, JWT validation, and document upload handling:

```bash
cd backend
.\.venv\Scripts\python.exe -m pytest tests -vv
```

All 31 test cases validate:
- ✅ CORS Preflight (OPTIONS), allowed methods, credentials, dynamic ports, and allowed domains
- ✅ CORS headers preserved across 401, 404, 422, and 500 error responses
- ✅ Configuration boolean parsing (`DEBUG=release`, `DEBUG=prod`, `true`, `false`)
- ✅ Auth edge cases: invalid credentials, expired token, malformed JWT, missing `sub` claim
- ✅ Upload validation: rejection of unauthenticated requests and unsupported file extensions

---

## 📁 Repository Structure

```text
NEXUS-AI/
├── backend/
│   ├── app/
│   │   ├── ai/            # RAG pipeline, loaders, chunkers, AI orchestrator
│   │   ├── api/v1/        # FastAPI endpoints (auth, chat, courses, documents, gen)
│   │   ├── core/          # Config, security, exceptions, telemetry logger
│   │   ├── database/      # Async engine and session factory
│   │   ├── models/        # SQLAlchemy ORM models (User, Course, Document, Message)
│   │   ├── repositories/  # Data access layer
│   │   ├── schemas/       # Pydantic v2 schemas for request/response validation
│   │   └── services/      # Business logic services
│   ├── tests/             # Pytest test suite and test data
│   ├── alembic/           # Database migration scripts
│   └── requirements.txt   # Python dependencies
├── nexus-learnforge-main/ # React frontend application
│   ├── src/
│   │   ├── api/           # Axios API client and service endpoints
│   │   ├── components/    # UI components, 3D Canvas, widgets
│   │   └── routes/        # TanStack router page definitions
│   └── package.json       # Node dependencies
├── RUNBOOK.md             # Developer runbook and operational commands
└── README.md              # Project documentation
```

---

## 🔒 Security & Privacy

- **Environment Files**: Secrets (`.env`) are strictly ignored via `.gitignore` and should never be committed.
- **Passwords**: Hashed with bcrypt before storage.
- **Tokens**: Stateless, signed JWTs with expiration checks.
- **CORS Protection**: Restricted to designated local development ports, Vercel, and Render deployments.
