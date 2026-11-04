-- =====================================================
-- Esquema de base de datos (MySQL 8+)
-- Generado a partir del diagrama ER
-- =====================================================

CREATE DATABASE IF NOT EXISTS veterinaria
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
USE veterinaria;

-- -----------------------------------------------------
-- Tablas independientes
-- -----------------------------------------------------

CREATE TABLE PRODUCTOS (
    ID_Producto    INT AUTO_INCREMENT NOT NULL,
    TipoProducto   VARCHAR(30) NOT NULL,
    ValorProducto  INT NOT NULL,
    PRIMARY KEY (ID_Producto)
);

CREATE TABLE CLIENTE (
    ID_Cliente        INT AUTO_INCREMENT NOT NULL,
    NombreCliente     VARCHAR(30) NOT NULL,
    ContactoCliente   VARCHAR(20) NOT NULL,
    DireccionCliente  VARCHAR(30) NOT NULL,
    CorreoCliente     VARCHAR(30) NULL,
    PRIMARY KEY (ID_Cliente)
);

CREATE TABLE EMPLEADO (
    ID_Empleado        INT AUTO_INCREMENT NOT NULL,
    NombreEmpleado     VARCHAR(50) NOT NULL,
    ContactoEmpleado   VARCHAR(20) NOT NULL,
    CargoEmpleado      VARCHAR(20) NOT NULL,
    PRIMARY KEY (ID_Empleado)
);

CREATE TABLE CATALOGO_SERVICIOS (
    ID_CataServicio   INT AUTO_INCREMENT NOT NULL,
    Servicio          VARCHAR(30) NOT NULL,
    DuracionServicio  INT NOT NULL,
    CostoServicio     INT NOT NULL,
    PRIMARY KEY (ID_CataServicio)
);

-- -----------------------------------------------------
-- Tablas con dependencias
-- -----------------------------------------------------

CREATE TABLE MASCOTA (
    ID_Mascota       INT AUTO_INCREMENT NOT NULL,
    ID_Cliente       INT NOT NULL,
    NombreMascota    VARCHAR(50) NOT NULL,
    Especie          VARCHAR(30) NOT NULL,
    Raza             VARCHAR(30) NOT NULL,
    FechaNacimiento  DATE NOT NULL,
    Tamano           VARCHAR(20) NOT NULL,
    Peso             DECIMAL(5,2) NOT NULL,
    Genero           VARCHAR(20) NOT NULL,
    PRIMARY KEY (ID_Mascota),
    CONSTRAINT fk_mascota_cliente
        FOREIGN KEY (ID_Cliente) REFERENCES CLIENTE (ID_Cliente)
);

CREATE TABLE HORARIO (
    ID_Horario   INT AUTO_INCREMENT NOT NULL,
    ID_Empleado  INT NOT NULL,
    DiaSemana    VARCHAR(20) NOT NULL,
    HoraInicio   TIME NOT NULL,
    HoraFin      TIME NOT NULL,
    PRIMARY KEY (ID_Horario),
    CONSTRAINT fk_horario_empleado
        FOREIGN KEY (ID_Empleado) REFERENCES EMPLEADO (ID_Empleado)
);

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
);

CREATE TABLE FACTURACION (
    ID_Facturacion  INT AUTO_INCREMENT NOT NULL,
    ID_Cliente      INT NOT NULL,   -- en el diagrama aparece VARCHAR(20); debe ser INT para coincidir con CLIENTE
    FECHA           DATETIME NOT NULL,
    ImpuestosIVA    DECIMAL(5,2) NOT NULL,
    TotalPagar      DECIMAL(5,2) NOT NULL,
    PRIMARY KEY (ID_Facturacion),
    CONSTRAINT fk_facturacion_cliente
        FOREIGN KEY (ID_Cliente) REFERENCES CLIENTE (ID_Cliente)
);

CREATE TABLE DETALLE_FACTURA (
    ID_DetFactura    INT AUTO_INCREMENT NOT NULL,
    ID_Producto      INT NOT NULL,
    ID_Facturacion   INT NOT NULL,
    ID_Servicio      INT NOT NULL,   -- referencia a CATALOGO_SERVICIOS
    Cantidad         INT NOT NULL,
    PrecioUnitario   INT NOT NULL,
    PRIMARY KEY (ID_DetFactura),
    CONSTRAINT fk_detfactura_producto
        FOREIGN KEY (ID_Producto) REFERENCES PRODUCTOS (ID_Producto),
    CONSTRAINT fk_detfactura_facturacion
        FOREIGN KEY (ID_Facturacion) REFERENCES FACTURACION (ID_Facturacion),
    CONSTRAINT fk_detfactura_servicio
        FOREIGN KEY (ID_Servicio) REFERENCES CATALOGO_SERVICIOS (ID_CataServicio)
);

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
);

CREATE TABLE USUARIOS (
    ID_USUARIO       INT AUTO_INCREMENT NOT NULL,
    ID_Empleado      INT NOT NULL,
    ID_Cliente       INT NOT NULL,
    ID_Reserva       INT NOT NULL,
    Fecha_Hora       DATETIME NOT NULL,
    Motivo_Consulta  VARCHAR(20) NOT NULL,
    Rol              VARCHAR(20) NOT NULL,
    PRIMARY KEY (ID_USUARIO),
    CONSTRAINT fk_usuarios_empleado
        FOREIGN KEY (ID_Empleado) REFERENCES EMPLEADO (ID_Empleado),
    CONSTRAINT fk_usuarios_cliente
        FOREIGN KEY (ID_Cliente) REFERENCES CLIENTE (ID_Cliente),
    CONSTRAINT fk_usuarios_reserva
        FOREIGN KEY (ID_Reserva) REFERENCES RESERVAS (ID_Reserva)
);

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
);

CREATE TABLE HISTORIAL_CLINICO (
    ID_HISTORIAL  INT AUTO_INCREMENT NOT NULL,
    ID_Empleado   INT NOT NULL,
    ID_Mascota    INT NOT NULL,
    ID_Reserva    INT NOT NULL,
    FechaHora     VARCHAR(20) NOT NULL,   -- según el diagrama; se recomienda DATETIME
    Diagnostico   VARCHAR(20) NOT NULL,
    Tratamiento   VARCHAR(20) NOT NULL,
    PRIMARY KEY (ID_HISTORIAL),
    CONSTRAINT fk_historial_empleado
        FOREIGN KEY (ID_Empleado) REFERENCES EMPLEADO (ID_Empleado),
    CONSTRAINT fk_historial_mascota
        FOREIGN KEY (ID_Mascota) REFERENCES MASCOTA (ID_Mascota),
    CONSTRAINT fk_historial_reserva
        FOREIGN KEY (ID_Reserva) REFERENCES RESERVAS (ID_Reserva)
);
