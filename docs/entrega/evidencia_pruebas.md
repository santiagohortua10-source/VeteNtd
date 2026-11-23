# Evidencia de pruebas PawCare

Fecha: 22 de noviembre de 2026.

## Auditoria en base academica

Base confirmada: `ahp_veterinaria`, MariaDB 10.4.32. La tabla `auditoria` y los 47 triggers se instalaron/verificaron. Se comprobo metadata de 45 AFTER (INSERT/UPDATE/DELETE en 15 tablas) y dos BEFORE auxiliares para cascadas de `usuarios` desde `cliente`/`empleado`.

La prueba de auditoria uso un JWT ficticio firmado por el proceso y filas ficticias dentro de una transaccion. INSERT registro `datos_nuevos`; UPDATE guardo ambos snapshots; DELETE guardo `datos_anteriores`; cascadas registraron INSERT/DELETE de `usuarios`; todos los eventos reflejaron identidad/fecha y omitieron `ClaveHash`/`Clave`. Se hizo rollback. La tabla quedo sin filas de esa prueba y los conteos de negocio no cambiaron.

El reporte Flask `/auditoria` respondio HTTP 200 como Administrador.

## Prueba del seed en copia aislada

Base: `pawcare_audit_test_cbed051b`. Se ejecuto el instalador corregido dos veces con destino explicitado. Ambas terminaron correctamente e idempotentemente: las tablas ya tenian al menos 11 filas, no se agregaron filas en ninguna repeticion; 19 FK, 0 huérfanos y sin grupos duplicados de fixtures. La base conserva 165 INSERT de seed en auditoria (11 por cada una de las 15 tablas).

La prueba HTTP completa se ejecuta contra una base `pawcare_audit_test_*`: logins de Administrador/Cliente/Veterinario, autorizacion por rol, CRUD, disponibilidad/reservas, agenda, compra, factura/pago, historial clinico, reporte y filtros. Notificaciones Mongo son no-op.

## Seed en `ahp_veterinaria`

Antes de insertar: 47 triggers, 19 FK, 0 filas huerfanas, sin duplicados fixture, 0 eventos previos `SEED_PRUEBAS`. Se suministro la confirmacion interactiva exacta del instalador y su transaccion confirmo 165 INSERT, 11 por tabla.

Conteos finales verificados: `catalogo_servicios` 16, `cliente` 16, `detalle_factura` 14, `empleado` 15, `facturacion` 13, `historial_clinico` 18, `horario` 31, `mascota` 18, `pago` 13, `pedidos` 12, `pedido_detalle` 13, `productos` 16, `reservas` 25, `responsable_alterno` 11 y `usuarios` 12. Integridad posterior: 19 FK, 0 huerfanos, 0 duplicados inesperados, triggers intactos.

Los eventos nuevos se agrupan como `SEED_PRUEBAS`: 11 INSERT en cada tabla de negocio. Se inspeccionaron las claves de todos los snapshots y no hay nombres de campos de clave/hash/contraseña.

## Backups

- `ahp_veterinaria_estructura_20261122T230949Z_548166.sql`: 13.959 bytes, 15 tablas.
- `ahp_veterinaria_datos_20261122T230949Z_548166.sql`: 10.629 bytes, 14 tablas con filas.

Se restauraron en `pawcare_restore_check_bb9ec946f434` y validaron 15 tablas, 19 FK, 0 filas huerfanas, 0 triggers y conteos coincidentes. No contienen instrucciones DROP. Los backups no se agregan a Git.

## Pruebas de cierre

- `python -m unittest discover -s tests -v`: 10 pruebas, OK.
- `python -m compileall -q .`: completado sin errores.
- `tests/mysql_integration_auditoria.py` en `pawcare_audit_test_cbed051b`: PASS para 47 triggers, minimo 11 filas, CRUD/snapshots/identidad/cascada y filtros del reporte (400 para filtro invalido).
- `tests/flask_http_smoke.py` en la misma base aislada: PASS para arranque Flask, logins y roles, catalogo, veterinarios, mascotas, disponibilidad/reserva, agenda, compra/factura, historial clinico y `/auditoria`.
- En la base academica, `/auditoria?usuario=SEED_PRUEBAS&operacion=INSERT&tabla=cliente` respondio HTTP 200 y mostro el filtro.
- El reporte final de auditoria comprob? 165 snapshots INSERT del seed, sin claves/hash en sus datos JSON.

La revision final de `git diff --check`, secretos y staging se realiza antes del commit; todavia no se ha publicado. No se inventaron capturas nuevas de navegador. Se conservan las capturas previas de UI en `docs/capturas/`.
