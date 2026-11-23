-- PawCare | Auditor?a CRUD
-- Destino: ahp_veterinaria. Ejecutar s?lo despu?s de respaldar y verificar una copia de pruebas.
-- Este archivo crea la tabla si no existe; no elimina ni modifica tablas de negocio.
USE ahp_veterinaria;

CREATE TABLE IF NOT EXISTS auditoria (
    id_auditoria BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    usuario VARCHAR(120) NOT NULL,
    fecha_hora DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    operacion VARCHAR(10) NOT NULL,
    nombre_tabla VARCHAR(64) NOT NULL,
    id_registro VARCHAR(255) NOT NULL,
    datos_anteriores JSON NULL,
    datos_nuevos JSON NULL,
    PRIMARY KEY (id_auditoria),
    KEY ix_auditoria_fecha (fecha_hora),
    KEY ix_auditoria_usuario_fecha (usuario, fecha_hora),
    KEY ix_auditoria_operacion_fecha (operacion, fecha_hora),
    KEY ix_auditoria_tabla_fecha (nombre_tabla, fecha_hora)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
