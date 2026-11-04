"""Conexión a MySQL y funciones auxiliares para consultar/modificar datos."""
import os
from contextlib import contextmanager

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error, IntegrityError  # noqa: F401  (se reexportan para app.py)

load_dotenv()


def _configuracion():
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "veterinaria"),
        "charset": "utf8mb4",
        "connection_timeout": 5,
    }


@contextmanager
def conexion():
    conn = mysql.connector.connect(**_configuracion())
    try:
        yield conn
    finally:
        conn.close()


def consultar(sql, params=(), uno=False):
    """SELECT. Devuelve una lista de dicts, o un solo dict (o None) si uno=True."""
    with conexion() as conn:
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute(sql, params)
            return cur.fetchone() if uno else cur.fetchall()
        finally:
            cur.close()


def ejecutar(sql, params=()):
    """INSERT / UPDATE / DELETE con commit. Devuelve las filas afectadas."""
    with conexion() as conn:
        cur = conn.cursor()
        try:
            cur.execute(sql, params)
            conn.commit()
            return cur.rowcount
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
