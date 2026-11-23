-- Consultas de sólo lectura para comprobar y consultar la auditoría.
USE ahp_veterinaria;

-- Preinstalación: base actual, tablas de negocio, tabla/triggers ya existentes.
SELECT DATABASE() AS base_actual;
SELECT COUNT(*) AS tablas_negocio
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = DATABASE() AND TABLE_TYPE = 'BASE TABLE' AND TABLE_NAME <> 'auditoria';
SELECT COUNT(*) AS tabla_auditoria
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'auditoria' AND TABLE_TYPE = 'BASE TABLE';
SELECT COUNT(*) AS triggers_auditoria
FROM information_schema.TRIGGERS
WHERE TRIGGER_SCHEMA = DATABASE() AND LEFT(TRIGGER_NAME, 4) = 'aud_';

-- Estado de instalación (debe devolver 47 triggers: 45 AFTER y 2 para cascadas).
SELECT EVENT_OBJECT_TABLE AS tabla, EVENT_MANIPULATION AS operacion, TRIGGER_NAME
FROM information_schema.TRIGGERS
WHERE TRIGGER_SCHEMA = DATABASE() AND LEFT(TRIGGER_NAME, 4) = 'aud_'
ORDER BY EVENT_OBJECT_TABLE, EVENT_MANIPULATION;

-- Postinstalación: debe sumar 45 AFTER y 2 BEFORE auxiliares.
SELECT ACTION_TIMING AS momento, EVENT_MANIPULATION AS operacion, COUNT(*) AS cantidad
FROM information_schema.TRIGGERS
WHERE TRIGGER_SCHEMA = DATABASE() AND LEFT(TRIGGER_NAME, 4) = 'aud_'
GROUP BY ACTION_TIMING, EVENT_MANIPULATION
ORDER BY ACTION_TIMING, EVENT_MANIPULATION;
SELECT COUNT(*) AS columnas_auditoria
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'auditoria';

-- Filtros editables para consulta manual (deje NULL para omitir un criterio).
SET @fecha_inicio = NULL;
SET @fecha_fin = NULL;
SET @usuario = NULL;
SET @operacion = NULL;
SET @tabla = NULL;

SELECT id_auditoria, usuario, fecha_hora, operacion, nombre_tabla, id_registro,
       datos_anteriores, datos_nuevos
FROM auditoria
WHERE (@fecha_inicio IS NULL OR fecha_hora >= @fecha_inicio)
  AND (@fecha_fin IS NULL OR fecha_hora < DATE_ADD(@fecha_fin, INTERVAL 1 DAY))
  AND (@usuario IS NULL OR usuario = @usuario)
  AND (@operacion IS NULL OR operacion = @operacion)
  AND (@tabla IS NULL OR nombre_tabla = @tabla)
ORDER BY fecha_hora DESC, id_auditoria DESC
LIMIT 200;
