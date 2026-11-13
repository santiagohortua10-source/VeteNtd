"""Portal de clientes: cuenta, mascotas, agenda de citas y notificaciones propias.

Página:      GET /cliente
API (JSON):  /api/cliente/...
La autenticación usa un JWT (ver auth.py) guardado en una cookie HttpOnly; el token lleva solo el id del cliente.
"""
import os
import re
import unicodedata
from datetime import date, datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from functools import wraps

from flask import Blueprint, jsonify, make_response, redirect, render_template, request
from werkzeug.security import check_password_hash, generate_password_hash

import auth
import db
import notificaciones

bp = Blueprint("clientes", __name__)

PASO_MIN = 30          # las horas se ofrecen cada 30 minutos
DIAS_MAX_AGENDA = 60   # hasta con cuántos días de anticipación se puede agendar
AGENDADA, CANCELADA = "Agendada", "Cancelada"
TAMANOS = ("Pequeño", "Mediano", "Grande")
GENEROS = ("Macho", "Hembra")

DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]

try:
    from zoneinfo import ZoneInfo
    _ZONA = ZoneInfo(os.getenv("ZONA_HORARIA", "America/Bogota"))
except Exception:  # en Windows hace falta:  pip install tzdata
    _ZONA = None


# ---------- Utilidades ----------
def ahora():
    """Hora actual de la clínica (sin zona, para comparar con las citas)."""
    return datetime.now(_ZONA).replace(tzinfo=None) if _ZONA else datetime.now()


def _ok(**datos):
    return jsonify({"estado": "exito", **datos})


def _error(mensaje, codigo=400):
    return jsonify({"estado": "error", "mensaje": mensaje}), codigo


def _cuerpo():
    datos = request.get_json(silent=True)
    return datos if isinstance(datos, dict) else {}


def _norm(texto):
    """'Miércoles' -> 'miercoles' (para comparar días sin importar tildes ni mayúsculas)."""
    sin_tildes = unicodedata.normalize("NFD", str(texto))
    return "".join(c for c in sin_tildes if not unicodedata.combining(c)).lower().strip()


def _formatear_precio(valor):
    return f"{int(valor):,}".replace(",", ".")      # 80000 -> "80.000"


def dia_texto(f):
    return f"{DIAS[f.weekday()]} {f.day} de {MESES[f.month - 1]} de {f.year}"


def hora_texto(minutos):
    h, m = divmod(minutos, 60)
    return f"{h % 12 or 12}:{m:02d} {'a. m.' if h < 12 else 'p. m.'}"


def _hhmm(minutos):
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def _minutos(valor):
    """TIME de MySQL (timedelta) o datetime.time -> minutos desde la medianoche."""
    if isinstance(valor, timedelta):
        return int(valor.total_seconds() // 60)
    return valor.hour * 60 + valor.minute


def _fecha(texto):
    try:
        return datetime.strptime(str(texto), "%Y-%m-%d").date()
    except ValueError:
        return None


def _hora_a_minutos(texto):
    if not re.fullmatch(r"\d{2}:\d{2}", str(texto)):
        return None
    h, m = int(texto[:2]), int(texto[3:])
    return h * 60 + m if h < 24 and m < 60 else None


def _fuera_de_rango(fecha):
    hoy = ahora().date()
    if fecha < hoy:
        return "Esa fecha ya pasó"
    if fecha > hoy + timedelta(days=DIAS_MAX_AGENDA):
        return f"Solo puedes agendar con hasta {DIAS_MAX_AGENDA} días de anticipación"
    return None


def _edad(nacimiento):
    hoy = ahora().date()
    meses = (hoy.year - nacimiento.year) * 12 + hoy.month - nacimiento.month - (hoy.day < nacimiento.day)
    if meses < 1:
        return "Menos de 1 mes"
    if meses < 12:
        return f"{meses} {'mes' if meses == 1 else 'meses'}"
    anios = meses // 12
    return f"{anios} {'año' if anios == 1 else 'años'}"


def requiere_cliente(vista):
    """Protege la ruta: pasa el id del cliente (leído del JWT) como primer argumento."""
    @wraps(vista)
    def interior(*args, **kwargs):
        cid = auth.cliente_id_actual()
        if not cid:
            return _error("Inicia sesión para continuar", 401)
        return vista(cid, *args, **kwargs)
    return interior


def _cliente_actual(cid):
    return db.consultar("SELECT ID_Cliente AS id, NombreCliente AS nombre, CorreoCliente AS correo "
                        "FROM CLIENTE WHERE ID_Cliente = %s", (cid,), uno=True)


# ---------- Disponibilidad de horas ----------
def _consulta_de(cur):
    """Adapta un cursor de transacción a la forma consulta(sql, params) -> filas."""
    def consulta(sql, params=()):
        cur.execute(sql, params)
        return cur.fetchall()
    return consulta


def _ocupado(consulta, columna, valor, fecha):
    """Intervalos (inicio, fin) en minutos de las citas activas de un veterinario o una mascota.
    `columna` sale siempre de este archivo, nunca del usuario."""
    filas = consulta(
        "SELECT r.HoraReserva AS hora, s.DuracionServicio AS dur FROM RESERVAS r "
        "JOIN CATALOGO_SERVICIOS s ON s.ID_CataServicio = r.ID_CataServicio "
        f"WHERE r.{columna} = %s AND r.FechaReserva = %s AND r.EstadoCita <> %s",
        (valor, fecha, CANCELADA))
    return [(_minutos(f["hora"]), _minutos(f["hora"]) + f["dur"]) for f in filas]


def horas_disponibles(consulta, vet_id, duracion, fecha, mascota_id=None):
    """Horas de inicio libres: [{'valor': '10:00', 'texto': '10:00 a. m.'}, ...].
    Una hora sirve si la cita completa cabe en el horario del veterinario, no se cruza con otra
    cita suya (ni de la misma mascota) y no es una hora que ya pasó."""
    dia = _norm(DIAS[fecha.weekday()])
    bloques = [(_minutos(f["HoraInicio"]), _minutos(f["HoraFin"]))
               for f in consulta("SELECT DiaSemana, HoraInicio, HoraFin FROM HORARIO "
                                 "WHERE ID_Empleado = %s", (vet_id,))
               if _norm(f["DiaSemana"]) == dia]
    if not bloques:
        return []

    tomadas = _ocupado(consulta, "ID_Empleado", vet_id, fecha)
    if mascota_id:
        tomadas += _ocupado(consulta, "ID_Mascota", mascota_id, fecha)

    ya = ahora()
    limite = ya.hour * 60 + ya.minute if fecha == ya.date() else -1
    libres = set()
    for inicio, fin in bloques:
        t = inicio
        while t + duracion <= fin:
            if t > limite and not any(t < b and t + duracion > a for a, b in tomadas):
                libres.add(t)
            t += PASO_MIN
    return [{"valor": _hhmm(t), "texto": hora_texto(t)} for t in sorted(libres)]


# ---------- Página ----------
@bp.route("/cliente")
def portal():
    if auth.veterinario_id_actual():
        return redirect("/veterinario")
    if auth.admin_id_actual():
        return redirect("/equipo")
    cid = auth.cliente_id_actual()
    cliente = _cliente_actual(cid) if cid else None
    hoy = ahora().date()
    resp = make_response(render_template(
        "cliente.html", cliente=cliente,
        no_leidas=notificaciones.contar_no_leidas_seguro(cid) if cliente else 0,
        fecha_min=hoy.isoformat(),
        fecha_max=(hoy + timedelta(days=DIAS_MAX_AGENDA)).isoformat()))
    if cid and not cliente:        # la cuenta ya no existe: se borra la cookie
        auth.borrar_cookie(resp)
    return resp


# ---------- Cuenta ----------
@bp.post("/api/cliente/registro")
def registro():
    d = _cuerpo()
    nombre = str(d.get("nombre", "")).strip()
    contacto = str(d.get("contacto", "")).strip()
    direccion = str(d.get("direccion", "")).strip()
    correo = str(d.get("correo", "")).strip().lower()
    clave = str(d.get("clave", ""))

    if not 2 <= len(nombre) <= 100:
        return _error("Escribe tu nombre completo (máximo 100 caracteres)")
    if not re.fullmatch(r"[0-9+\s-]{7,20}", contacto):
        return _error("El teléfono debe tener entre 7 y 20 números")
    if not 3 <= len(direccion) <= 100:
        return _error("Escribe tu dirección (máximo 100 caracteres)")
    if len(correo) > 100 or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", correo):
        return _error("Escribe un correo válido")
    if len(clave) < 8:
        return _error("La contraseña debe tener al menos 8 caracteres")
    if db.consultar("SELECT 1 FROM CLIENTE WHERE CorreoCliente = %s", (correo,), uno=True):
        return _error("Ya existe una cuenta con ese correo", 409)

    clave_hash = generate_password_hash(clave)
    try:
        with db.transaccion() as cur:
            cur.execute(
                "INSERT INTO CLIENTE (NombreCliente, ContactoCliente, DireccionCliente, "
                "CorreoCliente, ClaveHash) VALUES (%s, %s, %s, %s, %s)",
                (nombre, contacto, direccion, correo, clave_hash))
            cid = cur.lastrowid
            # Mismo registro en USUARIOS (solo con el hash, nunca la contraseña en texto plano)
            cur.execute(
                "INSERT INTO USUARIOS (ID_Cliente, Nombre, Correo, ClaveHash, Rol) "
                "VALUES (%s, %s, %s, %s, %s)",
                (cid, nombre, correo, clave_hash, "Cliente"))
    except db.IntegrityError:
        return _error("Ya existe una cuenta con ese correo", 409)

    return auth.poner_cookie(_ok(datos={"nombre": nombre}), cid)


@bp.post("/api/cliente/login")
def login():
    d = _cuerpo()
    correo = str(d.get("correo", "")).strip().lower()
    clave = str(d.get("clave", ""))
    fila = db.consultar("SELECT ID_Cliente, NombreCliente, ClaveHash FROM CLIENTE "
                        "WHERE CorreoCliente = %s", (correo,), uno=True)
    if fila and fila["ClaveHash"] and check_password_hash(fila["ClaveHash"], clave):
        return auth.poner_cookie(_ok(datos={"nombre": fila["NombreCliente"]}), fila["ID_Cliente"])
    admin = auth.credenciales_admin(correo, clave)      # el administrador también puede entrar aquí
    if admin:
        return auth.poner_cookie(_ok(datos={"nombre": admin[1], "destino": "/equipo"}),
                                 admin[0], auth.CARGO_ADMIN)
    return _error("Correo o contraseña incorrectos", 401)


@bp.post("/api/cliente/logout")
def logout():
    return auth.borrar_cookie(_ok())


# ---------- Mascotas ----------
def _mascota(f):
    return {"id": f["ID_Mascota"], "nombre": f["NombreMascota"], "especie": f["Especie"],
            "raza": f["Raza"], "nacimiento": f["FechaNacimiento"].isoformat(),
            "edad": _edad(f["FechaNacimiento"]), "tamano": f["Tamano"],
            "peso": float(f["Peso"]), "genero": f["Genero"]}


def _listar_mascotas(cid, mascota_id=None):
    sql = "SELECT * FROM MASCOTA WHERE ID_Cliente = %s"
    params = (cid,)
    if mascota_id:
        sql += " AND ID_Mascota = %s"
        params += (mascota_id,)
    return [_mascota(f) for f in db.consultar(sql + " ORDER BY NombreMascota", params)]


@bp.get("/api/cliente/mascotas")
@requiere_cliente
def mascotas(cid):
    return _ok(datos=_listar_mascotas(cid))


@bp.post("/api/cliente/mascotas")
@requiere_cliente
def crear_mascota(cid):
    d = _cuerpo()
    nombre = str(d.get("nombre", "")).strip()
    especie = str(d.get("especie", "")).strip()
    raza = str(d.get("raza", "")).strip() or "Mestizo"
    nacimiento = _fecha(d.get("nacimiento"))
    tamano, genero = d.get("tamano"), d.get("genero")
    try:
        peso = float(str(d.get("peso", "")).replace(",", "."))
    except ValueError:
        peso = 0

    if not 1 <= len(nombre) <= 50:
        return _error("Escribe el nombre de la mascota (máximo 50 caracteres)")
    if not 1 <= len(especie) <= 30:
        return _error("Elige la especie")
    if len(raza) > 50:
        return _error("La raza admite máximo 50 caracteres")
    if nacimiento is None or nacimiento > ahora().date():
        return _error("Escribe una fecha de nacimiento válida")
    if tamano not in TAMANOS or genero not in GENEROS:
        return _error("Elige el tamaño y el género")
    if not 0 < peso <= 999.99:
        return _error("Escribe el peso en kilos (por ejemplo 8.5)")

    with db.transaccion() as cur:
        cur.execute(
            "INSERT INTO MASCOTA (ID_Cliente, NombreMascota, Especie, Raza, FechaNacimiento, "
            "Tamano, Peso, Genero) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (cid, nombre, especie, raza, nacimiento, tamano, round(peso, 2), genero))
        nueva = cur.lastrowid
    return _ok(datos=_listar_mascotas(cid, nueva)[0])


@bp.delete("/api/cliente/mascotas/<int:mascota_id>")
@requiere_cliente
def eliminar_mascota(cid, mascota_id):
    try:
        borradas = db.ejecutar("DELETE FROM MASCOTA WHERE ID_Mascota = %s AND ID_Cliente = %s",
                               (mascota_id, cid))
    except db.IntegrityError:
        return _error("No se puede eliminar: tiene citas o historial clínico", 409)
    if borradas == 0:
        return _error("Mascota no encontrada", 404)
    return _ok()


# ---------- Facturación (FACTURACION + DETALLE_FACTURA + PAGO) ----------
# Los precios del catálogo ya incluyen IVA: el total que ve el cliente es el que se factura y el IVA
# se calcula como la parte de ese total. Cambia el porcentaje con IVA_PORCENTAJE en el .env.
IVA_PORCENTAJE = Decimal(os.getenv("IVA_PORCENTAJE", "19"))
METODOS_PAGO = ("Efectivo", "Tarjeta", "Transferencia")
METODO_PAGO_DEFECTO = "Efectivo"       # la página aún no pregunta el método: se puede enviar "metodo_pago"


def _metodo_pago(d):
    """(método, None) o (None, mensaje). Si el cliente no lo indica, se usa METODO_PAGO_DEFECTO."""
    metodo = str(d.get("metodo_pago") or METODO_PAGO_DEFECTO).strip().capitalize()
    return (metodo, None) if metodo in METODOS_PAGO else (None, "Elige un método de pago válido")


def _facturar(cur, cid, lineas, comprobante, metodo):
    """Registra la factura, su detalle y el pago DENTRO de la transacción en curso (cur): si algo falla,
    se deshace todo junto con la cita o el pedido. `lineas` = [(id_producto, id_servicio, cantidad,
    precio_unitario)]; en cada línea uno de los dos ids es None. Devuelve el id de la factura."""
    total = sum(cantidad * precio for _, _, cantidad, precio in lineas)
    iva = (Decimal(total) * IVA_PORCENTAJE / (100 + IVA_PORCENTAJE)).quantize(Decimal("0.01"), ROUND_HALF_UP)
    momento = ahora()
    cur.execute("INSERT INTO FACTURACION (ID_Cliente, FECHA, ImpuestosIVA, TotalPagar) VALUES (%s, %s, %s, %s)",
                (cid, momento, iva, total))
    factura_id = cur.lastrowid
    for producto, servicio, cantidad, precio in lineas:
        cur.execute("INSERT INTO DETALLE_FACTURA (ID_Producto, ID_Facturacion, ID_Servicio, Cantidad, "
                    "PrecioUnitario) VALUES (%s, %s, %s, %s, %s)",
                    (producto, factura_id, servicio, cantidad, precio))
    cur.execute("INSERT INTO PAGO (ID_Facturacion, MetodoPago, ValorRecibido, CambioValorRecibido, "
                "ComprobantePago, FechaPago) VALUES (%s, %s, %s, %s, %s, %s)",
                (factura_id, metodo, total, 0, comprobante, momento))
    return factura_id


# ---------- Servicios y veterinarios ----------
@bp.get("/api/cliente/servicios")
@requiere_cliente
def servicios(cid):
    filas = db.consultar(
        "SELECT ID_CataServicio AS id, Servicio AS nombre, Descripcion AS descripcion, "
        "DuracionServicio AS duracion, CostoServicio AS precio, Icono AS icono "
        "FROM CATALOGO_SERVICIOS ORDER BY ID_CataServicio")
    for f in filas:
        f["precio"] = _formatear_precio(f["precio"])
    return _ok(datos=filas)


@bp.get("/api/cliente/veterinarios")
@requiere_cliente
def veterinarios(cid):
    vets = db.consultar("SELECT ID_Empleado AS id, NombreEmpleado AS nombre, CargoEmpleado AS cargo "
                        "FROM EMPLEADO WHERE CargoEmpleado LIKE %s ORDER BY NombreEmpleado",
                        ("Veterinari%",))
    orden = {_norm(d): i for i, d in enumerate(DIAS)}
    dias = {}
    for f in db.consultar("SELECT DISTINCT ID_Empleado AS eid, DiaSemana AS dia FROM HORARIO"):
        dias.setdefault(f["eid"], set()).add(_norm(f["dia"]))
    for v in vets:
        v["dias"] = [DIAS[orden[d]].capitalize() for d in sorted(dias.get(v["id"], ()), key=lambda x: orden.get(x, 9))
                     if d in orden]
    return _ok(datos=vets)


@bp.get("/api/cliente/disponibilidad")
@requiere_cliente
def disponibilidad(cid):
    vet = request.args.get("veterinario", type=int)
    serv = request.args.get("servicio", type=int)
    mascota = request.args.get("mascota", type=int)
    fecha = _fecha(request.args.get("fecha"))
    if not vet or not serv or fecha is None:
        return _error("Elige servicio, veterinario y fecha")
    if (mensaje := _fuera_de_rango(fecha)):
        return _error(mensaje)
    s = db.consultar("SELECT DuracionServicio AS dur FROM CATALOGO_SERVICIOS "
                     "WHERE ID_CataServicio = %s", (serv,), uno=True)
    if not s:
        return _error("Servicio no encontrado", 404)
    if mascota and not db.consultar("SELECT 1 FROM MASCOTA WHERE ID_Mascota = %s AND ID_Cliente = %s",
                                    (mascota, cid), uno=True):
        mascota = None                    # no se usa la agenda de mascotas ajenas
    return _ok(datos=horas_disponibles(db.consultar, vet, s["dur"], fecha, mascota),
               dia_texto=dia_texto(fecha))


# ---------- Citas ----------
_SQL_CITAS = (
    "SELECT r.ID_Reserva AS id, r.FechaReserva AS fecha, r.HoraReserva AS hora, "
    "r.EstadoCita AS estado, m.NombreMascota AS mascota, e.NombreEmpleado AS veterinario, "
    "s.ID_CataServicio AS servicio_id, s.Servicio AS servicio, s.Icono AS icono, "
    "s.DuracionServicio AS duracion, s.CostoServicio AS precio "
    "FROM RESERVAS r "
    "JOIN MASCOTA m ON m.ID_Mascota = r.ID_Mascota "
    "JOIN EMPLEADO e ON e.ID_Empleado = r.ID_Empleado "
    "JOIN CATALOGO_SERVICIOS s ON s.ID_CataServicio = r.ID_CataServicio "
    "WHERE m.ID_Cliente = %s"
)


def _cita(f):
    minutos = _minutos(f["hora"])
    inicio = datetime.combine(f["fecha"], datetime.min.time()) + timedelta(minutes=minutos)
    return {
        "id": f["id"], "estado": f["estado"], "fecha": f["fecha"].isoformat(),
        "hora": _hhmm(minutos), "dia_texto": dia_texto(f["fecha"]), "hora_texto": hora_texto(minutos),
        "dia_num": f["fecha"].day, "mes_corto": MESES[f["fecha"].month - 1][:3],
        "futura": inicio > ahora(), "mascota": f["mascota"], "veterinario": f["veterinario"],
        "servicio_id": f["servicio_id"], "servicio": f["servicio"], "icono": f["icono"],
        "duracion": f["duracion"], "precio": _formatear_precio(f["precio"]),
    }


def _listar_citas(cid, cita_id=None):
    sql, params = _SQL_CITAS, (cid,)
    if cita_id:
        sql += " AND r.ID_Reserva = %s"
        params += (cita_id,)
    return [_cita(f) for f in db.consultar(sql + " ORDER BY r.FechaReserva, r.HoraReserva", params)]


def _frase(texto):
    """Cierra la frase con punto, sin duplicarlo cuando termina en «a. m.» o «p. m.»."""
    return texto if texto.endswith(".") else texto + "."


def _notificar_cita(cita, cid, nombre_cliente, cancelada=False):
    """Una notificación para el cliente y otra para el equipo. Ambas llevan el DÍA de la cita."""
    cuando = f"{cita['dia_texto']} a las {cita['hora_texto']}"
    s, m, v = cita["servicio"], cita["mascota"], cita["veterinario"]
    datos = {"reserva_id": cita["id"], "fecha_cita": cita["fecha"], "hora_cita": cita["hora"],
             "dia_texto": cita["dia_texto"], "hora_texto": cita["hora_texto"],
             "mascota": m, "veterinario": v, "servicio": s}
    item = {"id": f"S{cita['servicio_id']}", "nombre": s}
    if cancelada:
        tipo, titulo = "cita_cancelada", "Cita cancelada"
        para_cliente = _frase(f"Cancelaste la cita de «{s}» para {m} con {v} que era el {cuando}")
        para_equipo = f"{nombre_cliente} canceló «{s}» de {m} con {v} (era el {cuando})."
    else:
        tipo, titulo = "cita_agendada", "Cita agendada"
        para_cliente = _frase(f"{m} tiene cita de «{s}» con {v} el {cuando}")
        para_equipo = _frase(f"{nombre_cliente} agendó «{s}» para {m} con {v}: {cuando}")
    notificaciones.crear(tipo, titulo, para_cliente, item=item, datos=datos, cliente_id=cid)
    notificaciones.crear(tipo, titulo, para_equipo, item=item, datos=datos)


@bp.get("/api/cliente/citas")
@requiere_cliente
def citas(cid):
    return _ok(datos=_listar_citas(cid))


@bp.post("/api/cliente/citas")
@requiere_cliente
def agendar(cid):
    d = _cuerpo()
    try:
        mid, sid, vid = int(d.get("mascota")), int(d.get("servicio")), int(d.get("veterinario"))
    except (TypeError, ValueError):
        return _error("Elige la mascota, el servicio y el veterinario")
    fecha = _fecha(d.get("fecha"))
    if fecha is None or _hora_a_minutos(d.get("hora")) is None:
        return _error("Elige la fecha y la hora")
    if (mensaje := _fuera_de_rango(fecha)):
        return _error(mensaje)
    metodo, mensaje = _metodo_pago(d)
    if mensaje:
        return _error(mensaje)

    with db.transaccion() as cur:
        consulta = _consulta_de(cur)
        # Se bloquea al veterinario hasta el commit: dos clientes no pueden tomar la misma hora.
        vet = consulta("SELECT ID_Empleado FROM EMPLEADO WHERE ID_Empleado = %s "
                       "AND CargoEmpleado LIKE %s FOR UPDATE", (vid, "Veterinari%"))
        mascota = consulta("SELECT ID_Mascota FROM MASCOTA WHERE ID_Mascota = %s AND ID_Cliente = %s",
                           (mid, cid))
        servicio = consulta("SELECT DuracionServicio AS dur, CostoServicio AS costo FROM CATALOGO_SERVICIOS "
                            "WHERE ID_CataServicio = %s", (sid,))
        if not (vet and mascota and servicio):
            return _error("No encontramos la mascota, el servicio o el veterinario", 404)
        libres = [h["valor"] for h in horas_disponibles(consulta, vid, servicio[0]["dur"], fecha, mid)]
        if d["hora"] not in libres:
            return _error("Esa hora ya no está disponible. Elige otra.", 409)
        cur.execute(
            "INSERT INTO RESERVAS (ID_Empleado, ID_Mascota, ID_CataServicio, FechaReserva, "
            "HoraReserva, EstadoCita) VALUES (%s, %s, %s, %s, %s, %s)",
            (vid, mid, sid, fecha, f"{d['hora']}:00", AGENDADA))
        rid = cur.lastrowid
        _facturar(cur, cid, [(None, sid, 1, servicio[0]["costo"])], f"CIT-{rid}", metodo)

    cita = _listar_citas(cid, rid)[0]
    _notificar_cita(cita, cid, _cliente_actual(cid)["nombre"])   # MongoDB: si falla, la cita igual queda
    return _ok(datos=cita)


@bp.patch("/api/cliente/citas/<int:cita_id>/cancelar")
@requiere_cliente
def cancelar(cid, cita_id):
    encontrada = _listar_citas(cid, cita_id)
    if not encontrada:
        return _error("Cita no encontrada", 404)
    cita = encontrada[0]
    if cita["estado"] != AGENDADA or not cita["futura"]:
        return _error("Esta cita ya no se puede cancelar", 409)
    if db.ejecutar("UPDATE RESERVAS SET EstadoCita = %s WHERE ID_Reserva = %s AND EstadoCita = %s",
                   (CANCELADA, cita_id, AGENDADA)) == 0:
        return _error("Esta cita ya no se puede cancelar", 409)
    cita["estado"] = CANCELADA
    _notificar_cita(cita, cid, _cliente_actual(cid)["nombre"], cancelada=True)
    return _ok(datos=cita)

# ---------- Tienda: productos y compras ----------
CONFIRMADO = "Confirmado"
MAX_POR_PRODUCTO = 10          # unidades máximas de un mismo producto por compra
MAX_PRODUCTOS_DISTINTOS = 20


class _CompraInvalida(Exception):
    """Se lanza dentro de la transacción para que haga ROLLBACK de todo lo descontado."""
    def __init__(self, mensaje, codigo=400):
        super().__init__(mensaje)
        self.mensaje, self.codigo = mensaje, codigo


@bp.get("/api/cliente/productos")
@requiere_cliente
def productos(cid):
    filas = db.consultar(
        "SELECT ID_Producto AS id, TipoProducto AS nombre, Descripcion AS descripcion, "
        "ValorProducto AS valor, Icono AS icono, Stock AS stock "
        "FROM PRODUCTOS ORDER BY ID_Producto")
    for f in filas:
        f["precio"] = _formatear_precio(f["valor"])
    return _ok(datos=filas)


def _leer_carrito(d):
    """Devuelve ({id_producto: cantidad}, None) o (None, mensaje_de_error)."""
    items = d.get("items")
    if not isinstance(items, list) or not items:
        return None, "Tu carrito está vacío"
    carrito = {}
    for it in items:
        try:
            pid, cant = int(it.get("producto")), int(it.get("cantidad"))
        except (AttributeError, TypeError, ValueError):
            return None, "El carrito tiene datos inválidos"
        if cant < 1:
            return None, "Las cantidades deben ser mayores a cero"
        carrito[pid] = carrito.get(pid, 0) + cant
    if len(carrito) > MAX_PRODUCTOS_DISTINTOS:
        return None, f"Máximo {MAX_PRODUCTOS_DISTINTOS} productos distintos por compra"
    if any(c > MAX_POR_PRODUCTO for c in carrito.values()):
        return None, f"Máximo {MAX_POR_PRODUCTO} unidades de cada producto por compra"
    return carrito, None


def _listar_compras(cid, pedido_id=None):
    sql = ("SELECT ID_Pedido AS id, Fecha AS fecha, Total AS total, Estado AS estado "
           "FROM PEDIDOS WHERE ID_Cliente = %s")
    params = (cid,)
    if pedido_id:
        sql += " AND ID_Pedido = %s"
        params += (pedido_id,)
    pedidos = db.consultar(sql + " ORDER BY Fecha DESC, ID_Pedido DESC LIMIT 50", params)
    if not pedidos:
        return []

    marcas = ", ".join(["%s"] * len(pedidos))          # solo "%s": nada del usuario va en el SQL
    detalles = db.consultar(
        "SELECT d.ID_Pedido AS pedido, d.Cantidad AS cantidad, d.PrecioUnitario AS unitario, "
        "p.TipoProducto AS nombre, p.Icono AS icono "
        "FROM PEDIDO_DETALLE d JOIN PRODUCTOS p ON p.ID_Producto = d.ID_Producto "
        f"WHERE d.ID_Pedido IN ({marcas}) ORDER BY d.ID_Detalle",
        tuple(p["id"] for p in pedidos))
    por_pedido = {}
    for d in detalles:
        por_pedido.setdefault(d["pedido"], []).append({
            "nombre": d["nombre"], "icono": d["icono"], "cantidad": d["cantidad"],
            "unitario": _formatear_precio(d["unitario"]),
            "subtotal": _formatear_precio(d["unitario"] * d["cantidad"])})

    return [{
        "id": p["id"], "estado": p["estado"], "total": _formatear_precio(p["total"]),
        "dia_num": p["fecha"].day, "mes_corto": MESES[p["fecha"].month - 1][:3],
        "fecha_texto": f"{dia_texto(p['fecha'].date())} · "
                       f"{hora_texto(p['fecha'].hour * 60 + p['fecha'].minute)}",
        "items": por_pedido.get(p["id"], []),
    } for p in pedidos]


def _notificar_compra(cid, nombre_cliente, compra, stocks):
    """Una notificación para el cliente, otra para el equipo y alertas de stock para el equipo."""
    resumen = ", ".join(f"{i['cantidad']} × {i['nombre']}" for i in compra["items"])
    datos = {"pedido_id": compra["id"], "total": compra["total"],
             "unidades": sum(i["cantidad"] for i in compra["items"])}
    notificaciones.crear(
        "compra_realizada", "Compra confirmada",
        _frase(f"Tu pedido #{compra['id']} por ${compra['total']} está confirmado: {resumen}"),
        datos=datos, cliente_id=cid)
    notificaciones.crear(
        "compra_realizada", "Nueva compra",
        _frase(f"{nombre_cliente} compró {resumen} (${compra['total']})"), datos=datos)

    for s in stocks:
        ref = {"id": s["id"], "nombre": s["nombre"]}
        if s["stock"] <= 0:
            notificaciones.crear("sin_cupos", "Sin stock",
                                 f"«{s['nombre']}» se quedó sin stock.", item=ref, prioridad="alta")
        elif s["stock"] <= notificaciones.UMBRAL_STOCK_BAJO:
            notificaciones.crear("stock_bajo", "Stock bajo",
                                 f"«{s['nombre']}» tiene solo {s['stock']} disponibles.",
                                 item=ref, datos={"stock_restante": s["stock"]}, prioridad="alta")


@bp.get("/api/cliente/compras")
@requiere_cliente
def compras(cid):
    return _ok(datos=_listar_compras(cid))


@bp.post("/api/cliente/compras")
@requiere_cliente
def comprar(cid):
    d = _cuerpo()
    carrito, mensaje = _leer_carrito(d)
    if mensaje:
        return _error(mensaje)
    metodo, mensaje = _metodo_pago(d)
    if mensaje:
        return _error(mensaje)

    stocks, lineas, total = [], [], 0
    try:
        with db.transaccion() as cur:
            consulta = _consulta_de(cur)
            # Orden fijo por id: dos compras simultáneas no se bloquean entre sí.
            for pid in sorted(carrito):
                cant = carrito[pid]
                filas = consulta(
                    "SELECT TipoProducto AS nombre, ValorProducto AS valor, Stock AS stock "
                    "FROM PRODUCTOS WHERE ID_Producto = %s FOR UPDATE", (pid,))
                if not filas:
                    raise _CompraInvalida("Uno de los productos ya no existe", 404)
                prod = filas[0]
                if prod["stock"] < cant:
                    raise _CompraInvalida(
                        f"«{prod['nombre']}» está agotado" if prod["stock"] <= 0
                        else f"Solo quedan {prod['stock']} unidades de «{prod['nombre']}»", 409)
                cur.execute("UPDATE PRODUCTOS SET Stock = Stock - %s WHERE ID_Producto = %s",
                            (cant, pid))
                total += prod["valor"] * cant
                lineas.append((pid, cant, prod["valor"]))
                stocks.append({"id": f"P{pid}", "nombre": prod["nombre"],
                               "stock": prod["stock"] - cant})

            cur.execute("INSERT INTO PEDIDOS (ID_Cliente, Fecha, Total, Estado) "
                        "VALUES (%s, %s, %s, %s)", (cid, ahora(), total, CONFIRMADO))
            pedido_id = cur.lastrowid
            for pid, cant, valor in lineas:
                cur.execute("INSERT INTO PEDIDO_DETALLE (ID_Pedido, ID_Producto, Cantidad, "
                            "PrecioUnitario) VALUES (%s, %s, %s, %s)", (pedido_id, pid, cant, valor))
            _facturar(cur, cid, [(pid, None, cant, valor) for pid, cant, valor in lineas],
                      f"PED-{pedido_id}", metodo)
    except _CompraInvalida as e:
        return _error(e.mensaje, e.codigo)      # la transacción ya hizo rollback

    compra = _listar_compras(cid, pedido_id)[0]
    _notificar_compra(cid, _cliente_actual(cid)["nombre"], compra, stocks)   # Mongo: no rompe la compra
    return _ok(datos=compra)

# ---------- Notificaciones del cliente (MongoDB) ----------
@bp.get("/api/cliente/notificaciones")
@requiere_cliente
def notif_listar(cid):
    solo_no_leidas = request.args.get("solo_no_leidas", "").lower() in ("1", "true", "si")
    try:
        limite = min(max(int(request.args.get("limite", 20)), 1), 100)
    except ValueError:
        limite = 20
    return _ok(no_leidas=notificaciones.contar_no_leidas(cid),
               datos=notificaciones.listar(solo_no_leidas, limite, cid))


@bp.patch("/api/cliente/notificaciones/<notif_id>/leer")
@requiere_cliente
def notif_leer(cid, notif_id):
    if not notificaciones.marcar_leida(notif_id, cid):
        return _error("Notificación no encontrada", 404)
    return _ok(no_leidas=notificaciones.contar_no_leidas(cid))


@bp.patch("/api/cliente/notificaciones/leer-todas")
@requiere_cliente
def notif_leer_todas(cid):
    return _ok(marcadas=notificaciones.marcar_todas_leidas(cid), no_leidas=0)