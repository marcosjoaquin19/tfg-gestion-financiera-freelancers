# Guión de demostración — FreelanceControl

> Camino reproducible para la defensa del TFG. Cada paso indica qué hacer,
> qué se debería ver y qué decir. Tiempo total estimado: **5–7 minutos**.
>
> **Guion vigente de la defensa:** `defensa_final/01_GUION_DEFENSA_35MIN.md`.
> Esta guía usa los mismos datos: `seed_demo_defensa.py` (enero a septiembre
> 2026) y el extracto `defensa_final/demo/extracto_28sep_14oct.csv`. Las cifras
> son las del **14/10/2026** (simuladas con el código real el 27/09).

---

## 0. Preparación (antes de la defensa, NO en vivo)

### 0.1 Levantar el entorno

```bash
docker compose up -d
```

Esperar a que los tres servicios estén `Up` (db, api, frontend):

```bash
docker compose ps
curl -s http://localhost:8000/health      # {"status":"ok",...}
```

### 0.2 Entrenar el modelo base del clasificador (una sola vez por BD)

El clasificador de gastos necesita un modelo base entrenado. Si la base de
datos es nueva (o se recreó el volumen), hay que entrenarlo:

```bash
docker compose exec api python seed_modelo_base.py
# Esperado: {'mensaje': 'Modelo base entrenado', 'algoritmo': 'svm',
#            'precision': 0.76, 'n_ejemplos': 600, ...}

# El proceso del API cachea el modelo en memoria, así que reiniciarlo
# garantiza que tome el modelo recién entrenado:
docker compose restart api
```

> **Cómo saber si falta este paso:** si en la demo el clasificador devuelve
> "Otros" con confianza ~0.21 para *todas* las descripciones, el modelo base
> no está cargado. Correr este paso y reiniciar el API lo resuelve.
> Verificación rápida: `GET /ml/estado` debe responder
> `"tipo_modelo": "base", "modelo_base": true`.

### 0.3 Poblar los datos de demostración

```bash
docker compose exec api python seed_demo_defensa.py
```

Salida esperada:

```
Categorías Monotributo: 2 escalas (vigente desde 2026-08-01): ...
Usuario demo previo eliminado.
Usuario demo creado (id=NN, categoría G).
Ingresos: 27 ($37.300.000). Gastos: 65. Enero a septiembre de 2026.
Facturas: 8.

Datos de la defensa cargados.
  Login: demo@freelancecontrol.com / demo1234
```

> Se puede correr las veces que haga falta: borra y recrea el usuario demo
> (también lo que se haya cargado en los ensayos). **Correrlo la mañana del
> 14/10.**

### 0.4 Proyección y auditoría

**El 14/10 no pre-cargar la auditoría:** se ejecuta en vivo después de importar
el extracto. La proyección se genera sola al abrir Monotributo. Solo para
ensayos, estos comandos dejan todo calculado:

```bash
# Login y captura del token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -d "username=demo@freelancecontrol.com&password=demo1234" \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

curl -s -X POST http://localhost:8000/proyecciones/generar \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{}' > /dev/null

curl -s -X POST http://localhost:8000/alertas/ejecutar-auditoria \
  -H "Authorization: Bearer $TOKEN" > /dev/null
```

### 0.5 Checklist pre-defensa

- [ ] `docker compose ps` → 3 servicios `Up`
- [ ] `GET /ml/estado` → `"usa_modelo_base": true` (sin modelo propio todavía)
- [ ] `http://localhost:3000` abre el login
- [ ] Login `demo@freelancecontrol.com` / `demo1234` funciona
- [ ] Dashboard en **octubre, en cero** (se completa al importar el extracto)
- [ ] Monotributo: semáforo **rojo 109,4 %**, categoría G, "lo superarías en diciembre", sugiere **H**
- [ ] Video backup grabado y accesible (por si falla la red/proyector)

---

## 1. Login y panorama general (≈45 s)

**Hacer:** abrir `http://localhost:3000`, iniciar sesión con
`demo@freelancecontrol.com` / `demo1234`.

**Se ve:** dashboard de María Fernández, freelancer monotributista. Es 14 de
octubre y el mes todavía no tiene movimientos: se completa en el paso 4.

**Decir:**
> "FreelanceControl es un sistema de gestión financiera para monotributistas
> argentinos. Los datos que ven son de una freelancer de software con nueve
> meses de actividad, con meses de proyecto grande y meses flojos. Todo lo que voy a mostrar corre sobre datos reales
> persistidos en PostgreSQL."

---

## 2. Carga de gasto con clasificación automática (≈1 min) — HU-04

**Hacer:** ir a **Gastos** → nuevo gasto → escribir solo la descripción (por
ejemplo `Licencia Microsoft Office 365` o `Hosting servidor web`) y un monto.

**Se ve:** el sistema sugiere automáticamente una categoría con un valor de
confianza, sin que el usuario la elija. Si la confianza queda por debajo del
30%, sugiere "Otros" y marca el gasto para revisión.

> **Antes de la defensa, probá 2–3 descripciones reales** y quedate con las
> que el modelo clasifique con buena confianza (el modelo base tiene ~76% de
> precisión, así que no todas las descripciones aciertan). Así mostrás un caso
> de acierto claro y, si querés, uno que cae en "Otros" para introducir el
> paso siguiente (la corrección).

**Decir:**
> "La categoría la infiere un clasificador de lenguaje natural que corre
> **100% local** — Naive Bayes / SVM sobre TF-IDF. La descripción del gasto
> nunca sale del sistema; es una decisión de diseño por soberanía de datos.
> Si la confianza baja del 30%, el sistema sugiere 'Otros' y marca el gasto
> para revisión, en lugar de adivinar."

---

## 3. Corrección y aprendizaje (≈1 min) — HU-05

**Hacer:** tomar un gasto que haya quedado mal clasificado (o forzar uno),
corregir su categoría desde la pantalla **Clasificador** / edición de gasto.

**Se ve:** confirmación de que la corrección se guardó.

**Decir:**
> "Cuando corrijo una categoría pasan dos cosas. Primero, la corrección se
> guarda como ejemplo de entrenamiento y dispara un reentrenamiento en
> segundo plano, sin bloquear la interfaz. Segundo —y esto es clave— si
> vuelvo a cargar un gasto con esa misma descripción, el sistema devuelve mi
> corrección al instante con confianza 1.0, sin volver a preguntar. Reconoce
> variantes tipográficas: mayúsculas, tildes y espacios de más matchean igual."

---

## 4. Importación de extracto bancario (≈1 min) — HU-07

**Hacer:** ir a **Importar**, subir `defensa_final/demo/extracto_28sep_14oct.csv`
(34 filas, formato Galicia con `;` y punto de miles) y tocar **Analizar archivo**.

**Se ve:** columnas detectadas solas (Fecha, Concepto, Débito, Crédito), cada
movimiento con su categoría, y los avisos: **3 ya existen** (28 al 30/09, del
extracto anterior), **2 son una transferencia entre cuentas propias** (3 y 4/10),
**1 fila omitida** (fecha 31/09). Cuatro gastos quedan en "Otros" para revisar.
Al confirmar: **29 importados** (3 cobros por $ 3.460.000 y 26 gastos).

**Decir:**
> "El sistema detecta la estructura del archivo con heurísticas locales:
> reconoce los nombres de columna de distintos bancos argentinos y hasta el
> separador —Galicia exporta con punto y coma, otros con coma—. Marca los
> movimientos que ya existen para no duplicarlos. La importación es una
> transacción atómica: si algo falla, no queda nada a medias."

> **Nota:** archivos >10 MB se rechazan con HTTP 413; extensiones que no sean
> CSV/XLSX se rechazan antes de leer el contenido.

---

## 5. Auditoría automatizada (≈1 min) — HU-08

**Hacer:** ir a **Alertas** → ejecutar auditoría.

**Se ve (después de importar el extracto):** 5 alertas.
- **Gastos duplicados (2)** — dos "Suscripción Adobe Creative Cloud" de
  $ 38.000,00 (3 y 5 de junio) y dos "FIGMA PROFESSIONAL" de $ 21.000,00 (2 y 4
  de octubre, vinieron en el extracto).
- **Anomalía estadística** — "Servidor dedicado AWS Reserved" de $ 900.000,00 en
  julio, muy por encima de la media de Infraestructura en los últimos 6 meses.
- **Facturas vencidas (2)** — Consultora Aurora ($ 430.000,00, venció el 20/08)
  y Brand Studio ($ 980.000,00, venció el 08/10; su pago vino en el extracto el
  09/10 → marcarla pagada en Facturas).
- **Sin monotributo impago:** el extracto trajo el pago de octubre (día 7). Si
  se ejecuta la auditoría antes de importar, aparece la cuota de octubre
  ($ 230.313) como impaga.

**Decir:**
> "La auditoría corre cuatro detectores y acá vemos uno de cada tipo: gastos
> duplicados dentro de una ventana de tres días, anomalías estadísticas por
> z-score mayor a 2 sigma —fíjense que el servidor de $900.000 se desvía de la
> media de Infraestructura—, facturas vencidas sin cobrar, y la cuota de
> Monotributo del mes sin pagar. Un detalle de diseño: la anomalía solo se
> evalúa si la categoría tiene al menos 5 gastos, porque con menos datos la
> desviación estándar no es confiable. Las alertas resueltas se conservan como
> historial; las pendientes se regeneran en cada corrida para no duplicarlas."

---

## 6. Estado fiscal del Monotributo (≈1 min) — HU-09 + HU-10

> Valores del 14/10/2026 con la escala vigente desde el 1/8/2026 (simulados
> con el código real). Antes de esa fecha los números son otros, porque cambian
> los meses cerrados.

**Hacer:** ir a **Monotributo**.

**Se ve (14/10, después de importar):**
- Categoría actual: **G** (límite anual $ 53.995.799)
- Facturación real del año: **$ 40.760.000 → 75,5 %** del límite (antes de
  importar: $ 37.300.000 → 69,1 %)
- Proyección anual: **$ 59.093.741 → 109,4 %** del límite
- Semáforo: **ROJO** (proyección por encima del 90 %)
- "Lo superarías en **diciembre 2026**"; la categoría que cubre la proyección es la **H**
- Cuota de octubre **pagada** (vino en el extracto)

**Cómo se arma la proyección anual:** facturado real del año (hasta hoy) + el
mes en curso (lo mayor entre lo cobrado y lo esperado para un mes) + los meses
que faltan hasta diciembre según Prophet. La proyección se regenera sola si
cambiaron los ingresos, así que después de importar el CSV en vivo el semáforo
ya refleja los datos nuevos.

**Decir:**
> "Esta es la pantalla que cruza los dos modelos. Lo facturado en el año va
> por el 75 % del límite de la categoría G. Pero el sistema no se queda ahí:
> suma la proyección de Prophet hasta el cierre del año, y eso lleva la
> utilización al 109 %: semáforo rojo. No dice que me pasé: dice que a este
> ritmo me pasaría en diciembre, y que la categoría que cubriría esa
> facturación es la H. La decisión de recategorizarse es mía y de mi contador."

> **Distinción importante para la defensa:** el "75,5 %" es lo **ya facturado**
> (pasado); el semáforo se calcula sobre el porcentaje **proyectado** a fin de
> año (109,4 %). El sistema decide el color por la proyección, no por lo
> facturado a hoy.
>
> **Si preguntan por qué importar $ 3,46 M no movió la proyección:** el mes en
> curso cuenta lo mayor entre lo ya cobrado y lo esperado para un mes. Prophet
> espera unos $ 7,1 M para octubre; con $ 3,46 M cobrados, sigue mandando lo
> esperado.

---

## 7. Reporte mensual en PDF (≈45 s) — HU-13

**Hacer:** en el Dashboard, dejar el selector en el **último mes cerrado** (viene
preseleccionado; el 14-oct será septiembre 2026) y tocar **Descargar reporte PDF**.

**Se ve:** encabezado (nombre, período, hora de Argentina), resumen ejecutivo con
la variación contra el mes anterior, estado fiscal con **la escala que regía en
ese mes** (categoría, tope, cuota pagada / parcial / sin registrar),
gastos por categoría, facturación del período, alertas pendientes con nombres
legibles y el descargo al pie. Importes y porcentajes en formato argentino.

**Decir:**
> "El reporte es del mes cerrado, para archivar o mandarle al contador. Se arma
> de forma programática con ReportLab. Un detalle importante: la escala del
> Monotributo cambió el 1 de agosto, y el sistema guarda las dos escalas con su
> fecha de vigencia, así que un reporte de mayo evalúa la cuota y el tope con
> los valores de mayo, no con los de hoy. Y como sale de la aplicación, lleva
> consigo la aclaración de que no reemplaza a un contador matriculado."

> **Si preguntan por un mes anterior:** elegir mayo en el selector: la cuota
> figura "Pagada ($ 197.108,23)" con la escala vigente desde el 01/02/2026;
> septiembre figura "Pagada ($ 230.312,94)" con la de agosto.

---

## 8. Cierre (≈30 s)

**Decir:**
> "En resumen: un sistema que automatiza la clasificación de gastos con ML
> local respetando la privacidad, audita los registros, proyecta la
> facturación y anticipa el riesgo de recategorización fiscal. Está
> contenedorizado con Docker, cubierto por 115 tests automatizados y las 17
> historias de usuario del backlog están implementadas y verificadas."

---

## Apéndice — Datos del usuario demo

| Dato | Valor |
|---|---|
| Nombre | María Fernández |
| Email | `demo@freelancecontrol.com` |
| Password | `demo1234` |
| Categoría Monotributo | D |
| Período de datos | Enero–Mayo 2026 |
| Ingresos | 15 (3/mes, 5 meses) |
| Gastos | 36 (en 11 categorías; incluye 2 marcados como duplicados) |
| Facturas | 6 (2 pagadas, 3 pendientes vigentes, 1 vencida sin cobrar) |
| Alertas al auditar | 4 (una de cada tipo) |

## Apéndice — Plan B si algo falla en vivo

| Falla | Acción |
|---|---|
| La red/proyector falla | Reproducir el **video backup** |
| El frontend no levanta | Mostrar la API por Swagger en `http://localhost:8000/docs` |
| Datos raros / corruptos | Re-correr `docker compose exec api python seed_demo.py` |
| El semáforo no aparece | Confirmar categorías: el seed las asegura; si no, correr `seed_categorias_monotributo.py` |
| El clasificador devuelve "Otros" siempre (conf ~0.21) | Falta el modelo base: correr `seed_modelo_base.py` y `docker compose restart api` (paso 0.2) |
| Una pantalla queda vacía | Re-disparar proyecciones y auditoría (paso 0.4) |
