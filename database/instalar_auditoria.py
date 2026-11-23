"""Instala y valida auditoria CRUD exclusivamente en ahp_veterinaria."""
import json
import os
import re
import subprocess
import tempfile
import uuid
from pathlib import Path

import mysql.connector

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import db


ROOT = Path(__file__).resolve().parents[1]
DATABASE = "ahp_veterinaria"
MYSQL = Path(r"C:\xampp\mysql\bin\mysql.exe")
TABLES = (
    "catalogo_servicios", "cliente", "detalle_factura", "empleado", "facturacion",
    "historial_clinico", "horario", "mascota", "pago", "pedidos", "pedido_detalle",
    "productos", "reservas", "responsable_alterno", "usuarios",
)
TRIGGER_RE = re.compile(r"(?im)^CREATE TRIGGER `([^`]+)` (BEFORE|AFTER) (INSERT|UPDATE|DELETE) ON `([^`]+)`")
TRIGGER_STATEMENT_RE = re.compile(
    r"(?is)(CREATE TRIGGER `[^`]+` (?:BEFORE|AFTER) (?:INSERT|UPDATE|DELETE) "
    r"ON `[^`]+`\s+FOR EACH ROW\s+BEGIN.*?END)\$\$"
)


def option_value(value):
    value = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return '"' + value.replace("\n", "\\n").replace("\r", "\\r") + '"'


def read_config():
    config = db._configuracion()
    if config.get("database") != DATABASE:
        raise RuntimeError("Define DB_NAME=ahp_veterinaria explicitamente; no se ejecutaron scripts.")
    return config


def table_counts(cursor, schema):
    result = {}
    for table in TABLES:
        cursor.execute(f"SELECT COUNT(*) FROM `{schema}`.`{table}`")
        result[table] = cursor.fetchone()[0]
    return result


def audit_json(value):
    return json.loads(value) if isinstance(value, str) else value


def assert_no_credentials(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            if key.lower() in {"clave", "clavehash", "password", "password_hash"}:
                raise RuntimeError("Snapshot de auditoria contiene una clave/credencial.")
            assert_no_credentials(nested)
    elif isinstance(value, list):
        for item in value:
            assert_no_credentials(item)


def inspect_preconditions(connection, schema_sql, trigger_sql):
    cursor = connection.cursor()
    cursor.execute("SELECT DATABASE(),VERSION()")
    database, version = cursor.fetchone()
    if database != DATABASE:
        raise RuntimeError(f"Destino inesperado: {database!r}.")

    cursor.execute(
        "SELECT TABLE_NAME FROM information_schema.TABLES "
        "WHERE TABLE_SCHEMA=%s AND TABLE_TYPE='BASE TABLE' AND TABLE_NAME<>'auditoria' ORDER BY TABLE_NAME", (DATABASE,),
    )
    tables = {row[0] for row in cursor.fetchall()}
    if tables != set(TABLES):
        raise RuntimeError("El esquema no coincide con las 15 tablas revisadas.")

    cursor.execute(
        "SELECT TABLE_NAME,COLUMN_NAME FROM information_schema.KEY_COLUMN_USAGE "
        "WHERE TABLE_SCHEMA=%s AND CONSTRAINT_NAME='PRIMARY' AND TABLE_NAME<>'auditoria' "
        "ORDER BY TABLE_NAME,ORDINAL_POSITION",
        (DATABASE,),
    )
    primary_keys = {}
    for table, column in cursor.fetchall():
        primary_keys.setdefault(table, []).append(column)
    if set(primary_keys) != set(TABLES) or any(len(primary_keys[t]) != 1 for t in TABLES):
        raise RuntimeError("Las claves primarias no coinciden con la inspeccion previa.")

    cursor.execute("SELECT COUNT(*) FROM information_schema.REFERENTIAL_CONSTRAINTS WHERE CONSTRAINT_SCHEMA=%s", (DATABASE,))
    if cursor.fetchone()[0] != 19:
        raise RuntimeError("Se esperaban 19 claves foraneas.")
    cursor.execute(
        "SELECT k.REFERENCED_TABLE_NAME,r.DELETE_RULE FROM information_schema.KEY_COLUMN_USAGE k "
        "JOIN information_schema.REFERENTIAL_CONSTRAINTS r ON r.CONSTRAINT_SCHEMA=k.CONSTRAINT_SCHEMA "
        "AND r.CONSTRAINT_NAME=k.CONSTRAINT_NAME AND r.TABLE_NAME=k.TABLE_NAME "
        "WHERE k.TABLE_SCHEMA=%s AND k.TABLE_NAME='usuarios' AND k.REFERENCED_TABLE_NAME IS NOT NULL",
        (DATABASE,),
    )
    cascades = {(row[0], row[1]) for row in cursor.fetchall()}
    if cascades != {("cliente", "CASCADE"), ("empleado", "CASCADE")}:
        raise RuntimeError(f"Las cascadas de usuarios no coinciden: {cascades}.")

    if re.search(r"(?i)\bDROP\s+(?:TABLE|DATABASE|TRIGGER)\b", schema_sql + trigger_sql):
        raise RuntimeError("Un script contiene una operacion DROP; se detuvo.")
    if not re.search(r"(?im)^USE\s+ahp_veterinaria\s*;", schema_sql) or not re.search(
        r"(?im)^USE\s+ahp_veterinaria\s*;", trigger_sql
    ):
        raise RuntimeError("Un script no apunta explicitamente a ahp_veterinaria.")

    cursor.execute(
        "SELECT TABLE_TYPE FROM information_schema.TABLES WHERE TABLE_SCHEMA=%s "
        "AND TABLE_NAME='auditoria'", (DATABASE,),
    )
    audit_object = cursor.fetchone()
    if audit_object and audit_object[0] != "BASE TABLE":
        raise RuntimeError("Existe un objeto auditoria que no es una tabla; no se modifico.")
    planned = TRIGGER_RE.findall(trigger_sql)
    names = [item[0] for item in planned]
    if len(planned) != 47 or len(set(names)) != 47:
        raise RuntimeError("El script no contiene exactamente 47 nombres de trigger unicos.")
    cursor.execute(
        "SELECT TRIGGER_NAME FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=%s", (DATABASE,),
    )
    existing = {row[0] for row in cursor.fetchall()}
    unexpected = existing.difference(names)
    if unexpected:
        raise RuntimeError(f"Triggers ajenos al plan encontrados: {sorted(unexpected)}.")

    expected_main = {(table, op) for table in TABLES for op in ("INSERT", "UPDATE", "DELETE")}
    main = [(name, timing, op, table) for name, timing, op, table in planned if timing == "AFTER"]
    aux = [(name, timing, op, table) for name, timing, op, table in planned if timing == "BEFORE"]
    if len(main) != 45 or {(table, op) for _, _, op, table in main} != expected_main:
        raise RuntimeError("La cobertura de triggers AFTER no coincide con 15x3.")
    expected_aux = {
        ("aud_cliente_before_delete_usuarios", "cliente"),
        ("aud_empleado_before_delete_usuarios", "empleado"),
    }
    if len(aux) != 2 or any((name, table) not in expected_aux or op != "DELETE" for name, _, op, table in aux):
        raise RuntimeError("Los dos triggers BEFORE no corresponden a las cascadas previstas.")
    for _, _, _, table in main:
        pk = primary_keys[table][0]
        if not re.search(r"(?i)(?:NEW|OLD)\.`?" + re.escape(pk) + r"`?", trigger_sql):
            raise RuntimeError(f"No aparece la PK {table}.{pk} en el script de triggers.")
    cursor.close()
    return version, primary_keys, planned, bool(audit_object)


def mysql_defaults_file(config):
    if not MYSQL.is_file():
        raise FileNotFoundError(f"No se encontro mysql.exe: {MYSQL}")
    descriptor, defaults = tempfile.mkstemp(prefix="pawcare-audit-", suffix=".cnf")
    os.chmod(defaults, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write("[client]\n")
            for key in ("host", "port", "user", "password"):
                stream.write(f"{key}={option_value(config[key])}\n")
            stream.write("protocol=tcp\n")
        return defaults
    except Exception:
        os.unlink(defaults)
        raise


def install_sql(config, defaults, sql_path):
    result = subprocess.run(
        [str(MYSQL), "--defaults-extra-file=" + defaults, "--default-character-set=utf8mb4"],
        input=sql_path.read_bytes(), capture_output=True, timeout=180, check=False,
    )
    if result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(
            f"Ejecucion de {sql_path.name} fallo con codigo {result.returncode}; "
            f"se detuvo sin limpieza automatica. Diagnostico: {detail[:1000]}"
        )


def install_one_trigger(defaults, name, statement):
    payload = (
        f"USE {DATABASE};\nDELIMITER $$\n{statement}$$\nDELIMITER ;\n"
    ).encode("utf-8")
    result = subprocess.run(
        [str(MYSQL), "--defaults-extra-file=" + defaults, "--default-character-set=utf8mb4"],
        input=payload, capture_output=True, timeout=60, check=False,
    )
    if result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Creacion de {name} fallo (codigo {result.returncode}): {detail[:1000]}")


def parse_trigger_statements(trigger_sql):
    statements = {}
    for statement in TRIGGER_STATEMENT_RE.findall(trigger_sql):
        match = TRIGGER_RE.search(statement)
        if not match or match.group(1) in statements:
            raise RuntimeError("No se pudieron analizar nombres unicos de triggers.")
        statements[match.group(1)] = statement
    if len(statements) != 47:
        raise RuntimeError(f"Se esperaban 47 sentencias CREATE TRIGGER; se analizaron {len(statements)}.")
    return statements


def verify_one_trigger(config, planned_item, statement):
    name, timing, operation, table = planned_item
    connection = mysql.connector.connect(**config)
    connection.autocommit = True
    try:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT ACTION_TIMING,EVENT_MANIPULATION,EVENT_OBJECT_TABLE,ACTION_STATEMENT "
            "FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=%s AND TRIGGER_NAME=%s",
            (DATABASE, name),
        )
        row = cursor.fetchone()
        if not row:
            raise RuntimeError(f"information_schema no muestra el trigger {name}.")
        if tuple(row[:3]) != (timing, operation, table):
            raise RuntimeError(f"Metadata inesperada para {name}: {row[:3]}.")
        source_body = re.search(r"(?is)FOR EACH ROW\s+BEGIN(.*?)END$", statement)
        if not source_body:
            raise RuntimeError(f"No se pudo comparar el cuerpo fuente de {name}.")
        stored = row[3]
        if stored.lstrip().upper().startswith("BEGIN"):
            stored = re.sub(r"(?is)^\s*BEGIN\s*|\s*END\s*$", "", stored)
        normalize = lambda value: re.sub(r"\s+", "", value.replace("`", "")).lower()
        if normalize(stored) != normalize(source_body.group(1)):
            raise RuntimeError(f"El cuerpo almacenado de {name} no coincide con el script.")
        cursor.close()
    finally:
        connection.close()


def verify_audit_table(connection):
    cursor = connection.cursor(dictionary=True)
    cursor.execute(
        "SELECT COLUMN_NAME,DATA_TYPE,COLUMN_TYPE,IS_NULLABLE,EXTRA FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA=%s AND TABLE_NAME='auditoria' ORDER BY ORDINAL_POSITION", (DATABASE,),
    )
    columns = cursor.fetchall()
    expected = [
        ("id_auditoria", "bigint"), ("usuario", "varchar"), ("fecha_hora", "datetime"),
        ("operacion", "varchar"), ("nombre_tabla", "varchar"), ("id_registro", "varchar"),
        ("datos_anteriores", None), ("datos_nuevos", None),
    ]
    if len(columns) != 8:
        raise RuntimeError(f"La tabla auditoria tiene {len(columns)} columnas; se esperaban 8.")
    for column, (name, data_type) in zip(columns, expected):
        if column["COLUMN_NAME"] != name:
            raise RuntimeError(f"Columna inesperada en auditoria: {column['COLUMN_NAME']}.")
        if data_type and column["DATA_TYPE"].lower() != data_type:
            raise RuntimeError(f"Tipo inesperado en {name}: {column['DATA_TYPE']}.")
    for column in columns[-2:]:
        if column["DATA_TYPE"].lower() not in {"json", "longtext"}:
            raise RuntimeError(f"Tipo JSON invalido en {column['COLUMN_NAME']}: {column['DATA_TYPE']}.")
    cursor.execute("SELECT JSON_VALID('{\"pawcare\":true}') AS es_json_valido")
    if cursor.fetchone()["es_json_valido"] != 1:
        raise RuntimeError("El motor no valida JSON correctamente.")
    cursor.execute("SHOW CREATE TABLE auditoria")
    show_create = cursor.fetchone()["Create Table"]
    for name, _ in (("datos_anteriores", 1), ("datos_nuevos", 1)):
        if re.search(r"(?i)`" + name + r"`\s+longtext", show_create) and not re.search(
            r"(?i)json_valid\s*\(\s*`?" + name + r"`?\s*\)", show_create
        ):
            raise RuntimeError(f"La columna {name} usa LONGTEXT sin CHECK JSON_VALID.")
    cursor.close()
    return columns


def verify_triggers(connection, planned):
    cursor = connection.cursor()
    cursor.execute(
        "SELECT TRIGGER_NAME,ACTION_TIMING,EVENT_MANIPULATION,EVENT_OBJECT_TABLE "
        "FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=%s ORDER BY TRIGGER_NAME", (DATABASE,),
    )
    actual = {tuple(row) for row in cursor.fetchall()}
    expected = {(name, timing, op, table) for name, timing, op, table in planned}
    if actual != expected:
        raise RuntimeError(f"Los triggers instalados no coinciden con el plan (esperados={len(expected)}, encontrados={len(actual)}).")
    cursor.close()


def test_triggers_in_transaction(primary_keys):
    # Use the actual Flask before_request identity hook and a signed synthetic JWT.
    os.environ["JWT_SECRET_KEY"] = "pawcare-audit-transaction-probe-" + uuid.uuid4().hex
    import app as pawcare
    import auth

    token_id = 987654321
    identity = f"Cliente:{token_id}"
    jwt_token = auth.crear_token(token_id, "Cliente")
    class RollbackProbe(Exception):
        pass

    token = uuid.uuid4().hex[:12]
    service_id = None
    client_id = None
    user_id = None
    with pawcare.app.test_request_context("/", headers={"Cookie": f"{auth.COOKIE}={jwt_token}"}):
        pawcare.app.preprocess_request()
        try:
            with db.transaccion() as cursor:
                cursor.execute(
                    "INSERT INTO catalogo_servicios (Servicio,Descripcion,DuracionServicio,CostoServicio,Icono,Cupos) "
                    "VALUES (%s,%s,20,1001,'T',1)", ("AUDIT-" + token, "fila ficticia transaccional"),
                )
                service_id = cursor.lastrowid
                cursor.execute("UPDATE catalogo_servicios SET Servicio=%s,Descripcion=%s WHERE ID_CataServicio=%s",
                               ("AUDIT-U-" + token, "actualizacion ficticia", service_id))
                cursor.execute("DELETE FROM catalogo_servicios WHERE ID_CataServicio=%s", (service_id,))
                pk = primary_keys["cliente"][0]
                cursor.execute(
                    "INSERT INTO cliente (NombreCliente,ContactoCliente,DireccionCliente,CorreoCliente,ClaveHash) "
                    "VALUES (%s,%s,%s,%s,%s)",
                    ("AUDIT cascade " + token, "3000000000", "Direccion ficticia", token + "@example.invalid", "FAKE_HASH_NOT_A_PASSWORD"),
                )
                client_id = cursor.lastrowid
                cursor.execute(
                    "INSERT INTO usuarios (ID_Cliente,ID_Empleado,Nombre,Correo,ClaveHash,Rol) "
                    "VALUES (%s,NULL,%s,%s,%s,'Cliente')",
                    (client_id, "AUDIT cascade " + token, token + "@example.invalid", "FAKE_HASH_NOT_A_PASSWORD"),
                )
                user_id = cursor.lastrowid
                cursor.execute(f"DELETE FROM cliente WHERE `{pk}`=%s", (client_id,))

                cursor.execute(
                    "SELECT operacion,usuario,fecha_hora,datos_anteriores,datos_nuevos FROM auditoria "
                    "WHERE id_registro=%s AND nombre_tabla='catalogo_servicios' ORDER BY id_auditoria", (str(service_id),),
                )
                service_rows = cursor.fetchall()
                if [row["operacion"] for row in service_rows] != ["INSERT", "UPDATE", "DELETE"]:
                    raise RuntimeError("No se registraron INSERT/UPDATE/DELETE de la prueba transaccional.")
                for row in service_rows:
                    if row["usuario"] != identity or row["fecha_hora"] is None:
                        raise RuntimeError("Usuario o fecha incorrectos en la auditoria.")
                inserted = audit_json(service_rows[0]["datos_nuevos"])
                before_update = audit_json(service_rows[1]["datos_anteriores"])
                after_update = audit_json(service_rows[1]["datos_nuevos"])
                before_delete = audit_json(service_rows[2]["datos_anteriores"])
                if not inserted or inserted.get("Servicio") != "AUDIT-" + token:
                    raise RuntimeError("El snapshot INSERT no contiene datos_nuevos esperados.")
                if not before_update or not after_update or before_update.get("Servicio") != "AUDIT-" + token or after_update.get("Servicio") != "AUDIT-U-" + token:
                    raise RuntimeError("El snapshot UPDATE no contiene datos_anteriores/nuevos esperados.")
                if not before_delete or before_delete.get("Servicio") != "AUDIT-U-" + token or service_rows[2]["datos_nuevos"] is not None:
                    raise RuntimeError("El snapshot DELETE no contiene solo datos_anteriores.")

                cursor.execute(
                    "SELECT operacion,usuario,fecha_hora,datos_anteriores,datos_nuevos FROM auditoria "
                    "WHERE nombre_tabla='usuarios' AND id_registro=%s ORDER BY id_auditoria", (str(user_id),),
                )
                user_rows = cursor.fetchall()
                if [row["operacion"] for row in user_rows] != ["INSERT", "DELETE"]:
                    raise RuntimeError("Las cascadas a usuarios no generaron INSERT y DELETE de auditoria.")
                if any(row["usuario"] != identity or row["fecha_hora"] is None for row in user_rows):
                    raise RuntimeError("La identidad/fecha de la cascada no coincide.")
                for row in user_rows:
                    assert_no_credentials(audit_json(row["datos_anteriores"]))
                    assert_no_credentials(audit_json(row["datos_nuevos"]))
                raise RollbackProbe()
        except RollbackProbe:
            pass

    # Confirm rollback removed all probe rows and audit events (autoincrement gaps are harmless).
    check = mysql.connector.connect(**read_config())
    check.autocommit = True
    try:
        cursor = check.cursor()
        cursor.execute("SELECT COUNT(*) FROM auditoria WHERE id_registro IN (%s,%s)",
                       (str(service_id), str(user_id)))
        if cursor.fetchone()[0] != 0:
            raise RuntimeError("La prueba transaccional dejo filas de auditoria persistentes.")
        cursor.execute("SELECT COUNT(*) FROM catalogo_servicios WHERE Servicio LIKE %s", ("AUDIT-%" + token + "%",))
        if cursor.fetchone()[0] != 0:
            raise RuntimeError("La prueba transaccional dejo el servicio ficticio persistente.")
        cursor.execute(f"SELECT COUNT(*) FROM cliente WHERE `{primary_keys['cliente'][0]}`=%s", (client_id,))
        if cursor.fetchone()[0] != 0:
            raise RuntimeError("La prueba transaccional dejo el cliente ficticio persistente.")
        cursor.close()
    finally:
        check.close()

    # Exercise the administrator-only report over Flask's test client, without database writes.
    admin_jwt = auth.crear_token(1, "Administrador")
    client = pawcare.app.test_client()
    client.set_cookie(auth.COOKIE, admin_jwt)
    response = client.get("/auditoria?tabla=catalogo_servicios")
    if response.status_code != 200:
        raise RuntimeError(f"El reporte /auditoria respondio HTTP {response.status_code}.")
    print("Prueba transaccional: Flask/JWT, INSERT/UPDATE/DELETE, snapshots, cascada, identidad y exclusion de credenciales OK; rollback confirmado.")
    print("Reporte administrativo /auditoria: HTTP 200.")


def main():
    config = read_config()
    if not MYSQL.is_file():
        raise FileNotFoundError(f"No se encontro mysql.exe: {MYSQL}")
    schema_sql = (ROOT / "database/auditoria_schema.sql").read_text(encoding="utf-8")
    trigger_path = ROOT / "database/auditoria_triggers.sql"
    trigger_sql = trigger_path.read_text(encoding="utf-8")
    planned = TRIGGER_RE.findall(trigger_sql)
    statements = parse_trigger_statements(trigger_sql)
    connection = mysql.connector.connect(**config)
    connection.autocommit = True
    try:
        version, primary_keys, planned, audit_exists = inspect_preconditions(connection, schema_sql, trigger_sql)
        cursor = connection.cursor()
        before = table_counts(cursor, DATABASE)
        cursor.close()
    finally:
        connection.close()

    print(f"Destino verificado: {DATABASE}; motor {version}; 15 tablas, 19 FK.")
    if audit_exists:
        check = mysql.connector.connect(**config)
        check.autocommit = True
        try:
            columns = verify_audit_table(check)
        finally:
            check.close()
        print(f"Tabla auditoria existente validada sin modificar: {len(columns)} columnas; JSON valido.")
    else:
        print("Creando tabla auditoria...")
        defaults = mysql_defaults_file(config)
        try:
            install_sql(config, defaults, ROOT / "database/auditoria_schema.sql")
        finally:
            os.unlink(defaults)
        check = mysql.connector.connect(**config)
        check.autocommit = True
        try:
            columns = verify_audit_table(check)
        finally:
            check.close()
        print(f"Tabla auditoria verificada: {len(columns)} columnas; JSON valido.")

    defaults = mysql_defaults_file(config)
    try:
        print("Instalando triggers faltantes de uno en uno; conexiones de verificacion cerradas antes de cada DDL.")
        for item in sorted(planned):
            name = item[0]
            connection = mysql.connector.connect(**config)
            connection.autocommit = True
            try:
                cursor = connection.cursor()
                cursor.execute(
                    "SELECT TRIGGER_NAME FROM information_schema.TRIGGERS "
                    "WHERE TRIGGER_SCHEMA=%s AND TRIGGER_NAME=%s", (DATABASE, name),
                )
                exists = cursor.fetchone() is not None
                cursor.close()
            finally:
                connection.close()
            if exists:
                verify_one_trigger(config, item, statements[name])
                print(f"Ya existe y coincide; omitido: {name}")
                continue
            install_one_trigger(defaults, name, statements[name])
            verify_one_trigger(config, item, statements[name])
            print(f"Instalado y verificado: {name}")
    finally:
        os.unlink(defaults)

    connection = mysql.connector.connect(**config)
    connection.autocommit = True
    try:
        verify_audit_table(connection)
        verify_triggers(connection, planned)
        cursor = connection.cursor()
        after_ddl = table_counts(cursor, DATABASE)
        cursor.close()
    finally:
        connection.close()
    test_triggers_in_transaction(primary_keys)
    connection = mysql.connector.connect(**config)
    connection.autocommit = True
    try:
        cursor = connection.cursor()
        after_test = table_counts(cursor, DATABASE)
        cursor.close()
        if before != after_ddl or before != after_test:
            raise RuntimeError("Los conteos de negocio cambiaron durante la instalacion/prueba.")
    finally:
        connection.close()
    print("Fase 1 completa: tabla y 47 triggers verificados; pruebas revertidas; conteos de negocio sin cambios.")


if __name__ == "__main__":
    main()
