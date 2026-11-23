# PawCare - instalacion y operacion

## Estado actual de entrega

La base `ahp_veterinaria` tiene la tabla `auditoria`, 47 triggers (45 AFTER y 2 auxiliares) y fixtures ficticios. Las pruebas finales de integridad observaron 15 tablas, 19 FK, 0 filas huerfanas, cero duplicados fixture y al menos 11 filas por tabla. La base `veterinaria` no se modifico.

## Procedimiento para una instalacion nueva

### 1. Backup

En Windows/XAMPP, configura localmente `.env` con acceso a la base y ejecuta:

```powershell
python database/crear_backups.py
```

El generador apunta explicitamente a `ahp_veterinaria`, crea nombres unicos, valida la estructura y evita `DROP TABLE`/`DROP DATABASE`. Conserva los archivos fuera de Git. No uses backups sobreescritos ni los publiques.

### 2. Validacion de destino

Confirma nombre exacto, 15 tablas de negocio, claves primarias, 19 FK y ausencia de objetos en conflicto. Compara con el diccionario. Detente ante cualquier discrepancia.

### 3. Auditoria

La instalacion ya esta hecha en la base de entrega. En una base nueva compatible, establece localmente `DB_NAME=ahp_veterinaria` y ejecuta:

```powershell
python database/instalar_auditoria.py
```

El instalador verifica destino/PK/FK, valida una tabla preexistente sin recrearla, detecta triggers que coinciden y reanuda solo los faltantes. Crea/verifica cada trigger de uno en uno con conexiones cerradas antes de DDL. Comprueba 47 objetos, hace CRUD/cascada de prueba dentro de una transaccion revertida y valida el reporte Flask.

No uses `database/schema.sql` para instalar auditoria. Ese archivo contiene `DROP TABLE` y solo sirve para una base local nueva y descartable, nunca para una base con datos.

### 4. Fixtures academicos

El SQL usa identificadores ficticios bajo `example.invalid`, y el wrapper de pruebas `seed_academico_pruebas.py` solo permite `pawcare_audit_test_*`. El ejecutor de entrega exige destino explicito:

```powershell
python database/instalar_seed_academico.py --database ahp_veterinaria --confirm-target ahp_veterinaria
```

El ejecutor valida 15 tablas, 19 FK, cero huérfanos, tabla auditoria y 47 triggers; calcula faltantes para meta 11, detecta duplicados de fixtures y exige escribir la frase exacta. Usa INSERT idempotentes en transaccion, verifica integridad/conteos/auditoria antes de commit y hace rollback ante errores. No elimina ni actualiza filas existentes.

Resultado de esta entrega: se agregaron 11 filas ficticias a cada una de las 15 tablas; la segunda ejecucion en la copia aislada agrego cero. La insercion academica en la base de entrega queda registrada como 165 eventos `SEED_PRUEBAS`, 11 por tabla.

### 5. Comprobaciones posteriores

Conteos actuales de `ahp_veterinaria`: catalogo_servicios 16, cliente 16, detalle_factura 14, empleado 15, facturacion 13, historial_clinico 18, horario 31, mascota 18, pago 13, pedidos 12, pedido_detalle 13, productos 16, reservas 25, responsable_alterno 11, usuarios 12. Se confirmaron 19 FK y cero huerfanos. La auditoria conserva sus 47 triggers.

## Reversion segura

- MySQL puede confirmar DDL implicitamente. No intentes revertir tabla/triggers con rollback.
- Si el instalador se detiene, conserva todo objeto creado y consulta `information_schema`; no borres/recrees objetos automaticamente.
- La tabla `auditoria` es evidencia historica. No la elimines. Si se necesita suspender auditoria, exporta primero sus registros y retira triggers individualmente solo tras revisar y autorizar esa operacion.
- Los fixtures confirmados no tienen reversa automatica. No ejecutes `DELETE` general ni restaures encima de una base activa. Una limpieza de fixtures requiere revision/identificacion manual y autorizacion separada.

## Pruebas

- Unitaria: `python -m unittest discover -s tests -v`.
- Compilacion: `python -m compileall -q .`.
- MySQL y HTTP: solo sobre `pawcare_audit_test_*` ya preparado, con auditoria/47 triggers y al menos 11 filas. Las pruebas rechazan otros nombres y escriben datos ficticios unicamente en esa copia.
- Restauracion: `python database/verificar_restauracion.py` crea un schema `pawcare_restore_check_*`; `--verify-existing <nombre>` valida uno ya restaurado sin escribir.

## Aplicacion

Crea `.env` desde `.env.example`, genera tus secretos y define el `DB_NAME` local. Para iniciar:

```powershell
python app.py
```

Abre `http://127.0.0.1:5000`. Configura MongoDB solo para notificaciones. No se distribuyen credenciales de cuentas; usa cuentas locales propias.

## Evidencia pendiente

No se generaron capturas nuevas de base de datos ni navegador. Si se requieren para presentacion, toma capturas manuales en un entorno de prueba, sin contrasenas ni datos personales.
