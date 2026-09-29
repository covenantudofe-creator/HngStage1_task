import os
from datetime import date, datetime
from typing import Optional

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set")


app = FastAPI(
    title="HNG Stage 1 Task API",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://hng-stage1-task-nu.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    return psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row
    )


def init_db():
    with get_db() as conn:
        with conn.cursor() as cursor:

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(120) NOT NULL,
                    section VARCHAR(50) NOT NULL DEFAULT 'Personal',
                    description VARCHAR(500) NOT NULL DEFAULT '',
                    task_date DATE NOT NULL,
                    task_time TIME NOT NULL,
                    status VARCHAR(20) NOT NULL DEFAULT 'in_progress',
                    created_at TIMESTAMP NOT NULL
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS notes (
                    id SERIAL PRIMARY KEY,
                    task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL
                )
                """
            )

        conn.commit()


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


class NoteCreate(BaseModel):
    content: str = Field(min_length=1, max_length=2000)
    task_id: Optional[int] = None


def normalize_status(status: str) -> str:
    if status not in {"completed", "in_progress"}:
        raise HTTPException(
            status_code=400,
            detail="Status must be completed or in_progress"
        )
    return status


def validate_date_time(task_date: str, task_time: str):
    try:
        date.fromisoformat(task_date)
        datetime.strptime(task_time, "%H:%M")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid date or time format"
        )


@app.get("/api/health")
def health():
    try:
        with get_db() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()

        return {
            "status": "ok",
            "database": "connected"
        }

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed"
        )


@app.get("/api/tasks")
def list_tasks(
    task_date: Optional[str] = None,
    status: Optional[str] = None
):
    query = """
        SELECT
            id,
            title,
            section,
            description,
            task_date,
            task_time,
            status,
            created_at
        FROM tasks
    """

    filters = []
    params = []

    if task_date:
        filters.append("task_date = %s")
        params.append(task_date)

    if status:
        normalize_status(status)
        filters.append("status = %s")
        params.append(status)

    if filters:
        query += " WHERE " + " AND ".join(filters)

    query += """
        ORDER BY task_date ASC, task_time ASC, id DESC
    """

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()


@app.get("/api/tasks/{task_id}")
def get_task(task_id: int):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM tasks WHERE id = %s",
                (task_id,)
            )

            task = cursor.fetchone()

            if not task:
                raise HTTPException(
                    status_code=404,
                    detail="Task not found"
                )

            return task


@app.post("/api/tasks", status_code=201)
def create_task(task: TaskCreate):
    status = normalize_status(task.status)

    validate_date_time(
        task.task_date,
        task.task_time
    )

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO tasks (
                    title,
                    section,
                    description,
                    task_date,
                    task_time,
                    status,
                    created_at
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s
                )
                RETURNING *
                """,
                (
                    task.title.strip(),
                    task.section.strip() or "Personal",
                    task.description.strip(),
                    task.task_date,
                    task.task_time,
                    status,
                    datetime.now()
                )
            )

            created_task = cursor.fetchone()

        conn.commit()

    return created_task


@app.put("/api/tasks/{task_id}")
def update_task(
    task_id: int,
    task: TaskUpdate
):
    status = normalize_status(task.status)

    validate_date_time(
        task.task_date,
        task.task_time
    )

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM tasks WHERE id = %s",
                (task_id,)
            )

            if not cursor.fetchone():
                raise HTTPException(
                    status_code=404,
                    detail="Task not found"
                )

            cursor.execute(
                """
                UPDATE tasks
                SET
                    title = %s,
                    section = %s,
                    description = %s,
                    task_date = %s,
                    task_time = %s,
                    status = %s
                WHERE id = %s
                RETURNING *
                """,
                (
                    task.title.strip(),
                    task.section.strip() or "Personal",
                    task.description.strip(),
                    task.task_date,
                    task.task_time,
                    status,
                    task_id
                )
            )

            updated_task = cursor.fetchone()

        conn.commit()

    return updated_task


@app.patch("/api/tasks/{task_id}/status")
def toggle_status(task_id: int):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM tasks WHERE id = %s",
                (task_id,)
            )

            task = cursor.fetchone()

            if not task:
                raise HTTPException(
                    status_code=404,
                    detail="Task not found"
                )

            new_status = (
                "completed"
                if task["status"] == "in_progress"
                else "in_progress"
            )

            cursor.execute(
                """
                UPDATE tasks
                SET status = %s
                WHERE id = %s
                RETURNING *
                """,
                (new_status, task_id)
            )

            updated_task = cursor.fetchone()

        conn.commit()

    return updated_task


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int):
    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM tasks
                WHERE id = %s
                RETURNING id
                """,
                (task_id,)
            )

            deleted = cursor.fetchone()

            if not deleted:
                raise HTTPException(
                    status_code=404,
                    detail="Task not found"
                )

        conn.commit()

    return {"message": "Task deleted"}


@app.get("/api/notes")
def list_notes(task_id: Optional[int] = None):
    query = """
        SELECT
            id,
            task_id,
            content,
            created_at
        FROM notes
    """

    params = []

    if task_id is not None:
        query += " WHERE task_id = %s"
        params.append(task_id)

    query += " ORDER BY created_at DESC, id DESC"

    with get_db() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()


@app.post("/api/notes", status_code=201)
def create_note(note: NoteCreate):
    with get_db() as conn:
        with conn.cursor() as cursor:

            if note.task_id is not None:
                cursor.execute(
                    "SELECT id FROM tasks WHERE id = %s",
                    (note.task_id,)
                )

                if not cursor.fetchone():
                    raise HTTPException(
                        status_code=404,
                        detail="Task not found"
                    )

            cursor.execute(
                """
                INSERT INTO notes (
                    task_id,
                    content,
                    created_at
                )
                VALUES (%s, %s, %s)
                RETURNING *
                """,
                (
                    note.task_id,
                    note.content.strip(),
                    datetime.now()
                )
            )

            created_note = cursor.fetchone()

        conn.commit()

    return created_note


@app.put("/api/notes/{note_id}")
def update_note(
    note_id: int,
    note: NoteCreate
):
    with get_db() as conn:
        with conn.cursor() as cursor:

            cursor.execute(
                "SELECT id FROM notes WHERE id = %s",
                (note_id,)
            )

            if not cursor.fetchone():
                raise HTTPException(
                    status_code=404,
                    detail="Note not found"
                )

            cursor.execute(
                """
                UPDATE notes
                SET
                    content = %s,
                    task_id = %s
                WHERE id = %s
                RETURNING *
                """,
                (
                    note.content.strip(),
                    note.task_id,
                    note_id
                )
            )

            updated_note = cursor.fetchone()

        conn.commit()

    return updated_note


@app.delete("/api/notes/{note_id}")
def delete_note(note_id: int):
    with get_db() as conn:
        with conn.cursor() as cursor:

            cursor.execute(
                """
                DELETE FROM notes
                WHERE id = %s
                RETURNING id
                """,
                (note_id,)
            )

            deleted = cursor.fetchone()

            if not deleted:
                raise HTTPException(
                    status_code=404,
                    detail="Note not found"
                )

        conn.commit()

    return {"message": "Note deleted"}