# Usamos Python 3.11 como base
FROM python:3.11-slim

# Creamos la carpeta de trabajo dentro del contenedor
WORKDIR /app

# Copiamos primero el requirements.txt: así Docker reutiliza la capa con las
# librerías instaladas mientras no cambie, y solo rehace la copia del código.
COPY requirements.txt .

# Instalamos todas las librerías
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos todo el resto del proyecto
COPY . .

# Al arrancar el contenedor: primero aplica migraciones pendientes, luego levanta la API.
# Se usa CMD con shell para poder encadenar con &&.
# Nota: RUN no sirve aquí porque en build-time la BD no está disponible.
# --reload es modo desarrollo (en un despliegue real se quita). Como el código
# se copia a la imagen y no se monta, tras editar el backend hay que
# reconstruir: docker compose up -d --build api
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload