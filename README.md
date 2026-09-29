# HNG Stage 1 Task — Full-Stack Todo App

A professional task management application with a cinematic red-and-black interface, inspired by modern streaming-service aesthetics. Built with:

- React + Vite
- Python + FastAPI
- SQLite
- REST API

## Features

- Monthly calendar
- Task date and time
- Task sections/categories
- Task descriptions
- In Progress / Completed status
- Clickable completion checkbox
- Create, edit, delete, and toggle tasks
- Persistent SQLite storage
- Responsive red/black cinematic interface
- `AGENTS.md` project instructions

## Run locally

### 1. Backend

Open a terminal:

```bash
cd backend
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\\Scripts\\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Then:

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 2. Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the browser URL Vite prints, normally:

**http://localhost:5173**

FastAPI docs are available at:

**http://127.0.0.1:8000/docs**
