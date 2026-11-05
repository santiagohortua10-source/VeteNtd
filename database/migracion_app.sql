-- =====================================================
-- Portal de clientes: ajustes de tablas + veterinarios y horarios de ejemplo
-- Ejecutar UNA sola vez, después de schema.sql y migracion_app.sql
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