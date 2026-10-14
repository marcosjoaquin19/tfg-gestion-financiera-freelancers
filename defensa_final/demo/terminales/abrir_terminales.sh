#!/bin/sh
# Abre las cuatro terminales de la defensa, cada una con su comando YA ESCRITO:
# se hace clic en la ventana y se aprieta Enter. Para repetirlo, flecha arriba
# y Enter. Son los comandos de las filminas del anexo, para mostrar en vivo:
#
#   1 · La contraseña en la base        (filmina 29)   sh defensa_final/demo/ver_usuarios.sh
#   2 · Las cinco vueltas               (filmina 36)   docker compose exec -T api python - < evaluar_modelo.py
#   3 · Las pruebas de seguridad        (filmina 37)   docker compose exec api python -m pytest tests/test_auth.py -v -p no:warnings
#   4 · Todas las pruebas automáticas   (filmina 37)   docker compose exec api python -m pytest -p no:warnings
#
# Ninguno cambia los datos de la demo: el 1 y el 2 solo leen, y las pruebas
# usan una base aparte, en memoria, que se crea y se borra en cada prueba.
#
# Uso, desde la carpeta del proyecto y con Docker prendido:
#     sh defensa_final/demo/terminales/abrir_terminales.sh
#
# Cómo funciona: cada ventana se abre con un perfil de Terminal propio (letra
# grande y fondo oscuro sólido, para el proyector) y arranca una zsh que lee la
# configuración de zsh/ (esta carpeta): entra al proyecto, muestra el título y
# deja el comando escrito, sin correrlo. Terminal guarda esos perfiles como
# Defensa_FC_1 a Defensa_FC_4 (el de siempre no cambia); volver a correr el
# script no los duplica. Después de la defensa se pueden borrar en Terminal ›
# Configuración › Perfiles.
#
# Volver a correrlo tampoco duplica ventanas: primero cierra las cuatro que
# abrió la vez anterior (cada zsh anota su número de proceso al arrancar) y
# después abre cuatro nuevas, limpias y con el comando escrito otra vez.

AQUI=$(cd "$(dirname "$0")" && pwd)
PROYECTO=$(cd "$AQUI/../../.." && pwd)
TMP=$(mktemp -d)

# Cerrar las terminales de la vez anterior. Cada ventana tiene dos zsh: la
# de siempre (-zsh), que Terminal abre primero, y adentro la de la defensa.
# Se termina la de afuera y con ella la ventana entera (perfil con
# shellExitAction 0). Solo se toca si siguen siendo esas zsh: el número
# podría haberlo reusado otro programa después de reiniciar la Mac.
for N in 1 2 3 4; do
  PIDFILE="${TMPDIR:-/tmp}/defensa_terminal_$N.pid"
  [ -r "$PIDFILE" ] || continue
  PID=$(cat "$PIDFILE")
  if ps -p "$PID" -o command= 2>/dev/null | grep -q 'zsh -il'; then
    PADRE=$(ps -p "$PID" -o ppid= | tr -d ' ')
    kill -HUP "$PID" 2>/dev/null
    if ps -p "$PADRE" -o command= 2>/dev/null | grep -qx -- '-zsh'; then
      kill -HUP "$PADRE" 2>/dev/null
    fi
  fi
  rm -f "$PIDFILE"
done
sleep 1

# Letra SF Mono de 18 puntos, fondo azul noche (el de las filminas) y texto
# casi blanco: así lo guarda Terminal (NSFont y NSColor archivados).
FUENTE=YnBsaXN0MDDUAQIDBAUGGBlYJHZlcnNpb25YJG9iamVjdHNZJGFyY2hpdmVyVCR0b3ASAAGGoKQHCBESVSRudWxs1AkKCwwNDg8QVk5TU2l6ZVhOU2ZGbGFnc1ZOU05hbWVWJGNsYXNzI0AyAAAAAAAAEBCAAoADXxAWU0ZNb25vVGVybWluYWwtUmVndWxhctITFBUWWCRjbGFzc2VzWiRjbGFzc25hbWWiFhdWTlNGb250WE5TT2JqZWN0XxAPTlNLZXllZEFyY2hpdmVy0RobVHJvb3SAAQgRGiMtMjc8QktSW2JpcnR2eJGWn6qttL3P0tcAAAAAAAABAQAAAAAAAAAcAAAAAAAAAAAAAAAAAAAA2Q==
FONDO=YnBsaXN0MDDUAQIDBAUGBwpYJHZlcnNpb25ZJGFyY2hpdmVyVCR0b3BYJG9iamVjdHMSAAGGoF8QD05TS2V5ZWRBcmNoaXZlctEICVRyb290gAGjCwwTVSRudWxs0w0ODxARElVOU1JHQlxOU0NvbG9yU3BhY2VWJGNsYXNzTxAmMC4wNDMxMzcyNTQ5IDAuMTA1ODgyMzUyOSAwLjE2ODYyNzQ1MQAQAoAC0hQVFhdaJGNsYXNzbmFtZVgkY2xhc3Nlc1dOU0NvbG9yohYYWE5TT2JqZWN0CBEaJCkyN0lMUVNXXWRqd36nqauwu8TMzwAAAAAAAAEBAAAAAAAAABkAAAAAAAAAAAAAAAAAAADY
TEXTO=YnBsaXN0MDDUAQIDBAUGBwpYJHZlcnNpb25ZJGFyY2hpdmVyVCR0b3BYJG9iamVjdHMSAAGGoF8QD05TS2V5ZWRBcmNoaXZlctEICVRyb290gAGjCwwTVSRudWxs0w0ODxARElVOU1JHQlxOU0NvbG9yU3BhY2VWJGNsYXNzTxAPMC45MyAwLjk1IDAuOTcAEAKAAtIUFRYXWiRjbGFzc25hbWVYJGNsYXNzZXNXTlNDb2xvcqIWGFhOU09iamVjdAgRGiQpMjdJTFFTV11kand+kJKUmaSttbgAAAAAAAABAQAAAAAAAAAZAAAAAAAAAAAAAAAAAAAAwQ==
SELECCION=YnBsaXN0MDDUAQIDBAUGBwpYJHZlcnNpb25ZJGFyY2hpdmVyVCR0b3BYJG9iamVjdHMSAAGGoF8QD05TS2V5ZWRBcmNoaXZlctEICVRyb290gAGjCwwTVSRudWxs0w0ODxARElVOU1JHQlxOU0NvbG9yU3BhY2VWJGNsYXNzTxAPMC4xMSAwLjQ1IDAuNTgAEAKAAtIUFRYXWiRjbGFzc25hbWVYJGNsYXNzZXNXTlNDb2xvcqIWGFhOU09iamVjdAgRGiQpMjdJTFFTV11kand+kJKUmaSttbgAAAAAAAABAQAAAAAAAAAZAAAAAAAAAAAAAAAAAAAAwQ==

# Se abren de la 4 a la 1, así la 1 queda adelante y las demás escalonadas atrás.
for N in 4 3 2 1; do
  case $N in
    1) TITULO="1 · La contraseña en la base" ;;
    2) TITULO="2 · Las cinco vueltas" ;;
    3) TITULO="3 · Las pruebas de seguridad" ;;
    4) TITULO="4 · Todas las pruebas automáticas" ;;
  esac
  cat > "$TMP/Defensa_FC_$N.terminal" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>name</key>                         <string>Defensa $N</string>
	<key>type</key>                         <string>Window Settings</string>
	<key>ProfileCurrentVersion</key>        <real>2.07</real>
	<key>CommandString</key>                <string>/usr/bin/env ZDOTDIR='$AQUI/zsh' DEFENSA_PROYECTO='$PROYECTO' DEFENSA_TERMINAL=$N /bin/zsh -il</string>
	<key>RunCommandAsShell</key>            <false/>
	<key>WindowTitle</key>                  <string>$TITULO</string>
	<key>ShowActiveProcessInTitle</key>     <false/>
	<key>ShowActiveProcessArgumentsInTitle</key> <false/>
	<key>ShowCommandKeyInTitle</key>        <false/>
	<key>ShowDimensionsInTitle</key>        <false/>
	<key>ShowRepresentedURLInTitle</key>    <false/>
	<key>ShowRepresentedURLPathInTitle</key> <false/>
	<key>ShowShellCommandInTitle</key>      <false/>
	<key>ShowTTYNameInTitle</key>           <false/>
	<key>ShowWindowSettingsNameInTitle</key> <false/>
	<key>columnCount</key>                  <integer>96</integer>
	<key>rowCount</key>                     <integer>28</integer>
	<key>Font</key>                         <data>$FUENTE</data>
	<key>FontAntialias</key>                <true/>
	<key>BackgroundColor</key>              <data>$FONDO</data>
	<key>TextColor</key>                    <data>$TEXTO</data>
	<key>TextBoldColor</key>                <data>$TEXTO</data>
	<key>SelectionColor</key>               <data>$SELECCION</data>
	<key>shellExitAction</key>              <integer>0</integer>
</dict>
</plist>
EOF
  open "$TMP/Defensa_FC_$N.terminal"
  sleep 1
done
echo "Listo: cuatro terminales abiertas, cada una con su comando escrito. Clic en la ventana y Enter."
