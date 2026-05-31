# Guión de demo — versión cronometrada (5 minutos)

> Versión condensada de `DEMO.md` para la **defensa en vivo**. Objetivo: mostrar
> el valor del sistema en 5 minutos sin perderse en detalles. Cada bloque indica
> el tiempo, qué hacer en pantalla y la frase clave para decir.
>
> **Antes de empezar** (ya hecho en la preparación, ver `DEMO.md` §0):
> sistema levantado, modelo base entrenado, seed demo cargado, sesión iniciada
> como `demo@freelancecontrol.com`. Tener el navegador ya en el Dashboard.

---

## ⏱ 0:00 – 0:30 · Apertura (Dashboard)

**En pantalla:** Dashboard de María Fernández, con ingresos y gastos de 5 meses.

**Decir:**
> "FreelanceControl es un sistema de gestión financiera para monotributistas
> argentinos. Lo que ven son datos reales de un freelancer de software con cinco
> meses de actividad, persistidos en PostgreSQL. Voy a mostrar las cuatro
> capacidades que lo diferencian: clasificación con IA local, importación
> bancaria, auditoría automática y monitoreo fiscal anticipado."

---

## ⏱ 0:30 – 1:30 · Clasificación + aprendizaje (Gastos / Clasificador)

**En pantalla:** ir a **Gastos** → nuevo gasto → escribir solo una descripción
(p. ej. `Licencia anual JetBrains`) y un monto.

**Decir:**
> "Cuando cargo un gasto, solo escribo la descripción. Un clasificador de
> lenguaje natural le asigna una categoría con un valor de confianza. Y lo
> importante: **corre 100% local**. La descripción de un gasto es información
> sensible; nunca sale del sistema."

**En pantalla:** corregir una categoría (Clasificador → descripción + categoría
correcta → Corregir). Volver a clasificar la misma descripción.

**Decir:**
> "Si corrijo una clasificación, el sistema aprende: la próxima vez que aparezca
> esa misma descripción la reconoce al instante, con confianza máxima, y además
> alimenta el reentrenamiento del modelo."

> 💡 *Si preguntan por números:* el modelo base tiene **76% de exactitud** sobre
> 12 categorías, medido por validación cruzada de 5 particiones.

---

## ⏱ 1:30 – 2:30 · Importación bancaria (Importar)

**En pantalla:** ir a **Importar** → subir `docs/extractos_ejemplo/galicia.csv`.

**Decir:**
> "Para evitar la carga manual, importo el extracto del banco. Este es un CSV de
> Galicia, que usa punto y coma como separador. El sistema detecta la estructura
> con heurísticas locales —reconoce las columnas y el separador sin que yo
> configure nada— y marca los movimientos que ya existen para no duplicarlos."

**En pantalla:** mostrar la vista previa (columnas detectadas, tipos, duplicados).

**Decir:**
> "La importación es una transacción atómica: si algo falla, no queda nada a
> medias. Acepta CSV y Excel, rechaza archivos de más de 10 MB y otros formatos."

---

## ⏱ 2:30 – 3:30 · Auditoría automática (Alertas)

**En pantalla:** ir a **Alertas** → ejecutar auditoría.

**Decir:**
> "La auditoría corre cuatro detectores sobre los registros: gastos duplicados
> en una ventana de tres días, anomalías estadísticas por z-score mayor a dos
> sigma, facturas vencidas sin cobrar, y la cuota de Monotributo del mes sin
> pagar. Con estos datos se disparan alertas de cada tipo."

**En pantalla:** señalar la anomalía (el servidor de $900.000 en Infraestructura)
y la factura vencida.

**Decir:**
> "Fíjense en esta: detectó un gasto de infraestructura muy por encima de la
> media de su categoría. Y esta otra, una factura que venció sin cobrarse. Las
> alertas resueltas se conservan como historial; las pendientes se regeneran en
> cada corrida."

---

## ⏱ 3:30 – 4:30 · El diferencial: monitoreo fiscal (Monotributo)

**En pantalla:** ir a **Monotributo**.

**Decir:**
> "Esta es la pantalla que cruza los dos modelos. El acumulado real va por el
> **48% del límite** de la categoría D. Si miráramos solo el presente, todo
> tranquilo. Pero el sistema proyecta los ingresos con Prophet hasta el cierre
> del año fiscal, y esa proyección supera el límite. Por eso el **semáforo está
> en rojo** y sugiere recategorizar a la **E**, antes de que AFIP lo fuerce."

**Decir (remate):**
> "Este es el valor diferencial: el sistema anticipa el riesgo fiscal mirando el
> futuro proyectado, no solo lo ya facturado."

---

## ⏱ 4:30 – 5:00 · Reporte PDF + cierre (Reportes)

**En pantalla:** descargar el reporte PDF del mes. Abrirlo brevemente.

**Decir:**
> "Finalmente, el usuario descarga un reporte mensual en PDF para su contador:
> resumen, estado fiscal, gastos por categoría, facturación y auditoría, todo en
> formato argentino. En resumen: clasificación con IA respetando la privacidad,
> importación automática, auditoría y anticipación del riesgo fiscal. Está
> contenedorizado, cubierto por 97 tests y con las 13 historias de usuario
> implementadas. Gracias."

---

## Plan B durante la demo (si algo falla)

| Falla | Acción inmediata |
|---|---|
| El frontend no responde | Mostrar la API por Swagger: `localhost:8000/docs` |
| El clasificador devuelve "Otros" siempre | Falta el modelo base: ya debería estar; no improvises, pasá al siguiente módulo |
| Una pantalla queda vacía | Re-disparar auditoría/proyecciones (ver `DEMO.md` §0.4) |
| Se cae la red | Continuar: todo corre local, no se necesita internet (salvo el resumen Groq, que tiene fallback) |
| Pánico total | El reporte PDF ya descargado y los slides alcanzan para contar todo |

---

## Checklist de 1 minuto antes de entrar

- [ ] Navegador en el Dashboard, sesión `demo@freelancecontrol.com` iniciada
- [ ] `docs/extractos_ejemplo/galicia.csv` a mano para arrastrar
- [ ] Auditoría y proyecciones ya ejecutadas una vez (pantallas con datos)
- [ ] Semáforo Monotributo en **rojo**, sugiere **E**
- [ ] Zoom del navegador al 100–110% para que se lea de lejos
- [ ] Slides abiertos en otra ventana para volver al cierre
