"""Portal del veterinario: login, registro, citas propias e historial clínico de mascotas."""
import hmac
import os
import re
from functools import wraps

from flask import Blueprint, redirect, render_template, request
from werkzeug.security import check_password_hash, generate_password_hash

import auth
import db
from clientes import _cuerpo, _error, _hhmm, _minutos, _ok

bp = Blueprint("veterinarios", __name__)


def requiere_veterinario(vista):
    @wraps(vista)
    def interior(*args, **kwargs):
        vid = auth.veterinario_id_actual()
        if not vid:
            return _error("Inicia sesión como veterinario", 401)
        return vista(vid, *args, **kwargs)
    return interior


@bp.route("/veterinario")
def portal():
    vid = auth.veterinario_id_actual()
    vet = db.consultar("SELECT ID_Empleado AS id, NombreEmpleado AS nombre "
                       "FROM EMPLEADO WHERE ID_Empleado = %s", (vid,), uno=True) if vid else None
    if not vet:
        # Sin sesión (o cuenta borrada): vuelve al portal único y limpia la cookie
        return auth.borrar_cookie(redirect("/cliente"))
    return render_template("veterinario.html", vet=vet)


@bp.post("/api/veterinario/registro")
def registro():
    d = _cuerpo()
    esperado = os.getenv("CODIGO_VETERINARIO", "")
    recibido = str(d.get("codigo", ""))
    if not esperado or not hmac.compare_digest(recibido.encode(), esperado.encode()):
        return _error("Código de la clínica incorrecto", 403)

    nombre = str(d.get("nombre", "")).strip()
    contacto = str(d.get("contacto", "")).strip()
    correo = str(d.get("correo", "")).strip().lower()
    clave = str(d.get("clave", ""))
    cargo = str(d.get("cargo", "")).strip()

    if not 2 <= len(nombre) <= 50:
        return _error("El nombre debe tener entre 2 y 50 caracteres")
    if not 1 <= len(contacto) <= 20:
        return _error("El teléfono es obligatorio (máx. 20 caracteres)")
    if len(correo) > 100 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", correo):
        return _error("Correo no válido")
    if len(clave) < 8:
        return _error("La contraseña debe tener al menos 8 caracteres")
    if cargo not in ("Veterinario", "Veterinaria"):
        return _error("Elige un cargo válido")

    try:
        with db.transaccion() as cur:
            cur.execute("INSERT INTO EMPLEADO (NombreEmpleado, ContactoEmpleado, CargoEmpleado) "
                        "VALUES (%s, %s, %s)", (nombre, contacto, cargo))
            eid = cur.lastrowid
            cur.execute("INSERT INTO USUARIOS (ID_Empleado, Nombre, Correo, ClaveHash, Rol) "
                        "VALUES (%s, %s, %s, %s, 'Veterinario')",
                        (eid, nombre, correo, generate_password_hash(clave)))
    except db.IntegrityError:
        return _error("Ya existe una cuenta con ese correo", 409)

    return auth.poner_cookie(_ok(datos={"nombre": nombre}), eid, "Veterinario")

@bp.post("/api/veterinario/logout")
def logout():
    return auth.borrar_cookie(_ok())


# ---------- Mis citas ----------
@bp.get("/api/veterinario/citas")
@requiere_veterinario
def citas(vid):
    filas = db.consultar(
        "SELECT r.ID_Reserva AS id, r.FechaReserva AS fecha, r.HoraReserva AS hora, "
        "r.EstadoCita AS estado, m.ID_Mascota AS mascota_id, m.NombreMascota AS mascota, "
        "c.NombreCliente AS cliente, c.ContactoCliente AS contacto, s.Servicio AS servicio "
        "FROM RESERVAS r "
        "JOIN MASCOTA m ON m.ID_Mascota = r.ID_Mascota "
        "JOIN CLIENTE c ON c.ID_Cliente = m.ID_Cliente "
        "JOIN CATALOGO_SERVICIOS s ON s.ID_CataServicio = r.ID_CataServicio "
        "WHERE r.ID_Empleado = %s ORDER BY r.FechaReserva DESC, r.HoraReserva DESC", (vid,))
    for f in filas:
        f["fecha"] = f["fecha"].isoformat()
        f["hora"] = _hhmm(_minutos(f["hora"]))
    return _ok(datos=filas)


# ---------- Mascotas ----------
@bp.get("/api/veterinario/mascotas")
@requiere_veterinario
def buscar_mascotas(vid):
    q = f"%{request.args.get('q', '').strip()}%"
    filas = db.consultar(
        "SELECT m.ID_Mascota AS id, m.NombreMascota AS nombre, m.Especie AS especie, "
        "m.Raza AS raza, c.NombreCliente AS dueno "
        "FROM MASCOTA m JOIN CLIENTE c ON c.ID_Cliente = m.ID_Cliente "
        "WHERE m.NombreMascota LIKE %s OR c.NombreCliente LIKE %s "
        "ORDER BY m.NombreMascota LIMIT 50", (q, q))
    return _ok(datos=filas)


@bp.get("/api/veterinario/mascotas/<int:mascota_id>/historial")
@requiere_veterinario
def historial(vid, mascota_id):
    m = db.consultar(
        "SELECT m.ID_Mascota AS id, m.NombreMascota AS nombre, m.Especie AS especie, "
        "m.Raza AS raza, m.FechaNacimiento AS nacimiento, m.Peso AS peso, m.Genero AS genero, "
        "c.NombreCliente AS dueno, c.ContactoCliente AS contacto "
        "FROM MASCOTA m JOIN CLIENTE c ON c.ID_Cliente = m.ID_Cliente "
        "WHERE m.ID_Mascota = %s", (mascota_id,), uno=True)
    if not m:
        return _error("Mascota no encontrada", 404)
    m["nacimiento"] = m["nacimiento"].isoformat()
    m["peso"] = float(m["peso"])

    clinico = db.consultar(
        "SELECT h.ID_Reserva AS reserva_id, h.FechaHora AS fecha, h.Diagnostico AS diagnostico, "
        "h.Tratamiento AS tratamiento, e.NombreEmpleado AS veterinario "
        "FROM HISTORIAL_CLINICO h JOIN EMPLEADO e ON e.ID_Empleado = h.ID_Empleado "
        "WHERE h.ID_Mascota = %s ORDER BY h.FechaHora DESC", (mascota_id,))
    for f in clinico:
        f["fecha"] = f["fecha"].isoformat(sep=" ", timespec="minutes")

    citas_m = db.consultar(
        "SELECT r.ID_Reserva AS id, r.FechaReserva AS fecha, r.HoraReserva AS hora, "
        "r.EstadoCita AS estado, s.Servicio AS servicio, e.NombreEmpleado AS veterinario "
        "FROM RESERVAS r "
        "JOIN CATALOGO_SERVICIOS s ON s.ID_CataServicio = r.ID_CataServicio "
        "JOIN EMPLEADO e ON e.ID_Empleado = r.ID_Empleado "
        "WHERE r.ID_Mascota = %s ORDER BY r.FechaReserva DESC, r.HoraReserva DESC", (mascota_id,))
    for f in citas_m:
        f["fecha"] = f["fecha"].isoformat()
        f["hora"] = _hhmm(_minutos(f["hora"]))
    return _ok(datos={"mascota": m, "clinico": clinico, "citas": citas_m})


# ---------- Opcional: registrar una atención ----------
@bp.post("/api/veterinario/mascotas/<int:mascota_id>/historial")
@requiere_veterinario
def agregar_historial(vid, mascota_id):
    d = _cuerpo()
    diag = str(d.get("diagnostico", "")).strip()
    trat = str(d.get("tratamiento", "")).strip()
    try:
        rid = int(d.get("reserva_id"))
    except (TypeError, ValueError):
        return _error("Indica la cita a la que pertenece la atención")
    if not diag or not trat or len(diag) > 500 or len(trat) > 500:
        return _error("Diagnóstico y tratamiento son obligatorios (máx. 500 caracteres)")
    if not db.consultar("SELECT 1 FROM RESERVAS WHERE ID_Reserva = %s AND ID_Mascota = %s "
                        "AND ID_Empleado = %s", (rid, mascota_id, vid), uno=True):
        return _error("Esa cita no es tuya o no corresponde a esta mascota", 403)
    db.ejecutar("INSERT INTO HISTORIAL_CLINICO (ID_Empleado, ID_Mascota, ID_Reserva, FechaHora, "
                "Diagnostico, Tratamiento) VALUES (%s, %s, %s, NOW(), %s, %s)",
                (vid, mascota_id, rid, diag, trat))
    return _ok()