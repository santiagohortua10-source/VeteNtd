
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
   (Si no tienes `requirements.txt`, simplemente ejecuta `pip install flask`)
5. **Ejecuta la aplicación**:
```bash
   python app.py
```
6. Abre el navegador en **http://localhost:5000** para ver el sitio, o usa **http://127.0.0.1:5000** en Postman para probar la API.

## 🧪 Cómo probar la API con Postman

Con el servidor corriendo (`python app.py`), abre Postman y prueba los siguientes endpoints:

### 1. Listar todos los servicios (GET)
- **Método:** `GET`
- **URL:** `http://localhost:5000/api/servicios`
- **Body:** ninguno
- Debe devolver un JSON con `estado: "exito"` y la lista de servicios.

### 2. Reservar un servicio (POST)
- **Método:** `POST`
- **URL:** `http://localhost:5000/api/servicios/1/reservar`
- **Body:** ninguno
- Descuenta en 1 el `stock` del servicio con id `1`. Si el servicio no tiene cupos, devuelve error 400.

### 3. Actualizar un servicio completo (PUT)
- **Método:** `PUT`
- **URL:** `http://localhost:5000/api/servicios/1`
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
- **URL:** `http://localhost:5000/api/servicios/1`
- **Body:** ninguno
- Elimina el servicio con id `1` de la lista.

>  **Tip:** Cambia el número al final de la URL (`/1`, `/2`, etc.) para probar con distintos servicios. Si usas un id que no existe, la API responde `404` con `"mensaje": "Servicio no encontrado"`.

##  Notas

- Los datos se guardan **en memoria**: si reinicias el servidor (`python app.py`), la lista vuelve a su estado original.
- El sitio web (`http://localhost:5000/`) usa estos mismos endpoints desde los botones "Reservar", "Editar" y "Eliminar".
