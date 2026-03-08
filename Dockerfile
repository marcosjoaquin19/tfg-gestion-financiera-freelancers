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

# El comando para arrancar la API
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]