-- =====================================================
-- Datos de ejemplo (los mismos que tenía la lista en memoria de app.py)
-- Ejecutar después de migracion_app.sql, solo si las tablas están vacías
-- =====================================================
USE veterinaria;

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
