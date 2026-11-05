"""Conexión a MongoDB Atlas (base NoSQL).

Regla de la arquitectura:
  - MySQL   -> datos estructurados y transaccionales (servicios, productos, reservas, facturas).
  - MongoDB -> datos dinámicos y de alta frecuencia (colección única: `notificaciones`).
"""
import os

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError  # noqa: F401  (se reexporta para app.py)

load_dotenv()

NOMBRE_COLECCION = "notificaciones"

_cliente = None


def _obtener_cliente():
    """MongoClient es seguro entre hilos y se recomienda crear UNO solo por aplicación."""
    global _cliente
    if _cliente is None:
        uri = os.getenv("MONGO_URI")
        if not uri:
            raise PyMongoError("Falta MONGO_URI en el archivo .env")
        _cliente = MongoClient(
            uri,
            serverSelectionTimeoutMS=5000,  # falla rápido si Atlas no responde
            connectTimeoutMS=5000,
            retryWrites=True,
        )
    return _cliente


def base():
    return _obtener_cliente()[os.getenv("MONGO_DB", "veterinaria_nosql")]


def coleccion():
    return base()[NOMBRE_COLECCION]
