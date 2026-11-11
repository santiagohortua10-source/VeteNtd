"""Lógica de la colección `notificaciones` (MongoDB).

Forma de un documento (el campo `datos` es libre: ahí está la ventaja de NoSQL):
{
  "_id":        ObjectId,
  "tipo":       "reserva_creada" | "stock_bajo" | "sin_cupos" | "servicio_actualizado"
                | "servicio_eliminado" | "cita_agendada" | "cita_cancelada",
  "titulo":     "Cita agendada",
  "mensaje":    "Firulais tiene cita de «Vacuna» con Dra. Laura el lunes 9 de noviembre de 2026 a las 10:00 a. m.",
  "prioridad":  "baja" | "normal" | "alta",
  "leida":      false,
  "fecha":      datetime (UTC),
  "item":       {"id": "S2", "nombre": "Vacuna Antirrábica"},  # referencia al id de MySQL (S1, P3...)
  "datos":      {...},     # en las citas: fecha_cita, hora_cita, dia_texto, hora_texto, mascota, veterinario...
  "cliente_id": 7 | null   # dueño de la notificación (ID_Cliente de MySQL); null = notificación del equipo
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

TIPOS = {"reserva_creada", "stock_bajo", "sin_cupos", "servicio_actualizado", "servicio_eliminado",
         "cita_agendada", "cita_cancelada"}
PRIORIDADES = {"baja", "normal", "alta"}
UMBRAL_STOCK_BAJO = int(os.getenv("UMBRAL_STOCK_BAJO", "3"))
DIAS_RETENCION = int(os.getenv("NOTIF_DIAS_RETENCION", "30"))
TIPOS = {"reserva_creada", "stock_bajo", "sin_cupos", "servicio_actualizado", "servicio_eliminado",
         "cita_agendada", "cita_cancelada", "compra_realizada"}


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
            # id del cliente (MySQL) dueño de la notificación; null = notificación del equipo
            "cliente_id": {"bsonType": ["int", "long", "null"]},
        },
    }
}


def crear_indices():
    col = mongo.coleccion()
    # Listar / contar no leídas por fecha (consulta más frecuente)
    col.create_index([("leida", ASCENDING), ("fecha", DESCENDING)], name="idx_leida_fecha")
    # Lo mismo, pero por cliente (portal de clientes)
    col.create_index([("cliente_id", ASCENDING), ("leida", ASCENDING), ("fecha", DESCENDING)],
                     name="idx_cliente_leida_fecha")
    # TTL: Mongo borra solo las notificaciones viejas (evita que la colección crezca sin control)
    col.create_index("fecha", expireAfterSeconds=DIAS_RETENCION * 86400, name="ttl_fecha")


# ---------- Escritura ----------
def crear(tipo, titulo, mensaje, item=None, datos=None, prioridad="normal", cliente_id=None):
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
            "cliente_id": cliente_id,
        })
        return str(res.inserted_id)
    except PyMongoError as e:
        log.error("No se pudo guardar la notificación en MongoDB: %s", e)
        return None


# En las funciones de abajo, cliente_id=None significa "notificaciones del equipo" (panel de la
# página principal); con un id, solo las de ese cliente. Así cada quien lleva su propio "leído".
def marcar_leida(notif_id, cliente_id=None):
    """True si existía, False si el id no es válido o no existe."""
    if not ObjectId.is_valid(notif_id):
        return False
    res = mongo.coleccion().update_one({"_id": ObjectId(notif_id), "cliente_id": cliente_id},
                                       {"$set": {"leida": True}})
    return res.matched_count == 1


def marcar_todas_leidas(cliente_id=None):
    return mongo.coleccion().update_many({"leida": False, "cliente_id": cliente_id},
                                         {"$set": {"leida": True}}).modified_count


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


def listar(solo_no_leidas=False, limite=20, cliente_id=None):
    filtro = {"cliente_id": cliente_id}
    if solo_no_leidas:
        filtro["leida"] = False
    cursor = mongo.coleccion().find(filtro).sort("fecha", DESCENDING).limit(limite)
    return [_serializar(d) for d in cursor]


def contar_no_leidas(cliente_id=None):
    return mongo.coleccion().count_documents({"leida": False, "cliente_id": cliente_id})


def contar_no_leidas_seguro(cliente_id=None):
    """Para la página principal: si Mongo está caído, la página igual carga (con 0)."""
    try:
        return contar_no_leidas(cliente_id)
    except PyMongoError as e:
        log.error("MongoDB no disponible: %s", e)
        return 0