-- PawCare | 45 triggers AFTER (INSERT/UPDATE/DELETE) para las 15 tablas de ahp_veterinaria.
-- Incluye 2 triggers BEFORE auxiliares para registrar cascadas ON DELETE de USUARIOS.
-- No ejecutar sobre una base con datos reales sin respaldo y validaci?n previa en copia.
-- No contiene DROP. Cada nombre de trigger debe estar libre antes de instalar.
-- La identidad llega por @usuario_auditoria; si se ejecuta fuera de Flask queda SISTEMA.
-- Se excluyen ClaveHash y Clave de los JSON de auditor?a.
USE ahp_veterinaria;

DELIMITER $$
CREATE TRIGGER `aud_catalogo_servicios_insert` AFTER INSERT ON `catalogo_servicios` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'INSERT', 'catalogo_servicios', CAST(NEW.`ID_CataServicio` AS CHAR), NULL, JSON_OBJECT('ID_CataServicio', NEW.`ID_CataServicio`, 'Servicio', NEW.`Servicio`, 'Descripcion', NEW.`Descripcion`, 'DuracionServicio', NEW.`DuracionServicio`, 'CostoServicio', NEW.`CostoServicio`, 'Icono', NEW.`Icono`, 'Cupos', NEW.`Cupos`));
END$$

CREATE TRIGGER `aud_catalogo_servicios_update` AFTER UPDATE ON `catalogo_servicios` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'UPDATE', 'catalogo_servicios', CAST(NEW.`ID_CataServicio` AS CHAR), JSON_OBJECT('ID_CataServicio', OLD.`ID_CataServicio`, 'Servicio', OLD.`Servicio`, 'Descripcion', OLD.`Descripcion`, 'DuracionServicio', OLD.`DuracionServicio`, 'CostoServicio', OLD.`CostoServicio`, 'Icono', OLD.`Icono`, 'Cupos', OLD.`Cupos`), JSON_OBJECT('ID_CataServicio', NEW.`ID_CataServicio`, 'Servicio', NEW.`Servicio`, 'Descripcion', NEW.`Descripcion`, 'DuracionServicio', NEW.`DuracionServicio`, 'CostoServicio', NEW.`CostoServicio`, 'Icono', NEW.`Icono`, 'Cupos', NEW.`Cupos`));
END$$

CREATE TRIGGER `aud_catalogo_servicios_delete` AFTER DELETE ON `catalogo_servicios` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'DELETE', 'catalogo_servicios', CAST(OLD.`ID_CataServicio` AS CHAR), JSON_OBJECT('ID_CataServicio', OLD.`ID_CataServicio`, 'Servicio', OLD.`Servicio`, 'Descripcion', OLD.`Descripcion`, 'DuracionServicio', OLD.`DuracionServicio`, 'CostoServicio', OLD.`CostoServicio`, 'Icono', OLD.`Icono`, 'Cupos', OLD.`Cupos`), NULL);
END$$

CREATE TRIGGER `aud_cliente_insert` AFTER INSERT ON `cliente` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'INSERT', 'cliente', CAST(NEW.`ID_Cliente` AS CHAR), NULL, JSON_OBJECT('ID_Cliente', NEW.`ID_Cliente`, 'NombreCliente', NEW.`NombreCliente`, 'ContactoCliente', NEW.`ContactoCliente`, 'DireccionCliente', NEW.`DireccionCliente`, 'CorreoCliente', NEW.`CorreoCliente`));
END$$

CREATE TRIGGER `aud_cliente_update` AFTER UPDATE ON `cliente` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'UPDATE', 'cliente', CAST(NEW.`ID_Cliente` AS CHAR), JSON_OBJECT('ID_Cliente', OLD.`ID_Cliente`, 'NombreCliente', OLD.`NombreCliente`, 'ContactoCliente', OLD.`ContactoCliente`, 'DireccionCliente', OLD.`DireccionCliente`, 'CorreoCliente', OLD.`CorreoCliente`), JSON_OBJECT('ID_Cliente', NEW.`ID_Cliente`, 'NombreCliente', NEW.`NombreCliente`, 'ContactoCliente', NEW.`ContactoCliente`, 'DireccionCliente', NEW.`DireccionCliente`, 'CorreoCliente', NEW.`CorreoCliente`));
END$$

CREATE TRIGGER `aud_cliente_delete` AFTER DELETE ON `cliente` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'DELETE', 'cliente', CAST(OLD.`ID_Cliente` AS CHAR), JSON_OBJECT('ID_Cliente', OLD.`ID_Cliente`, 'NombreCliente', OLD.`NombreCliente`, 'ContactoCliente', OLD.`ContactoCliente`, 'DireccionCliente', OLD.`DireccionCliente`, 'CorreoCliente', OLD.`CorreoCliente`), NULL);
END$$

CREATE TRIGGER `aud_detalle_factura_insert` AFTER INSERT ON `detalle_factura` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'INSERT', 'detalle_factura', CAST(NEW.`ID_DetFactura` AS CHAR), NULL, JSON_OBJECT('ID_DetFactura', NEW.`ID_DetFactura`, 'ID_Producto', NEW.`ID_Producto`, 'ID_Facturacion', NEW.`ID_Facturacion`, 'ID_Servicio', NEW.`ID_Servicio`, 'Cantidad', NEW.`Cantidad`, 'PrecioUnitario', NEW.`PrecioUnitario`));
END$$

CREATE TRIGGER `aud_detalle_factura_update` AFTER UPDATE ON `detalle_factura` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'UPDATE', 'detalle_factura', CAST(NEW.`ID_DetFactura` AS CHAR), JSON_OBJECT('ID_DetFactura', OLD.`ID_DetFactura`, 'ID_Producto', OLD.`ID_Producto`, 'ID_Facturacion', OLD.`ID_Facturacion`, 'ID_Servicio', OLD.`ID_Servicio`, 'Cantidad', OLD.`Cantidad`, 'PrecioUnitario', OLD.`PrecioUnitario`), JSON_OBJECT('ID_DetFactura', NEW.`ID_DetFactura`, 'ID_Producto', NEW.`ID_Producto`, 'ID_Facturacion', NEW.`ID_Facturacion`, 'ID_Servicio', NEW.`ID_Servicio`, 'Cantidad', NEW.`Cantidad`, 'PrecioUnitario', NEW.`PrecioUnitario`));
END$$

CREATE TRIGGER `aud_detalle_factura_delete` AFTER DELETE ON `detalle_factura` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'DELETE', 'detalle_factura', CAST(OLD.`ID_DetFactura` AS CHAR), JSON_OBJECT('ID_DetFactura', OLD.`ID_DetFactura`, 'ID_Producto', OLD.`ID_Producto`, 'ID_Facturacion', OLD.`ID_Facturacion`, 'ID_Servicio', OLD.`ID_Servicio`, 'Cantidad', OLD.`Cantidad`, 'PrecioUnitario', OLD.`PrecioUnitario`), NULL);
END$$

CREATE TRIGGER `aud_empleado_insert` AFTER INSERT ON `empleado` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'INSERT', 'empleado', CAST(NEW.`ID_Empleado` AS CHAR), NULL, JSON_OBJECT('ID_Empleado', NEW.`ID_Empleado`, 'NombreEmpleado', NEW.`NombreEmpleado`, 'ContactoEmpleado', NEW.`ContactoEmpleado`, 'CargoEmpleado', NEW.`CargoEmpleado`, 'CorreoEmpleado', NEW.`CorreoEmpleado`));
END$$

CREATE TRIGGER `aud_empleado_update` AFTER UPDATE ON `empleado` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'UPDATE', 'empleado', CAST(NEW.`ID_Empleado` AS CHAR), JSON_OBJECT('ID_Empleado', OLD.`ID_Empleado`, 'NombreEmpleado', OLD.`NombreEmpleado`, 'ContactoEmpleado', OLD.`ContactoEmpleado`, 'CargoEmpleado', OLD.`CargoEmpleado`, 'CorreoEmpleado', OLD.`CorreoEmpleado`), JSON_OBJECT('ID_Empleado', NEW.`ID_Empleado`, 'NombreEmpleado', NEW.`NombreEmpleado`, 'ContactoEmpleado', NEW.`ContactoEmpleado`, 'CargoEmpleado', NEW.`CargoEmpleado`, 'CorreoEmpleado', NEW.`CorreoEmpleado`));
END$$

CREATE TRIGGER `aud_empleado_delete` AFTER DELETE ON `empleado` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'DELETE', 'empleado', CAST(OLD.`ID_Empleado` AS CHAR), JSON_OBJECT('ID_Empleado', OLD.`ID_Empleado`, 'NombreEmpleado', OLD.`NombreEmpleado`, 'ContactoEmpleado', OLD.`ContactoEmpleado`, 'CargoEmpleado', OLD.`CargoEmpleado`, 'CorreoEmpleado', OLD.`CorreoEmpleado`), NULL);
END$$

CREATE TRIGGER `aud_facturacion_insert` AFTER INSERT ON `facturacion` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'INSERT', 'facturacion', CAST(NEW.`ID_Facturacion` AS CHAR), NULL, JSON_OBJECT('ID_Facturacion', NEW.`ID_Facturacion`, 'ID_Cliente', NEW.`ID_Cliente`, 'FECHA', NEW.`FECHA`, 'ImpuestosIVA', NEW.`ImpuestosIVA`, 'TotalPagar', NEW.`TotalPagar`));
END$$

CREATE TRIGGER `aud_facturacion_update` AFTER UPDATE ON `facturacion` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'UPDATE', 'facturacion', CAST(NEW.`ID_Facturacion` AS CHAR), JSON_OBJECT('ID_Facturacion', OLD.`ID_Facturacion`, 'ID_Cliente', OLD.`ID_Cliente`, 'FECHA', OLD.`FECHA`, 'ImpuestosIVA', OLD.`ImpuestosIVA`, 'TotalPagar', OLD.`TotalPagar`), JSON_OBJECT('ID_Facturacion', NEW.`ID_Facturacion`, 'ID_Cliente', NEW.`ID_Cliente`, 'FECHA', NEW.`FECHA`, 'ImpuestosIVA', NEW.`ImpuestosIVA`, 'TotalPagar', NEW.`TotalPagar`));
END$$

CREATE TRIGGER `aud_facturacion_delete` AFTER DELETE ON `facturacion` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'DELETE', 'facturacion', CAST(OLD.`ID_Facturacion` AS CHAR), JSON_OBJECT('ID_Facturacion', OLD.`ID_Facturacion`, 'ID_Cliente', OLD.`ID_Cliente`, 'FECHA', OLD.`FECHA`, 'ImpuestosIVA', OLD.`ImpuestosIVA`, 'TotalPagar', OLD.`TotalPagar`), NULL);
END$$

CREATE TRIGGER `aud_historial_clinico_insert` AFTER INSERT ON `historial_clinico` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'INSERT', 'historial_clinico', CAST(NEW.`ID_HISTORIAL` AS CHAR), NULL, JSON_OBJECT('ID_HISTORIAL', NEW.`ID_HISTORIAL`, 'ID_Empleado', NEW.`ID_Empleado`, 'ID_Mascota', NEW.`ID_Mascota`, 'ID_Reserva', NEW.`ID_Reserva`, 'FechaHora', NEW.`FechaHora`, 'Diagnostico', NEW.`Diagnostico`, 'Tratamiento', NEW.`Tratamiento`));
END$$

CREATE TRIGGER `aud_historial_clinico_update` AFTER UPDATE ON `historial_clinico` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'UPDATE', 'historial_clinico', CAST(NEW.`ID_HISTORIAL` AS CHAR), JSON_OBJECT('ID_HISTORIAL', OLD.`ID_HISTORIAL`, 'ID_Empleado', OLD.`ID_Empleado`, 'ID_Mascota', OLD.`ID_Mascota`, 'ID_Reserva', OLD.`ID_Reserva`, 'FechaHora', OLD.`FechaHora`, 'Diagnostico', OLD.`Diagnostico`, 'Tratamiento', OLD.`Tratamiento`), JSON_OBJECT('ID_HISTORIAL', NEW.`ID_HISTORIAL`, 'ID_Empleado', NEW.`ID_Empleado`, 'ID_Mascota', NEW.`ID_Mascota`, 'ID_Reserva', NEW.`ID_Reserva`, 'FechaHora', NEW.`FechaHora`, 'Diagnostico', NEW.`Diagnostico`, 'Tratamiento', NEW.`Tratamiento`));
END$$

CREATE TRIGGER `aud_historial_clinico_delete` AFTER DELETE ON `historial_clinico` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'DELETE', 'historial_clinico', CAST(OLD.`ID_HISTORIAL` AS CHAR), JSON_OBJECT('ID_HISTORIAL', OLD.`ID_HISTORIAL`, 'ID_Empleado', OLD.`ID_Empleado`, 'ID_Mascota', OLD.`ID_Mascota`, 'ID_Reserva', OLD.`ID_Reserva`, 'FechaHora', OLD.`FechaHora`, 'Diagnostico', OLD.`Diagnostico`, 'Tratamiento', OLD.`Tratamiento`), NULL);
END$$

CREATE TRIGGER `aud_horario_insert` AFTER INSERT ON `horario` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'INSERT', 'horario', CAST(NEW.`ID_Horario` AS CHAR), NULL, JSON_OBJECT('ID_Horario', NEW.`ID_Horario`, 'ID_Empleado', NEW.`ID_Empleado`, 'DiaSemana', NEW.`DiaSemana`, 'HoraInicio', NEW.`HoraInicio`, 'HoraFin', NEW.`HoraFin`));
END$$

CREATE TRIGGER `aud_horario_update` AFTER UPDATE ON `horario` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'UPDATE', 'horario', CAST(NEW.`ID_Horario` AS CHAR), JSON_OBJECT('ID_Horario', OLD.`ID_Horario`, 'ID_Empleado', OLD.`ID_Empleado`, 'DiaSemana', OLD.`DiaSemana`, 'HoraInicio', OLD.`HoraInicio`, 'HoraFin', OLD.`HoraFin`), JSON_OBJECT('ID_Horario', NEW.`ID_Horario`, 'ID_Empleado', NEW.`ID_Empleado`, 'DiaSemana', NEW.`DiaSemana`, 'HoraInicio', NEW.`HoraInicio`, 'HoraFin', NEW.`HoraFin`));
END$$

CREATE TRIGGER `aud_horario_delete` AFTER DELETE ON `horario` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'DELETE', 'horario', CAST(OLD.`ID_Horario` AS CHAR), JSON_OBJECT('ID_Horario', OLD.`ID_Horario`, 'ID_Empleado', OLD.`ID_Empleado`, 'DiaSemana', OLD.`DiaSemana`, 'HoraInicio', OLD.`HoraInicio`, 'HoraFin', OLD.`HoraFin`), NULL);
END$$

CREATE TRIGGER `aud_mascota_insert` AFTER INSERT ON `mascota` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'INSERT', 'mascota', CAST(NEW.`ID_Mascota` AS CHAR), NULL, JSON_OBJECT('ID_Mascota', NEW.`ID_Mascota`, 'ID_Cliente', NEW.`ID_Cliente`, 'NombreMascota', NEW.`NombreMascota`, 'Especie', NEW.`Especie`, 'Raza', NEW.`Raza`, 'FechaNacimiento', NEW.`FechaNacimiento`, 'Tamano', NEW.`Tamano`, 'Peso', NEW.`Peso`, 'Genero', NEW.`Genero`));
END$$

CREATE TRIGGER `aud_mascota_update` AFTER UPDATE ON `mascota` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'UPDATE', 'mascota', CAST(NEW.`ID_Mascota` AS CHAR), JSON_OBJECT('ID_Mascota', OLD.`ID_Mascota`, 'ID_Cliente', OLD.`ID_Cliente`, 'NombreMascota', OLD.`NombreMascota`, 'Especie', OLD.`Especie`, 'Raza', OLD.`Raza`, 'FechaNacimiento', OLD.`FechaNacimiento`, 'Tamano', OLD.`Tamano`, 'Peso', OLD.`Peso`, 'Genero', OLD.`Genero`), JSON_OBJECT('ID_Mascota', NEW.`ID_Mascota`, 'ID_Cliente', NEW.`ID_Cliente`, 'NombreMascota', NEW.`NombreMascota`, 'Especie', NEW.`Especie`, 'Raza', NEW.`Raza`, 'FechaNacimiento', NEW.`FechaNacimiento`, 'Tamano', NEW.`Tamano`, 'Peso', NEW.`Peso`, 'Genero', NEW.`Genero`));
END$$

CREATE TRIGGER `aud_mascota_delete` AFTER DELETE ON `mascota` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'DELETE', 'mascota', CAST(OLD.`ID_Mascota` AS CHAR), JSON_OBJECT('ID_Mascota', OLD.`ID_Mascota`, 'ID_Cliente', OLD.`ID_Cliente`, 'NombreMascota', OLD.`NombreMascota`, 'Especie', OLD.`Especie`, 'Raza', OLD.`Raza`, 'FechaNacimiento', OLD.`FechaNacimiento`, 'Tamano', OLD.`Tamano`, 'Peso', OLD.`Peso`, 'Genero', OLD.`Genero`), NULL);
END$$

CREATE TRIGGER `aud_pago_insert` AFTER INSERT ON `pago` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'INSERT', 'pago', CAST(NEW.`ID_Pago` AS CHAR), NULL, JSON_OBJECT('ID_Pago', NEW.`ID_Pago`, 'ID_Facturacion', NEW.`ID_Facturacion`, 'MetodoPago', NEW.`MetodoPago`, 'ValorRecibido', NEW.`ValorRecibido`, 'CambioValorRecibido', NEW.`CambioValorRecibido`, 'ComprobantePago', NEW.`ComprobantePago`, 'FechaPago', NEW.`FechaPago`));
END$$

CREATE TRIGGER `aud_pago_update` AFTER UPDATE ON `pago` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'UPDATE', 'pago', CAST(NEW.`ID_Pago` AS CHAR), JSON_OBJECT('ID_Pago', OLD.`ID_Pago`, 'ID_Facturacion', OLD.`ID_Facturacion`, 'MetodoPago', OLD.`MetodoPago`, 'ValorRecibido', OLD.`ValorRecibido`, 'CambioValorRecibido', OLD.`CambioValorRecibido`, 'ComprobantePago', OLD.`ComprobantePago`, 'FechaPago', OLD.`FechaPago`), JSON_OBJECT('ID_Pago', NEW.`ID_Pago`, 'ID_Facturacion', NEW.`ID_Facturacion`, 'MetodoPago', NEW.`MetodoPago`, 'ValorRecibido', NEW.`ValorRecibido`, 'CambioValorRecibido', NEW.`CambioValorRecibido`, 'ComprobantePago', NEW.`ComprobantePago`, 'FechaPago', NEW.`FechaPago`));
END$$

CREATE TRIGGER `aud_pago_delete` AFTER DELETE ON `pago` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'DELETE', 'pago', CAST(OLD.`ID_Pago` AS CHAR), JSON_OBJECT('ID_Pago', OLD.`ID_Pago`, 'ID_Facturacion', OLD.`ID_Facturacion`, 'MetodoPago', OLD.`MetodoPago`, 'ValorRecibido', OLD.`ValorRecibido`, 'CambioValorRecibido', OLD.`CambioValorRecibido`, 'ComprobantePago', OLD.`ComprobantePago`, 'FechaPago', OLD.`FechaPago`), NULL);
END$$

CREATE TRIGGER `aud_pedidos_insert` AFTER INSERT ON `pedidos` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'INSERT', 'pedidos', CAST(NEW.`ID_Pedido` AS CHAR), NULL, JSON_OBJECT('ID_Pedido', NEW.`ID_Pedido`, 'ID_Cliente', NEW.`ID_Cliente`, 'Fecha', NEW.`Fecha`, 'Total', NEW.`Total`, 'Estado', NEW.`Estado`));
END$$

CREATE TRIGGER `aud_pedidos_update` AFTER UPDATE ON `pedidos` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'UPDATE', 'pedidos', CAST(NEW.`ID_Pedido` AS CHAR), JSON_OBJECT('ID_Pedido', OLD.`ID_Pedido`, 'ID_Cliente', OLD.`ID_Cliente`, 'Fecha', OLD.`Fecha`, 'Total', OLD.`Total`, 'Estado', OLD.`Estado`), JSON_OBJECT('ID_Pedido', NEW.`ID_Pedido`, 'ID_Cliente', NEW.`ID_Cliente`, 'Fecha', NEW.`Fecha`, 'Total', NEW.`Total`, 'Estado', NEW.`Estado`));
END$$

CREATE TRIGGER `aud_pedidos_delete` AFTER DELETE ON `pedidos` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'DELETE', 'pedidos', CAST(OLD.`ID_Pedido` AS CHAR), JSON_OBJECT('ID_Pedido', OLD.`ID_Pedido`, 'ID_Cliente', OLD.`ID_Cliente`, 'Fecha', OLD.`Fecha`, 'Total', OLD.`Total`, 'Estado', OLD.`Estado`), NULL);
END$$

CREATE TRIGGER `aud_pedido_detalle_insert` AFTER INSERT ON `pedido_detalle` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'INSERT', 'pedido_detalle', CAST(NEW.`ID_Detalle` AS CHAR), NULL, JSON_OBJECT('ID_Detalle', NEW.`ID_Detalle`, 'ID_Pedido', NEW.`ID_Pedido`, 'ID_Producto', NEW.`ID_Producto`, 'Cantidad', NEW.`Cantidad`, 'PrecioUnitario', NEW.`PrecioUnitario`));
END$$

CREATE TRIGGER `aud_pedido_detalle_update` AFTER UPDATE ON `pedido_detalle` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'UPDATE', 'pedido_detalle', CAST(NEW.`ID_Detalle` AS CHAR), JSON_OBJECT('ID_Detalle', OLD.`ID_Detalle`, 'ID_Pedido', OLD.`ID_Pedido`, 'ID_Producto', OLD.`ID_Producto`, 'Cantidad', OLD.`Cantidad`, 'PrecioUnitario', OLD.`PrecioUnitario`), JSON_OBJECT('ID_Detalle', NEW.`ID_Detalle`, 'ID_Pedido', NEW.`ID_Pedido`, 'ID_Producto', NEW.`ID_Producto`, 'Cantidad', NEW.`Cantidad`, 'PrecioUnitario', NEW.`PrecioUnitario`));
END$$

CREATE TRIGGER `aud_pedido_detalle_delete` AFTER DELETE ON `pedido_detalle` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'DELETE', 'pedido_detalle', CAST(OLD.`ID_Detalle` AS CHAR), JSON_OBJECT('ID_Detalle', OLD.`ID_Detalle`, 'ID_Pedido', OLD.`ID_Pedido`, 'ID_Producto', OLD.`ID_Producto`, 'Cantidad', OLD.`Cantidad`, 'PrecioUnitario', OLD.`PrecioUnitario`), NULL);
END$$

CREATE TRIGGER `aud_productos_insert` AFTER INSERT ON `productos` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'INSERT', 'productos', CAST(NEW.`ID_Producto` AS CHAR), NULL, JSON_OBJECT('ID_Producto', NEW.`ID_Producto`, 'TipoProducto', NEW.`TipoProducto`, 'Descripcion', NEW.`Descripcion`, 'ValorProducto', NEW.`ValorProducto`, 'Icono', NEW.`Icono`, 'Stock', NEW.`Stock`));
END$$

CREATE TRIGGER `aud_productos_update` AFTER UPDATE ON `productos` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'UPDATE', 'productos', CAST(NEW.`ID_Producto` AS CHAR), JSON_OBJECT('ID_Producto', OLD.`ID_Producto`, 'TipoProducto', OLD.`TipoProducto`, 'Descripcion', OLD.`Descripcion`, 'ValorProducto', OLD.`ValorProducto`, 'Icono', OLD.`Icono`, 'Stock', OLD.`Stock`), JSON_OBJECT('ID_Producto', NEW.`ID_Producto`, 'TipoProducto', NEW.`TipoProducto`, 'Descripcion', NEW.`Descripcion`, 'ValorProducto', NEW.`ValorProducto`, 'Icono', NEW.`Icono`, 'Stock', NEW.`Stock`));
END$$

CREATE TRIGGER `aud_productos_delete` AFTER DELETE ON `productos` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'DELETE', 'productos', CAST(OLD.`ID_Producto` AS CHAR), JSON_OBJECT('ID_Producto', OLD.`ID_Producto`, 'TipoProducto', OLD.`TipoProducto`, 'Descripcion', OLD.`Descripcion`, 'ValorProducto', OLD.`ValorProducto`, 'Icono', OLD.`Icono`, 'Stock', OLD.`Stock`), NULL);
END$$

CREATE TRIGGER `aud_reservas_insert` AFTER INSERT ON `reservas` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'INSERT', 'reservas', CAST(NEW.`ID_Reserva` AS CHAR), NULL, JSON_OBJECT('ID_Reserva', NEW.`ID_Reserva`, 'ID_Empleado', NEW.`ID_Empleado`, 'ID_Mascota', NEW.`ID_Mascota`, 'ID_CataServicio', NEW.`ID_CataServicio`, 'FechaReserva', NEW.`FechaReserva`, 'HoraReserva', NEW.`HoraReserva`, 'EstadoCita', NEW.`EstadoCita`));
END$$

CREATE TRIGGER `aud_reservas_update` AFTER UPDATE ON `reservas` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'UPDATE', 'reservas', CAST(NEW.`ID_Reserva` AS CHAR), JSON_OBJECT('ID_Reserva', OLD.`ID_Reserva`, 'ID_Empleado', OLD.`ID_Empleado`, 'ID_Mascota', OLD.`ID_Mascota`, 'ID_CataServicio', OLD.`ID_CataServicio`, 'FechaReserva', OLD.`FechaReserva`, 'HoraReserva', OLD.`HoraReserva`, 'EstadoCita', OLD.`EstadoCita`), JSON_OBJECT('ID_Reserva', NEW.`ID_Reserva`, 'ID_Empleado', NEW.`ID_Empleado`, 'ID_Mascota', NEW.`ID_Mascota`, 'ID_CataServicio', NEW.`ID_CataServicio`, 'FechaReserva', NEW.`FechaReserva`, 'HoraReserva', NEW.`HoraReserva`, 'EstadoCita', NEW.`EstadoCita`));
END$$

CREATE TRIGGER `aud_reservas_delete` AFTER DELETE ON `reservas` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'DELETE', 'reservas', CAST(OLD.`ID_Reserva` AS CHAR), JSON_OBJECT('ID_Reserva', OLD.`ID_Reserva`, 'ID_Empleado', OLD.`ID_Empleado`, 'ID_Mascota', OLD.`ID_Mascota`, 'ID_CataServicio', OLD.`ID_CataServicio`, 'FechaReserva', OLD.`FechaReserva`, 'HoraReserva', OLD.`HoraReserva`, 'EstadoCita', OLD.`EstadoCita`), NULL);
END$$

CREATE TRIGGER `aud_responsable_alterno_insert` AFTER INSERT ON `responsable_alterno` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'INSERT', 'responsable_alterno', CAST(NEW.`ID_RESPONSABLE` AS CHAR), NULL, JSON_OBJECT('ID_RESPONSABLE', NEW.`ID_RESPONSABLE`, 'ID_Mascota', NEW.`ID_Mascota`, 'Nombre', NEW.`Nombre`, 'Documento', NEW.`Documento`, 'Telefono', NEW.`Telefono`, 'Relacion', NEW.`Relacion`, 'AutorizacionDeRetiro', NEW.`AutorizacionDeRetiro`));
END$$

CREATE TRIGGER `aud_responsable_alterno_update` AFTER UPDATE ON `responsable_alterno` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'UPDATE', 'responsable_alterno', CAST(NEW.`ID_RESPONSABLE` AS CHAR), JSON_OBJECT('ID_RESPONSABLE', OLD.`ID_RESPONSABLE`, 'ID_Mascota', OLD.`ID_Mascota`, 'Nombre', OLD.`Nombre`, 'Documento', OLD.`Documento`, 'Telefono', OLD.`Telefono`, 'Relacion', OLD.`Relacion`, 'AutorizacionDeRetiro', OLD.`AutorizacionDeRetiro`), JSON_OBJECT('ID_RESPONSABLE', NEW.`ID_RESPONSABLE`, 'ID_Mascota', NEW.`ID_Mascota`, 'Nombre', NEW.`Nombre`, 'Documento', NEW.`Documento`, 'Telefono', NEW.`Telefono`, 'Relacion', NEW.`Relacion`, 'AutorizacionDeRetiro', NEW.`AutorizacionDeRetiro`));
END$$

CREATE TRIGGER `aud_responsable_alterno_delete` AFTER DELETE ON `responsable_alterno` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'DELETE', 'responsable_alterno', CAST(OLD.`ID_RESPONSABLE` AS CHAR), JSON_OBJECT('ID_RESPONSABLE', OLD.`ID_RESPONSABLE`, 'ID_Mascota', OLD.`ID_Mascota`, 'Nombre', OLD.`Nombre`, 'Documento', OLD.`Documento`, 'Telefono', OLD.`Telefono`, 'Relacion', OLD.`Relacion`, 'AutorizacionDeRetiro', OLD.`AutorizacionDeRetiro`), NULL);
END$$

CREATE TRIGGER `aud_usuarios_insert` AFTER INSERT ON `usuarios` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'INSERT', 'usuarios', CAST(NEW.`ID_USUARIO` AS CHAR), NULL, JSON_OBJECT('ID_USUARIO', NEW.`ID_USUARIO`, 'ID_Cliente', NEW.`ID_Cliente`, 'ID_Empleado', NEW.`ID_Empleado`, 'Nombre', NEW.`Nombre`, 'Correo', NEW.`Correo`, 'Rol', NEW.`Rol`, 'FechaRegistro', NEW.`FechaRegistro`));
END$$

CREATE TRIGGER `aud_usuarios_update` AFTER UPDATE ON `usuarios` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'UPDATE', 'usuarios', CAST(NEW.`ID_USUARIO` AS CHAR), JSON_OBJECT('ID_USUARIO', OLD.`ID_USUARIO`, 'ID_Cliente', OLD.`ID_Cliente`, 'ID_Empleado', OLD.`ID_Empleado`, 'Nombre', OLD.`Nombre`, 'Correo', OLD.`Correo`, 'Rol', OLD.`Rol`, 'FechaRegistro', OLD.`FechaRegistro`), JSON_OBJECT('ID_USUARIO', NEW.`ID_USUARIO`, 'ID_Cliente', NEW.`ID_Cliente`, 'ID_Empleado', NEW.`ID_Empleado`, 'Nombre', NEW.`Nombre`, 'Correo', NEW.`Correo`, 'Rol', NEW.`Rol`, 'FechaRegistro', NEW.`FechaRegistro`));
END$$

CREATE TRIGGER `aud_usuarios_delete` AFTER DELETE ON `usuarios` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  VALUES (COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'DELETE', 'usuarios', CAST(OLD.`ID_USUARIO` AS CHAR), JSON_OBJECT('ID_USUARIO', OLD.`ID_USUARIO`, 'ID_Cliente', OLD.`ID_Cliente`, 'ID_Empleado', OLD.`ID_Empleado`, 'Nombre', OLD.`Nombre`, 'Correo', OLD.`Correo`, 'Rol', OLD.`Rol`, 'FechaRegistro', OLD.`FechaRegistro`), NULL);
END$$

-- MySQL no ejecuta triggers de la tabla hija cuando una FK aplica ON DELETE CASCADE.
-- Estos BEFORE DELETE guardan el snapshot de USUARIOS antes de que cliente/empleado lo borren.
CREATE TRIGGER `aud_cliente_before_delete_usuarios` BEFORE DELETE ON `cliente` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  SELECT COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'DELETE', 'usuarios',
         CAST(u.`ID_USUARIO` AS CHAR),
         JSON_OBJECT('ID_USUARIO', u.`ID_USUARIO`, 'ID_Cliente', u.`ID_Cliente`, 'ID_Empleado', u.`ID_Empleado`,
                     'Nombre', u.`Nombre`, 'Correo', u.`Correo`, 'Rol', u.`Rol`, 'FechaRegistro', u.`FechaRegistro`),
         NULL
  FROM `usuarios` u WHERE u.`ID_Cliente` = OLD.`ID_Cliente`;
END$$

CREATE TRIGGER `aud_empleado_before_delete_usuarios` BEFORE DELETE ON `empleado` FOR EACH ROW
BEGIN
  INSERT INTO auditoria (usuario, fecha_hora, operacion, nombre_tabla, id_registro, datos_anteriores, datos_nuevos)
  SELECT COALESCE(NULLIF(@usuario_auditoria, ''), 'SISTEMA'), CURRENT_TIMESTAMP(6), 'DELETE', 'usuarios',
         CAST(u.`ID_USUARIO` AS CHAR),
         JSON_OBJECT('ID_USUARIO', u.`ID_USUARIO`, 'ID_Cliente', u.`ID_Cliente`, 'ID_Empleado', u.`ID_Empleado`,
                     'Nombre', u.`Nombre`, 'Correo', u.`Correo`, 'Rol', u.`Rol`, 'FechaRegistro', u.`FechaRegistro`),
         NULL
  FROM `usuarios` u WHERE u.`ID_Empleado` = OLD.`ID_Empleado`;
END$$

DELIMITER ;
