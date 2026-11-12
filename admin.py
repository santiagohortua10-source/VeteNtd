"""Administración: salida de sesión y atajo /admin.

El administrador no tiene formulario propio: puede ingresar por el formulario de clientes o por el
de veterinarios (ver auth.credenciales_admin) y siempre termina en su panel (/equipo). Su cuenta
vive en EMPLEADO con CargoEmpleado = 'Administrador'; se crea con  python database/crear_administrador.py
o con database/administrador.sql.
"""
from flask import Blueprint, redirect

import auth
from clientes import _ok

bp = Blueprint("admin", __name__)


@bp.route("/admin")
def portal():
    # Atajo: con sesión de administrador va al panel; si no, al ingreso común
    return redirect("/equipo" if auth.admin_id_actual() else "/cliente")


@bp.post("/api/admin/logout")
def logout():
    return auth.borrar_cookie(_ok())
