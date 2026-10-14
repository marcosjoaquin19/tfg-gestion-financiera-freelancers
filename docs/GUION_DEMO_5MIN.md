# Guión de demo — versión cronometrada (5 minutos)

> Versión condensada de `DEMO.md` para la **defensa en vivo**. Objetivo: mostrar
> el valor del sistema en 5 minutos sin perderse en detalles. Cada bloque indica
> el tiempo, qué hacer en pantalla y la frase clave para decir.
>
> **Antes de empezar** (ya hecho en la preparación, ver `DEMO.md` §0):
> sistema levantado, modelo base entrenado, seed demo cargado, sesión iniciada
> como `demo@freelancecontrol.com` / `demo1234`. Tener el navegador ya en el
> Dashboard.

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

**En pantalla:** ir a **Importar** → subir `defensa_final/demo/extracto_28sep_14oct.csv`
→ **Analizar archivo**.

**Decir:**
> "Para evitar la carga manual, importo el extracto del banco: del 28 de
> septiembre a hoy. Es un CSV con formato Galicia, punto y coma y punto de
> miles. El sistema detecta la estructura con heurísticas locales —reconoce las
> columnas y el separador sin que yo configure nada— y antes de guardar me
> avisa: tres movimientos ya estaban (los importé con el extracto anterior),
> dos son una transferencia entre mis propias cuentas y no son facturación, y
> una fila tiene una fecha que no existe, 31 de septiembre."

**En pantalla:** mostrar la vista previa (columnas detectadas, categorías, avisos)
y confirmar: **29 movimientos importados**.

**Decir:**
> "La importación es una transacción atómica: si algo falla, no queda nada a
> medias. Acepta CSV y Excel, rechaza archivos de más de 10 MB y otros formatos."

---

## ⏱ 2:30 – 3:30 · Auditoría automática (Alertas)

**En pantalla:** ir a **Auditoría** → *Ejecutar auditoría*.

**Decir:**
> "La auditoría corre cinco detectores sobre los registros: gastos duplicados
> en una ventana de tres días, anomalías estadísticas por z-score mayor a dos
> sigma, facturas vencidas sin cobrar, la cuota de Monotributo del mes sin
> pagar, y transferencias entre cuentas propias del usuario —que si no se
> detectan, inflan la facturación con ingresos que no son facturación real."

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
> "Esta es la pantalla que cruza los dos modelos. Lo facturado en el año va por
> el **75 % del límite** de la categoría G. Si miráramos solo el presente, todo
> tranquilo. Pero el sistema suma la proyección de Prophet hasta el cierre del
> año, y la utilización llega al **109 %**: **semáforo rojo**. No dice que me
> pasé: dice que a este ritmo me pasaría **en diciembre**, y que la categoría
> que cubriría esa facturación es la **H**. La decisión es mía y de mi contador."

> ⚠️ Valores del 14/10/2026 (simulados con el código real). Si se ensaya antes,
> los números son otros porque cambian los meses cerrados. Verde por debajo del
> 70 %, amarillo entre 70 y 90, rojo por encima de 90.

**Decir (remate):**
> "Este es el valor diferencial: el sistema anticipa el riesgo fiscal mirando el
> futuro proyectado, no solo lo ya facturado."

---

## ⏱ 4:30 – 5:00 · Reporte PDF + cierre (Reportes)

**En pantalla:** en el Dashboard, dejar el selector en el **último mes cerrado** (viene preseleccionado) → *Descargar reporte PDF*. Abrirlo brevemente.

**Decir:**
> "Finalmente, el usuario descarga un reporte mensual en PDF para su contador:
> resumen, estado fiscal, gastos por categoría, facturación y auditoría, todo en
> formato argentino. En resumen: clasificación con IA respetando la privacidad,
> importación automática, auditoría y anticipación del riesgo fiscal. Está
> contenedorizado, cubierto por 115 tests y con las 17 historias de usuario
> del backlog implementadas. Gracias."

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

- [ ] Navegador en el Dashboard, sesión `demo@freelancecontrol.com` / `demo1234` iniciada
- [ ] Esa mañana: `docker compose exec api python seed_demo_defensa.py`
- [ ] `defensa_final/demo/extracto_28sep_14oct.csv` a mano para arrastrar (Escritorio → TFG_Defensa → demo)
- [ ] **No** ejecutar la auditoría ni importar antes: son parte de la demo
- [ ] Semáforo Monotributo en **rojo 109,4 %**, sugiere **H**
- [ ] Zoom del navegador al 100–110% para que se lea de lejos
- [ ] Slides abiertos en otra ventana para volver al cierre
