#!/bin/sh
# Primera filmina del anexo (la contraseña en la base): muestra en la base las dos cuentas de la demo, que
# tienen la misma contraseña. La contraseña no está: se ve su hash bcrypt, y
# los dos hashes son distintos porque cada cuenta lleva su propia sal. Las tres
# últimas líneas de cada cuenta lo separan en sus partes solo para leerlo; en
# la base es una sola cadena (password_hash).
#
# La salida es la misma que la de la filmina: la siembra conserva el hash de
# la cuenta demo, y la del tribunal no se borra (borrar_cuenta_tribunal.sh
# solo si se muestra un registro en vivo).
#
# Uso, desde la carpeta del proyecto:   sh defensa_final/demo/ver_usuarios.sh
# (DB=<contenedor> para apuntar a otra base; por defecto, tfg_db)
docker exec -i "${DB:-tfg_db}" sh -c 'psql -q -U "$POSTGRES_USER" -d "$POSTGRES_DB" -x' <<'SQL'
SELECT email,
       password_hash,
       substring(password_hash from 1 for 7)  AS "  versión y costo",
       substring(password_hash from 8 for 22) AS "  sal",
       substring(password_hash from 30)       AS "  hash"
FROM usuarios
WHERE email IN ('demo@freelancecontrol.com', 'tribunal@freelancecontrol.com')
ORDER BY email;
SQL
