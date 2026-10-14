#!/bin/sh
# Apaga el link público y la copia aparte de la app: la dirección deja de
# funcionar. Los datos de la copia quedan guardados para la próxima vez
# (prender_link.sh --limpio los vuelve a cargar). No toca la app de la demo.
#
# Uso, desde la carpeta del proyecto:   sh defensa_final/link_publico/apagar_link.sh
cd "$(dirname "$0")"

if [ ! -f .env.publico ]; then
  echo "El link nunca se prendió: no hay nada que apagar."
  exit 0
fi

docker compose down
echo "Link apagado."
