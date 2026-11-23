"""Prueba CRUD real. Requiere DB_NAME=pawcare_audit_test_<sufijo> ya preparada."""
import json
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# No usar credenciales JWT privadas en una prueba reproducible.
os.environ["JWT_SECRET_KEY"] = "integration-test-only-" + uuid.uuid4().hex

import auth
import app
import db
import mysql.connector


def run():
    database = db._configuracion()["database"]
    if not database.startswith("pawcare_audit_test_"):
        raise SystemExit("Seguridad: DB_NAME debe apuntar a pawcare_audit_test_<sufijo>; no se ejecutó ninguna consulta.")

    cfg = db._configuracion()
    conn = mysql.connector.connect(**cfg)
    cur = conn.cursor(dictionary=True)
    cur.execute(
        "SELECT COUNT(*) AS n FROM information_schema.TRIGGERS "
        "WHERE TRIGGER_SCHEMA=%s", (database,)
    )
    trigger_count = cur.fetchone()["n"]
    if trigger_count != 47:
        raise SystemExit(f"Se esperaban 47 triggers en la base de pruebas; existen {trigger_count}.")

    cur.execute(
        "SELECT TABLE_NAME FROM information_schema.TABLES "
        "WHERE TABLE_SCHEMA=%s AND TABLE_TYPE='BASE TABLE' AND TABLE_NAME<>'auditoria'",
        (database,),
    )
    tables = [row["TABLE_NAME"] for row in cur.fetchall()]
    if len(tables) != 15:
        raise SystemExit(f"Se esperaban 15 tablas de negocio; existen {len(tables)}.")
    counts = {}
    for table in tables:
        cur.execute(f"SELECT COUNT(*) AS n FROM `{table}`")
        counts[table] = cur.fetchone()["n"]
    if not all(count >= 11 for count in counts.values()):
        raise SystemExit("La base de pruebas debe tener al menos 11 filas en cada tabla de negocio.")

    suffix = uuid.uuid4().hex[:10]
    service_name = "CRUD integration " + suffix
    cur.execute("SET @usuario_auditoria='Administrador:901'")
    cur.execute(
        "INSERT INTO catalogo_servicios "
        "(Servicio,Descripcion,DuracionServicio,CostoServicio,Icono,Cupos) "
        "VALUES (%s,'antes',25,33221,'T',3)", (service_name,),
    )
    service_id = cur.lastrowid
    conn.commit()

    cur.execute("SET @usuario_auditoria='Veterinario:902'")
    cur.execute(
        "UPDATE catalogo_servicios SET Descripcion='después' WHERE ID_CataServicio=%s",
        (service_id,),
    )
    conn.commit()
    cur.execute("SET @usuario_auditoria='ANONIMO'")
    cur.execute("DELETE FROM catalogo_servicios WHERE ID_CataServicio=%s", (service_id,))
    conn.commit()
    cur.execute(
        "SELECT operacion,usuario,datos_anteriores,datos_nuevos FROM auditoria "
        "WHERE nombre_tabla='catalogo_servicios' AND id_registro=%s ORDER BY id_auditoria",
        (str(service_id),),
    )
    operations = cur.fetchall()
    expected = [
        ("INSERT", "Administrador:901"),
        ("UPDATE", "Veterinario:902"),
        ("DELETE", "ANONIMO"),
    ]
    if [(row["operacion"], row["usuario"]) for row in operations] != expected:
        raise AssertionError("Los triggers no generaron las tres operaciones/identidades esperadas.")
    old = json.loads(operations[1]["datos_anteriores"])
    new = json.loads(operations[1]["datos_nuevos"])
    if old["Descripcion"] != "antes" or new["Descripcion"] != "después":
        raise AssertionError("El snapshot UPDATE no conserva valores anteriores y nuevos.")

    email = "cascade-" + suffix + "@example.invalid"
    cur.execute("SET @usuario_auditoria='FLASK-CASCADE'")
    cur.execute(
        "INSERT INTO CLIENTE (NombreCliente,ContactoCliente,DireccionCliente,CorreoCliente) "
        "VALUES ('Cliente test','3000000000','Fixture aislado',%s)", (email,),
    )
    client_id = cur.lastrowid
    cur.execute(
        "INSERT INTO USUARIOS (ID_Cliente,Nombre,Correo,ClaveHash,Rol) "
        "VALUES (%s,'Usuario test',%s,'unused-integration-test-value','Cliente')",
        (client_id, email),
    )
    user_id = cur.lastrowid
    conn.commit()
    cur.execute("SET @usuario_auditoria='Administrador:901'")
    cur.execute("DELETE FROM CLIENTE WHERE ID_Cliente=%s", (client_id,))
    conn.commit()
    cur.execute(
        "SELECT datos_anteriores FROM auditoria WHERE nombre_tabla='usuarios' "
        "AND operacion='DELETE' AND id_registro=%s ORDER BY id_auditoria DESC LIMIT 1",
        (str(user_id),),
    )
    cascade = cur.fetchone()
    if not cascade or "ClaveHash" in json.loads(cascade["datos_anteriores"]):
        raise AssertionError("La cascada no registró USUARIOS o filtró el campo de credencial.")
    cur.close()
    conn.close()

    # Endpoint efímero de este proceso: verifica middleware Flask y conexión MySQL reales.
    def insert_from_flask():
        db.ejecutar(
            "INSERT INTO catalogo_servicios "
            "(Servicio,Descripcion,DuracionServicio,CostoServicio,Icono,Cupos) "
            "VALUES (%s,'vía Flask',20,12345,'F',1)", ("Flask path " + suffix,),
        )
        return "ok"

    route_name = "audit_integration_" + suffix
    route_path = "/__integration/auditoria/" + suffix
    app.app.add_url_rule(route_path, endpoint=route_name, view_func=insert_from_flask)
    client = app.app.test_client()
    client.set_cookie(auth.COOKIE, auth.crear_token(903, "Administrador"))
    if client.get(route_path).status_code != 200:
        raise AssertionError("Falló la petición Flask de integración.")
    report = client.get(
        "/auditoria?usuario=Administrador%3A903&operacion=INSERT&tabla=catalogo_servicios"
    )
    if report.status_code != 200 or ("Flask path " + suffix).encode() not in report.data:
        raise AssertionError("El reporte no mostró el registro de la petición Flask autenticada.")
    if client.get("/auditoria?tabla=cliente%20OR%201%3D1").status_code != 400:
        raise AssertionError("El reporte no rechazó un filtro de tabla inválido.")

    print("PASS: 47 triggers; 15 tablas con al menos 11 filas en base aislada.")
    print("PASS: INSERT/UPDATE/DELETE, snapshots, identidad Flask y cascada auditados.")
    print("PASS: reporte con filtros y entrada inválida rechazada (400).")


if __name__ == "__main__":
    run()
