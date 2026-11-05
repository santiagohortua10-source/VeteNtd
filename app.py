import os
import re

from flask import Flask, jsonify, redirect, render_template, request, url_for

import clientes
import db
import mongo
import notificaciones

app = Flask(__name__)
# Firma la cookie de sesión del portal de clientes. En producción define SECRET_KEY en el .env.
app.secret_key = os.getenv("SECRET_KEY", "clave-solo-para-desarrollo-cambiala")
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.register_blueprint(clientes.bp)

# La página muestra servicios y productos en una sola lista, pero en la base de datos
# viven en dos tablas. Para que los ids no choquen, cada item usa un prefijo:
#   "S1" = CATALOGO_SERVICIOS.ID_CataServicio = 1
#   "P1" = PRODUCTOS.ID_Producto = 1
# (Los nombres de tabla/columna salen de este diccionario fijo, nunca del usuario.)
TABLAS = {
    "S": {"tabla": "CATALOGO_SERVICIOS", "pk": "ID_CataServicio",
          "nombre": "Servicio", "precio": "CostoServicio", "stock": "Cupos"},
    "P": {"tabla": "PRODUCTOS", "pk": "ID_Producto",
          "nombre": "TipoProducto", "precio": "ValorProducto", "stock": "Stock"},
}

CAMPOS_REQUERIDOS = ['nombre', 'descripcion', 'precio', 'icono', 'stock']


# ---------- Utilidades ----------
def _resolver_id(item_id):
    """'S3' -> ('S', 3). Devuelve None si el id no es válido."""
    if len(item_id) < 2 or not item_id[1:].isdigit():
        return None
    prefijo = item_id[0].upper()
    if prefijo not in TABLAS:
        return None
    return prefijo, int(item_id[1:])


def _formatear_precio(valor):
    # 80000 -> "80.000"
    return f"{int(valor):,}".replace(",", ".")


def _select(prefijo):
    t = TABLAS[prefijo]
    return (
        f"SELECT {t['pk']} AS num, {t['nombre']} AS nombre, Descripcion AS descripcion, "
        f"{t['precio']} AS precio, Icono AS icono, {t['stock']} AS stock "
        f"FROM {t['tabla']}"
    )


def _a_item(prefijo, fila):
    return {
        "id": f"{prefijo}{fila['num']}",
        "nombre": fila["nombre"],
        "descripcion": fila["descripcion"],
        "precio": _formatear_precio(fila["precio"]),
        "icono": fila["icono"],
        "stock": fila["stock"],
    }


def listar_items():
    items = []
    for prefijo, t in TABLAS.items():
        filas = db.consultar(_select(prefijo) + f" ORDER BY {t['pk']}")
        items.extend(_a_item(prefijo, f) for f in filas)
    return items


def obtener_item(item_id):
    """Devuelve el item (dict) o None si el id no es válido / no existe."""
    resuelto = _resolver_id(item_id)
    if not resuelto:
        return None
    prefijo, numero = resuelto
    fila = db.consultar(_select(prefijo) + f" WHERE {TABLAS[prefijo]['pk']} = %s",
                        (numero,), uno=True)
    return _a_item(prefijo, fila) if fila else None


def _no_encontrado():
    return jsonify({"estado": "error", "mensaje": "Servicio no encontrado"}), 404


def _validar_cuerpo(datos):
    """Devuelve (valores, None) si es válido, o (None, mensaje_de_error)."""
    if not isinstance(datos, dict):
        return None, "El cuerpo debe ser un JSON"
    for campo in CAMPOS_REQUERIDOS:
        if campo not in datos:
            return None, f"Falta el campo: {campo}"

    nombre = str(datos['nombre']).strip()
    descripcion = str(datos['descripcion']).strip()
    icono = str(datos['icono']).strip()
    digitos = re.sub(r"\D", "", str(datos['precio']))  # "90.000" -> "90000"

    if not nombre or len(nombre) > 100:
        return None, "El nombre es obligatorio y admite máximo 100 caracteres"
    if len(descripcion) > 255:
        return None, "La descripción admite máximo 255 caracteres"
    if len(icono) > 10:
        return None, "El icono admite máximo 10 caracteres"
    if not digitos:
        return None, "El precio debe ser un número"
    try:
        stock = int(datos['stock'])
    except (TypeError, ValueError):
        return None, "Los cupos deben ser un número entero"
    if stock < 0:
        return None, "Los cupos no pueden ser negativos"

    return {"nombre": nombre, "descripcion": descripcion, "precio": int(digitos),
            "icono": icono, "stock": stock}, None


# ---------- Errores de base de datos ----------
@app.errorhandler(db.Error)
def error_base_de_datos(e):
    app.logger.error("Error de base de datos: %s", e)
    if request.path.startswith('/api/'):
        return jsonify({"estado": "error",
                        "mensaje": "No se pudo conectar con la base de datos"}), 500
    return ("No se pudo conectar con la base de datos. "
            "Revisa tu archivo .env y que MySQL esté encendido."), 503


# ---------- Errores de MongoDB (solo afectan a /api/notificaciones) ----------
@app.errorhandler(mongo.PyMongoError)
def error_mongo(e):
    app.logger.error("Error de MongoDB: %s", e)
    if request.path.startswith('/api/'):
        return jsonify({"estado": "error",
                        "mensaje": "No se pudo conectar con MongoDB (notificaciones)"}), 503
    return "No se pudo conectar con MongoDB. Revisa MONGO_URI en tu .env.", 503


def _notificar_cambio_stock(item):
    """Genera notificaciones según el stock que quedó tras una reserva."""
    ref = {"id": item["id"], "nombre": item["nombre"]}
    stock = item["stock"]
    notificaciones.crear(
        "reserva_creada", "Nueva reserva",
        f"Se reservó «{item['nombre']}». Quedan {stock} disponibles.",
        item=ref, datos={"stock_restante": stock},
    )
    if stock <= 0:
        notificaciones.crear(
            "sin_cupos", "Sin cupos",
            f"«{item['nombre']}» se quedó sin cupos/stock.",
            item=ref, prioridad="alta",
        )
    elif stock <= notificaciones.UMBRAL_STOCK_BAJO:
        notificaciones.crear(
            "stock_bajo", "Stock bajo",
            f"«{item['nombre']}» tiene solo {stock} disponibles.",
            item=ref, datos={"stock_restante": stock,
                             "umbral": notificaciones.UMBRAL_STOCK_BAJO},
            prioridad="alta",
        )


# ---------- Rutas ----------
@app.route('/')
def inicio():
    # Siempre se entra por el portal: ahí está el ingreso / registro
    return redirect(url_for('clientes.portal'))


@app.route('/equipo')
def equipo():
    return render_template('index.html', servicios=listar_items(),
                           no_leidas=notificaciones.contar_no_leidas_seguro())


@app.route('/api/servicios')
def api_servicios():
    # Endpoint (GET)
    return jsonify({"estado": "exito", "datos": listar_items()})


# METODO POST
@app.route('/api/servicios/<item_id>/reservar', methods=['POST'])
def reservar_servicio(item_id):
    # Reserva 1 cupo/unidad: descuenta su disponibilidad (de forma atómica en la BD)
    resuelto = _resolver_id(item_id)
    if not resuelto:
        return _no_encontrado()
    prefijo, numero = resuelto
    t = TABLAS[prefijo]

    afectadas = db.ejecutar(
        f"UPDATE {t['tabla']} SET {t['stock']} = {t['stock']} - 1 "
        f"WHERE {t['pk']} = %s AND {t['stock']} > 0",
        (numero,),
    )
    item = obtener_item(item_id)
    if item is None:
        return _no_encontrado()
    if afectadas == 0:
        return jsonify({"estado": "error", "mensaje": "Sin cupos disponibles"}), 400
    _notificar_cambio_stock(item)  # MongoDB (no interrumpe la reserva si falla)
    return jsonify({"estado": "exito", "datos": item})


# METODO PUT
@app.route('/api/servicios/<item_id>', methods=['PUT'])
def reemplazar_servicio(item_id):
    valores, error = _validar_cuerpo(request.get_json(silent=True))
    if error:
        return jsonify({"estado": "error", "mensaje": error}), 400

    if obtener_item(item_id) is None:
        return _no_encontrado()

    prefijo, numero = _resolver_id(item_id)
    t = TABLAS[prefijo]
    db.ejecutar(
        f"UPDATE {t['tabla']} SET {t['nombre']} = %s, Descripcion = %s, "
        f"{t['precio']} = %s, Icono = %s, {t['stock']} = %s WHERE {t['pk']} = %s",
        (valores['nombre'], valores['descripcion'], valores['precio'],
         valores['icono'], valores['stock'], numero),
    )
    actualizado = obtener_item(item_id)
    notificaciones.crear(
        "servicio_actualizado", "Servicio actualizado",
        f"Se modificó «{actualizado['nombre']}» (precio ${actualizado['precio']}, "
        f"disponibles {actualizado['stock']}).",
        item={"id": actualizado["id"], "nombre": actualizado["nombre"]},
        datos={"precio": valores["precio"], "stock": valores["stock"]},
        prioridad="baja",
    )
    return jsonify({
        "estado": "exito",
        "mensaje": "Servicio actualizado correctamente",
        "datos": actualizado,
    })


# METODO DELETE
@app.route('/api/servicios/<item_id>', methods=['DELETE'])
def eliminar_servicio(item_id):
    item = obtener_item(item_id)
    if item is None:
        return _no_encontrado()

    prefijo, numero = _resolver_id(item_id)
    t = TABLAS[prefijo]
    try:
        db.ejecutar(f"DELETE FROM {t['tabla']} WHERE {t['pk']} = %s", (numero,))
    except db.IntegrityError:
        # Error 1451: hay reservas o facturas que dependen de este registro
        return jsonify({
            "estado": "error",
            "mensaje": "No se puede eliminar: tiene reservas o facturas asociadas",
        }), 409

    notificaciones.crear(
        "servicio_eliminado", "Servicio eliminado",
        f"Se eliminó «{item['nombre']}» del catálogo.",
        item={"id": item["id"], "nombre": item["nombre"]},
    )
    return jsonify({
        "estado": "exito",
        "mensaje": "Servicio eliminado correctamente",
        "datos": item,
    })


# ---------- Notificaciones (MongoDB) ----------
@app.route('/api/notificaciones')
def api_notificaciones():
    # ?solo_no_leidas=true  &  ?limite=20 (máx. 100)
    solo_no_leidas = request.args.get('solo_no_leidas', '').lower() in ('1', 'true', 'si')
    try:
        limite = min(max(int(request.args.get('limite', 20)), 1), 100)
    except ValueError:
        limite = 20
    return jsonify({
        "estado": "exito",
        "no_leidas": notificaciones.contar_no_leidas(),
        "datos": notificaciones.listar(solo_no_leidas, limite),
    })


@app.route('/api/notificaciones/<notif_id>/leer', methods=['PATCH'])
def leer_notificacion(notif_id):
    if not notificaciones.marcar_leida(notif_id):
        return jsonify({"estado": "error", "mensaje": "Notificación no encontrada"}), 404
    return jsonify({"estado": "exito", "no_leidas": notificaciones.contar_no_leidas()})


@app.route('/api/notificaciones/leer-todas', methods=['PATCH'])
def leer_todas_notificaciones():
    marcadas = notificaciones.marcar_todas_leidas()
    return jsonify({"estado": "exito", "marcadas": marcadas, "no_leidas": 0})


if __name__ == '__main__':
    # host='0.0.0.0' permite acceder desde otros dispositivos en tu red
    app.run(debug=True, host='0.0.0.0', port=5000)
