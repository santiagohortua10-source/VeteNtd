"""Crea (o actualiza) la cuenta de un veterinario en la tabla EMPLEADO.

Las cuentas de veterinario ya no se crean desde la página: las da de alta el administrador.

Uso (desde la carpeta del proyecto, con el .env ya configurado y MySQL encendido):
    python database/crear_veterinario.py

- Si el nombre ya existe en EMPLEADO (por ejemplo, uno de los veterinarios de ejemplo), solo se le
  asignan correo y contraseña.
- Si no existe, se crea el empleado nuevo con el cargo que elijas.
- Si el correo ya lo usa otra persona, no se cambia nada.
Es seguro ejecutarlo varias veces; volver a usar el mismo nombre cambia su correo y contraseña.
"""
import getpass
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from werkzeug.security import generate_password_hash  # noqa: E402

import db  # noqa: E402


def pedir(texto, minimo=1, maximo=100):
    while True:
        valor = input(texto).strip()
        if minimo <= len(valor) <= maximo:
            return valor
        print(f"  Debe tener entre {minimo} y {maximo} caracteres.")


def main():
    nombre = pedir("Nombre completo del veterinario: ", 2, 50)
    existente = db.consultar("SELECT ID_Empleado, CargoEmpleado FROM EMPLEADO "
                             "WHERE NombreEmpleado = %s ORDER BY ID_Empleado LIMIT 1", (nombre,), uno=True)

    if existente:
        if not existente["CargoEmpleado"].startswith("Veterinari"):
            print(f"✘ '{nombre}' existe pero su cargo es '{existente['CargoEmpleado']}'. "
                  "Solo los cargos Veterinario o Veterinaria pueden iniciar sesión en este portal.")
            return 1
        print(f"'{nombre}' ya existe: se le asignarán el correo y la contraseña.")
    else:
        contacto = pedir("Teléfono: ", 1, 20)
        cargo = ""
        while cargo not in ("Veterinario", "Veterinaria"):
            cargo = input("Cargo (Veterinario o Veterinaria): ").strip().capitalize()

    while True:
        correo = pedir("Correo (será su usuario para ingresar): ", 5, 100).lower()
        if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", correo):
            break
        print("  Escribe un correo válido.")

    otro = db.consultar("SELECT ID_Empleado FROM EMPLEADO WHERE CorreoEmpleado = %s", (correo,), uno=True)
    if otro and (not existente or otro["ID_Empleado"] != existente["ID_Empleado"]):
        print("✘ Ese correo ya lo usa otro empleado. No se cambió nada.")
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
        db.ejecutar("UPDATE EMPLEADO SET CorreoEmpleado = %s, ClaveHash = %s WHERE ID_Empleado = %s",
                    (correo, clave_hash, existente["ID_Empleado"]))
        print(f"✔ Listo: '{nombre}' ya puede iniciar sesión con {correo}.")
    else:
        db.ejecutar("INSERT INTO EMPLEADO (NombreEmpleado, ContactoEmpleado, CargoEmpleado, "
                    "CorreoEmpleado, ClaveHash) VALUES (%s, %s, %s, %s, %s)",
                    (nombre, contacto, cargo, correo, clave_hash))
        print(f"✔ Veterinario '{nombre}' creado. Ya puede iniciar sesión con {correo}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())