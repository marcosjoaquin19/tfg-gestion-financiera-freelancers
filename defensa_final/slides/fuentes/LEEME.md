# De dónde salen las capturas y los íconos de las filminas

Las filminas (`../FreelanceControl_Defensa_Final.pptx`) se generan con
`node defensa_final/gen_slides_defensa.js` y usan dos carpetas de imágenes que
**ya están en el repositorio**: `../capturas/` y `../iconos/`. Estos scripts
solo hacen falta si hay que **rehacerlas** (por ejemplo, si cambia una pantalla).

## Las capturas: la demo del 14/10, simulada

Son de una copia aparte del sistema, con el reloj de la API en el
**14/10/2026 a las 12:00** (hora argentina), el seed de la defensa y el extracto
importado por la pantalla, en el mismo orden que la demo. No tocan la base real
(`tfg_db`).

1. Levantar una base y una API aparte (puerto 8001, solo en esta computadora):

   ```bash
   docker network create tfgshot
   docker run -d --name shot_db --network tfgshot -e POSTGRES_USER=shot -e POSTGRES_PASSWORD=shotpass -e POSTGRES_DB=shotdb postgres:15
   docker run -d --name shot_api --network tfgshot -p 127.0.0.1:8001:8000 --env-file .env -e DATABASE_URL=postgresql://shot:shotpass@shot_db:5432/shotdb proyecto-tfg-api sleep infinity
   docker exec shot_api pip install freezegun
   docker exec shot_api sh -c "alembic upgrade head && python seed_demo_defensa.py"
   docker cp defensa_final/slides/fuentes/lanzar_1410.py shot_api:/app/
   docker exec -d shot_api sh -c "python lanzar_1410.py > /tmp/api.log 2>&1"
   ```

2. Con el frontend de siempre corriendo (`localhost:3000`), sacar las capturas
   (Playwright, del venv del proyecto). El navegador cree que es el 14/10 y sus
   pedidos a `localhost:8000` se desvían a la API simulada:

   ```bash
   mkdir -p /tmp/capturas && ./venv/bin/python defensa_final/slides/fuentes/capturar.py /tmp/capturas
   ```

3. Recortarlas para las filminas (`recortar.py` lee `capturas/` del directorio
   en el que se corre y escribe en `../capturas/`). Tapa las fechas que pone la
   base al guardar, que serían las del día en que se corrió la simulación.
   El PDF se pasa a imagen con `sips` (macOS), partido por hojas con `pypdf`.

4. Borrar la simulación: `docker rm -f shot_api shot_db && docker network rm tfgshot`.

## Los íconos

`iconos.js` dibuja los íconos (Lucide, vía `react-icons`) en PNG blanco
(`_b`) y azul noche (`_n`). Necesita `npm install react-icons react react-dom sharp`
en la carpeta donde se corra.

## La contraseña en la base (primera filmina del anexo)

No es una captura: es la salida real de `sh defensa_final/demo/ver_usuarios.sh`
sobre la base de la defensa (`tfg_db`, 10/10), escrita en la filmina. Las dos
cuentas tienen la misma contraseña y la base guarda dos hashes distintos por la
sal. Se puede correr en vivo y da lo mismo: `seed_demo_defensa.py` conserva el
hash de la cuenta demo al volver a sembrar, y la cuenta del tribunal no se
borra. Si alguna vez cambia (por ejemplo, se borra la cuenta del tribunal y se
registra de nuevo), copiar los hashes nuevos en `HASHES` del generador.

## El ejemplo de la corrección (filmina «Aprende de las correcciones»)

`clasif_mostaza*.png` salen de la misma simulación, después de importar (con el
modelo propio): en el Clasificador, «mostaza palermo» y «mostaza» → Otros 1 %;
se corrige «mostaza» a Alimentación (Corregir categoría); se espera el
reentrenamiento de fondo (`/ml/estado` pasa de 691 a 692 ejemplos); «mostaza»
→ Corrección tuya 100 % y «mostaza palermo» → Alimentación 73 %. Se recortan
con la misma caja que las demás del Clasificador (`recortar.py`).

## El video de la filmina 10

`../../video/FreelanceControl_Institucional.mp4` es el institucional pasado a
H.264 (yuv420p, para Keynote y PowerPoint); no se versiona. La portada
(`../capturas/video_portada.png`) es su cuadro del segundo 1:

```bash
ffmpeg -i ~/Desktop/FreelanceControl_Institucional.mp4 -c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart defensa_final/video/FreelanceControl_Institucional.mp4
ffmpeg -ss 1 -i defensa_final/video/FreelanceControl_Institucional.mp4 -frames:v 1 -vf scale=1280:-2 defensa_final/slides/capturas/video_portada.png
```
