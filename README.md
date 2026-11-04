
## Cómo abrir el proyecto

1. **Clona o descarga** el repositorio y abre la carpeta en VS Code.
2. **Crea un entorno virtual** (opcional pero recomendado):
```bash
   python -m venv venv
```
3. **Actívalo**:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
4. **Instala las dependencias**:
```bash
   pip install -r requirements.txt
```
   (Esto instala Flask, `mysql-connector-python` y `python-dotenv`.)
5. **Configura la base de datos** (sección *Base de datos MySQL* más abajo).
6. **Ejecuta la aplicación**:
```bash
   python app.py
```
7. Abre el navegador en **http://localhost:5000** para ver el sitio, o usa **http://127.0.0.1:5000** en Postman para probar la API.

## 🗄️ Base de datos MySQL

La app lee y guarda todo en MySQL 8+ (base `veterinaria`). Necesitas tener MySQL encendido.

1. **Crea las tablas y ajusta la estructura** (desde la carpeta del proyecto):
```bash
   mysql -u root -p < database/schema.sql
   mysql -u root -p < database/migracion_app.sql
   mysql -u root -p < database/datos_ejemplo.sql
```
   - `schema.sql`: tu esquema original.
   - `migracion_app.sql`: agrega `Descripcion`, `Icono` y `Cupos`/`Stock` (la página los muestra) y amplía los nombres a 100 caracteres. **Ejecútalo una sola vez.**
   - `datos_ejemplo.sql`: los 10 servicios y productos de ejemplo. Omítelo si ya tienes datos propios.
2. **Crea tu archivo `.env`** copiando `.env.example` y poniendo tu usuario y contraseña de MySQL:
```
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=tu_clave
   DB_NAME=veterinaria
```
   El `.env` está en `.gitignore`, así que tu contraseña no se sube a GitHub.
3. (Recomendado) en lugar de `root`, crea un usuario solo para la app:
```sql
   CREATE USER 'vete_app'@'localhost' IDENTIFIED BY 'una_clave_segura';
   GRANT SELECT, INSERT, UPDATE, DELETE ON veterinaria.* TO 'vete_app'@'localhost';
```

**Cómo se relaciona la página con las tablas:** la lista mezcla servicios (`CATALOGO_SERVICIOS`) y productos (`PRODUCTOS`), así que los ids llevan un prefijo: `S1` es el servicio 1 y `P1` es el producto 1.

## 🧪 Cómo probar la API con Postman

Con el servidor corriendo (`python app.py`), abre Postman y prueba los siguientes endpoints:

### 1. Listar todos los servicios (GET)
- **Método:** `GET`
- **URL:** `http://localhost:5000/api/servicios`
- **Body:** ninguno
- Debe devolver un JSON con `estado: "exito"` y la lista de servicios.

### 2. Reservar un servicio (POST)
- **Método:** `POST`
- **URL:** `http://localhost:5000/api/servicios/S1/reservar`
- **Body:** ninguno
- Descuenta en 1 el `stock` del servicio con id `S1`. Si el servicio no tiene cupos, devuelve error 400.

### 3. Actualizar un servicio completo (PUT)
- **Método:** `PUT`
- **URL:** `http://localhost:5000/api/servicios/S1`
- **Body:** selecciona `raw` → `JSON` y pega:
```json
  {
    "nombre": "Consulta General Veterinaria",
    "descripcion": "Revisión médica completa con veterinario certificado.",
    "precio": "90.000",
    "icono": "🩺",
    "stock": 15
  }
```
- Debes enviar **todos** los campos; si falta alguno, la API responde error 400.

### 4. Eliminar un servicio (DELETE)
- **Método:** `DELETE`
- **URL:** `http://localhost:5000/api/servicios/S1`
- **Body:** ninguno
- Elimina el servicio con id `S1`. Si tiene reservas o facturas asociadas, responde `409`.

>  **Tip:** Cambia el id al final de la URL (`/S1`, `/S2`, `/P1`, etc.; `S` = servicio, `P` = producto) para probar con distintos registros. Si usas un id que no existe, la API responde `404` con `"mensaje": "Servicio no encontrado"`.

##  Notas

- Los datos se guardan en **MySQL**: se conservan aunque reinicies el servidor.
- El sitio web (`http://localhost:5000/`) usa estos mismos endpoints desde los botones "Reservar", "Editar" y "Eliminar".
