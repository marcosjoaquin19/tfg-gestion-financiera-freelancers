# Preguntas anticipadas del jurado — y cómo responderlas

> Preparación para la ronda de preguntas de la defensa. Cada entrada tiene la
> pregunta probable, una respuesta concisa para decir, y —cuando aplica— el
> respaldo técnico por si profundizan. Las respuestas se apoyan en decisiones
> reales del código, no en generalidades.

---

## Sobre el clasificador de gastos (ML)

### ¿Por qué clasificás localmente y no usás un LLM como Groq o ChatGPT para todo?
**Respuesta corta:** Por soberanía de datos. La descripción de un gasto es
información financiera sensible —revela hábitos de consumo, proveedores,
clientes—. Enviarla a un servicio externo significaría ceder ese historial a un
tercero. El clasificador local resuelve la tarea con un 76% de exactitud sobre
12 categorías, suficiente para asistir al usuario, sin sacar el dato del sistema.

**Si profundizan:** Groq sí se usa, pero acotado a generar el resumen y las
recomendaciones, y solo sobre **datos numéricos agregados** (totales por
categoría, conteos), nunca descripciones individuales. Y siempre con un fallback
local determinístico por si el servicio no está.

### ¿76% no es poco? ¿Cómo lo justificás?
**Respuesta corta:** Es un número honesto, medido por validación cruzada de 5
particiones, no una estimación optimista. Hay que leerlo en contexto: son 12
categorías sobre texto corto en español con vocabulario heterogéneo. Además, el
diseño es conservador: cuando la confianza baja de 0.30, el sistema no adivina,
sugiere "Otros" y marca el gasto para revisión. Y aprende: cada corrección del
usuario mejora el modelo y se cortocircuita al instante.

**Si profundizan:** Las categorías de vocabulario distintivo rinden muy bien
(Monotributo F1 0.96, Impuestos 0.91, Transporte 0.88). Las que bajan —Marketing
0.58, Servicios 0.63— son categorías semánticamente amplias que se solapan con
otras; es un resultado esperable y lo documenté en el informe. La matriz de
confusión lo muestra con claridad.

### ¿Cómo validaste el clasificador?
**Respuesta corta:** Con validación cruzada de 5-fold sobre los 600 ejemplos
etiquetados, reportando accuracy global y precision/recall/F1 por categoría más
la matriz de confusión. Todo es reproducible corriendo `evaluar_modelo.py`.

### ¿Qué pasa cuando aparece una categoría nueva o un gasto que no encaja?
**Respuesta corta:** Cae en "Otros" con la marca de revisión. El usuario lo
corrige, y esa corrección entra como ejemplo de entrenamiento. El conjunto de
categorías es cerrado por diseño, alineado con las que usa un monotributista.

---

## Sobre la proyección y el Monotributo

### ¿Por qué Prophet y no una red neuronal o ARIMA?
**Respuesta corta:** Prophet está pensado para series temporales de negocio con
tendencia y estacionalidad, es robusto con pocos datos y da intervalos de
confianza de forma nativa. Para el volumen de un freelancer —decenas de
ingresos— una red neuronal sobreajustaría. Además, cuando hay menos de 10
ingresos, ni siquiera uso Prophet: caigo a una media móvil como arranque en frío.

### El semáforo mostró rojo pero el "porcentaje usado" decía 48%. ¿No es contradictorio?
**Respuesta corta:** No, son dos métricas distintas y es importante la
diferencia. El 48% es lo **ya facturado** hoy. El semáforo se calcula sobre el
porcentaje **proyectado** a fin de año, que supera el límite. El sistema decide
el color mirando el futuro, no el presente: ese es justamente el valor de
anticipar la recategorización antes del cierre fiscal.

### ¿Los límites de las categorías están actualizados?
**Respuesta corta:** Sí, las 11 categorías (A–K) con sus límites y cuotas de 2026
están cargadas en la base, con fecha de vigencia. Al actualizarse la normativa,
se cambian en un solo lugar (la tabla `categorias_monotributo`) sin tocar código.

---

## Sobre la auditoría

### ¿Cómo definís que un gasto es "anómalo"?
**Respuesta corta:** Por z-score: si el monto de un gasto supera en más de dos
desviaciones estándar la media de su categoría, se marca como anomalía. Con una
salvedad de diseño: solo evalúo categorías con al menos 5 gastos, porque con
menos datos la desviación estándar no es confiable y generaría falsos positivos.

### ¿Y los duplicados? ¿No marca de más?
**Respuesta corta:** Un duplicado es mismo monto, misma categoría y misma
descripción dentro de una ventana de 3 días. La ventana evita marcar como
duplicado un gasto recurrente legítimo (un café diario, por ejemplo). El usuario
siempre tiene la última palabra: la alerta es una sugerencia, no un borrado.

---

## Sobre arquitectura y calidad

### ¿Por qué FastAPI y PostgreSQL?
**Respuesta corta:** FastAPI por su rendimiento asíncrono y la documentación
OpenAPI automática. PostgreSQL por la integridad referencial con claves foráneas
y el soporte nativo de tipos numéricos de precisión arbitraria, que es un
requisito para operaciones financieras —no quiero errores de redondeo de punto
flotante en montos.

### Mencionaste que los tests corren sobre SQLite. ¿No es una debilidad?
**Respuesta corta:** Es una deuda técnica que reconozco abiertamente en las
conclusiones. La compensé con pruebas de humo extremo a extremo sobre PostgreSQL
real, que de hecho expusieron defectos que SQLite ocultaba —el más grave, un
tipo enumerado incompatible que rompía la auditoría solo en Postgres—. La línea
de trabajo futuro es migrar la suite de integración a PostgreSQL.

### ¿Cómo garantizás que un usuario no acceda a los datos de otro?
**Respuesta corta:** El `usuario_id` se extrae siempre del token JWT, nunca del
cuerpo de la solicitud. Ningún endpoint acepta un usuario por parámetro. Eso
hace imposible, por diseño, pedir los datos de otra cuenta. Además, el login usa
anti-enumeración: el mismo error para email inexistente y contraseña incorrecta.

### ¿El sistema escala a muchos usuarios?
**Respuesta corta:** La arquitectura lo soporta: cada usuario tiene sus datos y
su propio modelo ML aislados, y agregué índices compuestos (usuario_id, fecha)
para las consultas pesadas como la facturación móvil de 12 meses. El modelo base
se comparte; los personalizados se entrenan por usuario cuando acumula 20+
gastos. El cuello de botella real a futuro sería el reentrenamiento, que hoy
corre en background.

---

## Sobre el alcance y lo que falta

### ¿Por qué no integraste la facturación electrónica de AFIP?
**Respuesta corta:** Está explícitamente **fuera del límite** declarado en el
Entregable 2. Es una integración con un organismo externo que excede el alcance
de un prototipo y agrega una dependencia regulatoria. La verificación del pago
del Monotributo, por ejemplo, la infiero de la existencia de un gasto
categorizado como tal; es una aproximación consciente, documentada como trabajo
futuro.

### ¿Qué harías si tuvieras más tiempo?
**Respuesta corta:** Cuatro cosas concretas, en orden: ampliar y balancear el
dataset base para subir el F1 de Marketing y Servicios; cubrir el régimen de
venta de bienes además de servicios; migrar los tests a PostgreSQL; e integrar
la facturación electrónica de AFIP para precisión fiscal real. Todas están
listadas en las conclusiones del informe.

### Si esto fuera un producto real, ¿qué le falta para producción?
**Respuesta corta:** Configuración de CORS y secretos por entorno (hoy hay
separación dev, falta el hardening de prod), un healthcheck de la base en el
orquestador, logging estructurado, rate limiting en los endpoints de IA, y la
migración de tests a Postgres. Son mejoras de robustez operativa, no de
funcionalidad: el núcleo funcional está completo.

---

## Comodín — si no sé la respuesta

> "Es una buena observación, no lo evalué en profundidad para este prototipo.
> Mi intuición es [X], pero lo honesto es decir que habría que medirlo /
> probarlo antes de afirmarlo."

Mejor reconocer el límite que inventar. El jurado valora la honestidad técnica
más que una respuesta forzada.
