# Usamos Python 3.11 como base
FROM python:3.11-slim

# Creamos la carpeta de trabajo dentro del contenedor
WORKDIR /app

# Copiamos primero el requirements.txt
COPY requirements.txt .

# Instalamos todas las librerías
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos todo el resto del proyecto
COPY . .

# Al arrancar el contenedor: primero aplica migraciones pendientes, luego levanta la API.
# Se usa CMD con shell para poder encadenar con &&.
# Nota: RUN no sirve aquí porque en build-time la BD no está disponible.
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload