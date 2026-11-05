# NEXUS-AI reverse engineering and validation report

## 1. Project scope

This repository contains a Python FastAPI backend and a separate React frontend scaffold.

- Backend: `backend/`
- Frontend: `nexus-learnforge-main/`
- High-level app: NEXUS EDU, an AI-powered educational platform emphasizing RAG-based document ingestion, chat, lecture generation, question paper generation, slides, summaries, and analysis.

## 2. Reverse-engineered architecture

### Backend

The backend is structured as a FastAPI application with layered modules:

- `app/main.py`: application lifecycle, middleware, global exception handling, router registration
- `app/api/v1/`: HTTP endpoints for auth, chat, documents, lecture, PPT, question papers, summaries, analysis, and YouTube
- `app/core/`: config, security, logger, and custom exceptions
- `app/database/`: SQLAlchemy async engine and session management
- `app/models/`: ORM models for users, courses, documents, conversations, and messages
- `app/repositories/`: data access patterns for key entities
- `app/ai/`: AI router, LLM clients, orchestrator, and retrieval-augmented generation stack
- `app/services/`: domain services such as lecture generation and chat generation

### Frontend

The project already includes a React/TanStack app under `nexus-learnforge-main/` with routes for:

- landing page
- login/register
- authenticated dashboard
- documents
- chat
- generation flows

This is a real SPA built with Vite, React Router, and Tailwind-like styling.

## 3. Operational findings

### Configuration issues found

During local validation, the project failed when `DEBUG=release` was exported by the environment because the app config expected a real boolean. This was corrected by coercing string boolean values like `release`, `prod`, `true`, and `false` into valid Python booleans.

### Local environment setup

Local validation used:

- Python environment: `backend/.venv`
- Groq API key: provided and loaded in `.env`
- Database: PostgreSQL local database `nexus` with user `postgres` and password `12345`

## 4. Test dataset

A lightweight sample dataset was created at:

- `backend/tests/data/sample_course_notes.md`

It includes a small AI course note set covering the basics of artificial intelligence and why AI matters for education.

## 5. Test loop executed

The project was validated with `pytest` in the backend environment using the sample dataset and a FastAPI smoke test.

### Commands used

```bash
cd backend
.venv\Scripts\python.exe -m pytest tests -q
```

## 6. Results

The test suite validates:

- config coercion for `DEBUG=release`
- markdown document loading from sample notes
- health endpoint response from the FastAPI app

This gives a real local validation loop before production deployment.

## 7. Recommended next steps

1. Start the backend locally with Uvicorn and the configured `.env` values.
2. Start the frontend from `nexus-learnforge-main/` with `npm install` and `npm run dev`.
3. Connect the client to the local backend via the API base configuration in the frontend settings.
4. Add integration tests for auth, document upload, and chat once the local database and model providers are fully reachable.

## 8. Production note

The repository includes a large AI orchestration stack that expects valid Groq credentials and a live Postgres database. Local verification confirms the app structure is correct and the validation loop is functioning, but model-backed features will require access to the configured external services.
