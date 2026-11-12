-- =====================================================================
-- PawCare / VeteNtd - TODOS LOS INSERTS de la base "veterinaria"
--
-- Ejecutar DESPUES de veterinaria_estructura_completa.sql, con las tablas vacias.
-- Usa ID explicitos, asi que no se puede ejecutar dos veces seguidas
-- (la segunda vez falla por llaves duplicadas). Para repetirlo, vuelve a importar
-- primero la estructura, que reinicia las tablas.
--
-- Como usarlo:  phpMyAdmin -> pestana "Importar" -> elegir este archivo -> "Importar".
--
-- Contenido:
--   1. Servicios del catalogo (5)           5. Mascotas de ejemplo (6)
--   2. Productos de la tienda (5)           6. Citas / reservas de ejemplo (13)
--   3. Veterinarios + acceso + horarios     7. Historial clinico de ejemplo (7)
--   4. Clientes de ejemplo (4)
--
-- Acceso de los veterinarios (contrasenas de DEMOSTRACION, cambialas antes de publicar):
--   laura@pawcare.com   -> Laura#Vet2026
--   andres@pawcare.com  -> Andres#Vet2026
--   camila@pawcare.com  -> Camila#Vet2026
-- Los clientes de ejemplo no tienen contrasena (sirven para que el veterinario vea datos).
-- Las fechas de las citas se calculan respecto a la fecha en que importes el archivo.
-- =====================================================================

SET NAMES utf8mb4;
USE veterinaria;

-- ---------------------------------------------------------------------
-- 1. Servicios del catalogo
-- ---------------------------------------------------------------------
INSERT INTO CATALOGO_SERVICIOS (ID_CataServicio, Servicio, Descripcion, DuracionServicio, CostoServicio, Icono, Cupos) VALUES
(1, 'Consulta General Veterinaria',      'Revisión médica completa a cargo de un veterinario certificado.',          30,  80000, '🩺', 12),
(2, 'Vacuna Antirrábica',                'Aplicación de vacuna antirrábica para perros y gatos.',                    15,  60000, '💉', 25),
(3, 'Baño y Peluquería Canina',          'Baño medicado, corte de pelo y limpieza de oídos.',                        60,  55000, '🛁', 10),
(4, 'Desparasitación Interna y Externa', 'Tratamiento antiparasitario para perros y gatos de cualquier edad.',       20,  45000, '💊', 20),
(5, 'Cirugía Menor (Esterilización)',    'Procedimiento quirúrgico ambulatorio con seguimiento post-operatorio.',   120, 250000, '🏥',  4);

-- ---------------------------------------------------------------------
-- 2. Productos de la tienda
-- ---------------------------------------------------------------------
INSERT INTO PRODUCTOS (ID_Producto, TipoProducto, Descripcion, ValorProducto, Icono, Stock) VALUES
(1, 'Alimento Premium para Perros 15kg',      'Nutrición balanceada para perros adultos de todas las razas.',           189900, '🐶', 14),
(2, 'Alimento Premium para Gatos 10kg',       'Fórmula especial para el cuidado renal y urinario felino.',              159900, '🐱', 16),
(3, 'Kit de Primeros Auxilios para Mascotas', 'Vendas, antisépticos y elementos básicos para emergencias.',              69900, '🩹', 18),
(4, 'Transportadora para Mascotas',           'Resistente y ventilada, ideal para viajes y visitas al veterinario.',    129900, '🧳',  9),
(5, 'Juguete Interactivo para Mascotas',      'Estimula la mente de tu mascota y reduce la ansiedad.',                   34900, '🎾', 30);

-- ---------------------------------------------------------------------
-- 3. Veterinarios (con correo y contrasena hasheada) y horarios de atencion
-- ---------------------------------------------------------------------
INSERT INTO EMPLEADO (ID_Empleado, NombreEmpleado, ContactoEmpleado, CargoEmpleado, CorreoEmpleado, ClaveHash) VALUES
(1, 'Dra. Laura Gómez',   '3001112233', 'Veterinaria', 'laura@pawcare.com',  'scrypt:32768:8:1$XN80g7k5nSEKHrEg$0c1e4ae4f3dd3d5a91b2dcd2296fc2d61cd0da80eef32bc0194b7571cd667710a231350638c1cd5469ed71eb75d9f6011a81deec34f943c52a2e1eb8a8914d8c'),
(2, 'Dr. Andrés Ramírez', '3004445566', 'Veterinario', 'andres@pawcare.com', 'scrypt:32768:8:1$EShNjQelcftgfiRn$007958eaad0fdeddd9dcec77aaa323f14af9dd8b8405cea47de4c4e3f605e3a58c8ccee39df5f5a9bce6ac69457af0231fd921c6e76af95daab9714fd2a5b38b'),
(3, 'Dra. Camila Torres', '3007778899', 'Veterinaria', 'camila@pawcare.com', 'scrypt:32768:8:1$VBKTidvPBkf6CDwM$2b29272a3da836b48a0a2064395e63c87b7253e31e87469e170c7a1e29dbdbaa6fa9f68e7c5771de0cd21afb9851424b071c72494b73bccfe9f6a741416fa657');

-- Laura: lunes a viernes 8-12 y 14-18 | Andres: lun, mie, vie y sab 9-13 | Camila: mar, jue y sab 10-13 y 15-19
INSERT INTO HORARIO (ID_Empleado, DiaSemana, HoraInicio, HoraFin) VALUES
(1, 'Lunes',     '08:00:00', '12:00:00'), (1, 'Lunes',     '14:00:00', '18:00:00'),
(1, 'Martes',    '08:00:00', '12:00:00'), (1, 'Martes',    '14:00:00', '18:00:00'),
(1, 'Miércoles', '08:00:00', '12:00:00'), (1, 'Miércoles', '14:00:00', '18:00:00'),
(1, 'Jueves',    '08:00:00', '12:00:00'), (1, 'Jueves',    '14:00:00', '18:00:00'),
(1, 'Viernes',   '08:00:00', '12:00:00'), (1, 'Viernes',   '14:00:00', '18:00:00'),
(2, 'Lunes',     '09:00:00', '13:00:00'),
(2, 'Miércoles', '09:00:00', '13:00:00'),
(2, 'Viernes',   '09:00:00', '13:00:00'),
(2, 'Sábado',    '09:00:00', '13:00:00'),
(3, 'Martes',    '10:00:00', '13:00:00'), (3, 'Martes',    '15:00:00', '19:00:00'),
(3, 'Jueves',    '10:00:00', '13:00:00'), (3, 'Jueves',    '15:00:00', '19:00:00'),
(3, 'Sábado',    '10:00:00', '13:00:00'), (3, 'Sábado',    '15:00:00', '19:00:00');

-- ---------------------------------------------------------------------
-- 4. Clientes de ejemplo
-- ---------------------------------------------------------------------
INSERT INTO CLIENTE (ID_Cliente, NombreCliente, ContactoCliente, DireccionCliente, CorreoCliente) VALUES
(1, 'María Fernanda Rojas', '3101234567', 'Calle 45 #12-30',   'maria.rojas@ejemplo.com'),
(2, 'Carlos Andrés Pérez',  '3157654321', 'Carrera 7 #80-15',  'carlos.perez@ejemplo.com'),
(3, 'Laura Sofía Martínez', '3209876543', 'Avenida 68 #24-10', 'laura.martinez@ejemplo.com'),
(4, 'Juan David Torres',    '3012345678', 'Calle 100 #15-20',  'juan.torres@ejemplo.com');

-- ---------------------------------------------------------------------
-- 5. Mascotas de ejemplo
-- ---------------------------------------------------------------------
INSERT INTO MASCOTA (ID_Mascota, ID_Cliente, NombreMascota, Especie, Raza, FechaNacimiento, Tamano, Peso, Genero) VALUES
(1, 1, 'Max',   'Perro', 'Labrador',        '2020-03-15', 'Grande',  28.50, 'Macho'),
(2, 1, 'Luna',  'Gato',  'Siamés',          '2021-07-02', 'Pequeño',  4.20, 'Hembra'),
(3, 2, 'Rocky', 'Perro', 'Bulldog Francés', '2019-11-20', 'Mediano', 12.80, 'Macho'),
(4, 3, 'Mía',   'Gato',  'Persa',           '2022-01-10', 'Pequeño',  3.90, 'Hembra'),
(5, 3, 'Toby',  'Perro', 'Golden Retriever','2018-05-25', 'Grande',  32.00, 'Macho'),
(6, 4, 'Nala',  'Perro', 'Beagle',          '2023-02-14', 'Mediano',  9.60, 'Hembra');

-- ---------------------------------------------------------------------
-- 6. Citas / reservas de ejemplo
-- dow = dia de la semana (0=lunes ... 6=domingo); semanas: negativo = pasado, positivo = futuro.
-- La fecha cae siempre en un dia en que ese veterinario atiende.
-- ---------------------------------------------------------------------
INSERT INTO RESERVAS (ID_Reserva, ID_Empleado, ID_Mascota, ID_CataServicio, FechaReserva, HoraReserva, EstadoCita)
SELECT t.id, t.eid, t.mid, t.sid,
       CASE WHEN t.semanas > 0
            THEN DATE_ADD(CURDATE(), INTERVAL ((t.dow - WEEKDAY(CURDATE()) + 6) % 7 + 1 + 7 * (t.semanas - 1)) DAY)
            ELSE DATE_SUB(CURDATE(), INTERVAL ((WEEKDAY(CURDATE()) - t.dow + 6) % 7 + 1 + 7 * (-t.semanas - 1)) DAY)
       END,
       t.hora, t.estado
FROM (
    --            id  eid mid sid dow semanas hora        estado
    SELECT  1 AS id, 1 AS eid, 1 AS mid, 1 AS sid, 0 AS dow,  -4 AS semanas, '09:00:00' AS hora, 'Completada' AS estado  -- Laura  | Max   | Consulta
    UNION ALL SELECT  2, 1, 2, 2, 2,  -3, '10:30:00', 'Completada'   -- Laura  | Luna  | Vacuna
    UNION ALL SELECT  3, 2, 3, 4, 4,  -2, '09:00:00', 'Completada'   -- Andres | Rocky | Desparasitacion
    UNION ALL SELECT  4, 3, 5, 1, 1,  -2, '11:00:00', 'Completada'   -- Camila | Toby  | Consulta
    UNION ALL SELECT  5, 3, 4, 3, 3,  -1, '10:00:00', 'Completada'   -- Camila | Mia   | Bano (sin historial)
    UNION ALL SELECT  6, 2, 6, 2, 5,  -1, '09:30:00', 'Completada'   -- Andres | Nala  | Vacuna
    UNION ALL SELECT  7, 1, 1, 1, 4,  -9, '14:00:00', 'Completada'   -- Laura  | Max   | Consulta
    UNION ALL SELECT  8, 1, 3, 2, 1,  -8, '09:00:00', 'Completada'   -- Laura  | Rocky | Vacuna
    UNION ALL SELECT  9, 1, 3, 1, 3,  -1, '16:00:00', 'Cancelada'    -- Laura  | Rocky | Consulta
    UNION ALL SELECT 10, 1, 1, 2, 0,   1, '09:00:00', 'Agendada'     -- Laura  | Max   | Vacuna
    UNION ALL SELECT 11, 2, 4, 1, 2,   1, '10:00:00', 'Agendada'     -- Andres | Mia   | Consulta
    UNION ALL SELECT 12, 3, 5, 5, 1,   1, '10:00:00', 'Agendada'     -- Camila | Toby  | Cirugia
    UNION ALL SELECT 13, 2, 6, 1, 4,   1, '11:30:00', 'Agendada'     -- Andres | Nala  | Consulta
) t;

-- ---------------------------------------------------------------------
-- 7. Historial clinico de las citas completadas (una entrada por cita)
-- ---------------------------------------------------------------------
INSERT INTO HISTORIAL_CLINICO (ID_Empleado, ID_Mascota, ID_Reserva, FechaHora, Diagnostico, Tratamiento)
SELECT r.ID_Empleado, r.ID_Mascota, r.ID_Reserva, TIMESTAMP(r.FechaReserva, r.HoraReserva), d.diagnostico, d.tratamiento
FROM RESERVAS r
JOIN (
    SELECT 1 AS rid, 'Control anual: buen estado general' AS diagnostico, 'Alimentación balanceada y nuevo control en 12 meses' AS tratamiento
    UNION ALL SELECT 2, 'Vacunación al día',                    'Refuerzo de triple felina; próxima dosis en 1 año'
    UNION ALL SELECT 3, 'Parásitos intestinales leves',         'Desparasitante oral; repetir dosis en 15 días'
    UNION ALL SELECT 4, 'Dermatitis alérgica leve',             'Champú medicado y antihistamínico por 7 días'
    UNION ALL SELECT 6, 'Vacuna antirrábica aplicada',          'Observación 24 horas; sin reacciones adversas'
    UNION ALL SELECT 7, 'Otitis externa leve',                  'Gotas óticas cada 12 horas durante 7 días'
    UNION ALL SELECT 8, 'Vacunación antirrábica',               'Dosis aplicada; refuerzo anual'
) d ON d.rid = r.ID_Reserva
ORDER BY r.ID_Reserva;