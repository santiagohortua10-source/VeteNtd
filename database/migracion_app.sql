-- =====================================================================
-- VeteNtd - Base de datos completa "veterinaria" (MySQL / MariaDB XAMPP)
-- Unifica: schema.sql + ALTER del catalogo + migracion_app.sql
--          + tablas de la tienda + datos_ejemplo.sql
--
-- Como usarlo en phpMyAdmin:
--   http://localhost/phpmyadmin  ->  pestana "Importar"  ->  elegir este
--   archivo  ->  "Importar".  No hace falta crear la base antes.
--
-- AVISO: si ya existen las tablas, este script las BORRA y las vuelve a
-- crear (sirve para reiniciar la base desde cero).
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

CREATE TABLE EMPLEADO (
    ID_Empleado        INT AUTO_INCREMENT NOT NULL,
    NombreEmpleado     VARCHAR(50) NOT NULL,
    ContactoEmpleado   VARCHAR(20) NOT NULL,
    CargoEmpleado      VARCHAR(30) NOT NULL,
    PRIMARY KEY (ID_Empleado)
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

-- (Ampliado a DECIMAL(12,2): con DECIMAL(5,2) no caben valores en pesos)
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

-- Cuentas del portal de clientes (version de migracion_app.sql)
CREATE TABLE USUARIOS (
    ID_USUARIO     INT AUTO_INCREMENT NOT NULL,
    ID_Cliente     INT NULL,
    Nombre         VARCHAR(100) NOT NULL,
    Correo         VARCHAR(100) NOT NULL,
    ClaveHash      VARCHAR(255) NOT NULL,
    Clave          VARCHAR(255) NULL,
    Rol            VARCHAR(20)  NOT NULL DEFAULT 'Cliente',
    FechaRegistro  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ID_USUARIO),
    UNIQUE KEY uq_usuarios_correo (Correo),
    UNIQUE KEY uq_usuarios_cliente (ID_Cliente),
    CONSTRAINT fk_usuarios_cliente
        FOREIGN KEY (ID_Cliente) REFERENCES CLIENTE (ID_Cliente) ON DELETE CASCADE
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
    FechaHora     VARCHAR(20) NOT NULL,
    Diagnostico   VARCHAR(20) NOT NULL,
    Tratamiento   VARCHAR(20) NOT NULL,
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

-- ---------------------------------------------------------------------
-- Datos iniciales: veterinarios y horarios de atencion
-- (el portal lista a los empleados cuyo cargo empieza por "Veterinari")
-- ---------------------------------------------------------------------

INSERT INTO EMPLEADO (NombreEmpleado, ContactoEmpleado, CargoEmpleado) VALUES
('Dra. Laura Gómez',   '3001112233', 'Veterinaria'),
('Dr. Andrés Ramírez', '3004445566', 'Veterinario'),
('Dra. Camila Torres', '3007778899', 'Veterinaria');

INSERT INTO HORARIO (ID_Empleado, DiaSemana, HoraInicio, HoraFin)
SELECT e.ID_Empleado, d.dia, b.ini, b.fin
FROM EMPLEADO e
JOIN (SELECT 'Lunes' AS dia UNION ALL SELECT 'Martes' UNION ALL SELECT 'Miércoles'
      UNION ALL SELECT 'Jueves' UNION ALL SELECT 'Viernes') d
JOIN (SELECT '08:00' AS ini, '12:00' AS fin UNION ALL SELECT '14:00', '18:00') b
WHERE e.NombreEmpleado = 'Dra. Laura Gómez';

INSERT INTO HORARIO (ID_Empleado, DiaSemana, HoraInicio, HoraFin)
SELECT e.ID_Empleado, d.dia, b.ini, b.fin
FROM EMPLEADO e
JOIN (SELECT 'Lunes' AS dia UNION ALL SELECT 'Miércoles' UNION ALL SELECT 'Viernes'
      UNION ALL SELECT 'Sábado') d
JOIN (SELECT '09:00' AS ini, '13:00' AS fin) b
WHERE e.NombreEmpleado = 'Dr. Andrés Ramírez';

INSERT INTO HORARIO (ID_Empleado, DiaSemana, HoraInicio, HoraFin)
SELECT e.ID_Empleado, d.dia, b.ini, b.fin
FROM EMPLEADO e
JOIN (SELECT 'Martes' AS dia UNION ALL SELECT 'Jueves' UNION ALL SELECT 'Sábado') d
JOIN (SELECT '10:00' AS ini, '13:00' AS fin UNION ALL SELECT '15:00', '19:00') b
WHERE e.NombreEmpleado = 'Dra. Camila Torres';

-- ---------------------------------------------------------------------
-- Datos de ejemplo: servicios y productos
-- ---------------------------------------------------------------------

INSERT INTO CATALOGO_SERVICIOS (Servicio, Descripcion, DuracionServicio, CostoServicio, Icono, Cupos) VALUES
('Consulta General Veterinaria',      'Revisión médica completa a cargo de un veterinario certificado.',          30,  80000, '🩺', 12),
('Vacuna Antirrábica',                'Aplicación de vacuna antirrábica para perros y gatos.',                    15,  60000, '💉', 25),
('Baño y Peluquería Canina',          'Baño medicado, corte de pelo y limpieza de oídos.',                        60,  55000, '🛁', 10),
('Desparasitación Interna y Externa', 'Tratamiento antiparasitario para perros y gatos de cualquier edad.',       20,  45000, '💊', 20),
('Cirugía Menor (Esterilización)',    'Procedimiento quirúrgico ambulatorio con seguimiento post-operatorio.',   120, 250000, '🏥',  4);

INSERT INTO PRODUCTOS (TipoProducto, Descripcion, ValorProducto, Icono, Stock) VALUES
('Alimento Premium para Perros 15kg',      'Nutrición balanceada para perros adultos de todas las razas.',           189900, '🐶', 14),
('Alimento Premium para Gatos 10kg',       'Fórmula especial para el cuidado renal y urinario felino.',              159900, '🐱', 16),
('Kit de Primeros Auxilios para Mascotas', 'Vendas, antisépticos y elementos básicos para emergencias.',              69900, '🩹', 18),
('Transportadora para Mascotas',           'Resistente y ventilada, ideal para viajes y visitas al veterinario.',    129900, '🧳',  9),
('Juguete Interactivo para Mascotas',      'Estimula la mente de tu mascota y reduce la ansiedad.',                   34900, '🎾', 30);

-------------------------------------------------
-----Enlase de usuario a empleado----------------
USE veterinaria;

ALTER TABLE HISTORIAL_CLINICO
    MODIFY FechaHora   DATETIME NOT NULL,
    MODIFY Diagnostico VARCHAR(500) NOT NULL,
    MODIFY Tratamiento VARCHAR(500) NOT NULL;

ALTER TABLE USUARIOS
    ADD COLUMN ID_Empleado INT NULL AFTER ID_Cliente,
    ADD UNIQUE KEY uq_usuarios_empleado (ID_Empleado),
    ADD CONSTRAINT fk_usuarios_empleado
        FOREIGN KEY (ID_Empleado) REFERENCES EMPLEADO (ID_Empleado) ON DELETE CASCADE;

----------------------------------
---------insterts-----------------
USE veterinaria;

-- Veterinario dueño de las citas (el que tiene la sesión iniciada)
SET @vet   = (SELECT ID_Empleado FROM EMPLEADO WHERE NombreEmpleado = 'felipe' ORDER BY ID_Empleado DESC LIMIT 1);
SET @laura = (SELECT ID_Empleado FROM EMPLEADO WHERE NombreEmpleado LIKE 'Dra. Laura%' LIMIT 1);

-- Servicios (se buscan por nombre para no depender de los ids)
SET @s_consulta = (SELECT ID_CataServicio FROM CATALOGO_SERVICIOS WHERE Servicio LIKE 'Consulta%' LIMIT 1);
SET @s_vacuna   = (SELECT ID_CataServicio FROM CATALOGO_SERVICIOS WHERE Servicio LIKE 'Vacuna%'   LIMIT 1);
SET @s_bano     = (SELECT ID_CataServicio FROM CATALOGO_SERVICIOS WHERE Servicio LIKE 'Ba%'       LIMIT 1);
SET @s_despar   = (SELECT ID_CataServicio FROM CATALOGO_SERVICIOS WHERE Servicio LIKE 'Despar%'   LIMIT 1);
SET @s_cirugia  = (SELECT ID_CataServicio FROM CATALOGO_SERVICIOS WHERE Servicio LIKE 'Cir%'      LIMIT 1);

-- ---------- Clientes de ejemplo ----------
INSERT INTO CLIENTE (NombreCliente, ContactoCliente, DireccionCliente, CorreoCliente)
VALUES ('María Fernanda Rojas', '3101234567', 'Calle 45 #12-30', 'maria.rojas@ejemplo.com');
SET @c1 = LAST_INSERT_ID();
INSERT INTO CLIENTE (NombreCliente, ContactoCliente, DireccionCliente, CorreoCliente)
VALUES ('Carlos Andrés Pérez', '3157654321', 'Carrera 7 #80-15', 'carlos.perez@ejemplo.com');
SET @c2 = LAST_INSERT_ID();
INSERT INTO CLIENTE (NombreCliente, ContactoCliente, DireccionCliente, CorreoCliente)
VALUES ('Laura Sofía Martínez', '3209876543', 'Avenida 68 #24-10', 'laura.martinez@ejemplo.com');
SET @c3 = LAST_INSERT_ID();
INSERT INTO CLIENTE (NombreCliente, ContactoCliente, DireccionCliente, CorreoCliente)
VALUES ('Juan David Torres', '3012345678', 'Calle 100 #15-20', 'juan.torres@ejemplo.com');
SET @c4 = LAST_INSERT_ID();

-- ---------- Mascotas ----------
INSERT INTO MASCOTA (ID_Cliente, NombreMascota, Especie, Raza, FechaNacimiento, Tamano, Peso, Genero)
VALUES (@c1, 'Max', 'Perro', 'Labrador', '2020-03-15', 'Grande', 28.50, 'Macho');
SET @m_max = LAST_INSERT_ID();
INSERT INTO MASCOTA (ID_Cliente, NombreMascota, Especie, Raza, FechaNacimiento, Tamano, Peso, Genero)
VALUES (@c1, 'Luna', 'Gato', 'Siamés', '2021-07-02', 'Pequeño', 4.20, 'Hembra');
SET @m_luna = LAST_INSERT_ID();
INSERT INTO MASCOTA (ID_Cliente, NombreMascota, Especie, Raza, FechaNacimiento, Tamano, Peso, Genero)
VALUES (@c2, 'Rocky', 'Perro', 'Bulldog Francés', '2019-11-20', 'Mediano', 12.80, 'Macho');
SET @m_rocky = LAST_INSERT_ID();
INSERT INTO MASCOTA (ID_Cliente, NombreMascota, Especie, Raza, FechaNacimiento, Tamano, Peso, Genero)
VALUES (@c3, 'Mía', 'Gato', 'Persa', '2022-01-10', 'Pequeño', 3.90, 'Hembra');
SET @m_mia = LAST_INSERT_ID();
INSERT INTO MASCOTA (ID_Cliente, NombreMascota, Especie, Raza, FechaNacimiento, Tamano, Peso, Genero)
VALUES (@c3, 'Toby', 'Perro', 'Golden Retriever', '2018-05-25', 'Grande', 32.00, 'Macho');
SET @m_toby = LAST_INSERT_ID();
INSERT INTO MASCOTA (ID_Cliente, NombreMascota, Especie, Raza, FechaNacimiento, Tamano, Peso, Genero)
VALUES (@c4, 'Nala', 'Perro', 'Beagle', '2023-02-14', 'Mediano', 9.60, 'Hembra');
SET @m_nala = LAST_INSERT_ID();

-- ---------- Citas de tu veterinario: pasadas ----------
INSERT INTO RESERVAS (ID_Empleado, ID_Mascota, ID_CataServicio, FechaReserva, HoraReserva, EstadoCita)
VALUES (@vet, @m_max, @s_consulta, DATE_SUB(CURDATE(), INTERVAL 30 DAY), '09:00:00', 'Completada');
SET @r1 = LAST_INSERT_ID();
INSERT INTO RESERVAS (ID_Empleado, ID_Mascota, ID_CataServicio, FechaReserva, HoraReserva, EstadoCita)
VALUES (@vet, @m_luna, @s_vacuna, DATE_SUB(CURDATE(), INTERVAL 21 DAY), '10:30:00', 'Completada');
SET @r2 = LAST_INSERT_ID();
INSERT INTO RESERVAS (ID_Empleado, ID_Mascota, ID_CataServicio, FechaReserva, HoraReserva, EstadoCita)
VALUES (@vet, @m_rocky, @s_despar, DATE_SUB(CURDATE(), INTERVAL 14 DAY), '15:00:00', 'Completada');
SET @r3 = LAST_INSERT_ID();
INSERT INTO RESERVAS (ID_Empleado, ID_Mascota, ID_CataServicio, FechaReserva, HoraReserva, EstadoCita)
VALUES (@vet, @m_toby, @s_consulta, DATE_SUB(CURDATE(), INTERVAL 10 DAY), '11:00:00', 'Completada');
SET @r4 = LAST_INSERT_ID();
INSERT INTO RESERVAS (ID_Empleado, ID_Mascota, ID_CataServicio, FechaReserva, HoraReserva, EstadoCita)
VALUES (@vet, @m_mia, @s_bano, DATE_SUB(CURDATE(), INTERVAL 7 DAY), '14:30:00', 'Completada');
INSERT INTO RESERVAS (ID_Empleado, ID_Mascota, ID_CataServicio, FechaReserva, HoraReserva, EstadoCita)
VALUES (@vet, @m_rocky, @s_consulta, DATE_SUB(CURDATE(), INTERVAL 5 DAY), '16:00:00', 'Cancelada');
INSERT INTO RESERVAS (ID_Empleado, ID_Mascota, ID_CataServicio, FechaReserva, HoraReserva, EstadoCita)
VALUES (@vet, @m_nala, @s_vacuna, DATE_SUB(CURDATE(), INTERVAL 3 DAY), '09:30:00', 'Completada');
SET @r6 = LAST_INSERT_ID();

-- ---------- Citas de tu veterinario: próximas ----------
INSERT INTO RESERVAS (ID_Empleado, ID_Mascota, ID_CataServicio, FechaReserva, HoraReserva, EstadoCita) VALUES
(@vet, @m_max,  @s_vacuna,   DATE_ADD(CURDATE(), INTERVAL 1 DAY), '09:00:00', 'Agendada'),
(@vet, @m_mia,  @s_consulta, DATE_ADD(CURDATE(), INTERVAL 2 DAY), '10:00:00', 'Agendada'),
(@vet, @m_toby, @s_cirugia,  DATE_ADD(CURDATE(), INTERVAL 4 DAY), '08:30:00', 'Agendada'),
(@vet, @m_nala, @s_consulta, DATE_ADD(CURDATE(), INTERVAL 6 DAY), '11:30:00', 'Agendada');

-- ---------- Citas antiguas con la Dra. Laura (para ver más historial) ----------
INSERT INTO RESERVAS (ID_Empleado, ID_Mascota, ID_CataServicio, FechaReserva, HoraReserva, EstadoCita)
VALUES (@laura, @m_max, @s_consulta, DATE_SUB(CURDATE(), INTERVAL 90 DAY), '10:00:00', 'Completada');
SET @r12 = LAST_INSERT_ID();
INSERT INTO RESERVAS (ID_Empleado, ID_Mascota, ID_CataServicio, FechaReserva, HoraReserva, EstadoCita)
VALUES (@laura, @m_rocky, @s_vacuna, DATE_SUB(CURDATE(), INTERVAL 60 DAY), '09:00:00', 'Completada');
SET @r13 = LAST_INSERT_ID();

-- ---------- Historial clínico ----------
INSERT INTO HISTORIAL_CLINICO (ID_Empleado, ID_Mascota, ID_Reserva, FechaHora, Diagnostico, Tratamiento) VALUES
(@vet,   @m_max,   @r1,  TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 30 DAY), '09:00:00'), 'Control anual: buen estado general', 'Alimentación balanceada y nuevo control en 12 meses'),
(@vet,   @m_luna,  @r2,  TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 21 DAY), '10:30:00'), 'Vacunación al día', 'Refuerzo de triple felina; próxima dosis en 1 año'),
(@vet,   @m_rocky, @r3,  TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 14 DAY), '15:00:00'), 'Parásitos intestinales leves', 'Desparasitante oral; repetir dosis en 15 días'),
(@vet,   @m_toby,  @r4,  TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 10 DAY), '11:00:00'), 'Dermatitis alérgica leve', 'Champú medicado y antihistamínico por 7 días'),
(@vet,   @m_nala,  @r6,  TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 3 DAY),  '09:30:00'), 'Vacuna antirrábica aplicada', 'Observación 24 horas; sin reacciones adversas'),
(@laura, @m_max,   @r12, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 90 DAY), '10:00:00'), 'Otitis externa leve', 'Gotas óticas cada 12 horas durante 7 días'),
(@laura, @m_rocky, @r13, TIMESTAMP(DATE_SUB(CURDATE(), INTERVAL 60 DAY), '09:00:00'), 'Vacunación antirrábica', 'Dosis aplicada; refuerzo anual');