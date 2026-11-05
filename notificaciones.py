"""Lógica de la colección `notificaciones` (MongoDB).

Forma de un documento (el campo `datos` es libre: ahí está la ventaja de NoSQL):
{
  "_id":       ObjectId,
  "tipo":      "reserva_creada" | "stock_bajo" | "sin_cupos" | "servicio_actualizado" | "servicio_eliminado",
  "titulo":    "Nueva reserva",
  "mensaje":   "Se reservó 'Vacuna Antirrábica'. Quedan 24 cupos.",
  "prioridad": "baja" | "normal" | "alta",
  "leida":     false,
  "fecha":     datetime (UTC),
  "item":      {"id": "S2", "nombre": "Vacuna Antirrábica"},   # referencia al id de MySQL (S1, P3...)
  "datos":     {...}                                           # cualquier dato extra según el tipo
}
"""
import logging
import os
from datetime import datetime, timezone

from bson import ObjectId
from pymongo import ASCENDING, DESCENDING
from pymongo.errors import PyMongoError

import mongo

log = logging.getLogger(__name__)

TIPOS = {"reserva_creada", "stock_bajo", "sin_cupos", "servicio_actualizado", "servicio_eliminado"}
PRIORIDADES = {"baja", "normal", "alta"}
UMBRAL_STOCK_BAJO = int(os.getenv("UMBRAL_STOCK_BAJO", "3"))
DIAS_RETENCION = int(os.getenv("NOTIF_DIAS_RETENCION", "30"))


# ---------- Creación del esquema (se ejecuta con database/mongo_setup.py) ----------
VALIDADOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["tipo", "titulo", "mensaje", "prioridad", "leida", "fecha"],
        "properties": {
            "tipo": {"enum": sorted(TIPOS)},
            "titulo": {"bsonType": "string", "maxLength": 150},
            "mensaje": {"bsonType": "string", "maxLength": 500},
            "prioridad": {"enum": sorted(PRIORIDADES)},
            "leida": {"bsonType": "bool"},
            "fecha": {"bsonType": "date"},
            "item": {"bsonType": ["object", "null"]},
            "datos": {"bsonType": ["object", "null"]},
        },
    }
}


def crear_indices():
    col = mongo.coleccion()
    # Listar / contar no leídas por fecha (consulta más frecuente)
    col.create_index([("leida", ASCENDING), ("fecha", DESCENDING)], name="idx_leida_fecha")
    # TTL: Mongo borra solo las notificaciones viejas (evita que la colección crezca sin control)
    col.create_index("fecha", expireAfterSeconds=DIAS_RETENCION * 86400, name="ttl_fecha")


# ---------- Escritura ----------
def crear(tipo, titulo, mensaje, item=None, datos=None, prioridad="normal"):
    """Inserta una notificación. NUNCA lanza excepción: si Mongo falla solo se registra
    en el log, para que la operación principal (MySQL) no se caiga por una notificación."""
    if tipo not in TIPOS or prioridad not in PRIORIDADES:
        log.error("Notificación inválida: tipo=%s prioridad=%s", tipo, prioridad)
        return None
    try:
        res = mongo.coleccion().insert_one({
            "tipo": tipo,
            "titulo": titulo[:150],
            "mensaje": mensaje[:500],
            "prioridad": prioridad,
            "leida": False,
            "fecha": datetime.now(timezone.utc),
            "item": item,
            "datos": datos or {},
        })
        return str(res.inserted_id)
    except PyMongoError as e:
        log.error("No se pudo guardar la notificación en MongoDB: %s", e)
        return None


def marcar_leida(notif_id):
    """True si existía, False si el id no es válido o no existe."""
    if not ObjectId.is_valid(notif_id):
        return False
    res = mongo.coleccion().update_one({"_id": ObjectId(notif_id)}, {"$set": {"leida": True}})
    return res.matched_count == 1


def marcar_todas_leidas():
    return mongo.coleccion().update_many({"leida": False}, {"$set": {"leida": True}}).modified_count


# ---------- Lectura ----------
def _serializar(doc):
    return {
        "id": str(doc["_id"]),
        "tipo": doc["tipo"],
        "titulo": doc["titulo"],
        "mensaje": doc["mensaje"],
        "prioridad": doc["prioridad"],
        "leida": doc["leida"],
        "fecha": doc["fecha"].replace(tzinfo=timezone.utc).isoformat(),
        "item": doc.get("item"),
        "datos": doc.get("datos") or {},
    }


def listar(solo_no_leidas=False, limite=20):
    filtro = {"leida": False} if solo_no_leidas else {}
    cursor = mongo.coleccion().find(filtro).sort("fecha", DESCENDING).limit(limite)
    return [_serializar(d) for d in cursor]


def contar_no_leidas():
    return mongo.coleccion().count_documents({"leida": False})


def contar_no_leidas_seguro():
    """Para la página principal: si Mongo está caído, la página igual carga (con 0)."""
    try:
        return contar_no_leidas()
    except PyMongoError as e:
        log.error("MongoDB no disponible: %s", e)
        return 0
