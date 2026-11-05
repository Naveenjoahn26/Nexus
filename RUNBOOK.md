# NEXUS-AI Runbook

This file contains the commands to run the backend and frontend locally for the NEXUS EDU project, along with the local validation/test workflow for edge-case checks.

## 1) Backend commands

Open a terminal in the backend folder:

```bash
cd C:\projects\NEXUS-AI\backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

If you want to run the backend directly with the local virtual environment activated:

```powershell
cd C:\projects\NEXUS-AI\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Health check:

```bash
curl http://localhost:8000/health
```

Run tests:

```bash
cd C:\projects\NEXUS-AI\backend
.\.venv\Scripts\python.exe -m pytest tests -vv
```

## 2) Frontend commands

Open a separate terminal in the frontend folder:

```bash
cd C:\projects\NEXUS-AI\nexus-learnforge-main
npm install
npm run dev
```

Then open the local frontend in the browser:

```text
http://localhost:5173
```

> **Note on Backend API URL:**
> The frontend is configured via `.env` (`VITE_API_URL=http://localhost:8000`) and has an automatic dev fallback in `src/api/client.ts` to `http://localhost:8000`. You can also override it in real time using the floating settings gear icon in the bottom-right of the frontend UI.

## 3) CORS and Edge-Case Test Suite

The test suite in `tests/test_cors_and_edge_cases.py` and `tests/test_local_validation.py` covers 31 comprehensive test cases:

- **CORS Handling:**
  - Preflight OPTIONS responses with allowed methods, headers, and credentials
  - Origin reflection for dynamic local dev ports (5173, 5174, 3000, 8080) and IPv6 (`[::1]`)
  - Origin reflection for Vercel and Render deployments
  - Untrusted origin rejection (`access-control-allow-origin: None`)
  - Trailing-slash and whitespace normalisation in CORS settings
  - Preserved CORS headers on 401, 404, 422, and 500 error responses (preventing opaque browser CORS failures on server errors)
- **Configuration Parsing:**
  - Case-insensitive `DEBUG` flag coercion across `true`, `1`, `yes`, `on`, `false`, `0`, `no`, `off`, `release`, and `prod`
- **Auth & JWT Edge Cases:**
  - Invalid credentials on `/auth/login` (401 with standard error envelope)
  - Malformed JWT tokens (401)
  - Missing `sub` claim or non-UUID `sub` in JWT (401)
- **Validation Edge Cases:**
  - Protected endpoints rejecting unauthenticated requests (401)
  - Unsupported document upload file extensions (e.g. `.exe`)

### Run all tests

```bash
cd C:\projects\NEXUS-AI\backend
.\.venv\Scripts\python.exe -m pytest -vv
```

### Run single test file

```bash
cd C:\projects\NEXUS-AI\backend
.\.venv\Scripts\python.exe -m pytest tests/test_cors_and_edge_cases.py -vv
```

## 4) Local environment summary

- Backend environment: `backend/.venv` (Python 3.14)
- Frontend app: `nexus-learnforge-main/` (Vite + TanStack Start + React)
- Local DB: `postgresql://postgres:12345@localhost:5432/nexus`
- Groq API key: configured in `backend/.env`
