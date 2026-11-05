# PawCare - Sistema web para veterinaria

Aplicación web hecha con Flask para gestionar el catálogo de una veterinaria (servicios y productos) y permitir que los clientes registren sus mascotas y agenden citas en línea. Usa dos bases de datos: MySQL (a través de XAMPP) para los datos estructurados y MongoDB Atlas, en la nube, para las notificaciones.

## Contenido

1. [Qué hace el proyecto](#qué-hace-el-proyecto)
2. [Tecnologías](#tecnologías)
3. [Estructura del proyecto](#estructura-del-proyecto)
4. [Cómo funciona](#cómo-funciona)
5. [Requisitos previos](#requisitos-previos)
6. [Instalación y ejecución](#instalación-y-ejecución)
7. [Uso diario](#uso-diario)
8. [Variables de entorno](#variables-de-entorno)
9. [Referencia de la API](#referencia-de-la-api)
10. [Cómo probar la API con Postman](#cómo-probar-la-api-con-postman)
11. [Solución de problemas](#solución-de-problemas)
12. [Notas de seguridad](#notas-de-seguridad)

## Qué hace el proyecto

El sitio tiene dos partes:

**Catálogo (página principal, `/`)**
- Muestra servicios y productos en una sola lista, con filtros por tipo.
- Permite reservar (descuenta un cupo o una unidad), editar y eliminar elementos del catálogo.
- Incluye una campana de notificaciones para el equipo de la clínica.

**Portal de clientes (`/cliente`)**
- Registro e inicio de sesión de clientes (contraseña almacenada con hash).
- Gestión de mascotas: crear y eliminar.
- Agenda de citas: el cliente elige mascota, servicio, veterinario y fecha, y el sistema le muestra solo las horas realmente libres.
- Listado de citas y cancelación de citas futuras.
- Campana de notificaciones propia de cada cliente.

## Tecnologías

| Componente | Tecnología |
|------------|-----------|
| Backend | Python 3.9 o superior, Flask 3.1 |
| Base relacional | MySQL de XAMPP, que en realidad es MariaDB (`mysql-connector-python`) |
| Administración de la base | phpMyAdmin (incluido en XAMPP) |
| Base NoSQL | MongoDB Atlas, en la nube (`pymongo`) |
| Configuración | `python-dotenv` |
| Frontend | HTML con plantillas Jinja2, CSS y JavaScript sin frameworks |

## Estructura del proyecto

```
VeteNtd-main/
├── app.py                     Aplicación Flask: catálogo, reservas y notificaciones del equipo
├── clientes.py                Blueprint del portal de clientes (cuenta, mascotas, citas)
├── notificaciones.py          Lógica de la colección de notificaciones en MongoDB
├── db.py                      Conexión a MySQL/MariaDB y funciones de consulta y transacción
├── mongo.py                   Conexión a MongoDB Atlas
├── requirements.txt           Dependencias de Python
├── .env.example copy          Plantilla de variables de entorno
├── database/
│   ├── schema.sql             Esquema base de la base de datos
│   ├── migracion_app.sql      Ajustes para el portal de clientes y datos de veterinarios
│   ├── datos_ejemplo.sql      Servicios y productos de ejemplo
│   └── mongo_setup.py         Crea la colección de notificaciones, validación e índices
├── static/
│   ├── comun.js               Utilidades compartidas (llamadas a la API, avisos, campana)
│   └── estilos.css            Estilos del sitio
├── templates/
│   ├── index.html             Página del catálogo
│   └── cliente.html           Portal de clientes
└── AppFlask.zip               Prototipo inicial; no es necesario para ejecutar el proyecto
```

El proyecto no se copia dentro de la carpeta `htdocs` de XAMPP. Flask trae su propio servidor, por lo que Apache no es necesario para correr la aplicación; solo se usa para abrir phpMyAdmin.

## Cómo funciona

### Dos bases de datos

| Base | Dónde corre | Qué guarda | Motivo |
|------|-------------|-----------|--------|
| `veterinaria` (MySQL/MariaDB) | Tu equipo, con XAMPP | Servicios, productos, clientes, mascotas, empleados, horarios, reservas, facturas | Datos estructurados con relaciones y transacciones |
| `veterinaria_nosql` (MongoDB) | MongoDB Atlas, en la nube | Colección `notificaciones` | Datos dinámicos, de alta frecuencia y sin esquema rígido |

Si MongoDB falla, la aplicación sigue funcionando: la reserva o la cita se guarda igual en MySQL y solo se pierde la notificación, que queda registrada en el log.

### Catálogo unificado con ids con prefijo

El catálogo mezcla dos tablas distintas, `CATALOGO_SERVICIOS` y `PRODUCTOS`. Para que los ids no choquen, cada elemento usa un prefijo:

- `S1` es el servicio con `ID_CataServicio = 1`.
- `P1` es el producto con `ID_Producto = 1`.

Los nombres de tabla y columna salen de un diccionario fijo en `app.py`, nunca de datos enviados por el usuario. Los valores siempre se pasan como parámetros SQL.

### Reservas del catálogo

`POST /api/servicios/<id>/reservar` descuenta una unidad con un único `UPDATE ... SET stock = stock - 1 WHERE id = %s AND stock > 0`. Al ser una sola sentencia, el descuento es atómico: dos peticiones simultáneas no pueden dejar el stock en negativo. Si no hay cupos, responde error 400.

### Agenda de citas

El cálculo de horas disponibles (`horas_disponibles` en `clientes.py`) funciona así:

1. Toma los bloques de atención del veterinario para el día de la semana elegido (tabla `HORARIO`; puede haber varios bloques por día, por ejemplo mañana y tarde).
2. Genera horas de inicio cada 30 minutos, siempre que la cita completa (según `DuracionServicio`) quepa dentro del bloque.
3. Descarta las horas que se cruzan con citas activas del mismo veterinario o de la misma mascota.
4. Descarta las horas que ya pasaron si la fecha es hoy.

Reglas adicionales:
- Solo se puede agendar desde hoy hasta 60 días en adelante.
- Al agendar, la transacción bloquea la fila del veterinario con `SELECT ... FOR UPDATE` y recalcula la disponibilidad antes de insertar. Así, dos clientes no pueden tomar la misma hora.
- Cancelar solo es posible en citas con estado `Agendada` que todavía no han ocurrido.
- La zona horaria de la clínica es `America/Bogota` por defecto (configurable con `ZONA_HORARIA`).

### Cuentas de clientes

- La contraseña se guarda con `generate_password_hash` de Werkzeug (columna `ClaveHash`); nunca en texto plano.
- La sesión guarda únicamente el id del cliente en una cookie firmada con `SECRET_KEY`.
- Cada cliente solo puede ver y modificar sus propias mascotas, citas y notificaciones.

### Notificaciones (MongoDB Atlas)

Cada notificación es un documento con tipo, título, mensaje, prioridad, estado de lectura, fecha, referencia al elemento del catálogo (`item`), datos libres (`datos`) y un `cliente_id`.

- Si `cliente_id` es `null`, la notificación es del equipo y aparece en la página principal.
- Si tiene un id, pertenece a ese cliente y aparece en su portal. Cada quien lleva su propio estado de "leída".

Tipos que se generan automáticamente:

| Tipo | Cuándo se genera |
|------|------------------|
| `reserva_creada` | Se reserva un servicio o producto del catálogo |
| `stock_bajo` | El stock queda igual o por debajo de `UMBRAL_STOCK_BAJO` |
| `sin_cupos` | El stock llega a 0 |
| `servicio_actualizado` | Se edita un elemento del catálogo |
| `servicio_eliminado` | Se elimina un elemento del catálogo |
| `cita_agendada` | Un cliente agenda una cita (una para el cliente y otra para el equipo) |
| `cita_cancelada` | Un cliente cancela una cita (una para el cliente y otra para el equipo) |

La colección tiene validación de esquema (`$jsonSchema`) e índices por lectura y fecha. Además tiene un índice TTL: MongoDB borra solo las notificaciones con más de 30 días (configurable con `NOTIF_DIAS_RETENCION`).

## Requisitos previos

- **XAMPP** instalado (https://www.apachefriends.org). Se usa el módulo MySQL y phpMyAdmin.
- **Python 3.9 o superior**. En Windows, al instalarlo marca la casilla "Add Python to PATH".
- **Una cuenta de MongoDB Atlas** (https://www.mongodb.com/cloud/atlas). El plan gratuito es suficiente.
- Conexión a internet, porque las notificaciones viven en Atlas.
- Opcional: VS Code y Postman.

Nota sobre XAMPP: el "MySQL" de XAMPP es MariaDB. Es compatible con los scripts del proyecto, pero hay un detalle de conexión que se explica en el paso 7 de la instalación.

## Instalación y ejecución

Los comandos están pensados para Windows. En Mac o Linux los pasos son equivalentes, pero XAMPP se instala y se inicia de forma distinta.

### 1. Abrir el proyecto y crear el entorno virtual

Abre una terminal (CMD o PowerShell) dentro de la carpeta del proyecto:

```bash
cd VeteNtd-main
python -m venv venv
```

Activa el entorno:

- CMD: `venv\Scripts\activate`
- PowerShell: `venv\Scripts\Activate.ps1`
- Mac y Linux: `source venv/bin/activate`

Si PowerShell muestra "la ejecución de scripts está deshabilitada", ejecuta esto una vez en esa misma ventana y vuelve a activar:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### 2. Instalar las dependencias

```bash
pip install -r requirements.txt
```

### 3. Iniciar MySQL en XAMPP

1. Abre el **XAMPP Control Panel**.
2. Pulsa **Start** en el módulo **MySQL**. Cuando se ponga en verde, está listo.
3. Pulsa **Start** también en **Apache**, pero solo si vas a usar phpMyAdmin (el siguiente paso lo usa).

Por defecto, XAMPP crea el usuario `root` **sin contraseña**, en el puerto `3306`. Con esos valores funciona el `.env` de este proyecto sin cambios.

### 4. Crear la base de datos en phpMyAdmin

Abre http://localhost/phpmyadmin en el navegador.

Importa los scripts **uno por uno y en este orden**. Para cada uno: pestaña **Importar**, botón **Seleccionar archivo**, elige el archivo de la carpeta `database/` y pulsa **Importar** al final de la página. No hace falta crear ni seleccionar la base antes, porque `schema.sql` la crea.

| Orden | Archivo | Qué hace |
|-------|---------|----------|
| 1 | `schema.sql` | Crea la base `veterinaria` y las 13 tablas |
| 2 | Bloque `ALTER TABLE` de abajo | Agrega las columnas del catálogo (ver explicación) |
| 3 | `migracion_app.sql` | Amplía columnas de `CLIENTE`, `MASCOTA` y `EMPLEADO`, agrega `ClaveHash` y correo único, e inserta tres veterinarios con sus horarios. **Ejecutar una sola vez** |
| 4 | `datos_ejemplo.sql` | Inserta 5 servicios y 5 productos de ejemplo. Omítelo si ya tienes datos propios |

**Paso 2: columnas del catálogo.** El código y `datos_ejemplo.sql` usan las columnas `Descripcion`, `Icono`, `Cupos` (servicios) y `Stock` (productos). En los archivos revisados, ni `schema.sql` ni `migracion_app.sql` las crean, así que hay que agregarlas. En phpMyAdmin, selecciona la base `veterinaria` en el panel izquierdo, abre la pestaña **SQL**, pega este bloque y pulsa **Continuar** (solo una vez):

```sql
USE veterinaria;

ALTER TABLE CATALOGO_SERVICIOS
    MODIFY Servicio VARCHAR(100) NOT NULL,
    ADD COLUMN Descripcion VARCHAR(255) NOT NULL DEFAULT '',
    ADD COLUMN Icono VARCHAR(10) NOT NULL DEFAULT '',
    ADD COLUMN Cupos INT NOT NULL DEFAULT 0;

ALTER TABLE PRODUCTOS
    MODIFY TipoProducto VARCHAR(100) NOT NULL,
    ADD COLUMN Descripcion VARCHAR(255) NOT NULL DEFAULT '',
    ADD COLUMN Icono VARCHAR(10) NOT NULL DEFAULT '',
    ADD COLUMN Stock INT NOT NULL DEFAULT 0;
```

**Verificación.** Al terminar, en el panel izquierdo de phpMyAdmin debe aparecer la base `veterinaria` con sus tablas. Entra a `CATALOGO_SERVICIOS` y `PRODUCTOS` y comprueba que tengan datos, y a `EMPLEADO` para ver los tres veterinarios.

**Alternativa por consola (opcional).** Si prefieres la terminal, abre el cliente de XAMPP y carga los archivos con `source`, que funciona igual en CMD y en PowerShell y respeta las tildes y emojis de los datos de ejemplo:

```bash
C:\xampp\mysql\bin\mysql.exe -u root --default-character-set=utf8mb4
```

```sql
source database/schema.sql
source database/migracion_app.sql
```

Recuerda ejecutar el bloque `ALTER TABLE` del paso 2 entre `schema.sql` y `datos_ejemplo.sql`. No uses el operador `<` en PowerShell: no está soportado para redirigir archivos.

### 5. Crear el cluster en MongoDB Atlas

1. Entra a https://www.mongodb.com/cloud/atlas e inicia sesión o crea una cuenta.
2. Crea un cluster gratuito (**M0**) y espera a que termine de aprovisionarse.
3. **Database Access** (menú izquierdo): pulsa **Add New Database User**, elige autenticación con contraseña y crea un usuario con permisos de lectura y escritura sobre cualquier base de datos. Anota el usuario y la contraseña. Si la contraseña tiene caracteres especiales (`@`, `:`, `/`, `?`, `#`), debes codificarlos en la cadena de conexión (por ejemplo `@` se escribe `%40`); lo más simple es usar una contraseña solo con letras y números.
4. **Network Access** (menú izquierdo): pulsa **Add IP Address** y agrega tu IP actual con **Add Current IP Address**. Para pruebas rápidas también puedes permitir `0.0.0.0/0` (cualquier IP), pero no lo dejes así en producción.
5. **Database** (menú izquierdo): pulsa **Connect** en tu cluster, elige **Drivers** y copia la cadena de conexión. Se ve así:

```
mongodb+srv://<usuario>:<password>@cluster0.xxxxx.mongodb.net/
```

6. Reemplaza `<usuario>` y `<password>` por los datos del paso 3, sin dejar los símbolos `<` ni `>`.

No necesitas crear la base ni la colección a mano: el script del paso 8 lo hace.

### 6. Configurar el archivo `.env`

Copia la plantilla `.env.example copy` con el nombre `.env`:

```bash
# CMD
copy ".env.example copy" .env

# PowerShell, Mac y Linux
cp ".env.example copy" .env
```

Edita `.env` con los valores de tu entorno. Con XAMPP por defecto, queda así:

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=veterinaria

SECRET_KEY=una_frase_larga_y_secreta

MONGO_URI=mongodb+srv://TU_USUARIO:TU_PASSWORD@cluster0.xxxxx.mongodb.net/
MONGO_DB=veterinaria_nosql

UMBRAL_STOCK_BAJO=3
NOTIF_DIAS_RETENCION=30
```

- `DB_PASSWORD` se deja vacío si no le pusiste contraseña a `root` en XAMPP.
- `MONGO_URI` es la cadena que copiaste en el paso 5.
- El archivo `.env` está en `.gitignore`, por lo que no se sube al repositorio.

### 7. Ajuste de conexión para MariaDB (solo si hace falta)

XAMPP usa MariaDB, y algunas versiones del conector `mysql-connector-python` intentan usar una collation propia de MySQL 8 que MariaDB no conoce. Si al abrir el sitio aparece "No se pudo conectar con la base de datos" y en la terminal ves el error `1273 (HY000): Unknown collation: 'utf8mb4_0900_ai_ci'`, abre `db.py` y agrega la línea `collation` dentro de la función `_configuracion`:

```python
        "charset": "utf8mb4",
        "collation": "utf8mb4_unicode_ci",
        "connection_timeout": 5,
```

Esta collation es la misma que usa `schema.sql` y funciona tanto en MariaDB como en MySQL 8.

### 8. Crear la colección de notificaciones en Atlas

Con el entorno virtual activo y el `.env` listo, ejecuta una sola vez (es seguro repetirlo):

```bash
python database/mongo_setup.py
```

Debe imprimir que la colección `notificaciones` fue creada y que los índices fueron creados. Después, en Atlas puedes verla en **Database > Browse Collections**, dentro de la base `veterinaria_nosql`.

### 9. Ejecutar la aplicación

```bash
python app.py
```

Abre el navegador en:

- Catálogo: http://localhost:5000
- Portal de clientes: http://localhost:5000/cliente

Para detener el servidor, presiona `Ctrl + C` en la terminal.

### 10. Primer recorrido sugerido

1. Entra al portal de clientes y crea una cuenta (contraseña de al menos 8 caracteres).
2. Registra una mascota.
3. Agenda una cita: elige mascota, servicio, veterinario y una fecha que coincida con un día de atención del veterinario (los días se muestran junto a cada veterinario).
4. Revisa la campana de notificaciones en el portal y en la página principal.
5. En el catálogo, reserva un producto varias veces hasta que el stock baje del umbral y observa las notificaciones de stock bajo y sin cupos.
6. En Atlas, abre **Browse Collections** y confirma que los documentos aparecen en `notificaciones`.

## Uso diario

Cada vez que quieras trabajar con el proyecto:

1. Abre el XAMPP Control Panel y pulsa **Start** en **MySQL** (y en **Apache** si necesitas phpMyAdmin).
2. Abre una terminal en la carpeta del proyecto y activa el entorno virtual.
3. Ejecuta `python app.py` y abre http://localhost:5000.

Si tu IP cambia (por ejemplo, al usar otra red), recuerda agregar la nueva IP en **Network Access** de Atlas.

## Variables de entorno

| Variable | Obligatoria | Valor por defecto | Descripción |
|----------|-------------|-------------------|-------------|
| `DB_HOST` | No | `localhost` | Servidor de la base relacional (XAMPP) |
| `DB_PORT` | No | `3306` | Puerto de MySQL en XAMPP |
| `DB_USER` | No | `root` | Usuario de la base de datos |
| `DB_PASSWORD` | No | vacío | Contraseña del usuario. Vacía en la instalación por defecto de XAMPP |
| `DB_NAME` | No | `veterinaria` | Nombre de la base de datos |
| `SECRET_KEY` | Sí en producción | clave de desarrollo | Firma la cookie de sesión de los clientes. Usa una frase larga y secreta |
| `MONGO_URI` | Sí | ninguno | Cadena de conexión de MongoDB Atlas |
| `MONGO_DB` | No | `veterinaria_nosql` | Nombre de la base en MongoDB |
| `UMBRAL_STOCK_BAJO` | No | `3` | Stock a partir del cual se avisa de "stock bajo" |
| `NOTIF_DIAS_RETENCION` | No | `30` | Días que se conservan las notificaciones antes de que MongoDB las borre |
| `ZONA_HORARIA` | No | `America/Bogota` | Zona horaria de la clínica para validar y mostrar citas |

## Referencia de la API

Todas las respuestas son JSON con el campo `estado` (`"exito"` o `"error"`). Los errores incluyen `mensaje`.

### Catálogo

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/servicios` | Lista servicios y productos |
| POST | `/api/servicios/<id>/reservar` | Descuenta un cupo o unidad. Error 400 si no hay disponibilidad |
| PUT | `/api/servicios/<id>` | Reemplaza el elemento. Exige todos los campos: `nombre`, `descripcion`, `precio`, `icono`, `stock` |
| DELETE | `/api/servicios/<id>` | Elimina el elemento. Error 409 si tiene reservas o facturas asociadas |

El `<id>` lleva prefijo: `S1`, `S2`... para servicios y `P1`, `P2`... para productos. Un id inexistente devuelve 404.

### Notificaciones del equipo

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/notificaciones?solo_no_leidas=true&limite=20` | Lista notificaciones (límite máximo 100) |
| PATCH | `/api/notificaciones/<id>/leer` | Marca una como leída |
| PATCH | `/api/notificaciones/leer-todas` | Marca todas como leídas |

### Portal de clientes

Todas estas rutas, excepto registro, inicio de sesión y cierre de sesión, exigen sesión iniciada y responden 401 en caso contrario.

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/cliente/registro` | Crea la cuenta e inicia sesión |
| POST | `/api/cliente/login` | Inicia sesión con `correo` y `clave` |
| POST | `/api/cliente/logout` | Cierra la sesión |
| GET | `/api/cliente/mascotas` | Lista las mascotas del cliente |
| POST | `/api/cliente/mascotas` | Crea una mascota |
| DELETE | `/api/cliente/mascotas/<id>` | Elimina una mascota (409 si tiene citas o historial) |
| GET | `/api/cliente/servicios` | Lista los servicios con duración y precio |
| GET | `/api/cliente/veterinarios` | Lista veterinarios y sus días de atención |
| GET | `/api/cliente/disponibilidad?servicio=&veterinario=&fecha=&mascota=` | Horas libres para una fecha (`AAAA-MM-DD`) |
| GET | `/api/cliente/citas` | Lista las citas del cliente |
| POST | `/api/cliente/citas` | Agenda una cita (`mascota`, `servicio`, `veterinario`, `fecha`, `hora`) |
| PATCH | `/api/cliente/citas/<id>/cancelar` | Cancela una cita futura |
| GET | `/api/cliente/notificaciones` | Notificaciones del cliente |
| PATCH | `/api/cliente/notificaciones/<id>/leer` | Marca una como leída |
| PATCH | `/api/cliente/notificaciones/leer-todas` | Marca todas como leídas |

## Cómo probar la API con Postman

Con XAMPP (MySQL) encendido y el servidor corriendo (`python app.py`):

### 1. Listar servicios (GET)

- URL: `http://localhost:5000/api/servicios`
- Body: ninguno
- Resultado esperado: JSON con `estado: "exito"` y la lista de servicios y productos.

### 2. Reservar un servicio (POST)

- URL: `http://localhost:5000/api/servicios/S1/reservar`
- Body: ninguno
- Descuenta 1 del cupo del servicio `S1`. Si no quedan cupos, responde error 400.

### 3. Actualizar un servicio completo (PUT)

- URL: `http://localhost:5000/api/servicios/S1`
- Body: `raw` con tipo `JSON`:

```json
{
  "nombre": "Consulta General Veterinaria",
  "descripcion": "Revisión médica completa con veterinario certificado.",
  "precio": "90.000",
  "icono": "VET",
  "stock": 15
}
```

Se deben enviar todos los campos; si falta alguno, la API responde error 400. El campo `icono` admite hasta 10 caracteres.

### 4. Eliminar un servicio (DELETE)

- URL: `http://localhost:5000/api/servicios/S1`
- Body: ninguno
- Si el elemento tiene reservas o facturas asociadas, responde 409.

Cambia el id al final de la URL (`S1`, `S2`, `P1`, etc.) para probar con distintos registros. Con un id que no existe, la API responde 404 con `"mensaje": "Servicio no encontrado"`.

Para probar las rutas del portal de clientes en Postman, primero llama a `POST /api/cliente/login` con un body JSON `{"correo": "...", "clave": "..."}`; Postman conservará la cookie de sesión para las siguientes peticiones.

## Solución de problemas

| Síntoma | Causa probable y solución |
|---------|---------------------------|
| "No se pudo conectar con la base de datos" | El módulo MySQL de XAMPP no está iniciado, o los datos del `.env` no coinciden. Verifica que MySQL esté en verde en el Control Panel y revisa `DB_HOST`, `DB_USER`, `DB_PASSWORD` y `DB_NAME` |
| `1273: Unknown collation: 'utf8mb4_0900_ai_ci'` | MariaDB no reconoce la collation por defecto del conector. Aplica el ajuste del paso 7 en `db.py` |
| MySQL en XAMPP no inicia (puerto 3306 ocupado) | Hay otro servidor MySQL corriendo en tu equipo. Deténlo desde `services.msc`, o cambia el puerto de XAMPP en `my.ini` y pon el mismo valor en `DB_PORT` |
| `Access denied for user 'root'` | Le pusiste contraseña a `root` en XAMPP. Escríbela en `DB_PASSWORD` |
| `Unknown column 'Descripcion'` al cargar datos | Faltan las columnas del catálogo. Ejecuta el bloque `ALTER TABLE` del paso 2 de la sección 4 |
| `Duplicate column name 'ClaveHash'` | `migracion_app.sql` ya se ejecutó antes; no se debe repetir |
| "No se pudo conectar con MongoDB" o `ServerSelectionTimeoutError` | Tu IP no está en **Network Access** de Atlas, no tienes internet, o la red bloquea la conexión a Atlas (algunas redes de empresas o universidades lo hacen) |
| `Authentication failed` al ejecutar `mongo_setup.py` | Usuario o contraseña incorrectos en `MONGO_URI`, o la contraseña tiene caracteres especiales sin codificar |
| `Falta MONGO_URI en el archivo .env` | La variable no está definida o el archivo `.env` no está en la carpeta del proyecto |
| La campana muestra 0 siempre | MongoDB no está disponible o no se ejecutó `python database/mongo_setup.py` |
| `python` no se reconoce como comando | Python no está en el PATH. Reinstálalo marcando "Add Python to PATH", o prueba con `py` en lugar de `python` |
| PowerShell no deja activar el entorno virtual | Ejecuta `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` o usa CMD |
| Error de zona horaria en Windows | Instala `tzdata` con `pip install tzdata` (ya está en `requirements.txt`) |
| No aparecen horas disponibles | El veterinario no atiende ese día, la fecha ya pasó, o las horas ya están ocupadas. Revisa la tabla `HORARIO` en phpMyAdmin |

## Notas de seguridad

- Nunca subas el archivo `.env` al repositorio y no dejes credenciales reales en `.env.example`. Si una contraseña o cadena de conexión ya quedó expuesta en un archivo versionado, cámbiala en MongoDB Atlas (**Database Access > Edit**).
- Define siempre una `SECRET_KEY` propia; la clave por defecto es solo para desarrollo.
- El `root` de XAMPP sin contraseña es aceptable solo en tu equipo local. Si el equipo se comparte o se expone a una red, ponle contraseña desde phpMyAdmin (**Cuentas de usuarios**) y actualiza `DB_PASSWORD`.
- Para permitir acceso solo a la aplicación, puedes crear un usuario con permisos mínimos desde la pestaña **SQL** de phpMyAdmin:

```sql
CREATE USER 'vete_app'@'localhost' IDENTIFIED BY 'una_clave_segura';
GRANT SELECT, INSERT, UPDATE, DELETE ON veterinaria.* TO 'vete_app'@'localhost';
```

  Luego usa ese usuario en `DB_USER` y `DB_PASSWORD`.
- Evita dejar `0.0.0.0/0` en **Network Access** de Atlas fuera de pruebas.
- `app.run(debug=True, host='0.0.0.0')` es solo para desarrollo. Para producción usa un servidor WSGI como Waitress o Gunicorn, con `debug` desactivado. Además, Apache y XAMPP no están pensados para producción.
