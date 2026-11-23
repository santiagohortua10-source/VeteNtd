# PawCare - informe tecnico final

**Integrantes:** Santiago Ariza, Santiago Hortua y Hawin Pinzon
**Rama:** `feature/entrega-pawcare`
**Motor verificado:** MariaDB 10.4.32
**Base academica:** `ahp_veterinaria`

## Resumen de entrega

PawCare es una aplicacion Flask con portales para clientes, veterinarios y administradores. Gestiona mascotas, agenda, reservas, catalogo, compras, facturacion, pagos e historial clinico. MongoDB se usa opcionalmente para notificaciones.

La auditoria CRUD esta instalada en `ahp_veterinaria`: tabla `auditoria` y 47 triggers. Se insertaron fixtures academicos ficticios e idempotentes; las 15 tablas alcanzaron al menos 11 filas. El backup y las verificaciones de integridad se completaron antes/despues de insertar. La base `veterinaria` no fue modificada.

## Arquitectura de auditoria

Flask obtiene `Rol:id` del JWT firmado y establece `@usuario_auditoria` por conexion. La tabla guarda usuario, fecha/hora, operacion, tabla, PK y snapshots JSON anteriores/nuevos. Se excluyen `ClaveHash` y `Clave`. El reporte `/auditoria` requiere Administrador y filtra fecha, usuario, operacion y tabla.

El esquema tiene 45 triggers AFTER (INSERT, UPDATE y DELETE para las 15 tablas de negocio) y dos BEFORE auxiliares que registran filas de `usuarios` antes de las cascadas ON DELETE desde `cliente` y `empleado`.

## Estado de `ahp_veterinaria`

- 15 tablas de negocio, 19 claves foraneas.
- 47 triggers verificados mediante `information_schema`.
- 165 eventos INSERT de seed, 11 por tabla, atribuidos a `SEED_PRUEBAS`.
- 0 filas huerfanas y 0 grupos de duplicados de fixtures.
- La insercion fue aditiva; se conservaron las filas existentes.

Conteos finales:

| Tabla | Filas |
|---|---:|
| `catalogo_servicios` | 16 |
| `cliente` | 16 |
| `detalle_factura` | 14 |
| `empleado` | 15 |
| `facturacion` | 13 |
| `historial_clinico` | 18 |
| `horario` | 31 |
| `mascota` | 18 |
| `pago` | 13 |
| `pedidos` | 12 |
| `pedido_detalle` | 13 |
| `productos` | 16 |
| `reservas` | 25 |
| `responsable_alterno` | 11 |
| `usuarios` | 12 |

Los snapshots se revisaron: no contienen claves ni hashes. El procedimiento de instalacion y validacion esta en `docs/entrega/instalacion_final.md`.

## Backups

Se utilizaron los respaldos existentes, sin sobrescribirlos:

- `backups/ahp_veterinaria_estructura_20261122T230949Z_548166.sql` (13.959 bytes, 15 tablas).
- `backups/ahp_veterinaria_datos_20261122T230949Z_548166.sql` (10.629 bytes, datos de 14 tablas pobladas).

Se restauraron y verificaron en `pawcare_restore_check_bb9ec946f434`: 15 tablas, 19 FK, 0 filas huerfanas y conteos coincidentes. `backups/` esta excluida de Git. Una copia temporal previa incompleta, `pawcare_restore_check_a20ecd833517`, se conserva vacia; no se elimino.

## Pruebas

- Auditoria en la base academica: CRUD de prueba dentro de una transaccion revertida; snapshots INSERT/UPDATE/DELETE; identidad Flask/JWT; cascadas; exclusion de credenciales. Conteos de negocio sin cambios durante esa prueba.
- Reporte Flask `/auditoria`: HTTP 200 con sesion de Administrador.
- Seed probado dos veces en `pawcare_audit_test_cbed051b`: ambas ejecuciones idempotentes, 0 filas nuevas en la segunda repeticion, todas las tablas con 11 o mas filas, 19 FK, 0 huerfanos, sin duplicados y 165 eventos de auditoria del seed previamente registrados.
- Las 10 pruebas unitarias aprobaron; `compileall -q .` termino sin errores; las pruebas MySQL y HTTP pasaron en `pawcare_audit_test_cbed051b`. El reporte `/auditoria` en `ahp_veterinaria` respondio HTTP 200 con filtro por usuario/operacion/tabla. Los resultados estan en `docs/entrega/evidencia_pruebas.md`.
- La prueba HTTP cubre acceso administrativo, roles, catalogo, veterinarios, mascotas, disponibilidad, reservas, citas, compras/facturacion, historial clinico y filtros de `/auditoria`. Se ejecuta solo en una base aislada; Mongo se reemplaza por no-op.

## Configuracion y seguridad

`.env.example` contiene marcadores y apunta a `ahp_veterinaria`. El `.env` privado no se modifica ni se publica; su configuracion local permanece en `veterinaria`. `README.md` documenta requisitos, creacion/restauracion, instalacion de auditoria, seed, Flask y pruebas.

No se incluyeron backups ni `.env` en Git. No se encontraron claves privadas o URIs con credenciales operativas entre los cambios preparados. Permanecen en archivos heredados tres hashes Werkzeug de ejemplo y una clave de demostracion documentada en `database/schema.sql`; no se modificaron y no se documentan credenciales compartidas.

## Limitaciones

- MongoDB no se verifico; las notificaciones fueron sustituidas durante la prueba HTTP.
- La restauracion se comprobo en una base temporal del mismo servidor, no en un servidor independiente.
- Las pruebas de auditoria reales se hicieron sobre `ahp_veterinaria` con DML ficticio dentro de una transaccion revertida y sobre copias aisladas; no se hicieron capturas nuevas de esas pruebas.
- La publicacion se realiza despues de la revision de seguridad y del staging, sin incluir `.env` ni `backups/`.
