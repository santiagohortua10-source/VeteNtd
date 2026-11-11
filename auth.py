"""JWT del portal de clientes. El token viaja en una cookie HttpOnly."""
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


def crear_token(cliente_id):
    ahora = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": str(cliente_id), "iat": ahora, "exp": ahora + timedelta(minutes=EXPIRA_MIN)},
        _clave(), algorithm="HS256")


def cliente_id_actual():
    """Id del cliente según la cookie, o None si falta, es inválida o expiró."""
    token = request.cookies.get(COOKIE)
    if not token:
        return None
    try:
        datos = jwt.decode(token, _clave(), algorithms=["HS256"],
                           options={"require": ["exp", "sub"]})
        return int(datos["sub"])
    except (jwt.InvalidTokenError, ValueError):
        return None


def poner_cookie(respuesta, cliente_id):
    respuesta.set_cookie(COOKIE, crear_token(cliente_id), max_age=EXPIRA_MIN * 60,
                         httponly=True, samesite="Lax",
                         secure=os.getenv("COOKIE_SECURE", "0") == "1")
    return respuesta


def borrar_cookie(respuesta):
    respuesta.delete_cookie(COOKIE)
    return respuesta