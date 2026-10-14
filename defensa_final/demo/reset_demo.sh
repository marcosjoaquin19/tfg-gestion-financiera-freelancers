#!/bin/sh
# RESET DE LA DEMO: deja todo como al empezar la defensa, con un solo comando.
#
#     sh defensa_final/demo/reset_demo.sh
#
# 1. Levanta el sistema (si estaba apagado) y vuelve a sembrar los datos de la
#    defensa: borra al usuario demo y lo crea de nuevo, con enero a septiembre.
#    La cuenta del tribunal no se toca.
# 2. Comprueba que quedó como tiene que quedar: 27 ingresos, 65 gastos (ninguno
#    en octubre), 8 facturas, 0 alertas, sin proyecciones ni modelo propio, y los
#    hashes de la filmina 29.
# 3. Cierra las cuatro terminales de la vez anterior y abre cuatro nuevas, cada
#    una con su comando escrito (abrir_terminales.sh).
# 4. Abre VS Code en el proyecto, con el índice "pregunta del tribunal →
#    archivo:línea" (defensa_final/02_ARQUITECTURA_Y_PATRONES.md).
# 5. Deja la presentación adelante.
#
# En Chrome hay que recargar la pestaña (Cmd+R): la sesión vieja era del usuario
# demo anterior y cae sola al inicio de sesión.

AQUI=$(cd "$(dirname "$0")" && pwd)
PROYECTO=$(cd "$AQUI/../.." && pwd)
PRESENTACION="$HOME/Desktop/Defensa_FreelanceControl/1_Presentacion/FreelanceControl_Defensa_Final.key"
cd "$PROYECTO" || exit 1

if ! docker info >/dev/null 2>&1; then
  echo "Docker no está prendido: abrí Docker Desktop, esperá a que arranque y volvé a correr esto."
  exit 1
fi

echo "1/5 · Levantando el sistema y sembrando los datos de la defensa…"
docker compose up -d >/dev/null 2>&1
docker compose exec -T api python seed_demo_defensa.py || { echo "Falló la siembra."; exit 1; }

echo
echo "2/5 · Comprobando…"
OK=1
CUENTAS=$(docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -c "
  with d as (select id from usuarios where email = '"'"'demo@freelancecontrol.com'"'"')
  select (select count(*) from ingresos where usuario_id = (select id from d)) || '"'"'|'"'"' ||
         (select count(*) from gastos where usuario_id = (select id from d)) || '"'"'|'"'"' ||
         (select count(*) from gastos where usuario_id = (select id from d) and fecha >= '"'"'2026-10-01'"'"') || '"'"'|'"'"' ||
         (select count(*) from facturas where usuario_id = (select id from d)) || '"'"'|'"'"' ||
         (select count(*) from alertas_auditoria where usuario_id = (select id from d)) || '"'"'|'"'"' ||
         (select count(*) from proyecciones where usuario_id = (select id from d)) || '"'"'|'"'"' ||
         (select count(*) from modelos_clasificador where usuario_id = (select id from d));"' | tr -d '\r')
if [ "$CUENTAS" = "27|65|0|8|0|0|0" ]; then
  echo "    Datos: 27 ingresos, 65 gastos (0 en octubre), 8 facturas, 0 alertas, sin proyecciones ni modelo propio. OK"
else
  echo "    OJO, los datos no dan lo esperado (ingresos|gastos|gastos oct|facturas|alertas|proyecciones|modelo propio): $CUENTAS"
  OK=0
fi
USUARIOS=$(sh defensa_final/demo/ver_usuarios.sh 2>/dev/null)
if echo "$USUARIOS" | grep -q '2ywjtsYRN0kRv3xdX1dQ2\.' && echo "$USUARIOS" | grep -q '1LV63ca2SQx1bUjkl6KTRe'; then
  echo "    Hashes de demo y tribunal: iguales a la filmina 29. OK"
else
  echo "    OJO, los hashes no coinciden con la filmina 29 (¿se borró la cuenta del tribunal?)."
  OK=0
fi

echo
echo "3/5 · Abriendo las cuatro terminales…"
sh "$AQUI/terminales/abrir_terminales.sh" >/dev/null

echo "4/5 · Abriendo VS Code en el proyecto…"
if command -v code >/dev/null 2>&1; then
  code "$PROYECTO" "$PROYECTO/defensa_final/02_ARQUITECTURA_Y_PATRONES.md"
else
  open -a "Visual Studio Code" "$PROYECTO"
fi

echo "5/5 · Presentación adelante."
sleep 2
[ -e "$PRESENTACION" ] && open "$PRESENTACION"

echo
if [ "$OK" = 1 ]; then
  echo "Listo. Recargá Chrome (Cmd+R): cae en el inicio de sesión."
else
  echo "Terminó, pero con algo para mirar (arriba dice qué)."
fi
