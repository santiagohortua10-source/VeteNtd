"""Restaura backups en un schema temporal y valida su estructura y filas."""
import os
import re
import subprocess
import tempfile
import argparse
from collections import defaultdict
from pathlib import Path
from secrets import token_hex

import mysql.connector

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import db


ROOT = Path(__file__).resolve().parents[1]
BACKUPS = ROOT / "backups"
MYSQL = Path(r"C:\xampp\mysql\bin\mysql.exe")
PREFIX = "pawcare_restore_check_"
EXPECTED_TABLES = (
    "catalogo_servicios", "cliente", "detalle_factura", "empleado", "facturacion",
    "historial_clinico", "horario", "mascota", "pago", "pedidos", "pedido_detalle",
    "productos", "reservas", "responsable_alterno", "usuarios",
)


def option_value(value):
    value = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return '"' + value.replace("\n", "\\n").replace("\r", "\\r") + '"'


def pick_backup(kind):
    paths = sorted(BACKUPS.glob(f"ahp_veterinaria_{kind}_*.sql"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not paths:
        raise FileNotFoundError(f"No hay backup de {kind} en {BACKUPS}")
    return paths[0]


def safe_sql(path, target, require_create):
    content = path.read_text(encoding="utf-8")
    if re.search(r"(?i)\bDROP\s+(?:TABLE|DATABASE)\b", content):
        raise ValueError(f"Se rechazó backup con DROP: {path.name}")
    uses = re.findall(r"(?im)^\s*USE\s+`?([A-Za-z0-9_]+)`?\s*;", content)
    if uses not in ([], ["ahp_veterinaria"]):
        raise ValueError(f"USE inesperado en {path.name}: {uses}")
    content = re.sub(r"(?im)^(\s*USE\s+)`?ahp_veterinaria`?(\s*;)", rf"\g<1>`{target}`\g<2>", content)
    if require_create and not re.search(r"(?im)^CREATE TABLE\s+`?", content):
        raise ValueError("El archivo de estructura no contiene CREATE TABLE.")
    if not require_create and re.search(r"(?im)^CREATE TABLE\b", content):
        raise ValueError("El archivo de datos contiene DDL.")
    return content


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", help="Schema pawcare_restore_check_* vacío creado por una ejecución interrumpida.")
    parser.add_argument("--verify-existing", help="Valida de solo lectura un schema pawcare_restore_check_* ya restaurado.")
    args = parser.parse_args()
    if args.target and args.verify_existing:
        raise ValueError("Usa --target o --verify-existing, no ambos.")
    if not MYSQL.is_file():
        raise FileNotFoundError(f"No se encontró mysql.exe: {MYSQL}")
    schema_dump = pick_backup("estructura")
    data_dump = pick_backup("datos")
    verify_only = bool(args.verify_existing)
    if not verify_only:
        # Validate the input files before creating any schema.
        safe_sql(schema_dump, "pawcare_restore_check_preflight", True)
        safe_sql(data_dump, "pawcare_restore_check_preflight", False)
    target = args.verify_existing or args.target or PREFIX + token_hex(6)
    if not re.fullmatch(r"pawcare_restore_check_[a-f0-9]{12}", target):
        raise ValueError("Nombre de destino no permitido.")

    config = db._configuracion()
    config["database"] = "ahp_veterinaria"
    admin = mysql.connector.connect(**config)
    try:
        cur = admin.cursor()
        cur.execute("SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME=%s", (target,))
        exists = cur.fetchone() is not None
        if verify_only:
            if not exists:
                raise RuntimeError("No existe el schema temporal indicado; no se modificó nada.")
        elif exists:
            if not args.target:
                raise RuntimeError("El destino temporal ya existe; se cancela sin sobrescribir.")
            cur.execute("SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=%s", (target,))
            if cur.fetchone()[0] != 0:
                raise RuntimeError("El destino indicado no está vacío; se cancela sin modificarlo.")
        else:
            cur.execute("CREATE DATABASE `" + target + "` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            admin.commit()
    finally:
        admin.close()

    if not verify_only:
        schema_text = safe_sql(schema_dump, target, True)
        data_text = safe_sql(data_dump, target, False)
        fd, defaults = tempfile.mkstemp(prefix="pawcare-restore-", suffix=".cnf")
        os.chmod(defaults, 0o600)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
                f.write("[client]\n")
                for key in ("host", "port", "user", "password"):
                    f.write(f"{key}={option_value(config[key])}\n")
                f.write("protocol=tcp\n")
            for label, sql in (("estructura", schema_text), ("datos", data_text)):
                result = subprocess.run(
                    [str(MYSQL), "--defaults-extra-file=" + defaults, "--default-character-set=utf8mb4", "--database=" + target],
                    input=sql.encode("utf-8"), capture_output=True, timeout=180, check=False,
                )
                if result.returncode:
                    # Do not delete a partially restored schema; keep it for inspection.
                    raise RuntimeError(f"Importación de {label} falló (código {result.returncode}); destino conservado: {target}")
        finally:
            try:
                os.unlink(defaults)
            except OSError:
                pass

    restored_cfg = dict(config, database=target)
    conn = mysql.connector.connect(**restored_cfg)
    try:
        cur = conn.cursor()
        cur.execute("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA=%s AND TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME", (target,))
        tables = [row[0] for row in cur.fetchall()]
        if tuple(tables) != EXPECTED_TABLES:
            raise RuntimeError(f"El conjunto de tablas restauradas no coincide con las 15 esperadas. Destino: {target}")
        cur.execute("SELECT COUNT(*) FROM information_schema.REFERENTIAL_CONSTRAINTS WHERE CONSTRAINT_SCHEMA=%s", (target,))
        fk_count = cur.fetchone()[0]
        if fk_count != 19:
            raise RuntimeError(f"Se esperaban 19 relaciones FK; hay {fk_count}. Destino: {target}")
        cur.execute(
            "SELECT TABLE_NAME,CONSTRAINT_NAME,COLUMN_NAME,REFERENCED_TABLE_NAME,REFERENCED_COLUMN_NAME "
            "FROM information_schema.KEY_COLUMN_USAGE WHERE TABLE_SCHEMA=%s "
            "AND REFERENCED_TABLE_NAME IS NOT NULL ORDER BY TABLE_NAME,CONSTRAINT_NAME,ORDINAL_POSITION",
            (target,),
        )
        foreign_keys = defaultdict(list)
        for child, constraint, child_col, parent, parent_col in cur.fetchall():
            foreign_keys[(child, constraint, parent)].append((child_col, parent_col))
        orphan_count = 0
        for (child, constraint, parent), columns in foreign_keys.items():
            joins = " AND ".join(f"p.`{parent_col}` = c.`{child_col}`" for child_col, parent_col in columns)
            non_null = " AND ".join(f"c.`{child_col}` IS NOT NULL" for child_col, _ in columns)
            cur.execute(
                f"SELECT COUNT(*) FROM `{child}` c LEFT JOIN `{parent}` p ON {joins} "
                f"WHERE {non_null} AND p.`{columns[0][1]}` IS NULL"
            )
            orphan_count += cur.fetchone()[0]
        if orphan_count:
            raise RuntimeError(f"Se detectaron {orphan_count} filas huérfanas en las FK; destino: {target}")
        counts = {}
        for table in tables:
            cur.execute(f"SELECT COUNT(*) FROM `{table}`")
            counts[table] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=%s", (target,))
        triggers = cur.fetchone()[0]
        print(f"Destino temporal: {target}")
        print(f"Backups: {schema_dump.name}; {data_dump.name}")
        print(f"Validación: {len(tables)} tablas, {fk_count} claves foráneas, "
              f"{orphan_count} filas huérfanas, {triggers} triggers restaurados")
        for table, count in counts.items():
            print(f"{table}: {count}")
        print("El schema temporal se conserva para inspección; no se modificó ninguna base original.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
