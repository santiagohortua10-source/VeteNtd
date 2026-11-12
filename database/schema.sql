-- =====================================================================
-- PawCare / VeteNtd - ESTRUCTURA COMPLETA de la base "veterinaria"
-- MySQL 8+ / MariaDB (XAMPP)
--
-- Contiene solo tablas, llaves e indices (sin datos).
-- Los datos estan en:  veterinaria_inserts_completos.sql  (ejecutar DESPUES de este).
--
-- Como usarlo:  phpMyAdmin -> pestana "Importar" -> elegir este archivo -> "Importar".
-- No hace falta crear la base antes.
--
-- AVISO: si las tablas ya existen, este script las BORRA y las vuelve a crear
-- (reinicia la base desde cero). No lo ejecutes si tienes datos que quieras conservar.
--
-- Refleja el estado final del proyecto:
--   schema.sql + ampliaciones de migracion_app.sql + tablas de la tienda (PEDIDOS / PEDIDO_DETALLE)
--   + columnas CorreoEmpleado y ClaveHash en EMPLEADO (login de veterinarios)
--   + HISTORIAL_CLINICO con FechaHora DATETIME y textos de 500 caracteres
--   + USUARIOS.ID_Empleado (enlace de usuario a empleado)
-- =====================================================================

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

CREATE DATABASE IF NOT EXISTS veterinaria
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE veterinaria;

DROP TABLE IF EXISTS PEDIDO_DETALLE;
DROP TABLE IF EXISTS PEDIDOS;
DROP TABLE IF EXISTS HISTORIAL_CLINICO;
DROP TABLE IF EXISTS RESPONSABLE_ALTERNO;
DROP TABLE IF EXISTS USUARIOS;
DROP TABLE IF EXISTS PAGO;
DROP TABLE IF EXISTS DETALLE_FACTURA;
DROP TABLE IF EXISTS FACTURACION;
DROP TABLE IF EXISTS RESERVAS;
DROP TABLE IF EXISTS HORARIO;
DROP TABLE IF EXISTS MASCOTA;
DROP TABLE IF EXISTS CATALOGO_SERVICIOS;
DROP TABLE IF EXISTS EMPLEADO;
DROP TABLE IF EXISTS CLIENTE;
DROP TABLE IF EXISTS PRODUCTOS;

-- ---------------------------------------------------------------------
-- Tablas independientes
-- ---------------------------------------------------------------------

CREATE TABLE PRODUCTOS (
    ID_Producto    INT AUTO_INCREMENT NOT NULL,
    TipoProducto   VARCHAR(100) NOT NULL,
    Descripcion    VARCHAR(255) NOT NULL DEFAULT '',
    ValorProducto  INT NOT NULL,
    Icono          VARCHAR(10)  NOT NULL DEFAULT '',
    Stock          INT NOT NULL DEFAULT 0,
    PRIMARY KEY (ID_Producto)
) ENGINE=InnoDB;

CREATE TABLE CLIENTE (
    ID_Cliente        INT AUTO_INCREMENT NOT NULL,
    NombreCliente     VARCHAR(100) NOT NULL,
    ContactoCliente   VARCHAR(20)  NOT NULL,
    DireccionCliente  VARCHAR(100) NOT NULL,
    CorreoCliente     VARCHAR(100) NULL,
    ClaveHash         VARCHAR(255) NULL,
    PRIMARY KEY (ID_Cliente),
    UNIQUE KEY uq_cliente_correo (CorreoCliente)
) ENGINE=InnoDB;

-- Los veterinarios inician sesion con CorreoEmpleado + ClaveHash (hash de Werkzeug).
CREATE TABLE EMPLEADO (
    ID_Empleado        INT AUTO_INCREMENT NOT NULL,
    NombreEmpleado     VARCHAR(50)  NOT NULL,
    ContactoEmpleado   VARCHAR(20)  NOT NULL,
    CargoEmpleado      VARCHAR(30)  NOT NULL,
    CorreoEmpleado     VARCHAR(100) NULL,
    ClaveHash          VARCHAR(255) NULL,
    PRIMARY KEY (ID_Empleado),
    UNIQUE KEY uq_empleado_correo (CorreoEmpleado)
) ENGINE=InnoDB;

CREATE TABLE CATALOGO_SERVICIOS (
    ID_CataServicio   INT AUTO_INCREMENT NOT NULL,
    Servicio          VARCHAR(100) NOT NULL,
    Descripcion       VARCHAR(255) NOT NULL DEFAULT '',
    DuracionServicio  INT NOT NULL,
    CostoServicio     INT NOT NULL,
    Icono             VARCHAR(10)  NOT NULL DEFAULT '',
    Cupos             INT NOT NULL DEFAULT 0,
    PRIMARY KEY (ID_CataServicio)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Tablas con dependencias
-- ---------------------------------------------------------------------

CREATE TABLE MASCOTA (
    ID_Mascota       INT AUTO_INCREMENT NOT NULL,
    ID_Cliente       INT NOT NULL,
    NombreMascota    VARCHAR(50) NOT NULL,
    Especie          VARCHAR(30) NOT NULL,
    Raza             VARCHAR(50) NOT NULL,
    FechaNacimiento  DATE NOT NULL,
    Tamano           VARCHAR(20) NOT NULL,
    Peso             DECIMAL(5,2) NOT NULL,
    Genero           VARCHAR(20) NOT NULL,
    PRIMARY KEY (ID_Mascota),
    CONSTRAINT fk_mascota_cliente
        FOREIGN KEY (ID_Cliente) REFERENCES CLIENTE (ID_Cliente)
) ENGINE=InnoDB;

CREATE TABLE HORARIO (
    ID_Horario   INT AUTO_INCREMENT NOT NULL,
    ID_Empleado  INT NOT NULL,
    DiaSemana    VARCHAR(20) NOT NULL,
    HoraInicio   TIME NOT NULL,
    HoraFin      TIME NOT NULL,
    PRIMARY KEY (ID_Horario),
    CONSTRAINT fk_horario_empleado
        FOREIGN KEY (ID_Empleado) REFERENCES EMPLEADO (ID_Empleado)
) ENGINE=InnoDB;

CREATE TABLE RESERVAS (
    ID_Reserva       INT AUTO_INCREMENT NOT NULL,
    ID_Empleado      INT NOT NULL,
    ID_Mascota       INT NOT NULL,
    ID_CataServicio  INT NOT NULL,
    FechaReserva     DATE NOT NULL,
    HoraReserva      TIME NOT NULL,
    EstadoCita       VARCHAR(20) NOT NULL,
    PRIMARY KEY (ID_Reserva),
    CONSTRAINT fk_reservas_empleado
        FOREIGN KEY (ID_Empleado) REFERENCES EMPLEADO (ID_Empleado),
    CONSTRAINT fk_reservas_mascota
        FOREIGN KEY (ID_Mascota) REFERENCES MASCOTA (ID_Mascota),
    CONSTRAINT fk_reservas_servicio
        FOREIGN KEY (ID_CataServicio) REFERENCES CATALOGO_SERVICIOS (ID_CataServicio)
) ENGINE=InnoDB;

-- (DECIMAL(12,2): con DECIMAL(5,2) no caben valores en pesos)
CREATE TABLE FACTURACION (
    ID_Facturacion  INT AUTO_INCREMENT NOT NULL,
    ID_Cliente      INT NOT NULL,
    FECHA           DATETIME NOT NULL,
    ImpuestosIVA    DECIMAL(12,2) NOT NULL,
    TotalPagar      DECIMAL(12,2) NOT NULL,
    PRIMARY KEY (ID_Facturacion),
    CONSTRAINT fk_facturacion_cliente
        FOREIGN KEY (ID_Cliente) REFERENCES CLIENTE (ID_Cliente)
) ENGINE=InnoDB;

CREATE TABLE DETALLE_FACTURA (
    ID_DetFactura    INT AUTO_INCREMENT NOT NULL,
    ID_Producto      INT NOT NULL,
    ID_Facturacion   INT NOT NULL,
    ID_Servicio      INT NOT NULL,
    Cantidad         INT NOT NULL,
    PrecioUnitario   INT NOT NULL,
    PRIMARY KEY (ID_DetFactura),
    CONSTRAINT fk_detfactura_producto
        FOREIGN KEY (ID_Producto) REFERENCES PRODUCTOS (ID_Producto),
    CONSTRAINT fk_detfactura_facturacion
        FOREIGN KEY (ID_Facturacion) REFERENCES FACTURACION (ID_Facturacion),
    CONSTRAINT fk_detfactura_servicio
        FOREIGN KEY (ID_Servicio) REFERENCES CATALOGO_SERVICIOS (ID_CataServicio)
) ENGINE=InnoDB;

CREATE TABLE PAGO (
    ID_Pago              INT AUTO_INCREMENT NOT NULL,
    ID_Facturacion       INT NOT NULL,
    MetodoPago           VARCHAR(15) NOT NULL,
    ValorRecibido        DECIMAL(18,2) NOT NULL,
    CambioValorRecibido  DECIMAL(18,2) NOT NULL,
    ComprobantePago      VARCHAR(20) NULL,
    FechaPago            DATETIME NOT NULL,
    PRIMARY KEY (ID_Pago),
    CONSTRAINT fk_pago_facturacion
        FOREIGN KEY (ID_Facturacion) REFERENCES FACTURACION (ID_Facturacion)
) ENGINE=InnoDB;

-- Cuentas del portal de clientes (el registro escribe en CLIENTE y en USUARIOS).
-- ID_Empleado: enlace opcional de un usuario con un empleado.
CREATE TABLE USUARIOS (
    ID_USUARIO     INT AUTO_INCREMENT NOT NULL,
    ID_Cliente     INT NULL,
    ID_Empleado    INT NULL,
    Nombre         VARCHAR(100) NOT NULL,
    Correo         VARCHAR(100) NOT NULL,
    ClaveHash      VARCHAR(255) NOT NULL,
    Clave          VARCHAR(255) NULL,
    Rol            VARCHAR(20)  NOT NULL DEFAULT 'Cliente',
    FechaRegistro  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ID_USUARIO),
    UNIQUE KEY uq_usuarios_correo (Correo),
    UNIQUE KEY uq_usuarios_cliente (ID_Cliente),
    UNIQUE KEY uq_usuarios_empleado (ID_Empleado),
    CONSTRAINT fk_usuarios_cliente
        FOREIGN KEY (ID_Cliente) REFERENCES CLIENTE (ID_Cliente) ON DELETE CASCADE,
    CONSTRAINT fk_usuarios_empleado
        FOREIGN KEY (ID_Empleado) REFERENCES EMPLEADO (ID_Empleado) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE RESPONSABLE_ALTERNO (
    ID_RESPONSABLE        INT AUTO_INCREMENT NOT NULL,
    ID_Mascota            INT NOT NULL,
    Nombre                VARCHAR(50) NOT NULL,
    Documento             VARCHAR(20) NOT NULL,
    Telefono              VARCHAR(20) NOT NULL,
    Relacion              VARCHAR(30) NOT NULL,
    AutorizacionDeRetiro  BOOLEAN NOT NULL,
    PRIMARY KEY (ID_RESPONSABLE),
    CONSTRAINT fk_responsable_mascota
        FOREIGN KEY (ID_Mascota) REFERENCES MASCOTA (ID_Mascota)
) ENGINE=InnoDB;

CREATE TABLE HISTORIAL_CLINICO (
    ID_HISTORIAL  INT AUTO_INCREMENT NOT NULL,
    ID_Empleado   INT NOT NULL,
    ID_Mascota    INT NOT NULL,
    ID_Reserva    INT NOT NULL,
    FechaHora     DATETIME NOT NULL,
    Diagnostico   VARCHAR(500) NOT NULL,
    Tratamiento   VARCHAR(500) NOT NULL,
    PRIMARY KEY (ID_HISTORIAL),
    CONSTRAINT fk_historial_empleado
        FOREIGN KEY (ID_Empleado) REFERENCES EMPLEADO (ID_Empleado),
    CONSTRAINT fk_historial_mascota
        FOREIGN KEY (ID_Mascota) REFERENCES MASCOTA (ID_Mascota),
    CONSTRAINT fk_historial_reserva
        FOREIGN KEY (ID_Reserva) REFERENCES RESERVAS (ID_Reserva)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Tienda: pedidos de productos desde el portal
-- ---------------------------------------------------------------------

CREATE TABLE PEDIDOS (
    ID_Pedido   INT AUTO_INCREMENT NOT NULL,
    ID_Cliente  INT NOT NULL,
    Fecha       DATETIME NOT NULL,
    Total       INT NOT NULL,
    Estado      VARCHAR(20) NOT NULL DEFAULT 'Confirmado',
    PRIMARY KEY (ID_Pedido),
    KEY idx_pedidos_cliente (ID_Cliente, Fecha),
    CONSTRAINT fk_pedidos_cliente
        FOREIGN KEY (ID_Cliente) REFERENCES CLIENTE (ID_Cliente)
) ENGINE=InnoDB;

CREATE TABLE PEDIDO_DETALLE (
    ID_Detalle      INT AUTO_INCREMENT NOT NULL,
    ID_Pedido       INT NOT NULL,
    ID_Producto     INT NOT NULL,
    Cantidad        INT NOT NULL,
    PrecioUnitario  INT NOT NULL,
    PRIMARY KEY (ID_Detalle),
    CONSTRAINT fk_pdet_pedido
        FOREIGN KEY (ID_Pedido) REFERENCES PEDIDOS (ID_Pedido) ON DELETE CASCADE,
    CONSTRAINT fk_pdet_producto
        FOREIGN KEY (ID_Producto) REFERENCES PRODUCTOS (ID_Producto)
) ENGINE=InnoDB;

SET FOREIGN_KEY_CHECKS = 1;