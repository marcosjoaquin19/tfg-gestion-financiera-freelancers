# Terminales de la defensa (ver ../abrir_terminales.sh): entra al proyecto,
# muestra el título y deja el comando escrito en la línea, sin correrlo.
[ -r "$HOME/.zshrc" ] && . "$HOME/.zshrc"
HISTFILE="$HOME/.zsh_history"     # el historial de siempre, no uno en esta carpeta
cd "$DEFENSA_PROYECTO" || return

case $DEFENSA_TERMINAL in
  1) titulo="1 · La contraseña en la base"; filmina=29
     nota="Las dos cuentas tienen la misma contraseña. Solo lee la base."
     cmd='sh defensa_final/demo/ver_usuarios.sh' ;;
  2) titulo="2 · Las cinco vueltas"; filmina=36
     nota="El examen con gastos que no vio. No cambia nada; tarda segundos."
     cmd='docker compose exec -T api python - < evaluar_modelo.py' ;;
  3) titulo="3 · Las pruebas de seguridad"; filmina=37
     nota="Unos segundos, con el nombre de cada caso. Base aparte: no toca la demo."
     cmd='docker compose exec api python -m pytest tests/test_auth.py -v -p no:warnings' ;;
  4) titulo="4 · Todas las pruebas automáticas"; filmina=37
     nota="Unos dos minutos. Base aparte, en memoria: no toca la demo."
     cmd='docker compose exec api python -m pytest -p no:warnings' ;;
esac

# Se anota el número de esta zsh para que abrir_terminales.sh pueda cerrar
# esta ventana la próxima vez y no se acumulen repetidas.
print -- $$ > "${TMPDIR:-/tmp}/defensa_terminal_${DEFENSA_TERMINAL}.pid"

# Ventanas escalonadas: la 1 adelante, arriba a la izquierda.
printf '\033[3;%d;%dt' $(( 20 + 40 * (DEFENSA_TERMINAL - 1) )) $(( 30 + 40 * (DEFENSA_TERMINAL - 1) ))
printf '\033]0;%s\007' "$titulo"
clear
print -P "%B%F{cyan}${titulo}%f%b   %F{8}(anexo, filmina ${filmina})%f"
print -P "%F{8}${nota}%f"
print -P "%F{8}Enter para correrlo · flecha arriba y Enter para repetirlo%f"
print
print -z -- "$cmd"

unset ZDOTDIR DEFENSA_TERMINAL DEFENSA_PROYECTO titulo filmina nota cmd
