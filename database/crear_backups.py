"""Genera backups no destructivos de ahp_veterinaria usando mysqldump."""
import argparse
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import mysql.connector

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import db


DATABASE = "ahp_veterinaria"
ROOT = Path(__file__).resolve().parents[1]
BACKUP_DIR = ROOT / "backups"


def find_mysqldump(explicit=None):
    candidates = [explicit] if explicit else []
    candidates += [
        r"C:\xampp\mysql\bin\mysqldump.exe",
        r"C:\Program Files\MySQL\MySQL Server 9.7\bin\mysqldump.exe",
    ]
    path_candidate = __import__("shutil").which("mysqldump")
    if path_candidate:
        candidates.append(path_candidate)
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return str(Path(candidate))
    raise FileNotFoundError("No se encontró mysqldump; no se creó ningún backup.")


def option_value(value):
    value = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return '"' + value.replace("\n", "\\n").replace("\r", "\\r") + '"'


def make_defaults_file(config):
    descriptor, filename = tempfile.mkstemp(prefix="pawcare-mysqldump-", suffix=".cnf")
    os.chmod(filename, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
        stream.write("[client]\n")
        for key in ("host", "port", "user", "password"):
            stream.write(f"{key}={option_value(config[key])}\n")
        stream.write("protocol=tcp\n")
    return filename


def run_dump(binary, defaults_file, mode, output_path):
    common = [binary, "--defaults-extra-file=" + defaults_file, "--skip-add-drop-table"]
    if mode == "estructura":
        options = ["--no-data", "--triggers", "--routines", "--events", "--skip-lock-tables"]
    else:
        options = ["--no-create-info", "--skip-triggers", "--single-transaction", "--skip-lock-tables", "--hex-blob"]
    result = subprocess.run(
        common + options + [DATABASE], capture_output=True, timeout=180, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"mysqldump ({mode}) falló con código {result.returncode}; no se guardó su salida.")
    if not result.stdout:
        raise RuntimeError(f"mysqldump ({mode}) devolvió un archivo vacío.")
    with output_path.open("xb") as stream:
        stream.write(result.stdout)
    return result.stdout


def validate_dumps(schema_sql, data_sql, table_names):
    schema_text = schema_sql.decode("utf-8")
    data_text = data_sql.decode("utf-8")
    schema_tables = set(re.findall(r"(?im)^CREATE TABLE\s+`?([A-Za-z0-9_]+)`?", schema_text))
    if schema_tables != set(table_names):
        raise RuntimeError("El backup de estructura no contiene exactamente las 15 tablas esperadas.")
    if re.search(r"(?i)\bDROP\s+(?:TABLE|DATABASE)\b", schema_text + data_text):
        raise RuntimeError("Un backup contiene una instrucción DROP; se detuvo la validación.")
    if re.search(r"(?im)^CREATE TABLE\b", data_text):
        raise RuntimeError("El backup de datos contiene DDL inesperado.")
    insert_tables = set(re.findall(r"(?im)^INSERT INTO\s+`?([A-Za-z0-9_]+)`?", data_text))
    if not insert_tables or not insert_tables.issubset(set(table_names)):
        raise RuntimeError("El backup de datos no contiene INSERTs válidos para tablas esperadas.")
    return len(schema_tables), len(insert_tables)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mysqldump", help="Ruta opcional al ejecutable mysqldump.")
    args = parser.parse_args()
    binary = find_mysqldump(args.mysqldump)

    config = db._configuracion()
    config["database"] = DATABASE
    connection = mysql.connector.connect(**config)
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT VERSION()")
        server_version = cursor.fetchone()[0]
        cursor.execute(
            "SELECT TABLE_NAME FROM information_schema.TABLES "
            "WHERE TABLE_SCHEMA=%s AND TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME",
            (DATABASE,),
        )
        table_names = [row[0] for row in cursor.fetchall()]
        cursor.close()
    finally:
        connection.close()
    if len(table_names) != 15:
        raise RuntimeError(f"Se esperaban 15 tablas en {DATABASE}; no se generaron backups.")

    BACKUP_DIR.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = os.urandom(3).hex()
    paths = {
        "estructura": BACKUP_DIR / f"{DATABASE}_estructura_{stamp}_{suffix}.sql",
        "datos": BACKUP_DIR / f"{DATABASE}_datos_{stamp}_{suffix}.sql",
    }
    defaults_file = make_defaults_file(config)
    try:
        schema_sql = run_dump(binary, defaults_file, "estructura", paths["estructura"])
        data_sql = run_dump(binary, defaults_file, "datos", paths["datos"])
    finally:
        try:
            os.unlink(defaults_file)
        except OSError:
            pass

    schema_count, insert_count = validate_dumps(schema_sql, data_sql, table_names)
    print(f"Servidor: {server_version}")
    print(f"mysqldump: {binary}")
    print(f"Estructura válida: {paths['estructura'].name} ({paths['estructura'].stat().st_size} bytes, {schema_count} tablas)")
    print(f"Datos válidos: {paths['datos'].name} ({paths['datos'].stat().st_size} bytes, {insert_count} tablas con INSERT)")


if __name__ == "__main__":
    main()
