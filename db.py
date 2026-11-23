"""Conexión a MySQL y funciones auxiliares para consultar/modificar datos."""
import os
from contextlib import contextmanager
from contextvars import ContextVar

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import Error, IntegrityError  # noqa: F401  (se reexportan para app.py)

load_dotenv()

# El valor se conserva por contexto de solicitud, nunca en una conexión global.
# Cada conexión nueva recibe su propia variable MySQL antes del primer SQL.
_usuario_auditoria = ContextVar("usuario_auditoria", default="SISTEMA")


def establecer_usuario_auditoria(usuario):
    """Establece la identidad confiable de la solicitud actual y devuelve token de reset."""
    return _usuario_auditoria.set(str(usuario)[:120] if usuario else "ANONIMO")


def restablecer_usuario_auditoria(token):
    _usuario_auditoria.reset(token)


def _configuracion():
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "ahp_veterinaria"),
        "charset": "utf8mb4",
        "connection_timeout": 5,
    }


@contextmanager
def conexion():
    conn = mysql.connector.connect(**_configuracion())
    try:
        cur = conn.cursor()
        try:
            cur.execute("SET @usuario_auditoria = %s", (_usuario_auditoria.get(),))
        finally:
            cur.close()
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

@contextmanager
def transaccion():
    """Una sola conexión para varias consultas que deben ir juntas.
    Hace commit al salir bien y rollback si algo falla. Entrega un cursor (dict)."""
    with conexion() as conn:
        cur = conn.cursor(dictionary=True)
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
