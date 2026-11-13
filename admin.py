"""Administración: salida de sesión, atajo /admin y gestión de veterinarios.

El administrador no tiene formulario propio: puede ingresar por el formulario de clientes o por el
de veterinarios (ver auth.credenciales_admin) y siempre termina en su panel (/equipo). Su cuenta
vive en EMPLEADO con CargoEmpleado = 'Administrador'; se crea con  python database/crear_administrador.py
o con database/administrador.sql.

Gestión de veterinarios (solo rol Administrador): ver, agregar, editar y eliminar. Solo se tocan filas de
EMPLEADO cuyo cargo es 'Veterinario' o 'Veterinaria'; las cuentas de administrador quedan fuera.
"""
import re

from flask import Blueprint, redirect, request
from werkzeug.security import generate_password_hash

import auth
import db
from clientes import _cuerpo, _error, _ok

bp = Blueprint("admin", __name__)

CARGOS_VET = ("Veterinario", "Veterinaria")
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

SELECT_VET = (
    "SELECT e.ID_Empleado AS id, e.NombreEmpleado AS nombre, e.ContactoEmpleado AS contacto, "
    "e.CargoEmpleado AS cargo, e.CorreoEmpleado AS correo, "
    "(e.ClaveHash IS NOT NULL AND e.ClaveHash <> '') AS tiene_clave, "
    "(SELECT COUNT(*) FROM RESERVAS r WHERE r.ID_Empleado = e.ID_Empleado) AS citas, "
    "(SELECT COUNT(*) FROM HISTORIAL_CLINICO h WHERE h.ID_Empleado = e.ID_Empleado) AS atenciones "
    "FROM EMPLEADO e WHERE e.CargoEmpleado LIKE %s"
)


@bp.route("/admin")
def portal():
    # Atajo: con sesión de administrador va al panel; si no, al ingreso común
    return redirect("/equipo" if auth.admin_id_actual() else "/cliente")


@bp.post("/api/admin/logout")
def logout():
    return auth.borrar_cookie(_ok())


# ---------- Veterinarios (solo administrador) ----------
def _hhmm(t):
    """Las columnas TIME llegan como timedelta: 8:00:00 -> '08:00'."""
    segundos = int(t.total_seconds())
    return f"{segundos // 3600:02d}:{segundos % 3600 // 60:02d}"


def _con_horarios(vets):
    """Agrega a cada veterinario sus días y horarios de atención (solo lectura)."""
    bloques = {}
    for f in db.consultar("SELECT ID_Empleado AS eid, DiaSemana AS dia, HoraInicio AS ini, HoraFin AS fin "
                          "FROM HORARIO ORDER BY ID_Empleado, HoraInicio"):
        bloques.setdefault(f["eid"], {}).setdefault(f["dia"], []).append(f"{_hhmm(f['ini'])}–{_hhmm(f['fin'])}")
    for v in vets:
        por_dia = bloques.get(v["id"], {})
        dias = sorted(por_dia, key=lambda d: DIAS.index(d) if d in DIAS else len(DIAS))
        v["tiene_clave"] = bool(v["tiene_clave"])
        v["dias"] = dias
        v["horarios"] = [f"{d}: {', '.join(por_dia[d])}" for d in dias]
    return vets


def _veterinario(vid):
    """El veterinario (dict) o None. Nunca devuelve administradores ni el hash de la contraseña."""
    vets = db.consultar(SELECT_VET + " AND e.ID_Empleado = %s", ("Veterinari%", vid))
    return _con_horarios(vets)[0] if vets else None


def _validar_veterinario(d, clave_obligatoria=False):
    """(valores, None) si es válido, o (None, mensaje).
    Al editar la contraseña es opcional (si viene, se cambia); al crear es obligatoria."""
    nombre = str(d.get("nombre", "")).strip()
    contacto = str(d.get("contacto", "")).strip()
    correo = str(d.get("correo", "")).strip().lower()
    cargo = str(d.get("cargo", "")).strip()
    clave = str(d.get("clave", ""))
    if not 2 <= len(nombre) <= 50:
        return None, "El nombre debe tener entre 2 y 50 caracteres"
    if not re.fullmatch(r"[0-9+\s-]{7,20}", contacto):
        return None, "Escribe un teléfono válido (7 a 20 dígitos)"
    if len(correo) > 100 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", correo):
        return None, "Escribe un correo válido"
    if cargo not in CARGOS_VET:
        return None, "El cargo debe ser Veterinario o Veterinaria"
    if clave_obligatoria and not clave:
        return None, "La contraseña es obligatoria"
    if clave and len(clave) < 8:
        return None, "La contraseña debe tener al menos 8 caracteres"
    return {"nombre": nombre, "contacto": contacto, "correo": correo, "cargo": cargo, "clave": clave}, None

HORA_RE = re.compile(r"([01]\d|2[0-3]):[0-5]\d")


def _validar_horarios(lista):
    """([(dia, inicio, fin), ...], None) si es válido, o (None, mensaje). Es opcional: sin horarios, lista vacía.
    Un mismo día puede tener varios bloques (mañana y tarde), pero no pueden cruzarse entre sí."""
    if lista in (None, ""):
        return [], None
    if not isinstance(lista, list) or len(lista) > 28:
        return None, "Los horarios no son válidos"
    bloques, por_dia = [], {}
    for h in lista:
        if not isinstance(h, dict):
            return None, "Los horarios no son válidos"
        dia = str(h.get("dia", "")).strip()
        ini = str(h.get("inicio", "")).strip()
        fin = str(h.get("fin", "")).strip()
        if dia not in DIAS:
            return None, "Elige un día de la semana válido en cada horario"
        if not HORA_RE.fullmatch(ini) or not HORA_RE.fullmatch(fin):
            return None, f"Completa la hora de inicio y de fin del {dia}"
        if ini >= fin:                               # 'HH:MM' con ceros: la comparación de texto es válida
            return None, f"En el {dia}, la hora de inicio debe ser anterior a la de fin"
        por_dia.setdefault(dia, []).append((ini, fin))
        bloques.append((dia, ini + ":00", fin + ":00"))
    for dia, rangos in por_dia.items():
        rangos.sort()
        for (_, fin_a), (ini_b, _) in zip(rangos, rangos[1:]):
            if ini_b < fin_a:
                return None, f"Los horarios del {dia} se cruzan entre sí"
    return bloques, None
@bp.get("/api/admin/veterinarios")
@auth.solo_admin
def listar_veterinarios():
    vets = db.consultar(SELECT_VET + " ORDER BY e.NombreEmpleado", ("Veterinari%",))
    return _ok(datos=_con_horarios(vets))


@bp.post("/api/admin/veterinarios")
@auth.solo_admin
def crear_veterinario():
    """Da de alta a un veterinario. Solo el administrador puede hacerlo: no existe registro público
    y el cargo se valida en el servidor (nunca se puede crear otro administrador desde aquí)."""
    d = _cuerpo()
    v, error = _validar_veterinario(d, clave_obligatoria=True)
    if error:
        return _error(error, 400)
    horarios, error = _validar_horarios(d.get("horarios"))
    if error:
        return _error(error, 400)
    try:
        with db.transaccion() as cur:                # el veterinario y sus horarios se guardan juntos, o nada
            cur.execute(
                "INSERT INTO EMPLEADO (NombreEmpleado, ContactoEmpleado, CargoEmpleado, CorreoEmpleado, ClaveHash) "
                "VALUES (%s, %s, %s, %s, %s)",
                (v["nombre"], v["contacto"], v["cargo"], v["correo"], generate_password_hash(v["clave"])))
            nuevo_id = cur.lastrowid
            for dia, ini, fin in horarios:
                cur.execute("INSERT INTO HORARIO (ID_Empleado, DiaSemana, HoraInicio, HoraFin) "
                            "VALUES (%s, %s, %s, %s)", (nuevo_id, dia, ini, fin))
    except db.IntegrityError:                        # CorreoEmpleado es UNIQUE
        return _error("Ese correo ya lo usa otro empleado", 409)
    return _ok(mensaje="Veterinario creado correctamente", datos=_veterinario(nuevo_id)), 201


@bp.put("/api/admin/veterinarios/<int:vid>")
@auth.solo_admin
def editar_veterinario(vid):
    if not _veterinario(vid):
        return _error("Veterinario no encontrado", 404)
    v, error = _validar_veterinario(_cuerpo())
    if error:
        return _error(error, 400)

    sql = ("UPDATE EMPLEADO SET NombreEmpleado = %s, ContactoEmpleado = %s, "
           "CargoEmpleado = %s, CorreoEmpleado = %s")
    params = [v["nombre"], v["contacto"], v["cargo"], v["correo"]]
    if v["clave"]:                                   # solo si el administrador escribió una nueva
        sql += ", ClaveHash = %s"
        params.append(generate_password_hash(v["clave"]))
    try:
        db.ejecutar(sql + " WHERE ID_Empleado = %s AND CargoEmpleado LIKE %s", (*params, vid, "Veterinari%"))
    except db.IntegrityError:                        # CorreoEmpleado es UNIQUE
        return _error("Ese correo ya lo usa otro empleado", 409)
    return _ok(mensaje="Veterinario actualizado correctamente", datos=_veterinario(vid))


@bp.delete("/api/admin/veterinarios/<int:vid>")
@auth.solo_admin
def eliminar_veterinario(vid):
    vet = _veterinario(vid)
    if not vet:
        return _error("Veterinario no encontrado", 404)
    if vet["citas"] or vet["atenciones"]:
        # Las citas y el historial clínico son registros que no se deben perder ni quedar huérfanos
        return _error(f"No se puede eliminar: tiene {vet['citas']} cita(s) y {vet['atenciones']} "
                      "atención(es) en el historial clínico", 409)
    try:
        with db.transaccion() as cur:                # sus horarios se borran junto con él, o no se borra nada
            cur.execute("DELETE FROM HORARIO WHERE ID_Empleado = %s", (vid,))
            cur.execute("DELETE FROM EMPLEADO WHERE ID_Empleado = %s AND CargoEmpleado LIKE %s",
                        (vid, "Veterinari%"))
    except db.IntegrityError:                        # alguien agendó con él justo ahora
        return _error("No se puede eliminar: tiene citas asociadas", 409)
    return _ok(mensaje="Veterinario eliminado correctamente", datos=vet)