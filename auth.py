"""JWT del portal de clientes y del portal de veterinarios.
El token viaja en una cookie HttpOnly y lleva el id y el rol de quien inició sesión."""
import os
from datetime import datetime, timedelta, timezone

import jwt  # PyJWT
from flask import request

COOKIE = "access_token"
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