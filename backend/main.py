from datetime import date, datetime
from pathlib import Path
import sqlite3
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "todos.db"

app = FastAPI(title="HNG Stage 1 Task API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            section TEXT NOT NULL DEFAULT 'Personal',
            description TEXT NOT NULL DEFAULT '',
            task_date TEXT NOT NULL,
            task_time TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'in_progress',
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


init_db()


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    section: str = Field(default="Personal", max_length=50)
    description: str = Field(default="", max_length=500)
    task_date: str
    task_time: str
    status: str = "in_progress"


class TaskUpdate(TaskCreate):
    pass


def normalize_status(status: str) -> str:
    if status not in {"completed", "in_progress"}:
        raise HTTPException(status_code=400, detail="Status must be completed or in_progress")
    return status


def row_to_dict(row):
    return dict(row)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/tasks")
def list_tasks(task_date: Optional[str] = None, status: Optional[str] = None):
    conn = get_db()
    query = "SELECT * FROM tasks"
    params = []
    filters = []
    if task_date:
        filters.append("task_date = ?")
        params.append(task_date)
    if status:
        normalize_status(status)
        filters.append("status = ?")
        params.append(status)
    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += " ORDER BY task_date ASC, task_time ASC, id DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [row_to_dict(row) for row in rows]


@app.post("/api/tasks", status_code=201)
def create_task(task: TaskCreate):
    status = normalize_status(task.status)
    try:
        date.fromisoformat(task.task_date)
        datetime.strptime(task.task_time, "%H:%M")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date or time format")
    conn = get_db()
    cursor = conn.execute(
        """
        INSERT INTO tasks (title, section, description, task_date, task_time, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (task.title.strip(), task.section.strip() or "Personal", task.description.strip(), task.task_date, task.task_time, status, datetime.now().isoformat()),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)).fetchone()
    conn.close()
    return row_to_dict(row)


@app.put("/api/tasks/{task_id}")
def update_task(task_id: int, task: TaskUpdate):
    status = normalize_status(task.status)
    conn = get_db()
    existing = conn.execute("SELECT id FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")
    conn.execute(
        """
        UPDATE tasks
        SET title = ?, section = ?, description = ?, task_date = ?, task_time = ?, status = ?
        WHERE id = ?
        """,
        (task.title.strip(), task.section.strip() or "Personal", task.description.strip(), task.task_date, task.task_time, status, task_id),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return row_to_dict(row)


@app.patch("/api/tasks/{task_id}/status")
def toggle_status(task_id: int):
    conn = get_db()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")
    new_status = "completed" if row["status"] == "in_progress" else "in_progress"
    conn.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
    conn.commit()
    updated = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return row_to_dict(updated)


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int):
    conn = get_db()
    cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted"}
