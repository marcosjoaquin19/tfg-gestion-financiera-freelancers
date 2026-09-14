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
| [02_ARQUITECTURA_Y_PATRONES.md](02_ARQUITECTURA_Y_PATRONES.md) | Índice "pregunta del tribunal → `archivo:línea`". Cada patrón con su justificación y la alternativa descartada. | Ronda de preguntas |
| `tesis/` | El PDF de la tesis **aprobada**, como fuente de verdad de datos y terminología | Consulta |
| [gen_slides_defensa.js](gen_slides_defensa.js) | Generador reproducible del deck. Los slides se editan **acá**, no en PowerPoint. | Al cambiar el guion |
| `slides/` | `FreelanceControl_Defensa_Final.pptx` — 30 slides (27 + 3 de anexo) | Bloques 1, 2, 5 y 6 |
| `video/` | Video explicativo del sistema | Bloque 3 |
| [gen_pdfs_lectura.py](gen_pdfs_lectura.py) | Convierte los documentos a PDF para leerlos cómodo | Antes de cada lectura |
| `lectura/` | Los mismos documentos en PDF (generados, no se versionan) | Para leer y anotar |

---

## Estructura de los 35 minutos

| Bloque | Reloj | Soporte |
|---|---|---|
| 1 · Apertura: el problema | 0:00 – 3:00 | Slides |
| 2 · Propuesta y **límites** | 3:00 – 6:00 | Slides |
| 3 · Video explicativo | 6:00 – 10:00 | Video |
| 4 · **Demo en vivo** | 10:00 – 24:00 | App |
| 5 · Código y decisiones | 24:00 – 33:00 | Editor + slides |
| 6 · Cierre | 33:00 – 35:00 | Slides |

---

## Regenerar la presentación

Los slides no se editan a mano: se generan desde código, así se mantienen
sincronizados con el guion y con los datos reales del proyecto.

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

### Estructura del deck

| Slides | Bloque |
|---|---|
| 1 – 4 | Apertura: el problema |
| 5 – 9 | Propuesta, alcance y límites |
| 10 | Transición al video |
| 11 | Guion de la demo en vivo |
| 12 – 23 | Código y decisiones de diseño |
| 24 – 27 | Cierre: resultados y trabajo futuro |
| 28 – 30 | **Anexo**: respaldo para la ronda de preguntas |

Las tres últimas no se muestran en la exposición: están para proyectar si el
tribunal pregunta por los detectores de auditoría, los costos o dónde vive una
funcionalidad concreta en el código.

---

## Acceso desde el escritorio

`~/Desktop/TFG_Defensa` es un **enlace simbólico** a esta carpeta, no una copia:
lo que se abre desde el escritorio y lo que vive en el repositorio son el mismo
archivo. No hay dos versiones que se puedan desfasar.

Para volver a crearlo si se borra:

```bash
ln -s /Users/marcosjoaquin/proyecto-tfg/defensa_final ~/Desktop/TFG_Defensa
```

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
   aparece en Monotributo, Proyecciones, Recomendaciones, Resumen IA y Auditoría,
   y el mismo enunciado va en el pie del reporte PDF
   (`app/services/reportes_service.py`).

2. **Mostrar el prototipo funcionando**, en particular: clasificador, auditoría,
   importación, proyección, estado fiscal y reporte PDF.
   Los seis están cubiertos en el bloque 4, en ese orden narrativo.

---

## Buscar decisiones de diseño en el código

Todos los puntos con una decisión de diseño documentada llevan el marcador
literal `PATRÓN:` (con tilde):

```bash
grep -rn "PATRÓN:" app frontend/src
```

Devuelve 32 anotaciones en 16 archivos. El desarrollo completo de cada una
—qué resuelve, por qué se eligió, qué alternativa se descartó— está en
[02_ARQUITECTURA_Y_PATRONES.md](02_ARQUITECTURA_Y_PATRONES.md).

---

## Preparar el entorno antes de la defensa

```bash
docker compose up -d
```

Esperar a que los tres contenedores queden en estado saludable y entrar a
`http://localhost:3000` con `demo@freelancecontrol.com` / `demo1234`.

> ⚠️ **Importante:** el contenedor `api` **no tiene volumen montado**. Si se
> edita cualquier archivo del backend hay que reconstruirlo antes de que el
> cambio tome efecto:
>
> ```bash
> docker compose build api && docker compose up -d api
> ```
>
> El frontend sí recarga en caliente.

Verificación rápida de que todo está sano:

```bash
docker exec tfg_api python -m pytest -q
```

Debe dar **115 pruebas en verde**.
