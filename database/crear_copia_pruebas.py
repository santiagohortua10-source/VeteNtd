"""Copia sólo las tablas/columnas/índices/FK a una base nueva de prueba vacía."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import mysql.connector

import db


PREFIJO_PRUEBAS = "pawcare_audit_test_"


def identificador(valor):
    if not re.fullmatch(r"[A-Za-z0-9_]+", valor):
        raise ValueError("Identificador SQL no permitido.")
    return "`" + valor + "`"


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Uso: python database/crear_copia_pruebas.py pawcare_audit_test_<sufijo>")
    destino = sys.argv[1]
    if not destino.startswith(PREFIJO_PRUEBAS) or not re.fullmatch(r"pawcare_audit_test_[a-zA-Z0-9_]+", destino):
        raise SystemExit(f"El destino debe comenzar con {PREFIJO_PRUEBAS}.")

    config = db._configuracion()
    origen = config["database"]
    if origen != "ahp_veterinaria":
        raise SystemExit("Seguridad: configura DB_NAME=ahp_veterinaria explícitamente; no se ejecutó SQL.")

    admin = mysql.connector.connect(**config)
    cursor = admin.cursor(dictionary=True)
    cursor.execute(
        "SELECT DEFAULT_CHARACTER_SET_NAME,DEFAULT_COLLATION_NAME "
        "FROM information_schema.SCHEMATA WHERE SCHEMA_NAME=%s", (origen,)
    )
    schema = cursor.fetchone()
    if not schema:
        raise SystemExit("No existe la base origen ahp_veterinaria.")
    cursor.execute("SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME=%s", (destino,))
    if cursor.fetchone():
        raise SystemExit("El destino ya existe; no se sobrescribió ni modificó.")
    cursor.execute(
        "SELECT TABLE_NAME FROM information_schema.TABLES "
        "WHERE TABLE_SCHEMA=%s AND TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME", (origen,)
    )
    tablas = [fila["TABLE_NAME"] for fila in cursor.fetchall()]
    cursor.execute("SELECT TABLE_NAME FROM information_schema.VIEWS WHERE TABLE_SCHEMA=%s", (origen,))
    if cursor.fetchall():
        raise SystemExit("La base origen tiene vistas; este clonador requiere adaptación antes de continuar.")
    cursor.execute("SELECT TRIGGER_NAME FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=%s", (origen,))
    if cursor.fetchall():
        raise SystemExit("La base origen ya tiene triggers; este clonador requiere adaptación antes de continuar.")
    if not tablas:
        raise SystemExit("La base origen no contiene tablas.")

    charset = identificador(schema["DEFAULT_CHARACTER_SET_NAME"])
    collation = identificador(schema["DEFAULT_COLLATION_NAME"])
    cursor.execute(f"CREATE DATABASE {identificador(destino)} CHARACTER SET {charset} COLLATE {collation}")
    admin.commit()

    destino_config = dict(config, database=destino)
    copia = mysql.connector.connect(**destino_config)
    clone_cursor = copia.cursor()
    clone_cursor.execute("SET FOREIGN_KEY_CHECKS=0")
    for tabla in tablas:
        cursor.execute(f"SHOW CREATE TABLE {identificador(origen)}.{identificador(tabla)}")
        create_sql = cursor.fetchone()["Create Table"]
        clone_cursor.execute(create_sql)
    clone_cursor.execute("SET FOREIGN_KEY_CHECKS=1")
    copia.commit()
    clone_cursor.close()
    copia.close()
    cursor.close()
    admin.close()
    print(f"Copia sólo de estructura creada: {destino} ({len(tablas)} tablas). No se copiaron filas.")


if __name__ == "__main__":
    main()
