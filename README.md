# PawCare - Sistema web para veterinaria
 
Aplicación web hecha con Flask para que los clientes de una veterinaria creen su cuenta, registren a sus mascotas, agenden citas en línea y compren productos desde una tienda con carrito. Los veterinarios tienen su propio portal para ver sus citas y consultar el historial clínico, y el administrador gestiona el catálogo desde un panel protegido. El acceso se controla con contraseñas con hash, sesiones con JWT y tres roles (Cliente, Veterinario y Administrador). Usa dos bases de datos: MySQL (a través de XAMPP) para los datos estructurados y MongoDB Atlas, en la nube, para las notificaciones.
 
## Contenido
 
1. [Qué hace el proyecto](#qué-hace-el-proyecto)
2. [Capturas de pantalla](#capturas-de-pantalla)
3. [Tecnologías](#tecnologías)
4. [Estructura del proyecto](#estructura-del-proyecto)
5. [Cómo funciona](#cómo-funciona)
6. [Requisitos previos](#requisitos-previos)
7. [Instalación y ejecución](#instalación-y-ejecución)
8. [Uso diario](#uso-diario)
9. [Variables de entorno](#variables-de-entorno)
10. [Referencia de la API](#referencia-de-la-api)
11. [Cómo probar la API con Postman](#cómo-probar-la-api-con-postman)
12. [Solución de problemas](#solución-de-problemas)
13. [Notas de seguridad](#notas-de-seguridad)
## Qué hace el proyecto
 
El flujo es: primero la persona **crea su cuenta o inicia sesión** y, una vez dentro, el sistema la lleva al portal que corresponde a su rol. Al abrir `http://localhost:5000` el sitio lleva siempre al ingreso.
 
**Portal de clientes (`/cliente`)**
- Registro e inicio de sesión de clientes (contraseña almacenada con hash).
- Gestión de mascotas: crear y eliminar.
- Agenda de citas: el cliente elige mascota, servicio, veterinario y fecha, y el sistema le muestra solo las horas realmente libres.
- Listado de citas y cancelación de citas futuras.
- **Tienda**: catálogo de productos con carrito de compras, control de cantidades y validación de stock.
- **Mis compras**: historial de pedidos con el detalle de cada uno.
- Campana de notificaciones propia de cada cliente.
**Portal del veterinario (`/veterinario`)**
- Ingreso desde la pestaña **Soy veterinario** del formulario común. Las cuentas no se crean desde la página: se dan de alta con un script (o vienen en los datos de ejemplo).
- **Mis citas**: lista de las citas asignadas al veterinario que inició sesión.
- **Buscar mascota** por nombre de la mascota o del dueño, y consulta de su ficha con el historial clínico y el historial de citas.
- Registro de una atención (diagnóstico y tratamiento) sobre una cita propia. Esta función está disponible en la API; la página todavía no tiene formulario para ella.
**Panel de administración (`/equipo`)**
- Solo para el rol Administrador. No tiene formulario de ingreso propio: el administrador entra por el formulario de clientes o por el de veterinarios y siempre termina aquí.
- Muestra servicios y productos en una sola lista, con filtros por tipo.
- Permite reservar (descuenta un cupo o una unidad), editar y eliminar elementos del catálogo.
- Incluye una campana de notificaciones para el equipo de la clínica (citas, compras y alertas de stock).
## Capturas de pantalla
 
### Agendar una cita
El cliente elige mascota, servicio, veterinario y día; el resumen de la derecha se completa a medida que avanza.
 
![Agendar cita](docs/capturas/01-agendar-cita.png)
 
### Tienda y carrito
Catálogo de productos con stock disponible. El carrito, a la derecha, muestra las líneas, el total y el botón para confirmar la compra.
 
![Tienda](docs/capturas/02-tienda.png)
 
### Mis citas
Próximas citas con el día y la hora destacados, y la opción de cancelarlas.
 
![Mis citas](docs/capturas/03-mis-citas.png)
 
### Mis compras
Historial de pedidos del cliente. Cuando todavía no ha comprado nada, ofrece un acceso directo a la tienda.
 
![Mis compras](docs/capturas/04-mis-compras.png)
 
### Notificaciones
Cada cliente tiene su propia campana. Las notificaciones de citas destacan el día y la hora del servicio.
 
![Notificaciones](docs/capturas/05-notificaciones.png)
 
## Tecnologías
 
| Componente | Tecnología |
|------------|-----------|
| Backend | Python 3.9 o superior, Flask 3.1 |
| Autenticación | Contraseñas con hash scrypt (`werkzeug.security`) y sesiones con JWT HS256 (`PyJWT`) en una cookie HttpOnly |
| Autorización | Control de acceso por roles (RBAC) con decoradores propios en `auth.py` |
| Base relacional | MySQL de XAMPP, que en realidad es MariaDB (`mysql-connector-python`) |
| Administración de la base | phpMyAdmin (incluido en XAMPP) |
| Base NoSQL | MongoDB Atlas, en la nube (`pymongo`) |
| Configuración | `python-dotenv` |
| Frontend | HTML con plantillas Jinja2, CSS y JavaScript sin frameworks |
 
## Estructura del proyecto
 
```
VeteNtd-main/
├── app.py                     Aplicación Flask: redirección de inicio, panel de administración (/equipo), catálogo y notificaciones del equipo
├── auth.py                    JWT, cookie de sesión, roles y decoradores que protegen las rutas
├── admin.py                   Atajo /admin y cierre de sesión del administrador
├── clientes.py                Blueprint del portal de clientes (cuenta, mascotas, citas, tienda y compras)
├── veterinarios.py            Blueprint del portal del veterinario (ingreso, citas propias e historial clínico)
├── notificaciones.py          Lógica de la colección de notificaciones en MongoDB
├── db.py                      Conexión a MySQL/MariaDB y funciones de consulta y transacción
├── mongo.py                   Conexión a MongoDB Atlas
├── requirements.txt           Dependencias de Python
├── .env.example copy          Plantilla de variables de entorno
├── database/
│   ├── schema.sql             Esquema completo (15 tablas: catálogo, tienda y cuentas incluidos) y cuenta de administrador de demostración
│   ├── datos_ejemplo.sql      Servicios, productos, veterinarios con horarios, clientes, mascotas, citas e historial de ejemplo
│   ├── crear_administrador.py Crea o actualiza la cuenta del administrador
│   ├── crear_veterinario.py   Crea o actualiza la cuenta de un veterinario
│   └── mongo_setup.py         Crea la colección de notificaciones, validación e índices
├── docs/
│   └── capturas/              Capturas de pantalla que usa este README
├── static/
│   ├── comun.js               Utilidades compartidas (llamadas a la API, avisos, campana)
│   └── estilos.css            Estilos del sitio
├── templates/
│   ├── index.html             Panel de administración (catálogo administrable)
│   ├── cliente.html           Portal de clientes e ingreso común (Ingresar, Crear cuenta y Soy veterinario)
│   └── veterinario.html       Portal del veterinario (citas, búsqueda de mascotas e historial)
└── AppFlask.zip               Prototipo inicial; no es necesario para ejecutar el proyecto
```
 
El proyecto no se copia dentro de la carpeta `htdocs` de XAMPP. Flask trae su propio servidor, por lo que Apache no es necesario para correr la aplicación; solo se usa para abrir phpMyAdmin.
 
## Cómo funciona
 
### Dos bases de datos
 
| Base | Dónde corre | Qué guarda | Motivo |
|------|-------------|-----------|--------|
| `veterinaria` (MySQL/MariaDB) | Tu equipo, con XAMPP | Servicios, productos, clientes, cuentas de usuario, mascotas, empleados, horarios, reservas, historial clínico, pedidos, facturas | Datos estructurados con relaciones y transacciones |
| `veterinaria_nosql` (MongoDB) | MongoDB Atlas, en la nube | Colección `notificaciones` | Datos dinámicos, de alta frecuencia y sin esquema rígido |
 
Si MongoDB falla, la aplicación sigue funcionando: la reserva, la cita o la compra se guardan igual en MySQL y solo se pierde la notificación, que queda registrada en el log.
 
### Flujo de acceso
 
1. `GET /` redirige siempre a `/cliente`.
2. Sin sesión, `/cliente` muestra las pestañas **Ingresar**, **Crear cuenta** y **Soy veterinario**.
3. Al registrarse o iniciar sesión, el sistema lleva a cada persona a su portal según su rol: el cliente se queda en `/cliente`, el veterinario va a `/veterinario` y el administrador va a `/equipo`.
4. Si alguien con sesión abre el portal de otro rol, lo redirige al suyo (por ejemplo, un veterinario que abre `/cliente` termina en `/veterinario`).
5. Cada ruta de la API exige una sesión del rol correspondiente. Sin ella, las rutas `/api/...` responden 401 con un mensaje que indica qué rol hace falta, y las páginas (`/equipo`) redirigen al ingreso.
### Catálogo unificado con ids con prefijo
 
El panel de administración mezcla dos tablas distintas, `CATALOGO_SERVICIOS` y `PRODUCTOS`. Para que los ids no choquen, cada elemento usa un prefijo:
 
- `S1` es el servicio con `ID_CataServicio = 1`.
- `P1` es el producto con `ID_Producto = 1`.
Los nombres de tabla y columna salen de un diccionario fijo en `app.py`, nunca de datos enviados por el usuario. Los valores siempre se pasan como parámetros SQL.
 
### Reservas del catálogo (panel de administración)
 
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
### Tienda y compras
 
- El cliente agrega productos al carrito desde la pestaña **Tienda**. El carrito vive en el navegador hasta que se confirma la compra. Se permiten hasta 10 unidades por producto y 20 productos distintos por pedido.
- Al confirmar, `POST /api/cliente/compras` abre una única transacción. Por cada producto, en orden de id, bloquea la fila con `SELECT ... FOR UPDATE`, verifica que haya stock y lo descuenta. Al final inserta el pedido en `PEDIDOS` y sus líneas en `PEDIDO_DETALLE`.
- Si falta stock de **cualquier** producto, se hace rollback de toda la compra (no queda nada descontado) y la API responde 409 indicando cuántas unidades quedan.
- El precio se toma de la base de datos en el momento de la compra, nunca del navegador, y se guarda en `PrecioUnitario` para conservar el histórico.
- El pedido queda con estado `Confirmado` y el pago se hace al recoger en la clínica. El proyecto no integra pasarela de pago.
- Cada compra genera notificaciones: una para el cliente, una para el equipo y, si el stock queda bajo o en cero, alertas de `stock_bajo` o `sin_cupos` para el equipo.
### Cuentas y contraseñas
 
- **Clientes:** se registran solos desde la pestaña **Crear cuenta**. El registro valida nombre, teléfono, dirección, correo (único) y una contraseña de al menos 8 caracteres.
- **Veterinarios y administrador:** no hay registro desde la página. Sus cuentas viven en la tabla `EMPLEADO` (correo en `CorreoEmpleado`, contraseña en `ClaveHash`). Los archivos SQL traen cuentas de demostración (los veterinarios en `datos_ejemplo.sql` y un administrador en `schema.sql`), y se pueden crear o actualizar con los scripts `database/crear_veterinario.py` y `database/crear_administrador.py`.
- Las contraseñas nunca se guardan en texto plano: se almacenan con `generate_password_hash` de Werkzeug (scrypt) en la columna `ClaveHash`, y el ingreso las comprueba con `check_password_hash`.
- Al registrarse, el cliente queda en `CLIENTE` (la tabla que consulta el ingreso) y se registra una copia con su rol en `USUARIOS`, también solo con el hash.
- Los mensajes de error del ingreso no revelan si falló el correo o la contraseña: siempre dicen "Correo o contraseña incorrectos".
### Sesión con JWT
 
Al iniciar sesión, el servidor crea un token JWT firmado con HS256 y lo entrega en una cookie llamada `access_token`.
 
- El token lleva `sub` (el id de quien ingresó: `ID_Cliente` para clientes, `ID_Empleado` para veterinarios y administrador), `rol` (`Cliente`, `Veterinario` o `Administrador`), `iat` y `exp`. El rol decide a qué tabla corresponde el id.
- La cookie es `HttpOnly` (el JavaScript de la página no puede leerla), `SameSite=Lax` y dura lo mismo que el token (`JWT_EXP_MINUTOS`, 60 por defecto). Con `COOKIE_SECURE=1` solo viaja por HTTPS.
- En cada petición protegida se verifica la firma y que el token tenga `exp` y `sub`. Un token expirado, manipulado, firmado con otra clave o sin fecha de expiración se trata como si no hubiera sesión.
- La clave de firma sale de `JWT_SECRET_KEY` en el `.env`. No tiene valor por defecto: sin ella el ingreso falla con un error claro.
- Cerrar sesión borra la cookie del navegador.
### Roles y permisos (RBAC)
 
El proyecto define tres roles. Cada uno tiene su decorador en el código (`requiere_cliente`, `requiere_veterinario` y `solo_admin`) y solo ve las rutas de su propio grupo.
 
| Rol | Cómo obtiene la cuenta | Dónde ingresa | Su página | Qué puede hacer |
|-----|------------------------|---------------|-----------|-----------------|
| Cliente | Se registra en `/cliente` | Pestaña **Ingresar** | `/cliente` | Gestionar sus mascotas, agendar y cancelar sus citas, comprar en la tienda y leer sus notificaciones. Solo ve datos propios |
| Veterinario | Viene en `datos_ejemplo.sql` o se crea con `crear_veterinario.py` (cargo `Veterinario` o `Veterinaria`) | Pestaña **Soy veterinario** | `/veterinario` | Ver sus citas, buscar mascotas, consultar historiales y registrar atenciones en citas propias |
| Administrador | Viene de demostración en `schema.sql`; se reemplaza con `crear_administrador.py` (cargo `Administrador`) | Cualquiera de los dos formularios | `/equipo` | Listar, reservar, editar y eliminar el catálogo, y leer las notificaciones del equipo |
 
Qué responde cada grupo de rutas según la sesión:
 
| Grupo de rutas | Sin sesión | Cliente | Veterinario | Administrador |
|----------------|------------|---------|-------------|---------------|
| `/api/cliente/...` (salvo registro, login y logout) | 401 | Permitido | 401 | 401 |
| `/api/veterinario/...` (salvo login y logout) | 401 | 401 | Permitido | 401 |
| `/api/servicios/...`, `/api/notificaciones/...` y la página `/equipo` | 401 (la página redirige a `/cliente`) | 401 | 401 | Permitido |
 
Además del rol, hay controles de pertenencia a los datos:
- Un cliente solo puede ver y modificar sus propias mascotas, citas, compras y notificaciones. Si intenta tocar un recurso de otro cliente, la API responde 404.
- Un veterinario solo puede registrar una atención sobre una cita que tiene asignada y que corresponde a la mascota indicada; si no, responde 403.
### Notificaciones (MongoDB Atlas)
 
Cada notificación es un documento con tipo, título, mensaje, prioridad, estado de lectura, fecha, referencia al elemento del catálogo (`item`), datos libres (`datos`) y un `cliente_id`.
 
- Si `cliente_id` es `null`, la notificación es del equipo y aparece en el panel de administración.
- Si tiene un id, pertenece a ese cliente y aparece en su portal. Cada quien lleva su propio estado de "leída".
Tipos que se generan automáticamente:
 
| Tipo | Cuándo se genera |
|------|------------------|
| `reserva_creada` | Se reserva un servicio o producto desde el panel de administración |
| `stock_bajo` | El stock queda igual o por debajo de `UMBRAL_STOCK_BAJO` |
| `sin_cupos` | El stock llega a 0 |
| `servicio_actualizado` | Se edita un elemento del catálogo |
| `servicio_eliminado` | Se elimina un elemento del catálogo |
| `cita_agendada` | Un cliente agenda una cita (una para el cliente y otra para el equipo) |
| `cita_cancelada` | Un cliente cancela una cita (una para el cliente y otra para el equipo) |
| `compra_realizada` | Un cliente confirma una compra (una para el cliente y otra para el equipo) |
 
La colección tiene validación de esquema (`$jsonSchema`) e índices por lectura y fecha. Además tiene un índice TTL: MongoDB borra solo las notificaciones con más de 30 días (configurable con `NOTIF_DIAS_RETENCION`).
 
## Requisitos previos
 
- **XAMPP** instalado (https://www.apachefriends.org). Se usa el módulo MySQL y phpMyAdmin.
- **Python 3.9 o superior**. En Windows, al instalarlo marca la casilla "Add Python to PATH".
- **Una cuenta de MongoDB Atlas** (https://www.mongodb.com/cloud/atlas). El plan gratuito es suficiente.
- Conexión a internet, porque las notificaciones viven en Atlas.
- Opcional: VS Code y Postman.
Nota sobre XAMPP: el "MySQL" de XAMPP es MariaDB. Es compatible con los scripts del proyecto, pero en algunas versiones hay un detalle de conexión que se explica en el paso 7 de la instalación.
 
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
 
`schema.sql` ya trae todo lo necesario: crea la base `veterinaria`, las 15 tablas (con las columnas del catálogo, las tablas de la tienda y la de cuentas de usuario) y una cuenta de administrador de demostración con `ID_Empleado = 100`. No hace falta crear ni seleccionar la base antes, y no hay migraciones adicionales.
 
Importa los archivos **uno por uno y en este orden**. Para cada uno: pestaña **Importar**, botón **Seleccionar archivo**, elige el archivo de la carpeta `database/` y pulsa **Importar** al final de la página.
 
| Orden | Archivo | Qué logra |
|-------|---------|-----------|
| 1 | `schema.sql` | Crea la base y las 15 tablas, y deja el administrador de demostración. Cada vez que lo importas, borra y recrea las tablas, así que sirve también para empezar de cero |
| 2 | `datos_ejemplo.sql` | Inserta 5 servicios, 5 productos, 3 veterinarios con sus horarios, 4 clientes, 6 mascotas, 13 citas y 7 registros de historial clínico. Omítelo si prefieres empezar sin datos |
 
El administrador usa un id alto fijo (100) para no chocar con los veterinarios de ejemplo, que usan los ids 1, 2 y 3.
 
**Verificación.** Al terminar, en el panel izquierdo de phpMyAdmin debe aparecer la base `veterinaria` con 15 tablas. Entra a `CATALOGO_SERVICIOS` y `PRODUCTOS` y comprueba que tengan datos, y a `EMPLEADO` para ver los tres veterinarios y el administrador.
 
**Alternativa por consola (opcional).** Si prefieres la terminal, abre el cliente de XAMPP y carga los archivos con `source`, que funciona igual en CMD y en PowerShell y respeta las tildes y emojis de los datos de ejemplo:
 
```bash
C:\xampp\mysql\bin\mysql.exe -u root --default-character-set=utf8mb4
```
 
```sql
source database/schema.sql
source database/datos_ejemplo.sql
```
 
No uses el operador `<` en PowerShell: no está soportado para redirigir archivos.
 
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
 
Genera una clave secreta para firmar los tokens de sesión (JWT). Ejecuta este comando y copia el resultado:
 
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
 
Edita `.env` con los valores de tu entorno. Con XAMPP por defecto, queda así:
 
```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=
DB_NAME=veterinaria
 
JWT_SECRET_KEY=pega_aquí_la_clave_generada
JWT_EXP_MINUTOS=60
COOKIE_SECURE=0
 
MONGO_URI=mongodb+srv://TU_USUARIO:TU_PASSWORD@cluster0.xxxxx.mongodb.net/
MONGO_DB=veterinaria_nosql
 
UMBRAL_STOCK_BAJO=3
NOTIF_DIAS_RETENCION=30
```
 
- `DB_PASSWORD` se deja vacío si no le pusiste contraseña a `root` en XAMPP.
- `JWT_SECRET_KEY` es la clave que generaste. Es obligatoria: sin ella no funciona el inicio de sesión.
- `COOKIE_SECURE` se queda en `0` mientras uses la aplicación por HTTP (sin HTTPS), como en local. Pásalo a `1` solo cuando publiques el sitio con HTTPS.
- `MONGO_URI` es la cadena que copiaste en el paso 5.
- La plantilla `.env.example copy` todavía incluye una línea `SECRET_KEY`: ya no se usa y puedes borrarla.
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
 
Si actualizas el proyecto y se agregan tipos nuevos de notificación (como `compra_realizada`), vuelve a ejecutar este script para que el validador de la colección los acepte.
 
### 9. Cambiar la contraseña del administrador (y, si quieres, crear más veterinarios)
 
`schema.sql` ya dejó un administrador de demostración (`admin@pawcare.com`) con una contraseña pública, escrita en un comentario de ese archivo. Para usar tu propia contraseña, con el entorno virtual activo, el `.env` listo y MySQL encendido, ejecuta:
 
```bash
python database/crear_administrador.py
```
 
El script te pide un nombre, un correo (será tu usuario para ingresar) y una contraseña de al menos 8 caracteres, y guarda solo el hash. Es seguro repetirlo:
 
- Si escribes el correo `admin@pawcare.com`, solo se reemplaza la contraseña de ese administrador (el nombre no cambia). Es la forma de dejar de usar la contraseña de demostración.
- Si escribes otro correo, se crea un segundo administrador y el de demostración sigue activo con su contraseña pública. En ese caso bórralo desde phpMyAdmin (tabla `EMPLEADO`, fila con `CorreoEmpleado = 'admin@pawcare.com'`) o cámbiale la contraseña.
- Si el correo lo usa un empleado que no es administrador, no cambia nada.
Para crear otro veterinario, o cambiar el correo y la contraseña de uno de los de ejemplo:
 
```bash
python database/crear_veterinario.py
```
 
Pide el nombre completo. Si ya existe un veterinario con ese nombre, le asigna el correo y la contraseña; si no, lo crea con el cargo `Veterinario` o `Veterinaria`. Un veterinario nuevo todavía no tiene horarios: para que los clientes puedan agendar con él, agrégalos en la tabla `HORARIO` desde phpMyAdmin.
 
### 10. Ejecutar la aplicación
 
```bash
python app.py
```
 
Abre el navegador en:
 
- Inicio (te lleva al ingreso común): http://localhost:5000
- Portal de clientes: http://localhost:5000/cliente
- Portal del veterinario: http://localhost:5000/veterinario
- Panel de administración: http://localhost:5000/equipo (o el atajo http://localhost:5000/admin)
Las páginas de veterinario y de administración no tienen un formulario de ingreso propio: si abres una sin sesión, te devuelven al ingreso común de `/cliente`.
 
Para detener el servidor, presiona `Ctrl + C` en la terminal.
 
### 11. Primer recorrido sugerido
 
Cuentas con las que puedes ingresar:
 
| Rol | Correo | Contraseña |
|-----|--------|-----------|
| Cliente | El que registres en **Crear cuenta** | La que elijas (mínimo 8 caracteres). Los 4 clientes de ejemplo no tienen contraseña, así que no pueden ingresar |
| Veterinario | `laura@pawcare.com` | `Laura#Vet2026` |
| Veterinario | `andres@pawcare.com` | `Andres#Vet2026` |
| Veterinario | `camila@pawcare.com` | `Camila#Vet2026` |
| Administrador | `admin@pawcare.com` | `Admin#PawCare2026`, o la que definiste en el paso 9 |
 
Las contraseñas del administrador y de los veterinarios son de demostración y están escritas en `schema.sql` y en el encabezado de `datos_ejemplo.sql`; cámbialas con `crear_administrador.py` y `crear_veterinario.py` antes de publicar el proyecto.
 
1. Abre http://localhost:5000, entra a **Crear cuenta** y regístrate como cliente.
2. Registra una mascota en la pestaña **Mis mascotas**.
3. Agenda una cita: elige mascota, servicio, veterinario y una fecha que coincida con un día de atención del veterinario (los días se muestran junto a cada veterinario).
4. Ve a la pestaña **Tienda**, agrega productos al carrito y confirma la compra. Revisa el detalle en **Mis compras** y las notificaciones en la campana del portal.
5. Cierra sesión. En la pestaña **Soy veterinario**, ingresa como Laura: verás sus citas, podrás buscar una mascota y abrir su historial clínico.
6. Cierra sesión e ingresa como administrador (por cualquiera de los dos formularios): llegas al panel `/equipo`. Revisa la campana de notificaciones del equipo.
7. Compra un producto varias veces desde una cuenta de cliente hasta que el stock baje del umbral y observa las notificaciones de stock bajo y sin stock en el panel de administración.
8. Prueba los roles: con la sesión de un cliente, escribe `http://localhost:5000/equipo` en el navegador. Debe devolverte a `/cliente`, porque ese rol no tiene acceso al panel.
9. En Atlas, abre **Browse Collections** y confirma que los documentos aparecen en `notificaciones`.
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
| `JWT_SECRET_KEY` | Sí | ninguno | Clave con la que se firman los tokens de sesión. Sin ella el inicio de sesión falla. Genera una con `python -c "import secrets; print(secrets.token_hex(32))"` |
| `JWT_EXP_MINUTOS` | No | `60` | Minutos de vigencia del token y de la cookie de sesión |
| `COOKIE_SECURE` | No | `0` | Con `1`, la cookie de sesión solo viaja por HTTPS. Déjalo en `0` mientras uses HTTP (por ejemplo en local) y pásalo a `1` al publicar con HTTPS |
| `MONGO_URI` | Sí | ninguno | Cadena de conexión de MongoDB Atlas |
| `MONGO_DB` | No | `veterinaria_nosql` | Nombre de la base en MongoDB |
| `UMBRAL_STOCK_BAJO` | No | `3` | Stock a partir del cual se avisa de "stock bajo" |
| `NOTIF_DIAS_RETENCION` | No | `30` | Días que se conservan las notificaciones antes de que MongoDB las borre |
| `ZONA_HORARIA` | No | `America/Bogota` | Zona horaria de la clínica para validar y mostrar citas y compras |
| `FLASK_DEBUG` | No | vacío | Con `1`, activa el depurador de Flask. Solo para desarrollo y nunca en una red compartida |
 
## Referencia de la API
 
Todas las respuestas son JSON con el campo `estado` (`"exito"` o `"error"`). Los errores incluyen `mensaje`.
 
La sesión viaja en la cookie `access_token`, que el servidor entrega al iniciar sesión; no hay que enviar ningún encabezado `Authorization`. Cuando falta la sesión del rol que pide la ruta, la API responde **401** (no 403) con un mensaje como "Inicia sesión como administrador".
 
### Catálogo (panel de administración)
 
Requieren sesión de **Administrador**.
 
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/servicios` | Lista servicios y productos |
| POST | `/api/servicios/<id>/reservar` | Descuenta un cupo o unidad. Error 400 si no hay disponibilidad |
| PUT | `/api/servicios/<id>` | Reemplaza el elemento. Exige todos los campos: `nombre`, `descripcion`, `precio`, `icono`, `stock` |
| DELETE | `/api/servicios/<id>` | Elimina el elemento. Error 409 si tiene reservas, facturas o compras asociadas |
 
El `<id>` lleva prefijo: `S1`, `S2`... para servicios y `P1`, `P2`... para productos. Un id inexistente devuelve 404.
 
### Notificaciones del equipo
 
Requieren sesión de **Administrador**.
 
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/notificaciones?solo_no_leidas=true&limite=20` | Lista notificaciones (límite máximo 100) |
| PATCH | `/api/notificaciones/<id>/leer` | Marca una como leída |
| PATCH | `/api/notificaciones/leer-todas` | Marca todas como leídas |
 
### Administración
 
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/admin` | Atajo: con sesión de administrador redirige a `/equipo`; si no, al ingreso común |
| POST | `/api/admin/logout` | Cierra la sesión del administrador (borra la cookie) |
 
El administrador inicia sesión con `POST /api/cliente/login` o con `POST /api/veterinario/login`. En ambos casos la respuesta incluye `"destino": "/equipo"`.
 
### Portal de clientes
 
Todas estas rutas, excepto registro, inicio de sesión y cierre de sesión, exigen sesión de **Cliente** y responden 401 en caso contrario.
 
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/cliente/registro` | Crea la cuenta e inicia sesión. Body: `nombre`, `contacto`, `direccion`, `correo`, `clave` (mínimo 8 caracteres). Error 409 si el correo ya existe |
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
| GET | `/api/cliente/productos` | Lista los productos con precio y stock disponible |
| GET | `/api/cliente/compras` | Lista las compras del cliente (las 50 más recientes) con su detalle |
| POST | `/api/cliente/compras` | Confirma una compra. Body: `{"items": [{"producto": 1, "cantidad": 2}]}`. Error 409 si no hay stock suficiente |
| GET | `/api/cliente/notificaciones` | Notificaciones del cliente |
| PATCH | `/api/cliente/notificaciones/<id>/leer` | Marca una como leída |
| PATCH | `/api/cliente/notificaciones/leer-todas` | Marca todas como leídas |
 
### Portal del veterinario
 
Todas estas rutas, excepto inicio y cierre de sesión, exigen sesión de **Veterinario** y responden 401 en caso contrario.
 
| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/veterinario/login` | Inicia sesión con `correo` y `clave`. Solo cuentas con cargo `Veterinario` o `Veterinaria` (o el administrador, que va a `/equipo`) |
| POST | `/api/veterinario/logout` | Cierra la sesión |
| GET | `/api/veterinario/citas` | Lista las citas asignadas al veterinario, con mascota, cliente y servicio |
| GET | `/api/veterinario/mascotas?q=texto` | Busca mascotas por nombre de la mascota o del dueño (máximo 50 resultados) |
| GET | `/api/veterinario/mascotas/<id>/historial` | Ficha de la mascota con su historial clínico y su historial de citas. 404 si no existe |
| POST | `/api/veterinario/mascotas/<id>/historial` | Registra una atención. Body: `reserva_id`, `diagnostico`, `tratamiento` (máximo 500 caracteres cada uno). Error 403 si la cita no es del veterinario o no corresponde a esa mascota |
 
## Cómo probar la API con Postman
 
Con XAMPP (MySQL) encendido y el servidor corriendo (`python app.py`). Postman guarda la cookie de sesión y la reenvía en las siguientes peticiones, así que basta con iniciar sesión una vez. Como todos los roles comparten el mismo nombre de cookie, al iniciar sesión con otro rol la cookie anterior se reemplaza.
 
### 1. Iniciar sesión como administrador (POST)
 
Las rutas del catálogo exigen sesión de administrador, así que este es el primer paso. Usa las credenciales de demostración o las que definiste en el paso 9 de la instalación.
 
- URL: `http://localhost:5000/api/cliente/login`
- Body: `raw` con tipo `JSON`:
```json
{
  "correo": "admin@pawcare.com",
  "clave": "Admin#PawCare2026"
}
```
 
- Resultado esperado: `estado: "exito"` y `"destino": "/equipo"`. Con una clave incorrecta responde 401.
### 2. Listar servicios (GET)
 
- URL: `http://localhost:5000/api/servicios`
- Body: ninguno
- Resultado esperado: JSON con `estado: "exito"` y la lista de servicios y productos.
### 3. Reservar un servicio (POST)
 
- URL: `http://localhost:5000/api/servicios/S1/reservar`
- Body: ninguno
- Descuenta 1 del cupo del servicio `S1`. Si no quedan cupos, responde error 400.
### 4. Actualizar un servicio completo (PUT)
 
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
 
### 5. Eliminar un servicio (DELETE)
 
- URL: `http://localhost:5000/api/servicios/S1`
- Body: ninguno
- Si el elemento tiene reservas o facturas asociadas, responde 409.
Cambia el id al final de la URL (`S1`, `S2`, `P1`, etc.) para probar con distintos registros. Con un id que no existe, la API responde 404 con `"mensaje": "Servicio no encontrado"`.
 
### 6. Rutas del portal de clientes
 
Llama a `POST /api/cliente/login` con un body JSON `{"correo": "...", "clave": "..."}` usando una cuenta de cliente (o créala antes con `POST /api/cliente/registro`). Desde ese momento puedes llamar a las rutas `/api/cliente/...`.
 
### 7. Comprar productos (POST)
 
Con la sesión de cliente iniciada:
 
- URL: `http://localhost:5000/api/cliente/compras`
- Body: `raw` con tipo `JSON`:
```json
{
  "items": [
    { "producto": 1, "cantidad": 2 },
    { "producto": 5, "cantidad": 1 }
  ]
}
```
 
- Resultado esperado: `estado: "exito"` y el pedido con su total y sus líneas.
- Si pides más unidades de las que hay, responde 409 con el mensaje de cuántas quedan y no se descuenta nada.
### 8. Rutas del veterinario
 
Inicia sesión con `POST /api/veterinario/login` y el body `{"correo": "laura@pawcare.com", "clave": "Laura#Vet2026"}`. Después prueba:
 
- `GET http://localhost:5000/api/veterinario/citas`: sus citas.
- `GET http://localhost:5000/api/veterinario/mascotas?q=a`: búsqueda de mascotas.
- `GET http://localhost:5000/api/veterinario/mascotas/1/historial`: ficha de una mascota.
### 9. Comprobar los permisos por rol
 
Con la sesión de veterinario o de cliente activa, repite `GET http://localhost:5000/api/servicios`: debe responder 401 con "Inicia sesión como administrador". Con la sesión de cliente, `GET http://localhost:5000/api/veterinario/citas` también responde 401. Para comprobar que sin sesión no se entra, cierra la sesión con `POST /api/cliente/logout` y repite cualquier ruta protegida.
 
## Solución de problemas
 
| Síntoma | Causa probable y solución |
|---------|---------------------------|
| "No se pudo conectar con la base de datos" | El módulo MySQL de XAMPP no está iniciado, o los datos del `.env` no coinciden. Verifica que MySQL esté en verde en el Control Panel y revisa `DB_HOST`, `DB_USER`, `DB_PASSWORD` y `DB_NAME` |
| `1273: Unknown collation: 'utf8mb4_0900_ai_ci'` | MariaDB no reconoce la collation por defecto del conector. Aplica el ajuste del paso 7 en `db.py` |
| MySQL en XAMPP no inicia (puerto 3306 ocupado) | Hay otro servidor MySQL corriendo en tu equipo. Deténlo desde `services.msc`, o cambia el puerto de XAMPP en `my.ini` y pon el mismo valor en `DB_PORT` |
| `Access denied for user 'root'` | Le pusiste contraseña a `root` en XAMPP. Escríbela en `DB_PASSWORD` |
| `Unknown column 'Descripcion'` o `Table 'veterinaria.PEDIDOS' doesn't exist` | La base se creó con un `schema.sql` incompleto o antiguo. Importa de nuevo el `schema.sql` actual de la carpeta `database/` |
| La tienda o "Mis compras" no cargan | Casi siempre es lo mismo: faltan las tablas de pedidos. Importa de nuevo `schema.sql` (y luego `datos_ejemplo.sql`) y recarga la página |
| `RuntimeError: Define JWT_SECRET_KEY en el .env` (o error 500 al iniciar sesión) | Falta `JWT_SECRET_KEY` en el `.env`. Genera una clave con `python -c "import secrets; print(secrets.token_hex(32))"`, pégala en el `.env` y reinicia la app |
| Inicio sesión y la página me devuelve al ingreso | La cookie no se está guardando o ya expiró. Si entras por HTTP (sin HTTPS), por ejemplo desde otro equipo de tu red, deja `COOKIE_SECURE=0`: con `1` el navegador no envía la cookie. Además la sesión dura `JWT_EXP_MINUTOS` (60 por defecto) |
| "Correo o contraseña incorrectos" con una cuenta que sí existe | Revisa el formulario: los veterinarios deben ingresar por la pestaña **Soy veterinario** (o por **Ingresar** si son administradores). El cargo en `EMPLEADO` debe ser `Veterinario`, `Veterinaria` o `Administrador`, y la cuenta debe tener contraseña (créala con `crear_veterinario.py` o `crear_administrador.py`). Si el que no entra es el administrador de demostración, revisa que su `ClaveHash` en `EMPLEADO` empiece por `scrypt:` y, si no, restablécela ejecutando `crear_administrador.py` con el correo `admin@pawcare.com`. Los clientes de ejemplo no tienen contraseña |
| `/equipo` me manda a `/cliente`, o la API responde "Inicia sesión como administrador" | Esa sesión no es de administrador (o no hay sesión). Cierra sesión e ingresa con la cuenta de administrador |
| Las compras funcionan pero no llegan notificaciones de compra | La colección de Mongo todavía no acepta el tipo `compra_realizada`. Vuelve a ejecutar `python database/mongo_setup.py` y reinicia la app |
| "No se pudo conectar con MongoDB" o `ServerSelectionTimeoutError` | Tu IP no está en **Network Access** de Atlas, no tienes internet, o la red bloquea la conexión a Atlas (algunas redes de empresas o universidades lo hacen) |
| `Authentication failed` al ejecutar `mongo_setup.py` | Usuario o contraseña incorrectos en `MONGO_URI`, o la contraseña tiene caracteres especiales sin codificar |
| `Falta MONGO_URI en el archivo .env` | La variable no está definida o el archivo `.env` no está en la carpeta del proyecto |
| La campana muestra 0 siempre | MongoDB no está disponible o no se ejecutó `python database/mongo_setup.py` |
| `python` no se reconoce como comando | Python no está en el PATH. Reinstálalo marcando "Add Python to PATH", o prueba con `py` en lugar de `python` |
| PowerShell no deja activar el entorno virtual | Ejecuta `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` o usa CMD |
| Error de zona horaria en Windows | Instala `tzdata` con `pip install tzdata` (ya está en `requirements.txt`) |
| No aparecen horas disponibles | El veterinario no atiende ese día, la fecha ya pasó, o las horas ya están ocupadas. Revisa la tabla `HORARIO` en phpMyAdmin |
| Las imágenes del README no se ven | Verifica que los archivos estén en `docs/capturas/` con los nombres exactos de la sección de capturas |
 
## Notas de seguridad
 
- Nunca subas el archivo `.env` al repositorio y no dejes credenciales reales en `.env.example`. Si una contraseña o cadena de conexión ya quedó expuesta en un archivo versionado, cámbiala en MongoDB Atlas (**Database Access > Edit**).
- Define siempre una `JWT_SECRET_KEY` propia, larga y aleatoria. Quien la conozca puede fabricar tokens de cualquier rol, incluido el de administrador. No la compartas ni la subas al repositorio.
- Al publicar el sitio con HTTPS, pon `COOKIE_SECURE=1` para que la cookie de sesión nunca viaje sin cifrar.
- Las contraseñas se guardan con hash (scrypt), pero las cuentas de demostración son públicas: los veterinarios de `datos_ejemplo.sql` y el administrador que trae `schema.sql` tienen contraseñas escritas en esos archivos. Antes de publicar, cámbialas con `database/crear_veterinario.py` y `database/crear_administrador.py`.
- Las cuentas de veterinario y de administrador no se pueden crear desde la página: solo con los scripts o con SQL, que exigen acceso a la base de datos. Así nadie puede darse a sí mismo un rol con más permisos.
- Cerrar sesión borra la cookie del navegador, pero el token no se invalida en el servidor: sigue siendo válido hasta que vence (`JWT_EXP_MINUTOS`). Si necesitas sesiones más cortas, reduce ese valor.
- El rol viaja dentro del token y no se vuelve a consultar en la base en cada petición. Si cambias el cargo de un empleado, el cambio se aplica en su siguiente inicio de sesión.
- El proyecto no limita los intentos de inicio de sesión ni usa tokens CSRF. La cookie `SameSite=Lax` evita la mayoría de los ataques CSRF, pero si vas a publicar el sitio considera agregar un límite de intentos (por ejemplo con Flask-Limiter) y protección CSRF.
- El `root` de XAMPP sin contraseña es aceptable solo en tu equipo local. Si el equipo se comparte o se expone a una red, ponle contraseña desde phpMyAdmin (**Cuentas de usuarios**) y actualiza `DB_PASSWORD`.
- Para permitir acceso solo a la aplicación, puedes crear un usuario con permisos mínimos desde la pestaña **SQL** de phpMyAdmin:
```sql
CREATE USER 'vete_app'@'localhost' IDENTIFIED BY 'una_clave_segura';
GRANT SELECT, INSERT, UPDATE, DELETE ON veterinaria.* TO 'vete_app'@'localhost';
```
 
  Luego usa ese usuario en `DB_USER` y `DB_PASSWORD`.
- Evita dejar `0.0.0.0/0` en **Network Access** de Atlas fuera de pruebas.
- `app.py` arranca con `host='0.0.0.0'`, así que la aplicación es visible desde otros equipos de tu red. El depurador de Flask solo se activa si defines `FLASK_DEBUG=1`; nunca lo uses en una red compartida. Para producción usa un servidor WSGI como Waitress o Gunicorn, con `debug` desactivado. Además, Apache y XAMPP no están pensados para producción.