# Defensa final — FreelanceControl

Material de trabajo para la **defensa oral** del Trabajo Final de Grado.
La tesis escrita ya está **aprobada**; acá vive todo lo que se usa para
defenderla ante la comisión evaluadora.

**Formato de la instancia:** 35 minutos de exposición + 10 minutos de preguntas.
Modalidad presencial, demostración en vivo sobre equipo propio.

---

## Contenido

| Archivo | Para qué sirve | Cuándo se usa |
|---|---|---|
| [01_GUION_DEFENSA_35MIN.md](01_GUION_DEFENSA_35MIN.md) | Guion completo, cronometrado bloque por bloque. Idea fuerza + qué decir + trampas. | Para ensayar y el día de la defensa |
| [03_GUION_DEMO_EN_VIVO.md](03_GUION_DEMO_EN_VIVO.md) | Guion de la demo en vivo, módulo por módulo (HACÉ · DECÍ · palabras clave). Las filminas y sus notas siguen este guion. | Para ensayar la demo |
| [02_ARQUITECTURA_Y_PATRONES.md](02_ARQUITECTURA_Y_PATRONES.md) | Índice "pregunta del tribunal → `archivo:línea`". Cada patrón con su justificación y la alternativa descartada. | Ronda de preguntas |
| `tesis/` | El PDF de la tesis **aprobada**, como fuente de verdad de datos y terminología | Consulta |
| [gen_slides_defensa.js](gen_slides_defensa.js) | Generador reproducible del deck. Los slides se editan **acá**, no en PowerPoint. | Al cambiar el guion |
| `slides/` | `FreelanceControl_Defensa_Final.pptx` — 46 filminas (27 + 19 de anexo y plan B), con el video institucional adentro de la 10, sus capturas, íconos y los scripts que los generan. **Se presenta con `FreelanceControl_Defensa_Final.key`**, la misma presentación guardada en Keynote (no se versiona) | Toda la exposición |
| `demo/` | `extracto_28sep_14oct.csv`, el extracto que se importa en vivo; `resumen_banco.pdf` y `planilla_vacia.xlsx`, los dos archivos que se rechazan antes; `ver_usuarios.sh`, que muestra en la base las dos cuentas y sus hashes (la misma salida que la primera filmina del anexo); `borrar_cuenta_tribunal.sh`, solo si se muestra un registro en vivo; `terminales/abrir_terminales.sh`, que abre las cuatro terminales de las preguntas, cada una con su comando ya escrito (contraseña, cinco vueltas, pruebas de seguridad, todas las pruebas) | Bloques 4 y 5 |
| `video/` | `FreelanceControl_Institucional.mp4` (1:43), en H.264: la copia que el generador mete adentro de la filmina 10. No se versiona; si falta, el generador deja la filmina que anuncia el video. El original está en la carpeta de la presentación del Escritorio (`Defensa_FreelanceControl/3_Video`). El de la demo (`_v2`, 1:41) quedó viejo y es solo plan B | Bloque 3 |
| [gen_pdfs_lectura.py](gen_pdfs_lectura.py) | Convierte los documentos a PDF para leerlos cómodo | Antes de cada lectura |
| `lectura/` | Los mismos documentos en PDF (generados, no se versionan) | Para leer y anotar |

---

## Estructura de los 35 minutos (versión del 10/10)

| Parte | Reloj | Soporte |
|---|---|---|
| 1 · El problema | 0:00 – 3:30 | Filminas 1 – 4 |
| 2 · La propuesta, las tecnologías y **hasta dónde llega** | 3:30 – 6:50 | Filminas 5 – 8 |
| 3 · Lo que van a ver y el video institucional | 6:50 – 9:00 | Filmina 9 + filmina 10 (el video, adentro) |
| 4 · Lo que trae el extracto | 9:00 – 9:20 | Filmina 11 |
| **En vivo:** entrar (el hash, en palabras) e importar el extracto | 9:20 – 13:30 | Aplicación |
| 5 · El **clasificador**, con capturas | 13:30 – 18:15 | Filminas 12 – 17 |
| **En vivo:** auditoría y facturas | 19:45 – 21:30 | Filmina 18 + aplicación |
| 6 · Qué es un gasto irregular | 21:30 – 22:30 | Filmina 19 |
| **En vivo:** monotributo y proyecciones | 22:30 – 24:00 | Aplicación |
| 7 · El semáforo, Prophet y sus **límites** | 24:00 – 27:45 | Filminas 20 – 23 |
| **En vivo:** recomendaciones y reporte PDF | 27:45 – 29:15 | Aplicación |
| 8 · Recomendaciones, límites y cierre | 29:15 – 32:00 | Filminas 24 – 27 |
| Colchón | 32:00 – 35:00 | — |

El plan termina a las 32:00 a propósito: los tres minutos finales absorben lo
que se atrase en vivo. El reloj de cada filmina está en sus notas del orador.

---

## Regenerar la presentación

Los slides no se editan a mano: se generan desde código, así se mantienen
sincronizados con el guion y con los datos reales del proyecto.

**Para presentar se abre el `.key`, no el `.pptx`.** El `.pptx` (37 MB, con el
video adentro) tarda unos 15 segundos en importarse en Keynote, sin mostrar
nada mientras tanto, y después abre aparte una ventana «Warnings» (la portada
del video de la filmina 10 puede verse distinta: no es un error). El `.key`
abre en segundos. **Cada vez que se regenera el `.pptx` hay que rehacer el
`.key`:** abrir el `.pptx` en Keynote, cerrar «Warnings», Archivo → Guardar con
el mismo nombre y moverlo a `slides/` (reemplazando el anterior).

```bash
node defensa_final/gen_slides_defensa.js
```

Requiere `pptxgenjs` instalado de forma global (`npm i -g pptxgenjs`). Cada
slide lleva arriba a la derecha su **bloque del guion y su marca de reloj**, de
modo que en el ensayo se ve de un vistazo si se va atrasado o adelantado.

Para revisar el resultado sin abrir PowerPoint:

```bash
soffice --headless --convert-to pdf --outdir /tmp defensa_final/slides/FreelanceControl_Defensa_Final.pptx
```

### Estructura del deck (versión del 10/10, alineada con el guion de la demo)

Centrado en lo que pidió la cátedra: el prototipo funcionando (importación,
clasificador, auditoría, estado fiscal, proyección y reporte PDF), los límites
del clasificador, del motor predictivo y de las recomendaciones, y que el
sistema no se presente como asesoramiento. **Sin cifras en las filminas**: los
datos de respaldo, el reloj y qué decir van en las **notas del orador**
(Keynote → Ver → Notas del presentador).

| Filminas | Parte | En vivo después de… |
|---|---|---|
| 1 – 4 | El problema y la pregunta del trabajo | |
| 5 – 8 | La propuesta, las tecnologías capa por capa y hasta dónde llega (frase de alcance y lo que quedó afuera: qué no hace y qué hace en su lugar) | |
| 9 – 10 | Lo que van a ver funcionando · el video institucional, adentro de la filmina (arranca solo) | |
| 11 | Lo que trae el extracto (los dos rechazos y los seis casos). El hash se cuenta en palabras al entrar | 11: entrar e importar |
| 12 – 17 | El clasificador: ya lo vieron trabajar, qué es, la planilla de puntos, cuándo duda (la elección), cómo aprende (el ejemplo de Mostaza) y límites (con los desafíos y cómo se midió el 76 %, en una frase cada uno). La prueba con el script quedó en el anexo | |
| 18 – 19 | Auditoría y qué es un gasto irregular | 18: auditoría y facturas · 19: monotributo y proyecciones |
| 20 – 23 | El semáforo, Prophet, los tres escenarios y los límites del motor predictivo | 23: recomendaciones y PDF |
| 24 – 27 | Recomendaciones y sus límites, objetivos, trabajo futuro y gracias (con la frase de alcance, que queda de fondo en las preguntas) | |
| 28 – 38 | **Anexo**: la contraseña en la base (la salida real de `ver_usuarios.sh`, con el comando para copiar), archivo vs. banco, escala de ARCA, el semáforo al importar, por qué Prophet, por qué SVM, los desafíos del entrenamiento, la prueba del 76 % (las cinco vueltas de `evaluar_modelo.py`, con el comando para copiar), las pruebas automáticas (37: la salida real de la suite, con los dos comandos para copiar), seguridad | |
| 39 – 46 | **Plan B**: la demo en capturas (vista previa, resultado de la importación, panel, auditoría, monotributo, proyecciones, recomendaciones y PDF) | |

La filmina anterior a cada tramo en vivo lo anuncia abajo a la derecha
(«Ahora, en vivo: …»). Las capturas son de la demo simulada el 14/10 y los
íconos están en `slides/capturas/` y `slides/iconos/`; cómo rehacerlos, en
`slides/fuentes/LEEME.md`.

---

## Acceso desde el escritorio

`~/Desktop/TFG_Defensa` es un **enlace simbólico** a esta carpeta, no una copia:
lo que se abre desde el escritorio y lo que vive en el repositorio son el mismo
archivo. No hay dos versiones que se puedan desfasar.

Para volver a crearlo si se borra:

```bash
ln -s /Users/marcosjoaquin/proyecto-tfg/defensa_final ~/Desktop/TFG_Defensa
```

### La carpeta de la presentación: `~/Desktop/Defensa_FreelanceControl`

Todo lo que se usa el día de la defensa, junto y **copiado** (no enlazado), para
poder limpiar el Escritorio:

| Carpeta | Qué tiene |
|---|---|
| `1_Presentacion` | `FreelanceControl_Defensa_Final.key` (**la que se presenta**, con el video adentro) y el mismo deck en PDF, de respaldo |
| `2_Guion` | `Guion_Demo_en_Vivo.pdf` (el 03) |
| `3_Video` | `FreelanceControl_Institucional.mp4`, el original, por si el de la filmina 10 no arranca |
| `4_Demo` | `extracto_28sep_14oct.csv`, `resumen_banco.pdf` y `planilla_vacia.xlsx`: los que se eligen en vivo en Importar |
| `5_Tesis` | La tesis aprobada (reentrega final) |

Y un `LEEME.txt` con el checklist de la mañana. **Es una copia:** si cambian las
filminas o el guion, hay que volver a copiar el `.key`, el PDF del deck y el
del guion. Los comandos que se muestran en vivo (`ver_usuarios.sh`,
`evaluar_modelo.py` y las pruebas) se corren desde la carpeta del proyecto, no desde esta:
`sh defensa_final/demo/terminales/abrir_terminales.sh` abre las cuatro terminales
con cada comando ya escrito (clic en la ventana y Enter).

### Leer los documentos en PDF

Los `.md` son la fuente de verdad, pero se leen mejor en PDF:

```bash
./venv/bin/python defensa_final/gen_pdfs_lectura.py
```

Deja en `lectura/` el guion, el índice de patrones, este README y la
presentación, todos en PDF. **Hay que regenerarlos cada vez que se edita un
documento**, porque son una copia: por eso no se versionan en git.

---

## Los dos pedidos explícitos de la cátedra

1. **Sostener que el sistema informa, proyecta y alerta, pero no reemplaza
   asesoramiento contable, fiscal ni financiero.**
   Implementado en el producto, no solo dicho: `frontend/src/components/AvisoAlcance.js`
   aparece en seis pantallas —Dashboard, Monotributo, Proyecciones,
   Recomendaciones, Resumen IA y Auditoría— y el mismo enunciado va al final del
   reporte PDF (`app/services/reportes_service.py`).

2. **Mostrar el prototipo funcionando**, especialmente clasificador,
   auditoría, importación, proyección, estado fiscal y reporte PDF. Se hace en
   cuatro tramos en vivo: entrar e importar el extracto (ahí se ve el
   clasificador trabajando: cada gasto llega con su categoría), la auditoría,
   el monotributo y las proyecciones, y las recomendaciones con el reporte PDF.
   Cómo funciona el clasificador (y cómo aprende de una corrección) se explica
   con capturas reales, no escribiendo en vivo.

---

## Buscar decisiones de diseño en el código

Todos los puntos con una decisión de diseño documentada llevan el marcador
literal `PATRÓN:` (con tilde):

```bash
grep -rn "PATRÓN:" app frontend/src
```

Devuelve 36 anotaciones en 20 archivos. El desarrollo completo de cada una
—qué resuelve, por qué se eligió, qué alternativa se descartó— está en
[02_ARQUITECTURA_Y_PATRONES.md](02_ARQUITECTURA_Y_PATRONES.md).

---

## Preparar el entorno antes de la defensa

Con Docker Desktop abierto:

```bash
docker compose up -d
docker compose exec api python seed_demo_defensa.py
sh defensa_final/demo/ver_usuarios.sh
```

La siembra deja los datos exactos del ensayo (enero a septiembre de 2026) y
borra todo lo que se haya cargado en ensayos anteriores sobre la cuenta demo,
pero **conserva el hash de su contraseña**. El segundo comando tiene que dar
exactamente lo de la filmina de la contraseña (la primera del anexo): los dos hashes, el de la cuenta
demo y el de `tribunal@freelancecontrol.com` (misma contraseña). **No borrar la
cuenta del tribunal**: `borrar_cuenta_tribunal.sh` queda solo para el caso de
mostrar un registro en vivo, y después de correrlo el hash nuevo ya no es el de
la filmina. Después, abrir las cuatro terminales de las preguntas
(`sh defensa_final/demo/terminales/abrir_terminales.sh`) y dejar
`http://localhost:3000` en el inicio de sesión, **sin entrar**: el login es
parte de la demo. El checklist completo de la mañana
está en la sección "Antes de entrar a la sala" del guion.

> ⚠️ **Importante:** el contenedor `api` **no tiene volumen montado**. Si se
> edita cualquier archivo del backend hay que reconstruirlo antes de que el
> cambio tome efecto:
>
> ```bash
> docker compose build api && docker compose up -d api
> ```
>
> El frontend sí recarga en caliente.

Verificación de que todo está sano (unos 2 minutos):

```bash
docker exec tfg_api python -m pytest -q
```

Debe dar **446 pruebas en verde**. Las de la interfaz (16):

```bash
docker compose exec frontend sh -c "CI=true npx react-scripts test --watchAll=false"
```
