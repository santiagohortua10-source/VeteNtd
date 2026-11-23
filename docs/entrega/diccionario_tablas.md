# Diccionario de tablas PawCare

Descripciones elaboradas a partir de nombres de columna, claves, restricciones y usos observados en el c?digo Flask. La base de datos no contiene comentarios sem?nticos (`TABLE_COMMENT`/`COLUMN_COMMENT` vac?os); las descripciones explican los nombres y no agregan reglas de negocio no verificadas.

| Tabla | Descripci?n observada | Clave primaria |
|---|---|---|
| `catalogo_servicios` | Cat?logo de servicios veterinarios con duraci?n, costo y cupos. | `ID_CataServicio` |
| `cliente` | Datos de contacto y autenticaci?n de los clientes. | `ID_Cliente` |
| `detalle_factura` | Renglones de facturaci?n que referencian producto o servicio. | `ID_DetFactura` |
| `empleado` | Personal de la cl?nica, incluyendo veterinarios y administradores. | `ID_Empleado` |
| `facturacion` | Cabecera de factura, cliente, fecha, IVA y total. | `ID_Facturacion` |
| `historial_clinico` | Diagn?sticos y tratamientos asociados a una mascota, veterinario y reserva. | `ID_HISTORIAL` |
| `horario` | Bloques semanales de atenci?n asignados a empleados. | `ID_Horario` |
| `mascota` | Mascotas vinculadas a un cliente. | `ID_Mascota` |
| `pago` | Pagos y comprobantes asociados a una factura. | `ID_Pago` |
| `pedidos` | Cabecera de pedidos de tienda vinculados a clientes. | `ID_Pedido` |
| `pedido_detalle` | Productos y cantidades que componen un pedido. | `ID_Detalle` |
| `productos` | Cat?logo de productos de tienda con precio e inventario. | `ID_Producto` |
| `reservas` | Citas entre cliente/mascota, servicio, veterinario y horario. | `ID_Reserva` |
| `responsable_alterno` | Personas autorizadas o registradas para el retiro de una mascota. | `ID_RESPONSABLE` |
| `usuarios` | Cuentas de acceso asociadas a cliente o empleado y su rol. | `ID_USUARIO` |

## Relaciones verificadas

Las relaciones siguientes se copiaron de `information_schema.KEY_COLUMN_USAGE`; no se infirieron relaciones adicionales.

- `detalle_factura.ID_Producto` ? `productos.ID_Producto`
- `detalle_factura.ID_Facturacion` ? `facturacion.ID_Facturacion`
- `detalle_factura.ID_Servicio` ? `catalogo_servicios.ID_CataServicio`
- `facturacion.ID_Cliente` ? `cliente.ID_Cliente`
- `historial_clinico.ID_Empleado` ? `empleado.ID_Empleado`
- `historial_clinico.ID_Mascota` ? `mascota.ID_Mascota`
- `historial_clinico.ID_Reserva` ? `reservas.ID_Reserva`
- `horario.ID_Empleado` ? `empleado.ID_Empleado`
- `mascota.ID_Cliente` ? `cliente.ID_Cliente`
- `pago.ID_Facturacion` ? `facturacion.ID_Facturacion`
- `pedidos.ID_Cliente` ? `cliente.ID_Cliente`
- `pedido_detalle.ID_Pedido` ? `pedidos.ID_Pedido`
- `pedido_detalle.ID_Producto` ? `productos.ID_Producto`
- `reservas.ID_Empleado` ? `empleado.ID_Empleado`
- `reservas.ID_Mascota` ? `mascota.ID_Mascota`
- `reservas.ID_CataServicio` ? `catalogo_servicios.ID_CataServicio`
- `responsable_alterno.ID_Mascota` ? `mascota.ID_Mascota`
- `usuarios.ID_Cliente` ? `cliente.ID_Cliente`
- `usuarios.ID_Empleado` ? `empleado.ID_Empleado`

## Diccionario de columnas

Consulta `diccionario_datos.csv` para las 96 columnas, tipos SQL, nulabilidad, valores por defecto, AUTO_INCREMENT, PK/FK e ?ndices. Se excluyeron deliberadamente los valores de las filas de datos.
