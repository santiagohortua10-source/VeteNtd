"""Consultas validadas para el reporte administrativo de auditoría."""
from datetime import date, datetime, timedelta
import json

import db

TABLAS_NEGOCIO = (
    "catalogo_servicios", "cliente", "detalle_factura", "empleado",
    "facturacion", "historial_clinico", "horario", "mascota", "pago",
    "pedidos", "pedido_detalle", "productos", "reservas",
    "responsable_alterno", "usuarios",
)
OPERACIONES = ("INSERT", "UPDATE", "DELETE")


class FiltroInvalido(ValueError):
    pass


def _fecha(valor, nombre):
    if not valor:
        return None
    try:
        return date.fromisoformat(valor)
    except (TypeError, ValueError):
        raise FiltroInvalido(f"La {nombre} debe tener formato AAAA-MM-DD.")


def consultar_registros(parametros):
    inicio = _fecha(parametros.get("fecha_inicio"), "fecha inicial")
    fin = _fecha(parametros.get("fecha_fin"), "fecha final")
    if inicio and fin and inicio > fin:
        raise FiltroInvalido("La fecha inicial no puede ser posterior a la fecha final.")

    usuario = (parametros.get("usuario") or "").strip()
    if len(usuario) > 120:
        raise FiltroInvalido("El usuario no puede superar 120 caracteres.")

    operacion = (parametros.get("operacion") or "").upper()
    if operacion and operacion not in OPERACIONES:
        raise FiltroInvalido("La operación seleccionada no es válida.")

    tabla = (parametros.get("tabla") or "").lower()
    if tabla and tabla not in TABLAS_NEGOCIO:
        raise FiltroInvalido("La tabla seleccionada no es válida.")

    where, valores = [], []
    if inicio:
        where.append("fecha_hora >= %s")
        valores.append(datetime.combine(inicio, datetime.min.time()))
    if fin:
        where.append("fecha_hora < %s")
        valores.append(datetime.combine(fin + timedelta(days=1), datetime.min.time()))
    if usuario:
        where.append("usuario = %s")
        valores.append(usuario)
    if operacion:
        where.append("operacion = %s")
        valores.append(operacion)
    if tabla:
        where.append("nombre_tabla = %s")
        valores.append(tabla)

    consulta = (
        "SELECT id_auditoria, usuario, fecha_hora, operacion, nombre_tabla, "
        "id_registro, datos_anteriores, datos_nuevos FROM auditoria"
    )
    if where:
        consulta += " WHERE " + " AND ".join(where)
    consulta += " ORDER BY fecha_hora DESC, id_auditoria DESC LIMIT 200"
    registros = db.consultar(consulta, tuple(valores))
    for registro in registros:
        for campo in ("datos_anteriores", "datos_nuevos"):
            valor = registro.get(campo)
            if isinstance(valor, str):
                try:
                    registro[campo] = json.loads(valor)
                except (TypeError, ValueError):
                    pass
    return registros
