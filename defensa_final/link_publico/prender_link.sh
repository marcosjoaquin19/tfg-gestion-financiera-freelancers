#!/bin/sh
# Prende el link público de FreelanceControl: una dirección https://….trycloudflare.com
# que se abre desde cualquier navegador (gratis, sin cuenta de Cloudflare).
#
# El link muestra una COPIA APARTE de la app, con su propia base y los datos de
# la defensa: lo que se haga ahí no toca la app de la demo (tfg_db, tfg_api,
# tfg_frontend) ni sus puertos.
#   - La primera vez tarda unos minutos: compila la pantalla y entrena el modelo base.
#   - La dirección cambia cada vez que se prende el link.
#   - Anda mientras la Mac esté prendida, sin suspender, y con Docker abierto.
#   - --limpio vuelve a cargar los datos de la defensa en la copia.
#
# Uso, desde la carpeta del proyecto:   sh defensa_final/link_publico/prender_link.sh [--limpio]
# Para apagarlo:                        sh defensa_final/link_publico/apagar_link.sh
set -e
cd "$(dirname "$0")"

if ! docker info >/dev/null 2>&1; then
  echo "Docker no está abierto: abrí Docker Desktop y volvé a correr este comando."
  exit 1
fi

# Claves propias de la copia, generadas la primera vez (no se versionan).
if [ ! -f .env.publico ]; then
  clave_db=$(openssl rand -hex 24)
  cat > .env.publico <<EOF
POSTGRES_USER=publico
POSTGRES_PASSWORD=$clave_db
POSTGRES_DB=freelancecontrol
DATABASE_URL=postgresql://publico:$clave_db@db:5432/freelancecontrol
SECRET_KEY=$(openssl rand -hex 32)
EOF
fi

echo "Levantando la copia de la app..."
docker compose up -d --build db api web

printf "Esperando a la API"
intentos=0
until curl -fs http://127.0.0.1:8080/api/health >/dev/null 2>&1; do
  intentos=$((intentos + 1))
  if [ "$intentos" -gt 90 ]; then
    echo; echo "La API no respondió. Para ver el error: docker logs tfg_publico_api"; exit 1
  fi
  printf "."; sleep 2
done
echo " lista."

# La primera vez (sin usuario demo) se entrena el modelo base y se cargan los datos.
hay_demo=$(echo "SELECT count(*) FROM usuarios WHERE email = 'demo@freelancecontrol.com';" \
  | docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tA')
if [ "$hay_demo" = "0" ]; then
  echo "Primera vez: entrenando el modelo base del clasificador..."
  docker compose exec -T api python seed_modelo_base.py
fi
if [ "$hay_demo" = "0" ] || [ "$1" = "--limpio" ]; then
  echo "Cargando los datos de la defensa..."
  docker compose exec -T api python seed_demo_defensa.py
fi

docker compose up -d tunel
printf "Pidiendo la dirección a Cloudflare"
url=""
intentos=0
while [ -z "$url" ]; do
  intentos=$((intentos + 1))
  if [ "$intentos" -gt 30 ]; then
    echo; echo "Cloudflare no dio una dirección. Para ver el error: docker logs tfg_publico_tunel"; exit 1
  fi
  url=$(docker logs tfg_publico_tunel 2>&1 | grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' | tail -1)
  [ -z "$url" ] && printf "." && sleep 2
done
echo

echo
echo "  Link público:  $url"
echo "  Usuario:       demo@freelancecontrol.com  /  demo1234"
echo
echo "  Si recién lo prendiste y no abre, esperá medio minuto y recargá."
echo "  Para apagarlo: sh defensa_final/link_publico/apagar_link.sh"
