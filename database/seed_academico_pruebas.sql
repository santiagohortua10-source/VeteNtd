-- PawCare | Fixtures acad?micos ficticios para una COPIA AISLADA de ahp_veterinaria.
-- ADVERTENCIA: agrega filas permanentes. No ejecutar en la base original.
-- No borra ni modifica filas existentes. Identidades reservadas bajo example.invalid.
-- Repetible: cada fila verifica una clave natural de fixture antes de insertar.
-- Los registros USUARIOS tienen hash v?lido de una clave aleatoria descartada; no sirven para iniciar sesi?n.
-- Ejecute en una sesi?n MySQL dedicada; la tabla temporal desaparece al cerrar la conexi?n.
USE ahp_veterinaria;
SET NAMES utf8mb4;
SET @usuario_auditoria = 'SEED_PRUEBAS';
CREATE TEMPORARY TABLE IF NOT EXISTS pawcare_academic_fixture_ids (n INT NOT NULL PRIMARY KEY);
INSERT IGNORE INTO pawcare_academic_fixture_ids (n) VALUES (1),(2),(3),(4),(5),(6),(7),(8),(9),(10),(11);
START TRANSACTION;

INSERT INTO CLIENTE (NombreCliente,ContactoCliente,DireccionCliente,CorreoCliente,ClaveHash)
SELECT CONCAT('PawCare Prueba ',LPAD(i.n,2,'0')), CONCAT('300900',LPAD(i.n,4,'0')), CONCAT('Direcci?n prueba ',i.n), CONCAT('cliente',LPAD(i.n,2,'0'),'@pawcare.example.invalid'), NULL
FROM pawcare_academic_fixture_ids i
WHERE NOT EXISTS (SELECT 1 FROM CLIENTE c WHERE c.CorreoCliente=CONCAT('cliente',LPAD(i.n,2,'0'),'@pawcare.example.invalid'));

INSERT INTO EMPLEADO (NombreEmpleado,ContactoEmpleado,CargoEmpleado,CorreoEmpleado,ClaveHash)
SELECT CONCAT('Veterinario Prueba ',LPAD(i.n,2,'0')), CONCAT('301900',LPAD(i.n,4,'0')), 'Veterinario', CONCAT('vet',LPAD(i.n,2,'0'),'@pawcare.example.invalid'), NULL
FROM pawcare_academic_fixture_ids i
WHERE NOT EXISTS (SELECT 1 FROM EMPLEADO e WHERE e.CorreoEmpleado=CONCAT('vet',LPAD(i.n,2,'0'),'@pawcare.example.invalid'));

INSERT INTO CATALOGO_SERVICIOS (Servicio,Descripcion,DuracionServicio,CostoServicio,Icono,Cupos)
SELECT CONCAT('PawCare prueba servicio ',LPAD(i.n,2,'0')), 'Registro ficticio para copia acad?mica de pruebas.', 30, 50000+i.n, '??', 10
FROM pawcare_academic_fixture_ids i
WHERE NOT EXISTS (SELECT 1 FROM CATALOGO_SERVICIOS s WHERE s.Servicio=CONCAT('PawCare prueba servicio ',LPAD(i.n,2,'0')));

INSERT INTO PRODUCTOS (TipoProducto,Descripcion,ValorProducto,Icono,Stock)
SELECT CONCAT('PawCare prueba producto ',LPAD(i.n,2,'0')), 'Registro ficticio para copia acad?mica de pruebas.', 10000+i.n, '??', 20
FROM pawcare_academic_fixture_ids i
WHERE NOT EXISTS (SELECT 1 FROM PRODUCTOS p WHERE p.TipoProducto=CONCAT('PawCare prueba producto ',LPAD(i.n,2,'0')));

INSERT INTO USUARIOS (ID_Cliente,ID_Empleado,Nombre,Correo,ClaveHash,Rol)
SELECT c.ID_Cliente,NULL,c.NombreCliente,c.CorreoCliente,'__HASH_USUARIO_TEST__','Cliente'
FROM CLIENTE c WHERE c.CorreoCliente LIKE 'cliente%@pawcare.example.invalid'
AND NOT EXISTS (SELECT 1 FROM USUARIOS u WHERE u.Correo=c.CorreoCliente);

INSERT INTO MASCOTA (ID_Cliente,NombreMascota,Especie,Raza,FechaNacimiento,Tamano,Peso,Genero)
SELECT c.ID_Cliente,CONCAT('Mascota prueba ',LPAD(i.n,2,'0')),'Perro','Ficticia','2020-01-01','Mediano',10.00,'No especificado'
FROM pawcare_academic_fixture_ids i JOIN CLIENTE c ON c.CorreoCliente=CONCAT('cliente',LPAD(i.n,2,'0'),'@pawcare.example.invalid')
WHERE NOT EXISTS (SELECT 1 FROM MASCOTA m WHERE m.ID_Cliente=c.ID_Cliente AND m.NombreMascota=CONCAT('Mascota prueba ',LPAD(i.n,2,'0')));

INSERT INTO HORARIO (ID_Empleado,DiaSemana,HoraInicio,HoraFin)
SELECT e.ID_Empleado,'Martes','08:00:00','17:00:00'
FROM pawcare_academic_fixture_ids i JOIN EMPLEADO e ON e.CorreoEmpleado=CONCAT('vet',LPAD(i.n,2,'0'),'@pawcare.example.invalid')
WHERE NOT EXISTS (SELECT 1 FROM HORARIO h WHERE h.ID_Empleado=e.ID_Empleado AND h.DiaSemana='Martes' AND h.HoraInicio='08:00:00' AND h.HoraFin='17:00:00');

INSERT INTO RESERVAS (ID_Empleado,ID_Mascota,ID_CataServicio,FechaReserva,HoraReserva,EstadoCita)
SELECT e.ID_Empleado,m.ID_Mascota,s.ID_CataServicio,DATE_ADD('2035-01-01',INTERVAL i.n DAY),'09:00:00','Completada'
FROM pawcare_academic_fixture_ids i
JOIN EMPLEADO e ON e.CorreoEmpleado=CONCAT('vet',LPAD(i.n,2,'0'),'@pawcare.example.invalid')
JOIN CLIENTE c ON c.CorreoCliente=CONCAT('cliente',LPAD(i.n,2,'0'),'@pawcare.example.invalid')
JOIN MASCOTA m ON m.ID_Cliente=c.ID_Cliente AND m.NombreMascota=CONCAT('Mascota prueba ',LPAD(i.n,2,'0'))
JOIN CATALOGO_SERVICIOS s ON s.Servicio=CONCAT('PawCare prueba servicio ',LPAD(i.n,2,'0'))
WHERE NOT EXISTS (SELECT 1 FROM RESERVAS r WHERE r.ID_Empleado=e.ID_Empleado AND r.ID_Mascota=m.ID_Mascota AND r.ID_CataServicio=s.ID_CataServicio AND r.FechaReserva=DATE_ADD('2035-01-01',INTERVAL i.n DAY) AND r.HoraReserva='09:00:00');

INSERT INTO HISTORIAL_CLINICO (ID_Empleado,ID_Mascota,ID_Reserva,FechaHora,Diagnostico,Tratamiento)
SELECT r.ID_Empleado,r.ID_Mascota,r.ID_Reserva,TIMESTAMP(r.FechaReserva,r.HoraReserva),'Registro ficticio de prueba.','Seguimiento ficticio de prueba.'
FROM RESERVAS r JOIN MASCOTA m ON m.ID_Mascota=r.ID_Mascota JOIN CLIENTE c ON c.ID_Cliente=m.ID_Cliente
WHERE c.CorreoCliente LIKE 'cliente%@pawcare.example.invalid'
AND NOT EXISTS (SELECT 1 FROM HISTORIAL_CLINICO h WHERE h.ID_Reserva=r.ID_Reserva);

INSERT INTO FACTURACION (ID_Cliente,FECHA,ImpuestosIVA,TotalPagar)
SELECT c.ID_Cliente,DATE_ADD('2035-02-01',INTERVAL i.n DAY),ROUND((50000+i.n)-(50000+i.n)/1.19,2),50000+i.n
FROM pawcare_academic_fixture_ids i JOIN CLIENTE c ON c.CorreoCliente=CONCAT('cliente',LPAD(i.n,2,'0'),'@pawcare.example.invalid')
WHERE NOT EXISTS (SELECT 1 FROM FACTURACION f WHERE f.ID_Cliente=c.ID_Cliente AND f.FECHA=DATE_ADD('2035-02-01',INTERVAL i.n DAY));

INSERT INTO DETALLE_FACTURA (ID_Producto,ID_Facturacion,ID_Servicio,Cantidad,PrecioUnitario)
SELECT NULL,f.ID_Facturacion,s.ID_CataServicio,1,50000+i.n
FROM pawcare_academic_fixture_ids i
JOIN CLIENTE c ON c.CorreoCliente=CONCAT('cliente',LPAD(i.n,2,'0'),'@pawcare.example.invalid')
JOIN FACTURACION f ON f.ID_Cliente=c.ID_Cliente AND f.FECHA=DATE_ADD('2035-02-01',INTERVAL i.n DAY)
JOIN CATALOGO_SERVICIOS s ON s.Servicio=CONCAT('PawCare prueba servicio ',LPAD(i.n,2,'0'))
WHERE NOT EXISTS (SELECT 1 FROM DETALLE_FACTURA d WHERE d.ID_Facturacion=f.ID_Facturacion AND d.ID_Servicio=s.ID_CataServicio);

INSERT INTO PAGO (ID_Facturacion,MetodoPago,ValorRecibido,CambioValorRecibido,ComprobantePago,FechaPago)
SELECT f.ID_Facturacion,'Efectivo',f.TotalPagar,0,CONCAT('TEST-P',LPAD(i.n,2,'0')),f.FECHA
FROM pawcare_academic_fixture_ids i JOIN CLIENTE c ON c.CorreoCliente=CONCAT('cliente',LPAD(i.n,2,'0'),'@pawcare.example.invalid')
JOIN FACTURACION f ON f.ID_Cliente=c.ID_Cliente AND f.FECHA=DATE_ADD('2035-02-01',INTERVAL i.n DAY)
WHERE NOT EXISTS (SELECT 1 FROM PAGO p WHERE p.ID_Facturacion=f.ID_Facturacion);

INSERT INTO PEDIDOS (ID_Cliente,Fecha,Total,Estado)
SELECT c.ID_Cliente,DATE_ADD('2035-03-01',INTERVAL i.n DAY),(10000+i.n),'Confirmado'
FROM pawcare_academic_fixture_ids i JOIN CLIENTE c ON c.CorreoCliente=CONCAT('cliente',LPAD(i.n,2,'0'),'@pawcare.example.invalid')
WHERE NOT EXISTS (SELECT 1 FROM PEDIDOS p WHERE p.ID_Cliente=c.ID_Cliente AND p.Fecha=DATE_ADD('2035-03-01',INTERVAL i.n DAY));

INSERT INTO PEDIDO_DETALLE (ID_Pedido,ID_Producto,Cantidad,PrecioUnitario)
SELECT p.ID_Pedido,pr.ID_Producto,1,10000+i.n
FROM pawcare_academic_fixture_ids i
JOIN CLIENTE c ON c.CorreoCliente=CONCAT('cliente',LPAD(i.n,2,'0'),'@pawcare.example.invalid')
JOIN PEDIDOS p ON p.ID_Cliente=c.ID_Cliente AND p.Fecha=DATE_ADD('2035-03-01',INTERVAL i.n DAY)
JOIN PRODUCTOS pr ON pr.TipoProducto=CONCAT('PawCare prueba producto ',LPAD(i.n,2,'0'))
WHERE NOT EXISTS (SELECT 1 FROM PEDIDO_DETALLE d WHERE d.ID_Pedido=p.ID_Pedido AND d.ID_Producto=pr.ID_Producto);

INSERT INTO RESPONSABLE_ALTERNO (ID_Mascota,Nombre,Documento,Telefono,Relacion,AutorizacionDeRetiro)
SELECT m.ID_Mascota,CONCAT('Responsable prueba ',LPAD(i.n,2,'0')),CONCAT('PAWTEST-DOC-',LPAD(i.n,2,'0')),CONCAT('302900',LPAD(i.n,4,'0')),'Prueba',0
FROM pawcare_academic_fixture_ids i
JOIN CLIENTE c ON c.CorreoCliente=CONCAT('cliente',LPAD(i.n,2,'0'),'@pawcare.example.invalid')
JOIN MASCOTA m ON m.ID_Cliente=c.ID_Cliente AND m.NombreMascota=CONCAT('Mascota prueba ',LPAD(i.n,2,'0'))
WHERE NOT EXISTS (SELECT 1 FROM RESPONSABLE_ALTERNO r WHERE r.Documento=CONCAT('PAWTEST-DOC-',LPAD(i.n,2,'0')));

COMMIT;
-- Cierra la conexi?n para limpiar la tabla temporal de identificadores.
