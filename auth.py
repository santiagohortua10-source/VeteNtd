"""JWT del portal de clientes y del portal de veterinarios.
El token viaja en una cookie HttpOnly y lleva el id y el rol de quien inició sesión."""
import os
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt  # PyJWT
from flask import jsonify, redirect, request
from werkzeug.security import check_password_hash

import db

COOKIE = "access_token"
CARGO_ADMIN = "Administrador"
EXPIRA_MIN = int(os.getenv("JWT_EXP_MINUTOS", "60"))


def _clave():
    clave = os.getenv("JWT_SECRET_KEY")
    if not clave:
        raise RuntimeError("Define JWT_SECRET_KEY en el .env")
    return clave


def crear_token(sujeto_id, rol="Cliente"):
    ahora = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(sujeto_id), "rol": rol, "iat": ahora,
         "exp": ahora + timedelta(minutes=EXPIRA_MIN)},
        _clave(), algorithm="HS256")


def _datos_token():
    """(id, rol) según la cookie, o None si falta, es inválida o expiró."""
    token = request.cookies.get(COOKIE)
    if not token:
        return None
    try:
        datos = jwt.decode(token, _clave(), algorithms=["HS256"],
                           options={"require": ["exp", "sub"]})
        return int(datos["sub"]), datos.get("rol", "Cliente")
    except (jwt.InvalidTokenError, ValueError):
        return None


def cliente_id_actual():
    """Id del cliente, o None si no hay sesión o la sesión es de otro rol."""
    t = _datos_token()
    return t[0] if t and t[1] == "Cliente" else None


def veterinario_id_actual():
    """ID_Empleado del veterinario, o None si no hay sesión o la sesión es de otro rol."""
    t = _datos_token()
    return t[0] if t and t[1] == "Veterinario" else None


def poner_cookie(respuesta, sujeto_id, rol="Cliente"):
    respuesta.set_cookie(COOKIE, crear_token(sujeto_id, rol), max_age=EXPIRA_MIN * 60,
                         httponly=True, samesite="Lax",
                         secure=os.getenv("COOKIE_SECURE", "0") == "1")
    return respuesta


def borrar_cookie(respuesta):
    respuesta.delete_cookie(COOKIE)
    return respuesta


def credenciales_admin(correo, clave):
    """(ID_Empleado, nombre) si el correo y la contraseña son de un administrador; si no, None.
    Los formularios de ingreso de clientes y de veterinarios la usan para dejar entrar también
    al administrador (que siempre termina en su panel, /equipo)."""
    fila = db.consultar(
        "SELECT ID_Empleado, NombreEmpleado, ClaveHash FROM EMPLEADO "
        "WHERE CorreoEmpleado = %s AND CargoEmpleado = %s", (correo, CARGO_ADMIN), uno=True)
    if fila and fila["ClaveHash"] and check_password_hash(fila["ClaveHash"], clave):
        return fila["ID_Empleado"], fila["NombreEmpleado"]
    return None


def admin_id_actual():
    """ID_Empleado del administrador, o None si no hay sesión o la sesión es de otro rol."""
    t = _datos_token()
    return t[0] if t and t[1] == "Administrador" else None


def solo_admin(vista):
    """Protege el panel de administración: exige una sesión (JWT) con rol Administrador.
    Sin sesión: las rutas /api/ responden 401 y las páginas redirigen al ingreso común (/cliente)."""
    @wraps(vista)
    def interior(*args, **kwargs):
        if not admin_id_actual():
            if request.path.startswith("/api/"):
                return jsonify({"estado": "error",
                                "mensaje": "Inicia sesión como administrador"}), 401
            return redirect("/cliente")
        return vista(*args, **kwargs)
    return interior
