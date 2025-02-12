###Proyecto de Gestión de Tutores

##Este es un proyecto para gestionar tutores en una plataforma educativa. El proyecto está basado en Django para el backend, React para el frontend y PostgreSQL como base de datos. La plataforma permite la ##creación de usuarios con roles de administradores y tutores, junto con la funcionalidad para cargar encuestas y generar informes procesados por Inteligencia Artificial.

#Tecnologías utilizadas

Backend: Django, Django REST Framework


Base de Datos: PostgreSQL

IA: Integración para procesar encuestas y generar informes

Docker: Para contenedores de desarrollo y producción

Render: Despliegue de la base de datos y la aplicación

Instalación

1. Clonar el repositorio

git clone https://github.com//tu-repositorio.git
cd tu-repositorio

2. Crear y activar un entorno virtual (opcional, pero recomendado)

python -m venv venv
source venv/bin/activate  # En Linux/Mac
venv\Scripts\activate     # En Windows

3. Instalar dependencias

pip install -r requirements.txt

4. Configurar PostgreSQL

Instalar PostgreSQL si no lo tienes instalado.

Crear una base de datos para el proyecto:

createdb -U postgres nombre_base_de_datos

Ejecutar las migraciones de Django para configurar la base de datos:

python manage.py migrate

5. Ejecutar el servidor

python manage.py runserver

El servidor debería estar corriendo en http://localhost:8000.

Docker

1. Crear una imagen Docker

docker-compose up --build -d


Respaldo y Restauración de la Base de Datos

Realizar un respaldo (Backup)

PGPASSWORD=tu_contraseña pg_dump -h dpg-ctc4f49u0jms73cqloo0-a.oregon-postgres.render.com -U dbtutores_user -d dbtutores -F c -b -v -f "ruta/del/archivo/backup.dump"

Restaurar la base de datos

Crear una nueva base de datos:

createdb -U postgres nueva_base_de_datos

Restaurar desde el archivo de respaldo:

PGPASSWORD=tu_contraseña pg_restore -h localhost -U postgres -d nueva_base_de_datos -v "ruta/del/archivo/backup.dump"

Variables de Entorno en Django

Para gestionar las variables de entorno de manera segura en Django, puedes usar un paquete como python-decouple.

1. Instalar python-dotenv              

'''pip install python-dotenv                 

2. Crear un archivo .env

En la raíz de tu proyecto Django (donde está el archivo manage.py), crea un archivo llamado .env para almacenar tus variables de entorno.

Ejemplo de archivo .env:

DEBUG=True
SECRET_KEY=tu_clave_secreta
DB_NAME=nombre_base_de_datos
DB_USER=postgres
DB_PASSWORD=tu_contraseña
DB_HOST=localhost
DB_PORT=5432

3. Configurar Django para leer las variables de entorno



4. Asegúrate de que el archivo .env no sea versionado

Para evitar que tu archivo .env con credenciales sensibles se suba al repositorio, agrega el archivo .env al archivo .gitignore.

Ejemplo de .gitignore:

# .gitignore
.env

5. Usar las variables en otras partes del proyecto

Cualquier otra variable de entorno que necesites en tu proyecto puede ser cargada de la misma manera:

API_KEY = config('API_KEY')

Contribuciones


Contacto

Nombre: AdonayCorreo: tu_correo@example.comGitHub: @tu-usuario

