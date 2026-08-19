import os
import time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Récupération des variables d'environnement pour la base de données
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://user:password@db:5432/tododb"
)

# Attendre que la base de données soit disponible avant d'initialiser SQLAlchemy
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

# Modèle de la table dans la base de données
class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    completed = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)

# Modèle Pydantic pour la validation des données entrantes (JSON)
class TaskCreate(BaseModel):
    title: str

class TaskResponse(BaseModel):
    id: int
    title: str
    completed: bool

    class Config:
        from_attributes = True

app = FastAPI(title="To-Do API avec FastAPI & PostgreSQL")

@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API To-Do ! Accédez à /docs pour la documentation interactive."}

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

@app.get("/tasks/", response_model=list[TaskResponse])
def get_tasks():
    db: Session = SessionLocal()
    try:
        tasks = db.query(TaskModel).all()
        return tasks
    finally:
        db.close()
