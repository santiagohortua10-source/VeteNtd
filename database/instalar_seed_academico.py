"""Aplica fixtures ficticios a ahp_veterinaria solo tras confirmacion interactiva."""
import re
import sys
from pathlib import Path
from secrets import token_urlsafe

import mysql.connector
from werkzeug.security import generate_password_hash

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import db


DATABASE = None
CONFIRMATION = "INSERTAR FIXTURES FICTICIOS EN ahp_veterinaria"
TABLES = (
    "catalogo_servicios", "cliente", "detalle_factura", "empleado", "facturacion",
    "historial_clinico", "horario", "mascota", "pago", "pedidos", "pedido_detalle",
    "productos", "reservas", "responsable_alterno", "usuarios",
)


def quote_identifier(value):
    if not re.fullmatch(r"[A-Za-z0-9_]+", value):
        raise ValueError("Identificador inesperado en information_schema.")
    return f"`{value}`"


def count_orphans(cursor, database):
    cursor.execute(
        "SELECT TABLE_NAME,CONSTRAINT_NAME,COLUMN_NAME,REFERENCED_TABLE_NAME,REFERENCED_COLUMN_NAME "
        "FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA=%s "
        "AND REFERENCED_TABLE_NAME IS NOT NULL ORDER BY TABLE_NAME,CONSTRAINT_NAME,ORDINAL_POSITION",
        (database,),
    )
    relations = {}
    for child, constraint, child_col, parent, parent_col in cursor.fetchall():
        relations.setdefault((child, constraint, parent), []).append((child_col, parent_col))
    total = 0
    for (child, _constraint, parent), columns in relations.items():
        joins = " AND ".join(f"p.{quote_identifier(parent_col)}=c.{quote_identifier(child_col)}" for child_col, parent_col in columns)
        non_null = " AND ".join(f"c.{quote_identifier(child_col)} IS NOT NULL" for child_col, _ in columns)
        cursor.execute(
            f"SELECT COUNT(*) FROM {quote_identifier(child)} c LEFT JOIN {quote_identifier(parent)} p "
            f"ON {joins} WHERE {non_null} AND p.{quote_identifier(columns[0][1])} IS NULL"
        )
        total += cursor.fetchone()[0]
    return total


def count_fixture_duplicates(cursor):
    checks = (
        ("CLIENTE", ("CorreoCliente",), "CorreoCliente LIKE 'cliente%@pawcare.example.invalid'"),
        ("EMPLEADO", ("CorreoEmpleado",), "CorreoEmpleado LIKE 'vet%@pawcare.example.invalid'"),
        ("CATALOGO_SERVICIOS", ("Servicio",), "Servicio LIKE 'PawCare prueba servicio %'"),
        ("PRODUCTOS", ("TipoProducto",), "TipoProducto LIKE 'PawCare prueba producto %'"),
        ("USUARIOS", ("Correo",), "Correo LIKE 'cliente%@pawcare.example.invalid'"),
        ("MASCOTA", ("ID_Cliente", "NombreMascota"), "NombreMascota LIKE 'Mascota prueba %'"),
        ("HORARIO", ("ID_Empleado", "DiaSemana", "HoraInicio", "HoraFin"), "HoraInicio='08:00:00' AND HoraFin='17:00:00'"),
        ("RESERVAS", ("ID_Empleado", "ID_Mascota", "ID_CataServicio", "FechaReserva", "HoraReserva"), "FechaReserva BETWEEN '2035-01-02' AND '2035-01-12' AND HoraReserva='09:00:00'"),
        ("HISTORIAL_CLINICO", ("ID_Reserva",), "Diagnostico='Registro ficticio de prueba.'"),
        ("FACTURACION", ("ID_Cliente", "FECHA"), "FECHA BETWEEN '2035-02-02' AND '2035-02-12'"),
        ("DETALLE_FACTURA", ("ID_Facturacion", "ID_Servicio"), "ID_Servicio IS NOT NULL AND ID_Facturacion IN (SELECT ID_Facturacion FROM FACTURACION WHERE FECHA BETWEEN '2035-02-02' AND '2035-02-12')"),
        ("PAGO", ("ComprobantePago",), "ComprobantePago LIKE 'TEST-P%'"),
        ("PEDIDOS", ("ID_Cliente", "Fecha"), "Fecha BETWEEN '2035-03-02' AND '2035-03-12'"),
        ("PEDIDO_DETALLE", ("ID_Pedido", "ID_Producto"), "ID_Pedido IN (SELECT ID_Pedido FROM PEDIDOS WHERE Fecha BETWEEN '2035-03-02' AND '2035-03-12')"),
        ("RESPONSABLE_ALTERNO", ("Documento",), "Documento LIKE 'PAWTEST-DOC-%'"),
    )
    duplicates = []
    for table, columns, condition in checks:
        key_sql = ",".join(quote_identifier(column) for column in columns)
        cursor.execute(
            f"SELECT COUNT(*) FROM (SELECT {key_sql} FROM {quote_identifier(table)} "
            f"WHERE {condition} GROUP BY {key_sql} HAVING COUNT(*)>1) duplicate_rows"
        )
        count = cursor.fetchone()[0]
        if count:
            duplicates.append((table, count))
    return duplicates


def prepare_statements():
    sql_path = Path(__file__).with_name("seed_academico_pruebas.sql")
    sql = sql_path.read_text(encoding="utf-8")
    sql = re.sub(r"(?im)^\s*USE\s+`?ahp_veterinaria`?\s*;", "", sql)
    sql = re.sub(r"(?m)^\s*--.*(?:\n|$)", "", sql)
    sql = sql.replace("'__HASH_USUARIO_TEST__'", "'" + generate_password_hash(token_urlsafe(48)) + "'")
    if "__HASH_USUARIO_TEST__" in sql or "USE ahp_veterinaria" in sql:
        raise RuntimeError("No se pudo preparar el SQL para el destino verificado.")
    sql = re.sub(r"(?im)^\s*(START\s+TRANSACTION|COMMIT)\s*;", "", sql)
    statements = [part.strip() for part in sql.split(";") if part.strip()]
    forbidden = re.compile(r"(?im)^\s*(UPDATE|DELETE|DROP|ALTER|TRUNCATE)\b")
    if any(forbidden.search(statement) for statement in statements):
        raise RuntimeError("El seed contiene una operacion fuera de INSERT/configuracion; se cancelo.")
    if not any("__HASH_USUARIO_TEST__" not in s and "INSERT INTO USUARIOS" in s for s in statements):
        raise RuntimeError("No se encontro el INSERT de usuarios esperado.")
    return statements


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True, help="pawcare_audit_test_<sufijo> o ahp_veterinaria")
    parser.add_argument("--confirm-target", help="Debe ser exactamente ahp_veterinaria para permitir destino academico.")
    args = parser.parse_args()
    global DATABASE
    DATABASE = args.database
    if re.fullmatch(r"pawcare_audit_test_[A-Za-z0-9_]+", DATABASE):
        if args.confirm_target:
            raise SystemExit("--confirm-target solo se admite para ahp_veterinaria.")
        production = False
    elif DATABASE == "ahp_veterinaria" and args.confirm_target == "ahp_veterinaria":
        production = True
    else:
        raise SystemExit("Destino rechazado: usa un schema pawcare_audit_test_* o confirma ahp_veterinaria explicitamente.")

    config = db._configuracion()
    config["database"] = DATABASE
    statements = prepare_statements()
    connection = mysql.connector.connect(**config)
    connection.autocommit = True
    try:
        cur = connection.cursor()
        cur.execute("SELECT DATABASE()")
        if cur.fetchone()[0] != DATABASE:
            raise RuntimeError("La conexion no esta en ahp_veterinaria.")
        cur.execute(
            "SELECT TABLE_NAME FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA=%s AND TABLE_TYPE='BASE TABLE' AND TABLE_NAME<>'auditoria' ORDER BY TABLE_NAME", (DATABASE,),
        )
        actual_tables = tuple(row[0] for row in cur.fetchall())
        if set(actual_tables) != set(TABLES):
            raise RuntimeError(f"Esquema inesperado: se esperaban 15 tablas, se encontraron {len(actual_tables)}.")
        cur.execute("SELECT COUNT(*) FROM information_schema.REFERENTIAL_CONSTRAINTS WHERE CONSTRAINT_SCHEMA=%s", (DATABASE,))
        if cur.fetchone()[0] != 19:
            raise RuntimeError("Se esperaban exactamente 19 claves foraneas.")
        orphan_count = count_orphans(cur, DATABASE)
        if orphan_count:
            raise RuntimeError(f"La base ya contiene {orphan_count} filas huerfanas; no se insertaron fixtures.")
        cur.execute("SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=%s AND TABLE_NAME='auditoria' AND TABLE_TYPE='BASE TABLE'", (DATABASE,))
        if cur.fetchone()[0] != 1:
            raise RuntimeError("Instala y verifica auditoria antes de cargar fixtures.")
        cur.execute("SELECT COUNT(*) FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=%s AND LEFT(TRIGGER_NAME,4)='aud_'", (DATABASE,))
        if cur.fetchone()[0] != 47:
            raise RuntimeError("Se requieren los 47 triggers verificados antes de cargar fixtures.")

        before = {}
        for table in TABLES:
            cur.execute(f"SELECT COUNT(*) FROM {quote_identifier(table)}")
            before[table] = cur.fetchone()[0]
        missing = {table: max(0, 11 - count) for table, count in before.items()}
        duplicate_groups = count_fixture_duplicates(cur)
        if duplicate_groups:
            raise RuntimeError(f"Fixtures duplicados antes de insertar: {duplicate_groups}; se detuvo.")
        cur.execute("SELECT COUNT(*) FROM auditoria WHERE usuario='SEED_PRUEBAS' AND operacion='INSERT'")
        audit_insert_before = cur.fetchone()[0]
        print(f"Destino confirmado: {DATABASE}")
        print("El seed inserta filas ficticias identificadas y no actualiza ni elimina filas existentes.")
        print("Conteos actuales y faltantes para llegar a 11:")
        for table, count in before.items():
            print(f"  {table}: {count}; faltan {missing[table]}")
        if production:
            if input(f"Escribe exactamente '{CONFIRMATION}' para continuar: ").strip() != CONFIRMATION:
                raise SystemExit("Confirmacion no coincidente; no se ejecutaron los INSERT.")

        try:
            if connection.in_transaction:
                raise RuntimeError("La conexion tiene una transaccion previa; no se ejecutaron INSERT.")
            connection.start_transaction()
            if not connection.in_transaction:
                raise RuntimeError("No se pudo iniciar la transaccion de escritura; no se ejecutaron INSERT.")
            for statement in statements:
                cur.execute(statement)
            after = {}
            for table in TABLES:
                cur.execute(f"SELECT COUNT(*) FROM {quote_identifier(table)}")
                after[table] = cur.fetchone()[0]
            if any(after[table] < 11 for table in TABLES):
                raise RuntimeError("Al menos una tabla sigue con menos de 11 filas; se hara rollback.")
            orphan_count = count_orphans(cur, DATABASE)
            if orphan_count:
                raise RuntimeError(f"Se detectaron {orphan_count} filas huerfanas; se hara rollback.")
            duplicate_groups = count_fixture_duplicates(cur)
            if duplicate_groups:
                raise RuntimeError(f"Se detectaron duplicados de fixtures: {duplicate_groups}; se hara rollback.")
            cur.execute("SELECT COUNT(*) FROM auditoria WHERE usuario='SEED_PRUEBAS' AND operacion='INSERT'")
            audit_insert_count = cur.fetchone()[0] - audit_insert_before
            added_count = sum(after[table] - before[table] for table in TABLES)
            if audit_insert_count != added_count:
                raise RuntimeError(
                    f"Se esperaban {added_count} auditorias INSERT y se encontraron {audit_insert_count}; se hara rollback."
                )
            connection.commit()
        except Exception:
            if connection.in_transaction:
                connection.rollback()
            raise
        print("Fixtures confirmados. Conteos finales:")
        for table, count in after.items():
            print(f"  {table}: {count} (agregados {count - before[table]})")
        print(f"Integridad: 19 FK, {orphan_count} filas huerfanas, sin duplicados de fixtures.")
        print(f"Auditoria: {audit_insert_count} nuevos INSERT registrados como SEED_PRUEBAS.")
        cur.close()
    finally:
        connection.close()


if __name__ == "__main__":
    main()
