"""Crea la colección `notificaciones` en MongoDB Atlas (con validación e índices).

Uso (desde la carpeta del proyecto, con el .env ya configurado):
    python database/mongo_setup.py

Es seguro ejecutarlo varias veces.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mongo  # noqa: E402
import notificaciones  # noqa: E402

db = mongo.base()
nombre = mongo.NOMBRE_COLECCION

if nombre not in db.list_collection_names():
    db.create_collection(nombre, validator=notificaciones.VALIDADOR, validationLevel="strict")
    print(f"✔ Colección '{nombre}' creada en la base '{db.name}'.")
else:
    db.command("collMod", nombre, validator=notificaciones.VALIDADOR, validationLevel="strict")
    print(f"✔ La colección '{nombre}' ya existía: validación actualizada.")

notificaciones.crear_indices()
print("✔ Índices creados: idx_leida_fecha y ttl_fecha.")
print("Colecciones en la base:", db.list_collection_names())
