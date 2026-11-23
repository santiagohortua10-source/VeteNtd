"""Ejecuta los fixtures SQL sólo en una base aislada pawcare_audit_test_* ."""
import re
import sys
from pathlib import Path
from secrets import token_urlsafe

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import mysql.connector
from werkzeug.security import generate_password_hash

import db


def main():
    config = db._configuracion()
    database = config["database"]
    if not re.fullmatch(r"pawcare_audit_test_[A-Za-z0-9_]+", database):
        raise SystemExit("Seguridad: DB_NAME debe ser pawcare_audit_test_<sufijo>; no se ejecutó SQL.")

    password_hash = generate_password_hash(token_urlsafe(48))
    sql = Path(__file__).with_name("seed_academico_pruebas.sql").read_text(encoding="utf-8")
    if "'__HASH_USUARIO_TEST__'" not in sql:
        raise SystemExit("No se encontró el marcador del hash de fixture.")
    sql = sql.replace("'__HASH_USUARIO_TEST__'", "'" + password_hash + "'")
    sql = sql.replace("USE ahp_veterinaria;", "")
    sql = re.sub(r"(?m)^--[^\n]*\n?", "", sql)

    connection = mysql.connector.connect(**config)
    try:
        cursor = connection.cursor()
        try:
            for statement in sql.split(";"):
                statement = statement.strip()
                if statement:
                    cursor.execute(statement)
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            cursor.close()
    finally:
        connection.close()
    print("Fixtures aplicados o ya existentes en la base de pruebas aislada.")


if __name__ == "__main__":
    main()
