
import os
import time
from contextlib import closing

import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException, Response, Request
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST


app = FastAPI(
    title="Mi Proyecto Kubernetes",
    description="API de tareas con PostgreSQL y Prometheus",
    version="2.0.0"
)

REQUEST_COUNT = Counter(
    "api_http_requests_total",
    "Total de solicitudes HTTP",
    ["method", "endpoint", "status"]
)

REQUEST_DURATION = Histogram(
    "api_http_request_duration_seconds",
    "Duracion de solicitudes HTTP",
    ["method", "endpoint"]
)


def conectar_db():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        connect_timeout=5
    )


class Tarea(BaseModel):
    nombre: str = Field(min_length=1, max_length=200)


def validar_nombre(nombre):
    nombre = nombre.strip()
    if not nombre:
        raise HTTPException(
            status_code=422,
            detail="El nombre no puede estar vacio"
        )
    return nombre


@app.middleware("http")
async def registrar_metricas(request: Request, call_next):
    inicio = time.perf_counter()
    estado = 500

    try:
        response = await call_next(request)
        estado = response.status_code
        return response
    finally:
        ruta = request.scope.get("route")
        endpoint = getattr(ruta, "path", "unmatched")

        if endpoint != "/metrics":
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=endpoint,
                status=str(estado)
            ).inc()

            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=endpoint
            ).observe(time.perf_counter() - inicio)


@app.get("/")
def inicio():
    return {
        "mensaje": os.getenv(
            "API_MENSAJE",
            "Mi API funciona con Kubernetes y PostgreSQL"
        ),
        "proyecto": "Laboratorio Kubernetes",
        "base_datos": "PostgreSQL"
    }


@app.get("/saludo")
def saludo():
    return {"mensaje": "Hola desde FastAPI"}


@app.get("/health")
def health():
    try:
        with closing(conectar_db()) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        return {"status": "okas", "database": "connected"}
    except psycopg2.Error:
        raise HTTPException(
            status_code=503,
            detail="PostgreSQL no disponible"
        )


@app.get("/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get("/tareas")
def listar_tareas():
    with closing(conectar_db()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT id, nombre FROM tareas ORDER BY id"
            )
            return [dict(fila) for fila in cursor.fetchall()]


@app.get("/tareas/{tarea_id}")
def obtener_tarea(tarea_id: int):
    with closing(conectar_db()) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                "SELECT id, nombre FROM tareas WHERE id = %s",
                (tarea_id,)
            )
            fila = cursor.fetchone()

    if fila is None:
        raise HTTPException(
            status_code=404,
            detail="Tarea no encontrada"
        )

    return dict(fila)


@app.post("/tareas", status_code=201)
def crear_tarea(tarea: Tarea):
    nombre = validar_nombre(tarea.nombre)

    with closing(conectar_db()) as conn:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    INSERT INTO tareas (nombre)
                    VALUES (%s)
                    RETURNING id, nombre
                    """,
                    (nombre,)
                )
                return dict(cursor.fetchone())


@app.put("/tareas/{tarea_id}")
def actualizar_tarea(tarea_id: int, tarea: Tarea):
    nombre = validar_nombre(tarea.nombre)

    with closing(conectar_db()) as conn:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    UPDATE tareas
                    SET nombre = %s
                    WHERE id = %s
                    RETURNING id, nombre
                    """,
                    (nombre, tarea_id)
                )
                fila = cursor.fetchone()

    if fila is None:
        raise HTTPException(
            status_code=404,
            detail="Tarea no encontrada"
        )

    return dict(fila)


@app.delete("/tareas/{tarea_id}", status_code=204)
def eliminar_tarea(tarea_id: int):
    with closing(conectar_db()) as conn:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM tareas WHERE id = %s",
                    (tarea_id,)
                )
                eliminadas = cursor.rowcount

    if eliminadas == 0:
        raise HTTPException(
            status_code=404,
            detail="Tarea no encontrada"
        )

    return Response(status_code=204)
