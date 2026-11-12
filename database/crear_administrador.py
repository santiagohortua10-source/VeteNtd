"""Crea (o actualiza) la cuenta del administrador en la tabla EMPLEADO (CargoEmpleado = 'Administrador').

Uso (desde la carpeta del proyecto, con el .env ya configurado y MySQL encendido):
    python database/crear_administrador.py

- Si ya existe un administrador con ese correo, solo se le cambia la contraseña.
- Si el correo lo usa un empleado que no es administrador, no se cambia nada.
"""
import getpass
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from werkzeug.security import generate_password_hash  # noqa: E402

import db  # noqa: E402

CARGO = "Administrador"


def main():
    nombre = input("Nombre del administrador: ").strip()
    if not 2 <= len(nombre) <= 50:
        print("✘ El nombre debe tener entre 2 y 50 caracteres.")
        return 1

    correo = input("Correo (será su usuario para ingresar): ").strip().lower()
    if len(correo) > 100 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", correo):
        print("✘ Escribe un correo válido.")
        return 1

    existente = db.consultar("SELECT ID_Empleado, CargoEmpleado FROM EMPLEADO WHERE CorreoEmpleado = %s",
                             (correo,), uno=True)
    if existente and existente["CargoEmpleado"] != CARGO:
        print(f"✘ Ese correo ya lo usa un empleado con cargo '{existente['CargoEmpleado']}'. No se cambió nada.")
        return 1

    while True:
        clave = getpass.getpass("Contraseña (mínimo 8 caracteres): ")
        if len(clave) < 8:
            print("  Debe tener al menos 8 caracteres.")
        elif clave != getpass.getpass("Repite la contraseña: "):
            print("  Las contraseñas no coinciden.")
        else:
            break

    clave_hash = generate_password_hash(clave)
    if existente:
        db.ejecutar("UPDATE EMPLEADO SET ClaveHash = %s WHERE ID_Empleado = %s",
                    (clave_hash, existente["ID_Empleado"]))
        print(f"✔ Contraseña actualizada para {correo}.")
    else:
        db.ejecutar("INSERT INTO EMPLEADO (NombreEmpleado, ContactoEmpleado, CargoEmpleado, "
                    "CorreoEmpleado, ClaveHash) VALUES (%s, %s, %s, %s, %s)",
                    (nombre, "3000000000", CARGO, correo, clave_hash))
        print(f"✔ Administrador '{nombre}' creado. Ya puede ingresar en /admin con {correo}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
