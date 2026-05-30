# Guión de demostración — FreelanceControl

> Camino reproducible para la defensa del TFG. Cada paso indica qué hacer,
> qué se debería ver y qué decir. Tiempo total estimado: **5–7 minutos**.

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

### 0.2 Poblar los datos de demostración

```bash
docker compose exec api python seed_demo.py
```

Salida esperada:

```
Categorías Monotributo: 11 creadas, 0 actualizadas.
Usuario demo previo eliminado.        (solo si ya existía)
Usuario demo creado (id=NN).
Ingresos y gastos creados (enero a mayo 2026).
Facturas creadas (6).
Seed demo completado.
  Login: demo@freelancecontrol.com / demo1234
```

> El seed es **idempotente**: se puede correr varias veces sin romper nada.
> Asegura por sí mismo que las categorías de Monotributo existan, así que
> un solo comando deja todo listo.

### 0.3 Generar proyecciones y auditoría (para que el demo tenga datos vivos)

Estos dos se disparan desde la UI durante la demo, pero conviene pre-cargarlos
para que las pantallas no aparezcan vacías si se navega en otro orden:

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

### 0.4 Checklist pre-defensa

- [ ] `docker compose ps` → 3 servicios `Up`
- [ ] `http://localhost:3000` abre el login
- [ ] Login `demo@freelancecontrol.com` / `demo1234` funciona
- [ ] Dashboard muestra ingresos/gastos (no vacío)
- [ ] Pantalla Monotributo muestra semáforo **rojo** y sugiere categoría **E**
- [ ] Video backup grabado y accesible (por si falla la red/proyector)

---

## 1. Login y panorama general (≈45 s)

**Hacer:** abrir `http://localhost:3000`, iniciar sesión con
`demo@freelancecontrol.com` / `demo1234`.

**Se ve:** dashboard de María Fernández, freelancer monotributista, con
ingresos y gastos de enero a mayo 2026.

**Decir:**
> "FreelanceControl es un sistema de gestión financiera para monotributistas
> argentinos. Los datos que ven son de un freelancer de software con cinco
> meses de actividad. Todo lo que voy a mostrar corre sobre datos reales
> persistidos en PostgreSQL."

---

## 2. Carga de gasto con clasificación automática (≈1 min) — HU-04

**Hacer:** ir a **Gastos** → nuevo gasto → escribir solo la descripción, por
ejemplo `Suscripción Adobe Creative Cloud`, y un monto.

**Se ve:** el sistema sugiere automáticamente la categoría (**Suscripciones**)
con un valor de confianza, sin que el usuario la elija.

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

**Hacer:** ir a **Importar**, subir un CSV de banco (ver archivos de ejemplo
en `docs/extractos_ejemplo/`, o el de Galicia con `;`).

**Se ve:** vista previa de los primeros movimientos, columnas detectadas
automáticamente, y marca de posibles duplicados.

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

**Se ve:** se generan alertas de varios tipos. Con los datos del seed:
- **2 anomalías estadísticas** (gastos muy por encima de la media de su categoría — la notebook y el monitor)
- **3 discrepancias de facturación** (facturas vencidas sin cobrar)
- **1 monotributo impago** (no hay pago de la cuota del mes en curso)

**Decir:**
> "La auditoría corre cuatro detectores: gastos duplicados dentro de una
> ventana de tres días, anomalías estadísticas por z-score mayor a 2 sigma,
> facturas vencidas sin cobrar, y la cuota de Monotributo del mes sin pagar.
> Las alertas ya resueltas se conservan como historial; las pendientes se
> regeneran en cada corrida para no acumular duplicados."

---

## 6. Estado fiscal del Monotributo (≈1 min) — HU-09 + HU-10

**Hacer:** ir a **Monotributo**.

**Se ve (con los datos del seed):**
- Categoría actual: **D** (límite anual $16.450.000)
- Facturación real del año: ~$13,5 M → **82%** del límite
- Proyección anual (Prophet): ~$21,3 M → **129%** del límite
- Semáforo: **ROJO**
- Sugerencia: recategorizar a **E**

**Decir:**
> "Esta es la pantalla que cruza los dos modelos. El acumulado real va por el
> 82% del límite de la categoría D. Pero el sistema no se queda en el presente:
> proyecta los ingresos con Prophet hasta el cierre del año fiscal, y esa
> proyección supera el límite. Por eso el semáforo está en rojo y sugiere
> pasar a categoría E **antes** de que AFIP fuerce la recategorización.
> Es el valor diferencial: anticipa el riesgo fiscal en vez de reportarlo
> cuando ya es tarde."

---

## 7. Reporte mensual en PDF (≈45 s) — HU-13

**Hacer:** descargar el reporte PDF de abril 2026.

**Se ve:** PDF con encabezado, resumen ejecutivo (con comparativa vs mes
anterior), estado fiscal, distribución de gastos por categoría, facturación
y auditoría. Montos en formato argentino ($ 1.234.567,89). Disclaimer al pie.

**Decir:**
> "Finalmente, el usuario puede descargar un reporte mensual consolidado en
> PDF para archivar o compartir con su contador. Se genera de forma
> programática con ReportLab, usa formato argentino de pesos en todo el
> documento e incluye un disclaimer aclarando que no reemplaza el
> asesoramiento de un contador matriculado."

---

## 8. Cierre (≈30 s)

**Decir:**
> "En resumen: un sistema que automatiza la clasificación de gastos con ML
> local respetando la privacidad, audita los registros, proyecta la
> facturación y anticipa el riesgo de recategorización fiscal. Está
> contenedorizado con Docker, cubierto por 97 tests automatizados y las 13
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
| Gastos | 35 (7/mes, en 9 categorías) |
| Facturas | 6 (pagadas, pendientes y una vencida) |

## Apéndice — Plan B si algo falla en vivo

| Falla | Acción |
|---|---|
| La red/proyector falla | Reproducir el **video backup** |
| El frontend no levanta | Mostrar la API por Swagger en `http://localhost:8000/docs` |
| Datos raros / corruptos | Re-correr `docker compose exec api python seed_demo.py` |
| El semáforo no aparece | Confirmar categorías: el seed las asegura; si no, correr `seed_categorias_monotributo.py` |
| Una pantalla queda vacía | Re-disparar proyecciones y auditoría (paso 0.3) |
