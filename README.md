Proyecto de Gestión de Tutores

Este es un proyecto para gestionar tutores en una plataforma educativa. El proyecto está basado en Django para el backend, React para el frontend y PostgreSQL como base de datos. La plataforma permite la creación de usuarios con roles de administradores y tutores, junto con la funcionalidad para cargar encuestas y generar informes procesados por Inteligencia Artificial.

Tecnologías utilizadas

Backend: Django, Django REST Framework

Frontend: React

Base de Datos: PostgreSQL

IA: Integración para procesar encuestas y generar informes

Docker: Para contenedores de desarrollo y producción

Heroku/Render: Despliegue de la base de datos y la aplicación

Instalación

1. Clonar el repositorio

git clone https://github.com/tu-usuario/tu-repositorio.git
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

2. Ejecutar contenedor Docker

docker run --rm -it -p 8000:8000 nombre-del-contenedor

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

1. Instalar python-decouple

pip install python-decouple

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

En tu archivo settings.py de Django, importa Config desde decouple para cargar las variables del archivo .env.

from decouple import Config, Csv

config = Config()

# Usar las variables de entorno para la configuración
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)

# Configuración de la base de datos
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default=5432, cast=int),
    }
}

4. Asegúrate de que el archivo .env no sea versionado

Para evitar que tu archivo .env con credenciales sensibles se suba al repositorio, agrega el archivo .env al archivo .gitignore.

Ejemplo de .gitignore:

# .gitignore
.env

5. Usar las variables en otras partes del proyecto

Cualquier otra variable de entorno que necesites en tu proyecto puede ser cargada de la misma manera:

API_KEY = config('API_KEY')

Contribuciones

Haz un fork de este repositorio.

Crea una rama para tu característica (git checkout -b feature-nueva-caracteristica).

Haz tus cambios y confirma (git commit -am 'Añadir nueva característica').

Empuja a tu rama (git push origin feature-nueva-caracteristica).

Crea un Pull Request.

Licencia

Este proyecto está bajo la licencia MIT. Mira el archivo LICENSE para más detalles.

Contacto

Nombre: AdonayCorreo: tu_correo@example.comGitHub: @tu-usuario

