# PawCare: auditoria, fixtures y pruebas

## Estado de entrega

`ahp_veterinaria` tiene la tabla `auditoria` y 47 triggers: 45 AFTER (INSERT/UPDATE/DELETE para las 15 tablas de negocio) y 2 BEFORE para las cascadas a `usuarios`. El reporte `/auditoria` es exclusivo de Administrador y filtra por fechas, usuario, operacion y tabla. Flask escribe la identidad JWT como `Rol:id`; los snapshots excluyen `ClaveHash` y `Clave`.

La base de entrega tiene 15 tablas, 19 FK y al menos 11 filas por tabla. Se validaron cero huerfanos, cero duplicados de fixtures y 165 eventos de insercion del seed en auditoria (11 por tabla). La base `veterinaria` no fue modificada.

## Backups/restauracion

`database/crear_backups.py` usa la configuracion local sin imprimir credenciales, fija como objetivo `ahp_veterinaria` y crea nombres unicos. `backups/` esta excluida de Git. Se restauraron los respaldos existentes en `pawcare_restore_check_bb9ec946f434` y se confirmaron 15 tablas, 19 FK, cero huerfanos y conteos coincidentes.

## Instalacion de auditoria

En un entorno autorizado con `DB_NAME=ahp_veterinaria` y backup validado:

```powershell
python database/instalar_auditoria.py
```

El script reanuda una instalacion parcial, no recrea la tabla ni duplica triggers que coincidan; cierra conexiones antes de DDL y verifica objetos individualmente. Las pruebas CRUD/cascada son transaccionales y hacen rollback.

## Seed academico

`seed_academico_pruebas.py` es exclusivo para bases `pawcare_audit_test_*`. `instalar_seed_academico.py` exige un destino explicito; `ahp_veterinaria` requiere tambien `--confirm-target ahp_veterinaria` y una confirmacion interactiva. Hace preflight de esquema/conteos/FK/duplicados, usa hash efimero y transaccion, y valida auditoria y conteos antes de commit.

```powershell
python database/instalar_seed_academico.py --database ahp_veterinaria --confirm-target ahp_veterinaria
```

No ejecutes `database/seed_academico_pruebas.sql` directamente: tiene marcador de hash y `USE ahp_veterinaria`. No ejecutes `database/schema.sql` sobre una base existente; contiene `DROP TABLE`.

## Pruebas

```powershell
python -m unittest discover -s tests -v
python -m compileall -q .
$env:DB_NAME = 'pawcare_audit_test_cbed051b'
python tests/mysql_integration_auditoria.py
python tests/flask_http_smoke.py
Remove-Item Env:DB_NAME
```

Las pruebas MySQL/HTTP rechazan bases que no tengan prefijo `pawcare_audit_test_`; solo escriben en una copia aislada. La prueba HTTP no conecta a Mongo (notificaciones no-op). Las pruebas de cierre actuales se describen en `docs/entrega/evidencia_pruebas.md`.

## Configuracion privada y datos de ejemplo

`.env.example` contiene marcadores; `.env` y `backups/` no se publican. No hay credenciales de prueba compartidas documentadas. En archivos heredados permanecen hashes/credenciales demo de ejemplo; no se cambiaron. Revisa los artefactos de demostracion antes de publicar datos de ejemplo.
