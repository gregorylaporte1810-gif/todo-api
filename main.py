import os
import time
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://user:password@db:5432/tododb"
)

engine = None
for _ in range(10):
    try:
        engine = create_engine(DATABASE_URL)
        engine.connect()
        break
    except Exception:
        time.sleep(2)

if not engine:
    raise Exception("Impossible de se connecter à la base de données.")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    completed = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)

class TaskCreate(BaseModel):
    title: str

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    completed: Optional[bool] = None

class TaskResponse(BaseModel):
    id: int
    title: str
    completed: bool

    class Config:
        from_attributes = True

app = FastAPI(title="To-Do API avec FastAPI & PostgreSQL")

# Servir le fichier index.html à la racine /
@app.get("/", response_class=HTMLResponse)
def read_index():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Frontend non trouvé</h1>"

# --- ROUTES API ---

@app.get("/tasks/", response_model=list[TaskResponse])
def get_tasks():
    db: Session = SessionLocal()
    try:
        return db.query(TaskModel).all()
    finally:
        db.close()

@app.post("/tasks/", response_model=TaskResponse)
def create_task(task: TaskCreate):
    db: Session = SessionLocal()
    try:
        db_task = TaskModel(title=task.title)
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        return db_task
    finally:
        db.close()

@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task_update: TaskUpdate):
    db: Session = SessionLocal()
    try:
        db_task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
        if not db_task:
            raise HTTPException(status_code=404, detail="Tâche introuvable")

        if task_update.title is not None:
            db_task.title = task_update.title
        if task_update.completed is not None:
            db_task.completed = task_update.completed

        db.commit()
        db.refresh(db_task)
        return db_task
    finally:
        db.close()

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    db: Session = SessionLocal()
    try:
        db_task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
        if not db_task:
            raise HTTPException(status_code=404, detail="Tâche introuvable")

        db.delete(db_task)
        db.commit()
        return {"message": f"Tâche {task_id} supprimée"}
    finally:
        db.close()
