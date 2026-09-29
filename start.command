#!/usr/bin/env bash
#
# Inicio rápido de FreelanceControl con Docker (doble clic en macOS / Linux).
# Requisito: Docker Desktop instalado y ABIERTO.
#
# El script: crea el .env, levanta los contenedores, carga los datos de
# demostración y abre la aplicación en el navegador.
#
set -e
cd "$(dirname "$0")"

echo "======================================================"
echo "   FreelanceControl — arranque con Docker"
echo "======================================================"

# ¿Docker está corriendo?
if ! docker info >/dev/null 2>&1; then
  echo ""
  echo "  ERROR: Docker no está corriendo."
  echo "  Abrí Docker Desktop, esperá a que arranque y volvé a hacer doble clic."
  echo ""
  read -r -p "Presioná Enter para cerrar..."
  exit 1
fi

# 1) Crear .env si no existe. Las claves se generan al azar en cada equipo:
#    ninguna queda escrita en el repositorio. La de la base se usa una sola
#    vez, cuando Docker crea la base; por eso, si ya existe una base de una
#    instalación anterior, no borres el .env (o borrá también la base con
#    "docker compose down -v").
if [ ! -f .env ]; then
  echo "-> Generando archivo .env ..."
  # openssl viene con macOS; si faltara, se usa el generador del sistema.
  aleatoria() { openssl rand -hex "$1" 2>/dev/null || LC_ALL=C tr -dc 'a-f0-9' < /dev/urandom | head -c $(( $1 * 2 )); }
  SECRET=$(aleatoria 32)     # 64 caracteres (la API no arranca con menos de 32)
  DB_PASSWORD=$(aleatoria 16)
  cat > .env <<EOF
DATABASE_URL=postgresql://freelancecontrol:$DB_PASSWORD@db:5432/tfg_freelancers
POSTGRES_USER=freelancecontrol
POSTGRES_PASSWORD=$DB_PASSWORD
POSTGRES_DB=tfg_freelancers
SECRET_KEY=$SECRET
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
GROQ_API_KEY=
GROQ_MODEL=openai/gpt-oss-120b
EOF
fi

# 2) Levantar los contenedores
echo "-> Construyendo y levantando contenedores (la primera vez puede tardar varios minutos)..."
docker compose up --build -d

# 3) Esperar a que la API esté lista
echo "-> Esperando a que la API responda..."
for _ in $(seq 1 90); do
  if curl -s -o /dev/null http://localhost:8000/health 2>/dev/null; then
    echo "   API lista."
    break
  fi
  sleep 2
done

# 4) Cargar datos de demostración
echo "-> Cargando datos de demostración..."
docker compose exec -T api python seed_modelo_base.py
docker compose exec -T api python seed_demo.py

# 5) Abrir el navegador
echo "-> Abriendo http://localhost:3000 ..."
open http://localhost:3000 2>/dev/null || xdg-open http://localhost:3000 2>/dev/null || true

echo ""
echo "======================================================"
echo "   Listo. Usuario de prueba:"
echo "      demo@freelancecontrol.com   /   demo1234"
echo ""
echo "   Para detener todo:  docker compose down"
echo "======================================================"
read -r -p "Presioná Enter para cerrar esta ventana..."
