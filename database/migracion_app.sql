-- =====================================================
-- Ajustes para que la página (app.py) funcione con la BD
-- Ejecutar UNA sola vez, después de schema.sql
-- =====================================================
USE veterinaria;

-- La página muestra descripción, icono y cupos/stock, que el esquema original no tenía.
-- También se amplían los nombres: los textos de ejemplo superan los 30 caracteres.

ALTER TABLE CATALOGO_SERVICIOS
    MODIFY Servicio     VARCHAR(100) NOT NULL,
    ADD COLUMN Descripcion VARCHAR(255) NOT NULL DEFAULT '',
    ADD COLUMN Icono       VARCHAR(10)  NOT NULL DEFAULT '🐾',
    ADD COLUMN Cupos       INT          NOT NULL DEFAULT 0;

ALTER TABLE PRODUCTOS
    MODIFY TipoProducto VARCHAR(100) NOT NULL,
    ADD COLUMN Descripcion VARCHAR(255) NOT NULL DEFAULT '',
    ADD COLUMN Icono       VARCHAR(10)  NOT NULL DEFAULT '🐾',
    ADD COLUMN Stock       INT          NOT NULL DEFAULT 0;
