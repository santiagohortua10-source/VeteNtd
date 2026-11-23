"""End-to-end Flask HTTP smoke test; mutates only a pawcare_audit_test_* schema."""
import json
import os
import sys
import threading
import uuid
from datetime import date, timedelta
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPCookieProcessor, HTTPRedirectHandler, Request, build_opener

from werkzeug.security import generate_password_hash
from werkzeug.serving import WSGIRequestHandler, make_server

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["JWT_SECRET_KEY"] = "http-smoke-" + uuid.uuid4().hex
os.environ["MONGO_URI"] = "mongodb://127.0.0.1:27019/?serverSelectionTimeoutMS=50"
os.environ["MONGO_DB"] = "pawcare_test_no_external_writes"

import app as pawcare
import db
import mysql.connector
import notificaciones


class QuietHandler(WSGIRequestHandler):
    def log_request(self, code="-", size="-"):
        pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

    def log_error(self, *args, **kwargs):
        pass


def main():
    database = db._configuracion()["database"]
    if not database.startswith("pawcare_audit_test_"):
        raise SystemExit("Seguridad: DB_NAME debe apuntar a pawcare_audit_test_<sufijo>; no se inició Flask.")

    # No se conecta a Mongo durante estos tests; las mutaciones probadas son sólo MySQL local de prueba.
    notificaciones.crear = lambda *args, **kwargs: None
    notificaciones.contar_no_leidas_seguro = lambda *args, **kwargs: 0
    notificaciones.contar_no_leidas = lambda *args, **kwargs: 0

    suffix = uuid.uuid4().hex[:10]
    admin_email = f"admin-http-{suffix}@example.invalid"
    admin_password = uuid.uuid4().hex + "Aa1!"
    client_email = f"cliente-http-{suffix}@example.invalid"
    client_password = uuid.uuid4().hex + "Bb2!"

    connection = mysql.connector.connect(**db._configuracion())
    cursor = connection.cursor()
    cursor.execute(
        "INSERT INTO EMPLEADO (NombreEmpleado,ContactoEmpleado,CargoEmpleado,CorreoEmpleado,ClaveHash) "
        "VALUES (%s,%s,'Administrador',%s,%s)",
        ("Administrador prueba HTTP", "3009000011", admin_email, generate_password_hash(admin_password)),
    )
    admin_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO CLIENTE (NombreCliente,ContactoCliente,DireccionCliente,CorreoCliente,ClaveHash) "
        "VALUES (%s,%s,%s,%s,%s)",
        ("Cliente prueba HTTP", "3009000022", "Dirección ficticia", client_email,
         generate_password_hash(client_password)),
    )
    client_id = cursor.lastrowid
    service_name = "HTTP catálogo " + suffix
    cursor.execute(
        "INSERT INTO CATALOGO_SERVICIOS (Servicio,Descripcion,DuracionServicio,CostoServicio,Icono,Cupos) "
        "VALUES (%s,'fixture HTTP',25,33321,'T',2)", (service_name,),
    )
    service_id = cursor.lastrowid
    product_name = "HTTP producto " + suffix
    cursor.execute(
        "INSERT INTO PRODUCTOS (TipoProducto,Descripcion,ValorProducto,Icono,Stock) "
        "VALUES (%s,'fixture HTTP',17777,'P',5)", (product_name,),
    )
    product_id = cursor.lastrowid
    connection.commit()
    cursor.close()
    connection.close()

    server = make_server("127.0.0.1", 0, pawcare.app, threaded=True, request_handler=QuietHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    base = f"http://127.0.0.1:{server.server_port}"

    def send(opener, method, path, body=None):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request = Request(base + path, data=data, method=method)
        if body is not None:
            request.add_header("Content-Type", "application/json")
        try:
            with opener.open(request, timeout=8) as response:
                payload = response.read()
                return response.status, payload
        except HTTPError as error:
            return error.code, error.read()
        except URLError as error:
            raise AssertionError("No respondió el servidor Flask local.") from error

    try:
        no_session = build_opener()
        root_status, _ = send(no_session, "GET", "/")
        if root_status != 200:  # El redirect termina en el portal de ingreso.
            raise AssertionError("El servidor no sirvió el portal inicial.")
        if send(no_session, "GET", "/api/servicios")[0] != 401:
            raise AssertionError("La API administrativa no rechazó una sesión anónima.")
        if send(no_session, "GET", "/api/admin/veterinarios")[0] != 401:
            raise AssertionError("La administración aceptó una sesión anónima.")

        admin_browser = build_opener(HTTPCookieProcessor(CookieJar()))
        status, login_body = send(admin_browser, "POST", "/api/cliente/login",
                                  {"correo": admin_email, "clave": admin_password})
        if status != 200 or json.loads(login_body).get("estado") != "exito":
            raise AssertionError("Falló el login administrativo real de prueba.")
        if send(admin_browser, "GET", "/api/servicios")[0] != 200:
            raise AssertionError("El Administrador autenticado no accedió a la API de catálogo.")
        if send(admin_browser, "GET", "/equipo")[0] != 200:
            raise AssertionError("Falló la página administrativa.")
        if send(admin_browser, "GET", "/api/admin/veterinarios")[0] != 200:
            raise AssertionError("Falló el acceso administrativo protegido.")

        item_id = "S" + str(service_id)
        put_status, _ = send(admin_browser, "PUT", "/api/servicios/" + item_id, {
            "nombre": service_name, "descripcion": "actualizado HTTP", "precio": 33321,
            "icono": "T", "stock": 2,
        })
        reserve_status, _ = send(admin_browser, "POST", "/api/servicios/" + item_id + "/reservar")
        if (put_status, reserve_status) != (200, 200):
            raise AssertionError(f"Catálogo respondió {(put_status, reserve_status)}.")

        vet_email = f"vet-http-{suffix}@example.invalid"
        vet_password = uuid.uuid4().hex + "Cc3!"
        agenda_day = date.today() + timedelta(days=2)
        day_names = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        vet_body = {"nombre": "Vet prueba HTTP", "contacto": "3009000033", "cargo": "Veterinario",
                    "correo": vet_email, "clave": vet_password,
                    "horarios": [{"dia": day_names[agenda_day.weekday()], "inicio": "08:00", "fin": "18:00"}]}
        create_status, create_body = send(admin_browser, "POST", "/api/admin/veterinarios", vet_body)
        if create_status != 201:
            raise AssertionError("Falló el alta HTTP del veterinario en la base de pruebas.")
        vet_id = json.loads(create_body)["datos"]["id"]
        list_status, list_body = send(admin_browser, "GET", "/api/admin/veterinarios")
        vets = json.loads(list_body).get("datos", [])
        if list_status != 200 or not any(v.get("correo") == vet_email for v in vets):
            raise AssertionError("El veterinario creado no aparece en el listado.")
        update_body = dict(vet_body, nombre="Vet HTTP actualizado", clave="")
        update_status, _ = send(admin_browser, "PUT", f"/api/admin/veterinarios/{vet_id}", update_body)
        if update_status != 200:
            raise AssertionError("Falló la actualización HTTP del veterinario.")

        client_browser = build_opener(HTTPCookieProcessor(CookieJar()))
        client_status, _ = send(client_browser, "POST", "/api/cliente/login",
                                {"correo": client_email, "clave": client_password})
        if client_status != 200:
            raise AssertionError("Falló el login real del cliente de prueba.")
        pet_body = {"nombre": "Mascota HTTP", "especie": "Perro", "raza": "Prueba",
                    "nacimiento": "2021-01-01", "tamano": "Mediano", "peso": 8.5, "genero": "Macho"}
        pet_status, pet_response = send(client_browser, "POST", "/api/cliente/mascotas", pet_body)
        if pet_status != 200:
            raise AssertionError("Falló el alta HTTP de mascota.")
        pet_id = json.loads(pet_response)["datos"]["id"]
        pet_list_status, _ = send(client_browser, "GET", "/api/cliente/mascotas")
        if pet_list_status != 200:
            raise AssertionError("Falló la consulta HTTP de mascotas.")

        availability_path = (f"/api/cliente/disponibilidad?veterinario={vet_id}&servicio={service_id}"
                             f"&mascota={pet_id}&fecha={agenda_day.isoformat()}")
        availability_status, availability_body = send(client_browser, "GET", availability_path)
        hours = json.loads(availability_body).get("datos", [])
        if availability_status != 200 or not hours:
            raise AssertionError("La agenda no devolvió horarios disponibles.")
        reservation_status, reservation_body = send(client_browser, "POST", "/api/cliente/citas", {
            "mascota": pet_id, "servicio": service_id, "veterinario": vet_id,
            "fecha": agenda_day.isoformat(), "hora": hours[0]["valor"], "metodo_pago": "Efectivo",
        })
        if reservation_status != 200:
            raise AssertionError(f"Falló la reserva HTTP: {reservation_status} {reservation_body!r}")
        reservation_id = json.loads(reservation_body)["datos"]["id"]
        client_citas_status, client_citas_body = send(client_browser, "GET", "/api/cliente/citas")
        if client_citas_status != 200 or not any(
            x["id"] == reservation_id for x in json.loads(client_citas_body)["datos"]
        ):
            raise AssertionError("La reserva no apareció en las citas del cliente.")

        vet_browser = build_opener(HTTPCookieProcessor(CookieJar()))
        vet_login_status, _ = send(vet_browser, "POST", "/api/veterinario/login",
                                  {"correo": vet_email, "clave": vet_password})
        vet_citas_status, vet_citas_body = send(vet_browser, "GET", "/api/veterinario/citas")
        if vet_login_status != 200 or vet_citas_status != 200 or not any(
            x["id"] == reservation_id for x in json.loads(vet_citas_body)["datos"]
        ):
            raise AssertionError("El veterinario no pudo iniciar sesión/consultar su cita.")
        history_path = f"/api/veterinario/mascotas/{pet_id}/historial"
        history_post_status, _ = send(vet_browser, "POST", history_path, {
            "reserva_id": reservation_id, "diagnostico": "Control ficticio HTTP",
            "tratamiento": "Seguimiento ficticio HTTP",
        })
        history_status, history_body = send(vet_browser, "GET", history_path)
        history = json.loads(history_body).get("datos", {}).get("clinico", [])
        if history_post_status != 200 or history_status != 200 or not any(
            x["reserva_id"] == reservation_id for x in history
        ):
            raise AssertionError("No se pudo registrar/leer el historial clínico HTTP.")

        buy_status, buy_body = send(client_browser, "POST", "/api/cliente/compras", {
            "items": [{"producto": product_id, "cantidad": 1}], "metodo_pago": "Efectivo",
        })
        if buy_status != 200:
            raise AssertionError(f"Falló la compra HTTP: {buy_status} {buy_body!r}")
        purchase_id = json.loads(buy_body)["datos"]["id"]
        purchases_status, purchases_body = send(client_browser, "GET", "/api/cliente/compras")
        if purchases_status != 200 or not any(
            x["id"] == purchase_id for x in json.loads(purchases_body)["datos"]
        ):
            raise AssertionError("La compra no apareció en el historial de compras.")

        check = mysql.connector.connect(**db._configuracion())
        qc = check.cursor()
        qc.execute("SELECT COUNT(*) FROM FACTURACION WHERE ID_Cliente=%s", (client_id,))
        if qc.fetchone()[0] < 2:
            raise AssertionError("La cita y la compra no generaron las facturas esperadas.")
        qc.execute("SELECT COUNT(*) FROM HISTORIAL_CLINICO WHERE ID_Reserva=%s", (reservation_id,))
        if qc.fetchone()[0] != 1:
            raise AssertionError("La atención de prueba no quedó persistida.")
        qc.close()
        check.close()

        report_status, report_body = send(admin_browser, "GET", "/auditoria?tabla=mascota")
        if report_status != 200 or b"Auditor" not in report_body:
            raise AssertionError("Falló la interfaz HTTP del reporte de auditoría.")
        client_no_redirect = build_opener(HTTPCookieProcessor(CookieJar()), NoRedirect())
        if send(client_no_redirect, "GET", "/auditoria")[0] != 302:
            raise AssertionError("Un cliente pudo acceder al reporte de auditoría.")
        filtered_status, filtered_body = send(
            admin_browser, "GET", f"/auditoria?usuario=Cliente:{client_id}&operacion=INSERT&tabla=reservas"
        )
        if filtered_status != 200 or b"reservas" not in filtered_body:
            raise AssertionError("Los filtros del reporte de auditoría no respondieron.")

        check = mysql.connector.connect(**db._configuracion())
        q = check.cursor(dictionary=True)
        q.execute(
            "SELECT usuario,operacion FROM auditoria WHERE nombre_tabla='mascota' "
            "AND id_registro=%s ORDER BY id_auditoria", (str(pet_id),),
        )
        pet_audit = q.fetchall()
        q.execute(
            "SELECT usuario,operacion FROM auditoria WHERE nombre_tabla='catalogo_servicios' "
            "AND id_registro=%s ORDER BY id_auditoria", (str(service_id),),
        )
        service_audit = q.fetchall()
        q.execute("SELECT usuario,operacion FROM auditoria WHERE nombre_tabla='reservas' AND id_registro=%s",
                  (str(reservation_id),))
        reservation_audit = q.fetchall()
        q.execute("SELECT usuario,operacion FROM auditoria WHERE nombre_tabla='pedidos' AND id_registro=%s",
                  (str(purchase_id),))
        purchase_audit = q.fetchall()
        q.execute(
            "SELECT a.usuario,a.operacion FROM auditoria a JOIN HISTORIAL_CLINICO h "
            "ON h.ID_Historial=a.id_registro WHERE a.nombre_tabla='historial_clinico' AND h.ID_Reserva=%s",
            (reservation_id,),
        )
        history_audit = q.fetchall()
        if not any(r["operacion"] == "INSERT" and r["usuario"] == f"Cliente:{client_id}" for r in reservation_audit):
            raise AssertionError("La reserva no registro al cliente autenticado.")
        if not any(r["operacion"] == "INSERT" and r["usuario"] == f"Cliente:{client_id}" for r in purchase_audit):
            raise AssertionError("La compra no registro al cliente autenticado.")
        if not any(r["operacion"] == "INSERT" and r["usuario"] == f"Veterinario:{vet_id}" for r in history_audit):
            raise AssertionError("El historial no registro al veterinario autenticado.")
        q.close()
        check.close()
        if "INSERT" not in {r["operacion"] for r in pet_audit} or any(r["usuario"] != f"Cliente:{client_id}" for r in pet_audit):
            raise AssertionError("La identidad del cliente no quedó en la auditoría HTTP.")
        if "UPDATE" not in {r["operacion"] for r in service_audit} or any(r["usuario"] != f"Administrador:{admin_id}" for r in service_audit if r["operacion"] == "UPDATE"):
            raise AssertionError("La identidad del administrador no quedó en la auditoría HTTP.")

        print("PASS: Flask/Werkzeug escuchó por HTTP local; portal y conexión MySQL respondieron.")
        print("PASS: login real de Administrador y Cliente; rutas protegidas aplicaron roles.")
        print("PASS: acceso administrativo protegido y CRUD HTTP de veterinarios y catálogo.")
        print("PASS: agenda, disponibilidad, reserva y citas del cliente/veterinario.")
        print("PASS: compra, factura e historial clínico por HTTP en base aislada.")
        print("PASS: /auditoria, filtros, restricción de rol y usuarios autenticados en triggers.")
    finally:
        server.shutdown()
        server.server_close()
        server_thread.join(timeout=5)


if __name__ == "__main__":
    main()
