# AGENTS.md — HNG Stage 1 Task

## Project overview
HNG Stage 1 Task is a full-stack task manager with a React/Vite frontend, FastAPI backend, and SQLite database.

## Repository structure

- `frontend/` — React UI and Netflix-inspired red/black visual system.
- `backend/` — FastAPI REST API and SQLite persistence.
- `backend/todos.db` — generated SQLite database after the backend starts.

## Development commands

### Backend

From `backend/`:

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend

From `frontend/`:

```bash
npm install
npm run dev
```

Then open the Vite URL shown in the terminal, normally `http://localhost:5173`.

## Architecture rules

1. Keep the REST API under `/api`.
2. Keep SQLite access in `backend/main.py` unless the project is later refactored into a database module.
3. The frontend must never write directly to SQLite; all persistence goes through FastAPI.
4. Task statuses are only `in_progress` and `completed`.
5. Dates use `YYYY-MM-DD`; times use 24-hour `HH:MM` in the API/database.
6. Preserve responsive behavior on desktop and mobile.
7. Keep the visual identity cinematic: near-black backgrounds, Netflix-inspired red accents, strong typography, restrained motion.

## Task model

Each task contains:

- `id`
- `title`
- `section`
- `description`
- `task_date`
- `task_time`
- `status`
- `created_at`

## API endpoints

- `GET /api/health`
- `GET /api/tasks`
- `POST /api/tasks`
- `PUT /api/tasks/{task_id}`
- `PATCH /api/tasks/{task_id}/status`
- `DELETE /api/tasks/{task_id}`

## UI requirements

The task experience should include:

- Monthly calendar with selected day.
- Task date and time.
- Section/category.
- Description.
- Completed checkbox.
- In-progress/completed status.
- Add, edit, toggle, and delete actions.
- Responsive red-and-black cinematic styling.

## Testing checklist

Before shipping changes:

1. Start FastAPI and confirm `/api/health` returns `{"status":"ok"}`.
2. Run `npm run build` in `frontend/`.
3. Create a task from the UI.
4. Refresh the browser and confirm the task remains.
5. Toggle completion and confirm it persists after refresh.
6. Edit and delete a task.
7. Test at a narrow mobile viewport.
