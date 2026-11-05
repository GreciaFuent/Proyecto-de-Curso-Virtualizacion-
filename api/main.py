from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3

app = FastAPI(
    title="Mi Proyecto Kubernetes",
    description="API ligera para nuestro laboratorio",
    version="1.1.0"
)

DB_PATH = "/data/mi_proyecto.db"


def conectar_db():
    return sqlite3.connect(DB_PATH)


def crear_tabla():
    with conectar_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tareas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL
            )
        """)


crear_tabla()


class Tarea(BaseModel):
    nombre: str


@app.get("/")
def inicio():
    return {
        "mensaje": "¡Mi API está funcionando!",
        "proyecto": "Laboratorio Kubernetes"
    }


@app.get("/saludo")
def saludo():
    return {"mensaje": "Hola desde FastAPI"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/tareas")
def crear_tarea(tarea: Tarea):
    with conectar_db() as conn:
        cursor = conn.execute(
            "INSERT INTO tareas (nombre) VALUES (?)",
            (tarea.nombre,)
        )
        return {"id": cursor.lastrowid, "nombre": tarea.nombre}


@app.get("/tareas")
def listar_tareas():
    with conectar_db() as conn:
        filas = conn.execute(
            "SELECT id, nombre FROM tareas ORDER BY id"
        ).fetchall()

    return [
        {"id": fila[0], "nombre": fila[1]}
        for fila in filas
    ]

# Prueba de despliegue automatico CI/CD de mi-api
