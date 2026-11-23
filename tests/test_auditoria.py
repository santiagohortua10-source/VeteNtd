"""Pruebas sin escritura en MySQL; la capa de datos se sustituye por un mock."""
import re
import os
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

import auditoria
import app
import auth
import db


ROOT = Path(__file__).resolve().parents[1]


class FiltrosAuditoriaTests(unittest.TestCase):
    def test_arranque_y_rutas_basicas_flask(self):
        client = app.app.test_client()
        home = client.get("/")
        self.assertEqual(302, home.status_code)
        self.assertEqual("/cliente", home.headers["Location"])
        self.assertEqual(401, client.get("/api/servicios").status_code)

    @patch("auditoria.db.consultar", return_value=[])
    def test_compone_filtros_parametrizados_y_fecha_fin_inclusiva(self, consultar):
        auditoria.consultar_registros({
            "fecha_inicio": "2026-01-02", "fecha_fin": "2026-01-03",
            "usuario": "Administrador:7", "operacion": "update",
            "tabla": "cliente",
        })
        sql, params = consultar.call_args.args
        self.assertEqual(5, sql.count("%s"))
        self.assertEqual((
            auditoria.datetime(2026, 1, 2), auditoria.datetime(2026, 1, 4),
            "Administrador:7", "UPDATE", "cliente",
        ), params)
        self.assertIn("LIMIT 200", sql)
        self.assertIn("ORDER BY fecha_hora DESC", sql)

    def test_rechaza_filtros_invalidos(self):
        for filtros in (
            {"fecha_inicio": "mañana"},
            {"fecha_inicio": "2026-02-01", "fecha_fin": "2026-01-01"},
            {"operacion": "DROP"},
            {"tabla": "auditoria; DROP TABLE cliente"},
            {"usuario": "x" * 121},
        ):
            with self.subTest(filtros=filtros), self.assertRaises(auditoria.FiltroInvalido):
                auditoria.consultar_registros(filtros)

    def test_reporte_denegado_sin_sesion(self):
        response = app.app.test_client().get("/auditoria")
        self.assertEqual(302, response.status_code)
        self.assertEqual("/cliente", response.headers["Location"])

    @patch.dict(os.environ, {"JWT_SECRET_KEY": "unit-test-secret"})
    @patch("auditoria.consultar_registros", return_value=[])
    def test_reporte_disponible_con_jwt_administrador(self, consultar):
        token = auth.crear_token(9, "Administrador")
        client = app.app.test_client()
        client.set_cookie(auth.COOKIE, token)
        response = client.get("/auditoria?operacion=INSERT")
        self.assertEqual(200, response.status_code)
        self.assertIn("Auditoría de operaciones".encode(), response.data)
        consultar.assert_called_once()

    @patch.dict(os.environ, {"JWT_SECRET_KEY": "unit-test-secret"})
    def test_identidad_auditoria_sale_del_jwt_firmado(self):
        token = auth.crear_token(42, "Veterinario")
        with app.app.test_request_context("/", headers={"Cookie": f"{auth.COOKIE}={token}"}):
            self.assertEqual("Veterinario:42", auth.identidad_auditoria_actual())


class ConexionIdentidadTests(unittest.TestCase):
    def test_variable_mysql_se_establece_por_conexion_y_no_se_reutiliza(self):
        class Cursor:
            def __init__(self): self.calls = []
            def execute(self, sql, params): self.calls.append((sql, params))
            def close(self): pass
        class Connection:
            def __init__(self): self.cursors = []
            def cursor(self, **kwargs):
                cursor = Cursor(); self.cursors.append(cursor); return cursor
            def close(self): pass
        connections = []
        def connect(**_kwargs):
            conn = Connection(); connections.append(conn); return conn
        with patch.object(db.mysql.connector, "connect", side_effect=connect):
            token = db.establecer_usuario_auditoria("Administrador:4")
            try:
                with db.conexion(): pass
            finally:
                db.restablecer_usuario_auditoria(token)
            with db.conexion(): pass
        self.assertEqual(("SET @usuario_auditoria = %s", ("Administrador:4",)), connections[0].cursors[0].calls[0])
        self.assertEqual(("SET @usuario_auditoria = %s", ("SISTEMA",)), connections[1].cursors[0].calls[0])


class TriggersAuditoriaTests(unittest.TestCase):
    def test_cubre_quince_tablas_y_tres_operaciones_sin_drop(self):
        sql = (ROOT / "database" / "auditoria_triggers.sql").read_text(encoding="utf-8")
        triggers = re.findall(r"CREATE TRIGGER `([^`]+)` AFTER (INSERT|UPDATE|DELETE) ON `([^`]+)`", sql)
        self.assertEqual(45, len(triggers))
        self.assertEqual(set(auditoria.TABLAS_NEGOCIO), {tabla for _, _, tabla in triggers})
        for tabla in auditoria.TABLAS_NEGOCIO:
            self.assertEqual({"INSERT", "UPDATE", "DELETE"}, {op for _, op, t in triggers if t == tabla})
        self.assertNotRegex(sql, r"(?i)\bDROP\s+(TABLE|DATABASE|TRIGGER)\b")
        self.assertNotRegex(sql, r"'ClaveHash'\s*,\s*(?:NEW|OLD)\.")
        self.assertNotRegex(sql, r"'Clave'\s*,\s*(?:NEW|OLD)\.")
        self.assertIn("aud_cliente_before_delete_usuarios", sql)
        self.assertIn("aud_empleado_before_delete_usuarios", sql)

    def test_seed_academico_apunta_a_copia_y_no_es_destructivo(self):
        sql = (ROOT / "database" / "seed_academico_pruebas.sql").read_text(encoding="utf-8")
        self.assertIn("USE ahp_veterinaria", sql)
        self.assertIn("example.invalid", sql)
        self.assertIn("'__HASH_USUARIO_TEST__'", sql)
        self.assertNotIn("scrypt:", sql)
        self.assertNotRegex(sql, r"(?i)\b(DROP|TRUNCATE|DELETE\s+FROM|UPDATE\s+\w+)\b")
        targets = set(re.findall(r"(?i)INSERT\s+INTO\s+`?(\w+)`?", sql))
        self.assertEqual({t.upper() for t in auditoria.TABLAS_NEGOCIO}, {t.upper() for t in targets})

    def test_diagramas_xml_y_svg_validos_con_cobertura_del_esquema(self):
        drawio = ET.parse(ROOT / "docs" / "entrega" / "diagrama_er.drawio").getroot()
        graph = drawio.find("./diagram/mxGraphModel/root")
        self.assertEqual(15, len(graph.findall(".//mxCell[@vertex='1']")))
        self.assertEqual(19, len(graph.findall(".//mxCell[@edge='1']")))
        svg = ET.parse(ROOT / "docs" / "entrega" / "diagrama_er.svg").getroot()
        ns = {"s": "http://www.w3.org/2000/svg"}
        self.assertEqual(15, len(svg.findall(".//s:rect", ns)) - 1)  # fondo + 15 entidades
        relations = [p for p in svg.findall(".//s:path", ns) if p.get("stroke") == "#63897c"]
        self.assertEqual(19, len(relations))


if __name__ == "__main__":
    unittest.main()
