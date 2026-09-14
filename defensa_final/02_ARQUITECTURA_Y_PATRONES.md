# Arquitectura y patrones de diseño — FreelanceControl

> **Para qué sirve este documento.** Es el índice de consulta rápida durante la
> defensa oral. Si el tribunal pregunta *"¿dónde manejás X?"* o *"¿qué patrón
> usaste y por qué?"*, la respuesta está acá con archivo y línea.
>
> **Cómo buscar en el código:** todos los puntos con una decisión de diseño
> documentada llevan el marcador literal `PATRÓN:` (con tilde). Buscar esa
> cadena en el editor devuelve los 32 puntos anotados en 16 archivos.
>
> ```bash
> grep -rn "PATRÓN:" app frontend/src
> ```

---

## 1 · Arquitectura general

El sistema es una **aplicación web cliente–servidor en tres capas físicas**
(navegador → API → base de datos), y dentro del backend, una **arquitectura en
capas (layered architecture)** de cuatro niveles.

```
┌───────────────────────────────────────────────────────────────┐
│  FRONTEND — React 19 (SPA)                                    │
│  pages/ (13 pantallas) · components/ · api.js (cliente HTTP)  │
└──────────────────────────┬────────────────────────────────────┘
                           │  HTTP/JSON + JWT (Bearer)
┌──────────────────────────▼────────────────────────────────────┐
│  BACKEND — FastAPI                                            │
│                                                               │
│  routers/   (12)  ← HTTP: rutas, códigos de estado, permisos  │
│      │                                                        │
│  schemas/   (6)   ← DTO: validación de entrada/salida         │
│      │                                                        │
│  services/  (9)   ← LÓGICA DE NEGOCIO (el corazón del TFG)    │
│      │                                                        │
│  models/    (9)   ← ORM: mapeo objeto-relacional              │
└──────────────────────────┬────────────────────────────────────┘
                           │  SQLAlchemy
┌──────────────────────────▼────────────────────────────────────┐
│  PostgreSQL 15 · 9 tablas · migraciones con Alembic           │
└───────────────────────────────────────────────────────────────┘
```

**Por qué en capas y no todo en el router.** La regla que sostiene el diseño es:
*un router no calcula nada*. Recibe la petición, valida con el schema, llama a
un servicio y devuelve el resultado. Esto trajo tres beneficios concretos y
verificables en este proyecto:

1. **Testeabilidad.** Los 115 tests prueban los servicios directamente contra una
   base SQLite en memoria, sin levantar HTTP. La suite corre en 35 segundos.
2. **Reutilización real.** `monotributo_service.verificar_pago_monotributo()` lo
   usan el router de monotributo *y* el servicio de auditoría. Si la regla
   fiscal estuviera dentro del endpoint, habría que duplicarla.
3. **Un solo lugar por decisión.** El formato de moneda argentina vive en
   `app/services/formato.py`; lo consumen la auditoría y el PDF. Cambiar la
   convención es cambiar una función.

**Alternativa descartada:** un backend monolítico tipo Django con la lógica en
las vistas. Se descartó porque el núcleo del trabajo es la lógica financiera y
de ML: necesitaba estar aislada y testeable, no acoplada al ciclo de request.

---

## 2 · Tabla maestra: pregunta del tribunal → dónde está

| Si preguntan… | Archivo:línea | Patrón |
|---|---|---|
| ¿Cómo se conecta a la base? | [app/database.py:38](../app/database.py) | Factory · Singleton · Unit of Work |
| ¿Cómo protegés las rutas privadas? | [app/dependencies.py:40](../app/dependencies.py) | Inyección de dependencias · Guard |
| ¿Dónde se hashean las contraseñas? | [app/services/auth.py](../app/services/auth.py) | Facade de seguridad |
| ¿Dónde está el índice de módulos? | [app/main.py:78](../app/main.py) | Front Controller / registro de routers |
| ¿Cómo elegís entre Naive Bayes y SVM? | [app/services/ml_service.py:728](../app/services/ml_service.py) | **Strategy** |
| ¿Cómo se arma el clasificador? | [app/services/ml_service.py:699](../app/services/ml_service.py) | **Pipeline** |
| ¿Dónde se guarda el modelo entrenado? | [app/services/ml_service.py:713](../app/services/ml_service.py) | **Memento** (joblib + base64 → BD) |
| ¿Qué pasa si un usuario no tiene modelo? | [app/services/ml_service.py:794](../app/services/ml_service.py) | Lazy loading con cadena de fallback |
| ¿Cómo calculás la confianza del SVM? | [app/services/ml_service.py:826](../app/services/ml_service.py) | (decisión algorítmica, ver §4) |
| ¿Y si no hay datos para proyectar? | [app/services/prophet_service.py:91](../app/services/prophet_service.py) | **Strategy** + degradación elegante |
| ¿Cómo soportás 9 bancos distintos? | [app/services/csv_service.py:41](../app/services/csv_service.py) | **Adapter** / capa anticorrupción |
| ¿Dónde detectás el formato del archivo? | [app/services/csv_service.py:197](../app/services/csv_service.py) | Adapter (heurística local) |
| ¿Cómo evitás contar transferencias propias? | [app/services/csv_service.py:581](../app/services/csv_service.py) | Regla de dominio |
| ¿Qué pasa si el usuario ya corrigió esa categoría? | [app/services/ia_service.py:276](../app/services/ia_service.py) | **Cache-Aside** + Chain of Responsibility |
| ¿Y si se cae la API de IA? | [app/services/ia_service.py:49](../app/services/ia_service.py) | Fallback determinístico |
| ¿Cómo se crean las alertas? | [app/services/auditoria.py:48](../app/services/auditoria.py) | **Factory Method** |
| ¿Repite alertas que ya resolví? | [app/services/auditoria.py:66](../app/services/auditoria.py) | Idempotencia por huella |
| ¿Cómo orquestás los detectores? | [app/services/auditoria.py:222](../app/services/auditoria.py) | **Strategy** de reglas |
| ¿Cómo detectás montos atípicos? | [app/services/auditoria.py:110](../app/services/auditoria.py) | Desvío estándar sobre 6 meses |
| ¿Cómo se construye el PDF? | [app/services/reportes_service.py:406](../app/services/reportes_service.py) | **Builder** |
| ¿Cómo numerás las páginas del PDF? | [app/services/reportes_service.py:457](../app/services/reportes_service.py) | **Template Method** |
| ¿Dónde está el cálculo fiscal? | [app/services/monotributo_service.py:36](../app/services/monotributo_service.py) | Servicio de dominio |
| ¿Cómo maneja el frontend el token? | [frontend/src/api.js:23](../frontend/src/api.js) | **Interceptor** · Singleton |
| ¿Qué pasa si expira la sesión? | [frontend/src/api.js:32](../frontend/src/api.js) | Interceptor de respuesta |
| ¿Cómo bloqueás pantallas sin login? | [frontend/src/App.js:31](../frontend/src/App.js) | **Guard** / Protected Route |
| ¿Dónde está el descargo de responsabilidad? | [frontend/src/components/AvisoAlcance.js](../frontend/src/components/AvisoAlcance.js) | Single Source of Truth |

---

## 3 · Los patrones, uno por uno

Para cada patrón: **qué es**, **dónde está**, **por qué lo elegí** y **qué
alternativa descarté**. Este es el guion de la respuesta oral.

### 3.1 · Strategy — selección de algoritmo de clasificación

**Dónde:** `app/services/ml_service.py:728` (`_elegir_algoritmo`) y `:699`
(`_crear_pipeline`).

```python
def _elegir_algoritmo(n_ejemplos: int) -> str:
    return "svm" if n_ejemplos >= 100 else "naive_bayes"
```

**Qué resuelve.** El clasificador tiene que funcionar el primer día (usuario sin
datos, solo el dataset base de 600 ejemplos) y también cuando el usuario ya
acumuló cientos de gastos propios. Son dos escenarios estadísticos distintos y
ningún algoritmo gana en los dos.

**Por qué así.** Naive Bayes multinomial es fuerte con pocos datos porque asume
independencia entre términos: con el dataset base no sobreajusta. LinearSVC busca
el hiperplano de máximo margen, y eso necesita volumen — pero con más de 100
ejemplos propios supera claramente a Naive Bayes en este dominio.

El punto del patrón es que **el resto del código no sabe cuál se usó**.
`clasificar_gasto()` pide un pipeline y lo usa; la familia de algoritmos es
intercambiable detrás de una interfaz común (`fit` / `predict`), que es
exactamente la definición de Strategy.

**Alternativa descartada:** fijar un solo algoritmo. Se descartó porque medí
ambos: con el dataset base, Naive Bayes rinde mejor; con datos de usuario, SVM.
Elegir uno solo significaba aceptar el peor caso en la mitad de los escenarios.

**Segunda alternativa descartada:** un modelo de lenguaje (Groq) clasificando
cada gasto. Descartada por **soberanía de datos**: implicaba enviar la
descripción de cada gasto del usuario a un tercero. La decisión fue explícita y
está documentada en el docstring de `clasificar_gasto()`.

### 3.2 · Strategy + degradación elegante — proyecciones

**Dónde:** `app/services/prophet_service.py:91` (`generar_proyecciones`).

**Qué resuelve.** Prophet necesita al menos 10 ingresos y **dos meses distintos**
de historial: ajusta una tendencia sobre totales mensuales, y con una sola fila
el `fit` falla. Un usuario nuevo que carga todo junto rompería la pantalla.

**Por qué así.** En vez de mostrar un error, el sistema cambia de estrategia:
proyecta la media móvil con un rango de ±1 desvío estándar. El usuario siempre
ve una proyección; la calidad mejora sola cuando hay más historial.

**Alternativa descartada:** exigir un mínimo de datos y bloquear la pantalla.
Se descartó porque castiga justamente al usuario nuevo, que es el que más
necesita entender qué hace la herramienta.

### 3.3 · Adapter (capa anticorrupción) — importación bancaria

**Dónde:** `app/services/csv_service.py:41` (diccionarios de sinónimos) y `:197`
(`detectar_columnas_csv`).

**Qué resuelve.** Nueve bancos argentinos (Galicia, Santander, BBVA, Macro,
Nación, Brubank, ICBC, Mercado Pago, Naranja X) exportan extractos con nombres
de columna distintos: `Fecha`, `Fecha Mov.`, `Fecha de Operación`, `F. Mov`…
Y algunos usan débito/crédito en columnas separadas; otros, un importe con signo.

**Por qué así.** El caos externo se traduce a un **modelo interno único** antes
de tocar la lógica de negocio. El resto del sistema solo conoce un movimiento
con `fecha`, `descripción`, `monto` y `tipo`. El mapeo es declarativo: agregar
un décimo banco es agregar un sinónimo a una lista, sin tocar una línea de lógica.

**Alternativa descartada:** un parser por banco (`parse_galicia()`,
`parse_santander()`…). Se descartó porque no escala: cada banco nuevo era código
nuevo, y los bancos cambian el formato de sus exportaciones sin avisar.

**Segunda alternativa descartada:** pedirle al usuario que mapee las columnas a
mano. Se descartó porque elimina el valor de la funcionalidad — si tengo que
explicarle qué columna es cuál, ya perdí.

### 3.4 · Cache-Aside + Chain of Responsibility — clasificación de un gasto

**Dónde:** `app/services/ia_service.py:276` (`clasificar_gasto`).

**Cadena de resolución:**

1. ¿El usuario ya corrigió *esta misma descripción* antes? → devolver su
   corrección con confianza 1.0. **Es ground truth: no hay nada que predecir.**
2. Si no → invocar el clasificador ML local.
3. Si la confianza está por debajo del umbral → sugerir `"Otros"` y marcar
   `requiere_revision = True`.

**Por qué así.** Dos razones. La primera es de producto: si el usuario ya me
dijo que "Adobe Photoshop" es Software, volver a equivocarme en esa misma
descripción es inaceptable. La segunda es de honestidad del sistema: cuando el
modelo duda, **lo dice** en vez de adivinar. El campo `requiere_revision` es la
materialización de esa política.

**Detalle fino:** la comparación usa una forma canónica
(`ml_service.normalizar_descripcion`, línea 876): sin tildes, sin mayúsculas,
sin espacios múltiples. Así "Adobe Photoshop" y "adobe  photoshop" matchean.

**Alternativa descartada:** no guardar las correcciones y reentrenar siempre.
Se descartó porque el reentrenamiento es costoso y no garantiza que el modelo
aprenda ese caso puntual; la corrección explícita sí lo garantiza.

### 3.5 · Factory Method + idempotencia — auditoría

**Dónde:** `app/services/auditoria.py:48` (`_crear_alerta`), `:66`
(`_huella_alerta`), `:222` (`ejecutar_auditoria`).

**Qué resuelve.** Hay cinco detectores (duplicados, montos atípicos, facturas
impagas, monotributo sin pagar, transferencias entre cuentas propias). Cada uno
es una función independiente con la misma firma. `ejecutar_auditoria()` las
corre todas y persiste los resultados.

**Factory Method:** `_crear_alerta()` es el único punto donde se construye una
`AlertaAuditoria`. Si mañana la alerta necesita un campo nuevo, se agrega ahí y
los cinco detectores lo heredan.

**Idempotencia:** `_huella_alerta()` devuelve `(tipo, monto)` como identidad
estable de una condición. Si el usuario ya marcó una alerta como resuelta, la
siguiente corrida **no la regenera**. Sin esto, la auditoría sería ruido: el
usuario resuelve, vuelve a correr y aparece todo de nuevo.

> Se usa `(tipo, monto)` y no la descripción porque algunas descripciones varían
> entre corridas — incluyen promedios y desvíos recalculados.

**Alternativa descartada:** una jerarquía de clases `DetectorBase` con herencia.
Se descartó por sobreingeniería: cinco funciones con la misma firma ya dan el
polimorfismo necesario en Python, sin el peso de una jerarquía.

### 3.6 · Builder + Template Method — reporte PDF

**Dónde:** `app/services/reportes_service.py:406` (`generar_pdf_mensual`), `:457`
(`_pie_pagina`).

**Builder:** cada `_seccion_*()` devuelve una lista de elementos (encabezado,
resumen ejecutivo, monotributo, categorías, facturación, auditoría, pie).
`generar_pdf_mensual()` las concatena en una lista `historia` y ReportLab la
renderiza. Agregar una sección es agregar una función y una línea.

**Template Method:** `_pie_pagina()` se pasa a ReportLab como
`onFirstPage`/`onLaterPages`. Es la biblioteca la que decide *cuándo*
invocarlo — nosotros solo aportamos el paso variable del algoritmo.

**Por qué ReportLab y no WeasyPrint.** WeasyPrint necesita un motor de
renderizado HTML/CSS completo dentro del contenedor: pesa, arrastra
dependencias de sistema y falla distinto según la plataforma. ReportLab arma el
documento programáticamente. El costo es escribir más código; el beneficio es
un contenedor liviano y un PDF idéntico en cualquier máquina.

### 3.7 · Inyección de dependencias + Guard — seguridad de las rutas

**Dónde:** `app/dependencies.py:40` (`get_current_user`), `app/database.py:38`
(`get_db`).

**Qué resuelve.** Cada endpoint privado necesita dos cosas: una sesión de base
de datos y el usuario autenticado. En vez de que cada función las consiga por su
cuenta, FastAPI las **inyecta**:

```python
def listar_gastos(db: Session = Depends(get_db),
                  usuario: Usuario = Depends(get_current_user)):
```

**Por qué así.** Tres consecuencias directas:

1. **Imposible olvidarse la autorización por accidente.** Si falta el `Depends`,
   el endpoint no compila su firma con el usuario: la omisión es visible.
2. **La sesión siempre se cierra**, incluso ante una excepción — `get_db()` usa
   `yield` dentro de un `try/finally`.
3. **Los tests sustituyen las dependencias** con `app.dependency_overrides`:
   por eso la suite corre contra SQLite en memoria sin tocar PostgreSQL.

**Alternativa descartada:** un middleware global que validara el token para
todas las rutas. Se descartó porque el sistema tiene rutas públicas (login,
registro, health) y la excepción por URL en un middleware es frágil: un error
de string deja una ruta privada abierta. Con `Depends`, la protección es
explícita, endpoint por endpoint.

### 3.8 · Interceptor — cliente HTTP del frontend

**Dónde:** `frontend/src/api.js:23` (request) y `:32` (response).

**Qué resuelve.** Trece pantallas hacen llamadas a la API. Las dos
preocupaciones transversales — adjuntar el token y reaccionar a un 401 —
están **una sola vez**, en los interceptores de axios, no repetidas en cada
`fetch`.

**Detalle no trivial:** el interceptor de respuesta excluye `/auth/login` y
`/auth/register`. En esos endpoints un 401 significa "contraseña incorrecta", no
"sesión expirada": si redirigiera al login, el usuario nunca vería el mensaje de
error. Está comentado en el código porque es un caso que se descubrió probando.

**Alternativa descartada:** `fetch` directo en cada pantalla. Se descartó porque
son 13 pantallas × 2 preocupaciones = 26 lugares donde olvidarse algo.

### 3.9 · Factory · Singleton · Unit of Work — capa de datos

**Dónde:** `app/database.py`.

- **Singleton:** un único `engine` con pool (5 conexiones + 10 de desborde) para
  todo el proceso. Abrir una conexión por request sería el cuello de botella.
- **Factory:** `sessionmaker()` fabrica sesiones configuradas de forma idéntica.
- **Unit of Work:** cada `Session` agrupa las operaciones de un request y las
  confirma o revierte en bloque. Es lo que hace que una importación de 200
  movimientos entre entera o no entre.

Estos tres los aporta SQLAlchemy: el mérito no es haberlos implementado, es
haberlos **usado deliberadamente** y saber qué problema resuelve cada uno.

### 3.10 · Single Source of Truth — texto legal y formato de moneda

**Dónde:** `frontend/src/components/AvisoAlcance.js` y
`app/services/formato.py`.

Dos casos del mismo principio: un enunciado que debe ser idéntico en varios
lugares vive en **un** lugar. El descargo de alcance aparece en cinco pantallas
y en el PDF; el formato de pesos, en las alertas y en el reporte. Si cambia, se
cambia una vez.

---

## 4 · Decisiones técnicas que no son patrones pero sí preguntas probables

### 4.1 · Confianza del SVM — por qué no softmax

**Dónde:** `app/services/ml_service.py:826` (`_confianza_svm`).

LinearSVC no devuelve probabilidades, devuelve distancias al hiperplano
(`decision_function`). Aplicar softmax sobre esas distancias **no funciona**
con 12 clases: reparte densidad entre todas y hasta las predicciones correctas
quedan en ~0.20, por debajo de cualquier umbral razonable.

La solución fue usar la **brecha entre las dos mejores clases**: vale 0 si dos
categorías empatan (el modelo realmente duda) y crece cuando hay una dominante.
Se mapea a [0,1) con `1 - e^(-brecha)`, que es monótona y acotada.

> Esta es una buena respuesta para la pregunta *"¿qué te costó del ML?"*: el
> problema no fue entrenar el modelo, fue **medir cuánta confianza tenerle**.

### 4.2 · Por qué el entrenamiento corre local y no en la nube

Política de soberanía de datos del trabajo: la descripción de un gasto puede
revelar clientes, proveedores y hábitos. Se entrena con scikit-learn dentro del
contenedor, el modelo se serializa y se guarda en la base del propio sistema.
**Ningún texto libre del usuario sale hacia un tercero.**

Groq se usa únicamente para redactar el resumen mensual, y se le envían **solo
totales numéricos agregados** — nunca descripciones. Si la clave no está
configurada, el resumen se arma con un fallback determinístico local y la
aplicación funciona igual.

### 4.3 · Por qué la escala de monotributo está versionada en un seed

**Dónde:** `seed_categorias_monotributo.py`.

Los valores de ARCA cambian por inflación (la escala vigente es la de agosto
2026, +16,8 % sobre la de junio). Cada escala publicada se conserva como una
constante fechada y `ESCALA_VIGENTE` toma la más reciente: cargar una escala
nueva es agregar una constante, sin tocar la aplicación.

**Limitación conocida y asumida** (está documentada en el archivo): la tabla
tiene un índice único sobre `letra`, así que solo puede alojar una escala a la
vez. Guardar el histórico en base requeriría un unique compuesto
(`letra + actividad + fecha_vigencia`) y cambiar las consultas de
`monotributo_service`. Se documentó en vez de ocultarse.

### 4.4 · Límite de responsabilidad del sistema

**Dónde:** `frontend/src/components/AvisoAlcance.js` (5 pantallas) y
`app/services/reportes_service.py:388` (pie del PDF).

> *FreelanceControl informa, proyecta y alerta sobre la base de los datos que
> usted carga. No constituye asesoramiento contable, fiscal ni financiero, y no
> reemplaza la intervención de un profesional matriculado.*

El descargo está **en el producto**, no solo en la documentación:

| Pantalla | Aclaración específica |
|---|---|
| Monotributo | La categorización definitiva la determina ARCA |
| Proyecciones | Son estimaciones estadísticas, no garantía de ingresos |
| Recomendaciones | Reglas sobre sus propios datos, carácter orientativo |
| Resumen IA | Redactado por un modelo de lenguaje; verificar cifras |
| Auditoría | Señala posibles inconsistencias, no dictamina error |
| **PDF** | Además: verificar contra documentación respaldatoria |

Va también en el PDF porque el reporte es el artefacto que **sale** de la
aplicación y circula fuera de ella: tiene que llevar el límite consigo.

---

## 5 · Mapa de módulos — dónde se maneja cada cosa

| Funcionalidad | Router | Servicio | Modelo |
|---|---|---|---|
| Registro y login | `auth.py` | `auth.py` | `usuario.py` |
| Ingresos | `ingresos.py` | — | `ingreso.py` |
| Gastos (+ clasificación) | `gastos.py` | `ia_service.py` → `ml_service.py` | `gasto.py` |
| Facturas | `facturas.py` | — | `factura.py` |
| Auditoría | `alertas.py` | `auditoria.py` | `alerta_auditoria.py` |
| Proyecciones | `proyecciones.py` | `prophet_service.py` | `proyeccion.py` |
| Importación CSV/Excel | `importar.py` | `csv_service.py` | `ingreso.py` + `gasto.py` |
| Monotributo | `monotributo.py` | `monotributo_service.py` | `categoria_monotributo.py` |
| Clasificador (playground) | `ml.py` | `ml_service.py` | `modelo_clasificador.py` + `cache_clasificacion.py` |
| Resumen IA | `resumen.py` | `ia_service.py` | — |
| Recomendaciones | `recomendaciones.py` | `ia_service.py` | — |
| Reportes PDF | `reportes.py` | `reportes_service.py` | — |

**Volumen:** 6.140 líneas de backend · 4.609 de frontend · 115 tests
automatizados · 9 tablas · 12 routers · 9 servicios · 13 pantallas.
