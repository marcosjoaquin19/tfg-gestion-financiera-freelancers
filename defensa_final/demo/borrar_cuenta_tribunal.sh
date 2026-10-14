#!/bin/sh
# Borra la cuenta tribunal@freelancecontrol.com y todo lo que tenga, para poder
# volver a registrarla en vivo. Solo si se muestra un registro: su hash es el de
# la primera filmina del anexo, y al registrarla de nuevo sale otro (sal nueva), así
# que ver_usuarios.sh deja de coincidir con la filmina. NO correrlo la mañana
# del 14/10. No toca ninguna otra cuenta. Si la cuenta no existe, no hace nada.
#
# Uso, desde la carpeta del proyecto:   sh defensa_final/demo/borrar_cuenta_tribunal.sh
docker exec -i "${DB:-tfg_db}" sh -c 'psql -q -U "$POSTGRES_USER" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1' <<'SQL'
BEGIN;
CREATE TEMP TABLE cuenta AS SELECT id FROM usuarios WHERE email = 'tribunal@freelancecontrol.com';
DELETE FROM alertas_auditoria    WHERE usuario_id IN (SELECT id FROM cuenta);
DELETE FROM cache_clasificacion  WHERE usuario_id IN (SELECT id FROM cuenta);
DELETE FROM modelos_clasificador WHERE usuario_id IN (SELECT id FROM cuenta);
DELETE FROM proyecciones         WHERE usuario_id IN (SELECT id FROM cuenta);
DELETE FROM facturas             WHERE usuario_id IN (SELECT id FROM cuenta);
DELETE FROM gastos               WHERE usuario_id IN (SELECT id FROM cuenta);
DELETE FROM ingresos             WHERE usuario_id IN (SELECT id FROM cuenta);
DELETE FROM usuarios             WHERE id IN (SELECT id FROM cuenta);
SELECT CASE WHEN count(*) = 0 THEN 'No había cuenta de ensayo: listo para registrarla.'
            ELSE 'Cuenta de ensayo borrada: lista para registrarla de nuevo.' END AS resultado
FROM cuenta;
COMMIT;
SQL
