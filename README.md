# PawCare

Proyecto universitario de gestion veterinaria con portales de cliente, veterinario y administrador.

**Integrantes:** Santiago Ariza, Santiago Hortua y Hawin Pinzon.

## Funcionalidades

- Registro, inicio de sesion y control de acceso por roles.
- Mascotas, agenda, disponibilidad, reservas y cancelaciones.
- Catalogo y compras con inventario, facturacion y pagos.
- Portal veterinario con citas e historial clinico.
- Panel administrativo y reporte CRUD `/auditoria` con filtros.
- Notificaciones MongoDB opcionales.

## Tecnologias

Python 3.9+, Flask 3, MySQL/MariaDB (desarrollo local probado con XAMPP MariaDB 10.4), JWT, MongoDB/PyMongo opcional, HTML, CSS y JavaScript.

## Requisitos

- Python 3.9 o posterior.
- MySQL o MariaDB local. En Windows se puede usar XAMPP.
- Git para clonar el proyecto.
- MongoDB local o Atlas solo si se van a usar notificaciones.

## Clonar e instalar

```powershell
git clone -b feature/entrega-pawcare https://github.com/santiagohortua10-source/VeteNtd.git
cd VeteNtd
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

En macOS/Linux, crea y activa el entorno con `python3 -m venv .venv` y `source .venv/bin/activate`.

## Configurar `.env`

Edita `.env` localmente. Define `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `SECRET_KEY` y `JWT_SECRET_KEY`. Genera secretos aleatorios independientes; no reutilices los marcadores del ejemplo. No compartas `.env` ni lo agregues a Git.

`.env.example` apunta a `ahp_veterinaria` como base de entrega. El proyecto no distribuye volcados de bases ni credenciales de cuentas. Completa `MONGO_URI` solo si vas a habilitar las notificaciones MongoDB.

## Crear o restaurar una base local

Para una instalacion nueva y descartable, `database/schema.sql` crea la base `veterinaria`, pero contiene `DROP TABLE`. Usalo solo en una instancia local nueva, despues de confirmar que no contiene datos que quieras conservar. Nunca lo ejecutes sobre `ahp_veterinaria`, una base compartida o una base existente con informacion.

Para trabajar con `ahp_veterinaria`, usa una base local autorizada o restaura un backup suministrado de forma segura. Los archivos de `backups/` se excluyen de Git porque pueden contener datos privados; no se incluyen en el repositorio. `database/verificar_restauracion.py` restaura el backup disponible en un schema nuevo `pawcare_restore_check_*` y valida tablas, FK, filas huerfanas y conteos.

Despues ajusta `DB_NAME` en `.env` al schema local que realmente preparaste. No apuntes la aplicacion a una base remota o compartida sin autorizacion.

## Instalar auditoria

La instalacion de entrega requiere una base local `ahp_veterinaria` con el esquema esperado. Configura `DB_NAME=ahp_veterinaria`, valida y conserva un backup, y ejecuta:

```powershell
python database/instalar_auditoria.py
```

El instalador crea la tabla si falta, reanuda triggers parciales sin duplicarlos y verifica los 47 triggers mediante `information_schema`. Las pruebas CRUD transaccionales revierten sus filas ficticias. No ejecutes `database/schema.sql` para instalar auditoria.

El seed academico es opcional y requiere autorizacion expresa porque inserta filas en la base indicada. En `ahp_veterinaria`, ejecuta:

```powershell
python database/instalar_seed_academico.py --database ahp_veterinaria --confirm-target ahp_veterinaria
```

Escribe la frase que solicita el instalador solo despues de verificar el destino y el backup. El seed agrega datos ficticios idempotentes; no actualiza ni elimina filas existentes.

## Ejecutar Flask

Con MySQL disponible y `.env` configurado:

```powershell
python app.py
```

Abre `http://127.0.0.1:5000`. Para una ejecucion local no expongas Flask en redes publicas. Las cuentas de ejemplo no tienen contrasenas reutilizables documentadas; crea cuentas de prueba con contrasenas propias en una base local.

## Pruebas

Las pruebas unitarias no requieren una base externa:

```powershell
python -m unittest discover -s tests -v
python -m compileall -q .
git diff --check
```

Las pruebas MySQL y HTTP requieren una base desechable ya preparada cuyo nombre empiece por `pawcare_audit_test_`, con 15 tablas, auditoria, 47 triggers y al menos 11 filas por tabla. Establece el nombre explicitamente y usa solo datos ficticios:

```powershell
$env:DB_NAME = 'pawcare_audit_test_<sufijo>'
python tests/mysql_integration_auditoria.py
python tests/flask_http_smoke.py
Remove-Item Env:DB_NAME
```

Ambas pruebas rechazan otros nombres de base. La prueba HTTP genera usuarios aleatorios y sustituye las notificaciones Mongo por no-op. No se publican usuarios ni contrasenas de prueba.

## Documentacion

- [Informe tecnico](docs/entrega/informe_tecnico.md)
- [Procedimiento de instalacion](docs/entrega/instalacion_final.md)
- [Evidencia de pruebas](docs/entrega/evidencia_pruebas.md)
- [Diccionario de datos](docs/entrega/diccionario_datos.csv)
- Diagramas Draw.io y SVG en `docs/entrega/`
- Capturas de interfaz en `docs/capturas/`

No hay capturas nuevas de las pruebas de auditoria; no se presentan como evidencia visual.
