-- =====================================================
-- Portal de clientes: ajustes de tablas, tabla USUARIOS + veterinarios y horarios de ejemplo
-- Ejecutar UNA sola vez, después de schema.sql
-- =====================================================
USE veterinaria;

-- Los campos de 30 caracteres no alcanzan para nombres, correos ni direcciones reales.
-- ClaveHash guarda la contraseña cifrada (nunca en texto plano).
ALTER TABLE CLIENTE
    MODIFY NombreCliente    VARCHAR(100) NOT NULL,
    MODIFY DireccionCliente VARCHAR(100) NOT NULL,
    MODIFY CorreoCliente    VARCHAR(100) NULL,
    ADD COLUMN ClaveHash    VARCHAR(255) NULL,
    ADD UNIQUE KEY uq_cliente_correo (CorreoCliente);

ALTER TABLE MASCOTA  MODIFY Raza          VARCHAR(50) NOT NULL;
ALTER TABLE EMPLEADO MODIFY CargoEmpleado VARCHAR(30) NOT NULL;

-- USUARIOS: guarda a cada persona que se registra en el portal.
-- Se recrea porque la versión de schema.sql exigía empleado, reserva y motivo en cada fila.
DROP TABLE IF EXISTS USUARIOS;

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
);

-- Pasa a USUARIOS los clientes que ya tenían cuenta
INSERT INTO USUARIOS (ID_Cliente, Nombre, Correo, ClaveHash, Rol)
SELECT ID_Cliente, NombreCliente, CorreoCliente, ClaveHash, 'Cliente'
FROM CLIENTE
WHERE ClaveHash IS NOT NULL AND CorreoCliente IS NOT NULL;

-- Veterinarios (el portal lista a los empleados cuyo cargo empieza por "Veterinari")
INSERT INTO EMPLEADO (NombreEmpleado, ContactoEmpleado, CargoEmpleado) VALUES
('Dra. Laura Gómez',   '3001112233', 'Veterinaria'),
('Dr. Andrés Ramírez', '3004445566', 'Veterinario'),
('Dra. Camila Torres', '3007778899', 'Veterinaria');

-- Horarios de atención (puedes poner varios bloques el mismo día, por ejemplo mañana y tarde)
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