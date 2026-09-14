# Guion de defensa oral — FreelanceControl

**Marcos Gamaliel Joaquín · Legajo SOF02218 · Ingeniería de Software · Universidad Siglo 21**
Trabajo Final de Grado — Prototipado Tecnológico · Profesor TFG: Alejandro Mainero

> **35 minutos de exposición + 10 de preguntas.**
>
> **No memorices palabra por palabra. Memorizá la *idea fuerza* de cada bloque**
> (están en negrita al inicio). El texto literal está para que sepas el tono, el
> orden y los números exactos — pero si lo recitás se nota, y si te perdés no
> tenés de dónde agarrarte. La idea fuerza sí te salva.
>
> Cada bloque indica: **tiempo · qué hay en pantalla · idea fuerza · qué decir ·
> trampas**.

---

## Mapa de la defensa

| # | Bloque | Reloj | Duración | Soporte |
|---|---|---|---|---|
| 1 | Apertura: el problema | 0:00 – 3:00 | 3' | Slides |
| 2 | La propuesta y sus **límites** | 3:00 – 6:00 | 3' | Slides |
| 3 | **Video explicativo** | 6:00 – 10:00 | 4' | Video |
| 4 | **DEMO EN VIVO** | 10:00 – 24:00 | 14' | App |
| 5 | **Código y decisiones de diseño** | 24:00 – 33:00 | 9' | Editor + slides |
| 6 | Cierre: resultados y trabajo futuro | 33:00 – 35:00 | 2' | Slides |

**Regla de oro del reloj:** si a los **10 minutos** no arrancaste la demo, salteá
lo que falte del bloque 2 y arrancá igual. La demo es lo que el tribunal pidió
ver; todo lo demás es negociable.

---

# 1 · Apertura: el problema (0:00 – 3:00)

**En pantalla:** portada → slide del problema.

> **IDEA FUERZA:** el monotributista argentino no tiene un problema de desorden
> administrativo. Tiene un problema **fiscal**: se entera tarde de que se pasó
> de categoría, y cuando ARCA se lo notifica ya es un hecho consumado.

**Decir:**

> "Buenos días. Soy Marcos Gamaliel Joaquín, legajo SOF02218, y presento
> *FreelanceControl: sistema de gestión financiera para monotributistas
> argentinos*, mi Trabajo Final de Grado de Ingeniería de Software bajo la
> modalidad de prototipado tecnológico.
>
> Arranco con el número que delimita el problema. Según la Encuesta Permanente
> de Hogares del INDEC, en el tercer trimestre de 2025 el trabajo por cuenta
> propia alcanzó el **24,5 % del empleo total** en Argentina: **3,3 millones de
> personas**, un 42 % más que en 2016. Y los inscriptos al régimen simplificado
> crecieron un 35 % en el mismo período.
>
> Ese universo enfrenta cuatro problemáticas concretas que releve al inicio del
> trabajo."

**Enumerá las cuatro, en este orden, sin apurarte** (están en la slide):

1. **Variabilidad estructural del flujo de caja.** Los ingresos dependen de
   cuándo termina un entregable y de cuándo paga cada cliente. Las herramientas
   convencionales **registran** movimientos pero no **proyectan** escenarios.
2. **Control de la categoría fiscal.** Cada categoría del Monotributo tiene un
   límite anual de facturación. Superarlo fuerza la recategorización obligatoria
   o, en casos extremos, la exclusión del régimen. Monitorearlo a mano exige
   consolidar la facturación acumulada y compararla contra la tabla oficial.
3. **Ausencia de auditoría.** Nadie le avisa al freelancer que cargó un gasto
   dos veces, que una factura venció sin cobrarse o que no pagó la cuota del mes.
   Esa detección depende del cruce manual y **se posterga hasta el cierre anual**.
4. **Fragmentación documental.** Planillas, apps móviles, mails con comprobantes,
   PDFs de facturas y exportaciones CSV del homebanking. Nada consolidado.

**Cerrá el bloque con la pregunta que originó el trabajo:**

> "El relevamiento de las soluciones del mercado argentino —Contabilium, Xubio,
> Colppy, y las internacionales QuickBooks y FreshBooks— mostró que todas están
> pensadas para pymes con estructura administrativa formal, y que **ninguna
> incorpora clasificación automática de gastos, predicción de ingresos ni
> auditoría automatizada**.
>
> Así que la pregunta fue: **¿puede un software anticipar ese riesgo, en lugar
> de solamente registrarlo?**"

> ⏱ **Chequeo de reloj: 3:00.**

---

# 2 · La propuesta y sus límites (3:00 – 6:00)

**En pantalla:** slide de propuesta → slide de alcance y límites.

> **IDEA FUERZA:** no es "otro gestor de gastos". Es un sistema que **cruza la
> contabilidad diaria con el régimen fiscal** y mira hacia adelante. Y sabe
> exactamente hasta dónde llega.

**Decir:**

> "El objetivo general fue desarrollar un sistema web de gestión financiera para
> monotributistas argentinos que integre cuatro componentes automatizados: un
> clasificador de gastos por procesamiento de lenguaje natural entrenado
> localmente, un motor de predicción de ingresos, un módulo fiscal de monitoreo
> de la categoría de Monotributo y un componente de auditoría automatizada.
>
> Eso se desagregó en cuatro objetivos específicos, y los cuatro se cumplieron.
> El más exigente era el del clasificador, porque tenía una **meta numérica**:
> exactitud igual o superior al **70 % sobre doce categorías**. El resultado
> medido fue **76 %**.
>
> El prototipo se construyó sobre diecisiete elementos de Product Backlog y
> diecisiete historias de usuario, distribuidas en ocho sprints a lo largo de
> cuatro meses, siguiendo Scrum."

### ⚠️ El bloque más importante de toda la defensa

**En pantalla:** slide **"Lo que el sistema hace y lo que NO hace"**.

> **IDEA FUERZA:** el sistema **informa, proyecta y alerta. No asesora.** Y eso
> no es una nota al pie de la tesis: **está dentro del producto**.

**Decir, despacio y mirando al tribunal:**

> "Quiero ser muy explícito en un punto, porque hace al alcance del trabajo y a
> la responsabilidad profesional.
>
> **FreelanceControl informa, proyecta y alerta sobre la base de los datos que
> el usuario carga. No constituye asesoramiento contable, fiscal ni financiero,
> y no reemplaza la intervención de un profesional matriculado.**
>
> El sistema puede decirle a un usuario que a su ritmo actual de facturación
> superaría el límite de su categoría en cinco meses. **No puede decirle qué
> hacer al respecto.** Puede señalarle que tiene dos gastos con el mismo monto
> en tres días. **No puede dictaminar que uno sea un error.** Puede proyectar
> sus ingresos con un intervalo de confianza. **No puede garantizarlos.**
>
> Y esto no quedó solamente escrito en la tesis: **está implementado en el
> producto**. Cuando lleguemos a la demo lo van a ver en pantalla, en las cinco
> secciones donde una salida del sistema podría llegar a confundirse con una
> opinión profesional —Monotributo, Proyecciones, Recomendaciones, Resumen y
> Auditoría— cada una con su aclaración específica. Y está también en el pie del
> **reporte PDF**, porque el reporte es el único artefacto que **sale** de la
> aplicación y circula: se lo manda al contador, lo imprime. Tiene que llevar el
> límite consigo."

**Después, los límites del prototipo** (también en la slide):

> "En cuanto al alcance del prototipo, quedaron deliberadamente fuera cuatro
> cosas: la integración con el sistema de facturación electrónica del organismo
> recaudador, la conciliación bancaria automatizada contra cuentas reales, la
> gestión de clientes como entidad independiente de las facturas, y el
> tratamiento de la venta de productos —el prototipo se orienta a la prestación
> de servicios, que es donde está el segmento estudiado."

> ⏱ **Chequeo de reloj: 6:00.** Acá arranca el video.

---

# 3 · Video explicativo (6:00 – 10:00)

**En pantalla:** video a pantalla completa. **Audio del sistema al máximo.**

**Presentalo en una frase y callate:**

> "Antes de mostrarles el sistema en vivo, les propongo ver el recorrido
> completo en video. Son cuatro minutos y muestran el ciclo de uso en el mismo
> orden en que fueron diagnosticados los problemas."

**Durante el video: NO HABLES.** El video tiene narración propia. Si hablás
encima, el tribunal no escucha ninguna de las dos cosas.

> 🎯 **Para qué sirve este bloque, más allá de mostrar el sistema:** son cuatro
> minutos en los que **no estás expuesto**. Usalos para respirar, tomar agua,
> mirar el reloj y recomponerte antes del tramo más difícil. Es deliberado que
> esté acá y no al final.

**Al terminar, la transición:**

> "Eso es el sistema grabado. Ahora, lo mismo en vivo."

> ⏱ **Chequeo de reloj: 10:00.**

---

# 4 · DEMO EN VIVO (10:00 – 24:00) — 14 minutos

> **IDEA FUERZA GLOBAL DE LA DEMO:** cada funcionalidad que mostrás responde a
> **una** de las cuatro problemáticas del diagnóstico. No estás mostrando
> features: estás cerrando el círculo entre problema y solución. **Nombrá el
> problema antes de mostrar la solución.**

### Preparación previa (hacelo ANTES de entrar a la sala)

- [ ] `docker compose up -d` y esperar que los tres contenedores estén `healthy`
- [ ] Abrir `http://localhost:3000` y **hacer login** con `demo@freelancecontrol.com` / `demo1234`
- [ ] Dejar abiertas, en pestañas: **Dashboard** · **Gastos** · **Importar CSV** · **Auditoría** · **Monotributo** · **Proyecciones**
- [ ] Tener el archivo de extracto de ejemplo **ya localizado** en `docs/extractos_ejemplo/` (no lo busques en vivo)
- [ ] Zoom del navegador al **110 %** — el tribunal está lejos de la pantalla
- [ ] Notificaciones del sistema en **silencio**
- [ ] El video del bloque 3 **minimizado pero abierto**, por si hay que volver a él

---

### 4.1 · Punto de partida — Dashboard (10:00 – 10:30) · 30"

> **IDEA FUERZA:** esto es lo que el freelancer hoy no tiene: una sola pantalla.

> "Este es el panel principal. Ingresos del mes, gastos, balance, facturas
> pendientes y las alertas activas. Es la respuesta a la cuarta problemática, la
> fragmentación: hoy esta información vive en cinco lugares distintos."

**No te quedes.** Treinta segundos y seguís.

---

### 4.2 · Clasificador de gastos (10:30 – 13:00) · 2'30"

**Pantalla:** Gastos → nuevo gasto.

> **IDEA FUERZA:** el sistema clasifica solo, **dice cuánta confianza tiene**, y
> **aprende de la corrección**. Las tres cosas importan; la del medio es la que
> distingue un trabajo de grado de un ejercicio.

**Hacé:**

1. Crear un gasto con descripción **`licencia jetbrains anual`** → mostrar que
   sugiere **Software** sola.
   > "No elegí la categoría. La sugirió el clasificador a partir del texto."

2. Crear uno **ambiguo**, por ejemplo **`servicio mensual`** → va a dar confianza
   baja y marcar revisión.
   > "Y acá está lo importante: el modelo **no adivina**. Cuando la confianza
   > cae por debajo del umbral, devuelve 'Otros' y marca el gasto para revisión
   > manual. Prefiero un sistema que diga 'no sé' a uno que invente una
   > categoría con la que después el usuario arma su balance."

3. Ir a **Clasificador** → corregir esa descripción a la categoría correcta →
   volver a clasificarla y mostrar que ahora acierta con confianza 1.0.
   > "Corregí una vez. A partir de ahora, esa descripción se resuelve con la
   > corrección del usuario, que es dato real, no predicción. Y además queda
   > guardada como ejemplo de entrenamiento para el próximo reentrenamiento del
   > modelo personal."

4. Mostrar **Estado ML**: algoritmo activo, cantidad de ejemplos, exactitud.

> ⚠️ **Trampa:** no prometas que el reentrenamiento es instantáneo. Se dispara
> por umbral de correcciones acumuladas, no en cada corrección.

---

### 4.3 · Importación de extractos bancarios (13:00 – 16:00) · 3'

**Pantalla:** Importar CSV.

> **IDEA FUERZA:** nueve bancos, nueve formatos distintos, **cero configuración
> del usuario** y **cero datos enviados afuera**. Este es el módulo que más
> trabajo llevó y el que más se nota.

**Decir primero el problema:**

> "Segunda problemática del diagnóstico: la carga manual. Un freelancer que
> quiere tener sus números al día tiene que transcribir a mano el extracto del
> banco. Y cada banco exporta distinto."

**Hacé:**

1. Subir el archivo de ejemplo.
2. **Detenerte en la vista previa.** Es el momento clave:
   > "El sistema detectó solo qué columna es la fecha, cuál la descripción y
   > cuál el importe. No le dije nada. Esa detección se hace con heurísticas
   > locales sobre un diccionario de sinónimos que armé relevando las
   > exportaciones de nueve entidades: Galicia, Santander, BBVA, Macro, Nación,
   > Brubank, ICBC, Mercado Pago y Naranja X."
3. Señalar los movimientos **ya clasificados** en la vista previa.
4. Señalar los marcados como **posible duplicado**.
   > "Y antes de confirmar, me avisa cuáles ya están en el sistema. Si importo
   > el mismo extracto dos veces, no me duplica los movimientos."
5. Confirmar la importación.

**El remate — decilo, es el mejor argumento técnico del bloque:**

> "Quiero subrayar una decisión de diseño. Detectar la estructura de un archivo
> desconocido es **exactamente** el tipo de tarea que hoy se delega a un modelo
> de lenguaje. Yo decidí **no hacerlo**. Un extracto bancario contiene los
> clientes, los proveedores y los hábitos de consumo de una persona. Mandarlo a
> un servicio de terceros para ahorrarme escribir un diccionario de sinónimos me
> parecía un intercambio malo. La heurística local resuelve nueve bancos, corre
> en milisegundos y **no saca un solo byte del contenedor**."

---

### 4.4 · Auditoría automatizada (16:00 – 18:30) · 2'30"

**Pantalla:** Auditoría → *Ejecutar auditoría*.

> **IDEA FUERZA:** transforma una revisión anual en un control continuo. Cinco
> detectores. Y no molesta dos veces con lo mismo.

**Decir el problema primero:**

> "Tercera problemática: hoy nadie audita estos registros hasta el cierre fiscal."

**Hacé:** ejecutar la auditoría y recorrer las alertas, nombrando los cinco
detectores a medida que aparecen:

1. **Gastos duplicados** — mismo monto y categoría en una ventana de 3 días.
2. **Anomalías estadísticas** — montos que se desvían del comportamiento
   histórico de esa categoría en los últimos 6 meses.
3. **Facturas vencidas o impagas** — plata que debería haber entrado y no entró.
4. **Cuota de Monotributo sin registrar** en el mes corriente.
5. **Transferencias entre cuentas propias** — y explicá por qué existe:
   > "Este detector es el más específico del dominio. Si alguien mueve plata de
   > su cuenta del banco a Mercado Pago, eso aparece en los extractos como un
   > egreso y un ingreso. Si el sistema lo contara como ingreso, le estaría
   > **inflando la facturación acumulada**, que es justamente el número del que
   > depende su categoría fiscal. Detectarlo no es una comodidad: es evitar un
   > falso positivo con consecuencias impositivas."

**Cerrá con la idempotencia — es una pregunta probable, adelantate:**

> "Y una decisión que parece menor pero define si la herramienta se usa o se
> abandona: cuando el usuario marca una alerta como resuelta, la siguiente
> corrida **no la vuelve a generar**. Cada condición tiene una huella estable.
> Sin eso, la auditoría sería ruido: resolvés, volvés a correr y aparece todo de
> nuevo."

**Mostrá el aviso de alcance al pie de la pantalla.**

---

### 4.5 · Estado fiscal del Monotributo (18:30 – 21:00) · 2'30"

**Pantalla:** Monotributo.

> **IDEA FUERZA:** **este es el núcleo de valor del trabajo.** Es la única
> pantalla que responde la pregunta que originó todo: *¿cuándo me paso?*

> 🎯 Si te quedás sin tiempo en la demo, **este bloque no se recorta**.

**Decir:**

> "Esta es la pantalla que responde la pregunta que dio origen al trabajo.
>
> Arriba, la categoría del usuario y su facturación de los últimos doce meses
> contra el límite anual de esa categoría — un límite **móvil**, no calendario.
> El semáforo cambia de verde a amarillo y a rojo según el porcentaje consumido.
>
> Y acá está la parte predictiva, que es lo que ninguna de las herramientas
> relevadas hace: **el sistema cruza la proyección de ingresos con el límite de
> la categoría y estima en cuántos meses lo superaría a este ritmo.** No espera
> a que pase: lo anticipa."

**Mostrá también:**

- La cuota mensual y si está registrada como pagada.
- El botón **"Registrar pago ahora"**, que precarga el gasto con el monto exacto
  de la cuota.

**Y ahora el momento que los profesores pidieron — señalá el aviso al pie:**

> "Y noten el pie de esta pantalla. Dice: *el cálculo se basa en la escala
> publicada por ARCA y en los ingresos registrados en el sistema; la
> categorización definitiva la determina ARCA*. El sistema **informa y alerta**.
> La decisión de recategorizarse, y el asesoramiento sobre cómo hacerlo, son de
> un contador."

**Anécdota fuerte — usala si hay tiempo, es de las mejores que tenés:**

> "Un dato que me parece que valida el diseño. En la matriz de riesgos del
> trabajo identifiqué el riesgo R2: que ARCA actualizara la escala durante o
> después del desarrollo. **Se materializó**: el 1 de agosto de 2026 se publicó
> una escala nueva, con un ajuste del 16,8 % sobre los topes y las cuotas.
> Incorporarla fue cargar los valores nuevos en el catálogo. **No tuve que tocar
> una sola línea de código de la aplicación.** La acción preventiva que había
> definido funcionó, y lo puedo demostrar: las dos escalas están versionadas en
> el proyecto."

---

### 4.6 · Proyección de ingresos (21:00 – 23:00) · 2'

**Pantalla:** Proyecciones.

> **IDEA FUERZA:** proyecta con intervalo de confianza, y **funciona también
> para el usuario que recién empieza**. Eso último es la decisión de ingeniería.

> ⚠️ **Trampa concreta:** el gráfico tarda ~2 segundos en animarse. **Esperá a
> que termine antes de hablar.** Si hablás encima, el tribunal ve puntos
> amontonados a la izquierda y parece un error.

**Decir:**

> "Proyección a seis meses con el modelo Prophet, que descompone la serie
> temporal en tendencia, estacionalidad y ruido. La línea blanca es el histórico
> real; la azul, la proyección; y las punteadas, el escenario pesimista y el
> optimista — el intervalo de confianza.
>
> Lo que quiero destacar no es que ande, sino **qué pasa cuando no puede andar**.
> Prophet necesita un mínimo de historial: al menos diez ingresos y, sobre todo,
> **al menos dos meses distintos**, porque ajusta sobre totales mensuales y con
> una sola fila el ajuste falla directamente.
>
> Un usuario nuevo que carga todos sus movimientos el mismo día cae justo en ese
> caso. Podría haber bloqueado la pantalla con un 'datos insuficientes'. Decidí
> lo contrario: **el sistema cambia de estrategia** y proyecta con una media
> móvil, con un rango de más/menos un desvío estándar. El usuario siempre ve una
> proyección, y la calidad mejora sola cuando acumula historial. Bloquear la
> pantalla castigaría justamente al usuario nuevo, que es el que más necesita
> entender para qué sirve la herramienta."

---

### 4.7 · Reporte PDF (23:00 – 24:00) · 1'

**Pantalla:** generar y **abrir** el PDF.

> **IDEA FUERZA:** es el entregable que el usuario le lleva al contador. Y es el
> único artefacto que sale del sistema, por eso lleva el descargo adentro.

**Hacé:** generar el PDF, abrirlo y **hacer scroll hasta el final**.

> "Reporte mensual consolidado: resumen ejecutivo con variación contra el mes
> anterior, estado del Monotributo, gastos por categoría, facturación por estado
> y las alertas de auditoría pendientes.
>
> Y en el pie —" *(señalá)* "— el mismo descargo: el documento informa, proyecta
> y alerta, no constituye asesoramiento profesional, y las cifras deben
> verificarse contra la documentación respaldatoria antes de presentarse ante
> organismos de control. Porque este PDF se lo va a mandar al contador, y tiene
> que llevar su propio límite."

> ⏱ **Chequeo de reloj: 24:00.** Cerrá la app y pasá al editor de código.

---

# 5 · Código y decisiones de diseño (24:00 – 33:00) — 9 minutos

> **IDEA FUERZA GLOBAL:** este bloque no es "mostrar código". Es demostrar que
> **cada decisión tuvo una alternativa considerada y descartada por una razón**.
> Eso es lo que separa a un ingeniero de alguien que programa.

**Abrí el proyecto en el editor. Arrancá con la transición:**

> "Hasta acá mostré **qué** hace el sistema. Los próximos nueve minutos son
> sobre **cómo** está construido y, sobre todo, **por qué** está construido así."

---

### 5.1 · Arquitectura (24:00 – 26:30) · 2'30"

**En pantalla:** slide del diagrama de arquitectura (Figura 24 de la tesis) y
después el árbol de carpetas en el editor.

> "La arquitectura son tres contenedores Docker que se comunican por una red
> interna definida en Docker Compose: el frontend con React 19, el backend con
> FastAPI sobre Python 3.11, y PostgreSQL 15.
>
> Dentro del backend hay cuatro capas, y una regla que sostiene todo el diseño:
> **un router no calcula nada.**" *(mostrá el árbol: `routers/`, `schemas/`,
> `services/`, `models/`)*
>
> "El router recibe la petición, valida con el schema, llama a un servicio y
> devuelve. Toda la lógica de negocio —el clasificador, la auditoría, el cálculo
> fiscal, las proyecciones— vive en `services/`.
>
> Eso me dio tres cosas concretas. Primero, **testeabilidad**: las 115 pruebas
> automatizadas ejercitan los servicios directamente contra una base SQLite en
> memoria, sin levantar HTTP, y la suite completa corre en 35 segundos. Segundo,
> **reutilización real**: la función que verifica el pago de la cuota la usan el
> módulo fiscal y el de auditoría; si esa regla viviera dentro de un endpoint,
> estaría duplicada. Tercero, **un solo lugar por decisión**.
>
> La alternativa que descarté fue un monolito con la lógica en las vistas, tipo
> Django. La descarté porque el núcleo de este trabajo es la lógica financiera y
> de aprendizaje automático: necesitaba estar aislada y probada, no acoplada al
> ciclo de vida de un request HTTP."

---

### 5.2 · Patrones de diseño (26:30 – 30:00) · 3'30"

> ⚠️ **NO recorras los doce patrones.** No entran y aburren. **Elegí tres y
> contalos bien.** Los otros los tenés en el documento de respaldo si preguntan.

**Anunciá el criterio — te compra tiempo y suena profesional:**

> "Usé varios patrones de diseño. Voy a desarrollar tres, que son los que
> resolvieron los problemas más difíciles, y el resto está documentado en el
> código: cada punto con una decisión de diseño está anotado con el marcador
> `PATRÓN`, así que es buscable."

**Demostralo en vivo — buscá `PATRÓN:` en el editor y mostrá los 32 resultados.
Es un gesto de treinta segundos que vale mucho.**

#### Patrón 1 — Strategy, en el clasificador

**Abrí:** `app/services/ml_service.py:728`

```python
def _elegir_algoritmo(n_ejemplos: int) -> str:
    return "svm" if n_ejemplos >= 100 else "naive_bayes"
```

> "El clasificador tiene que funcionar el primer día, cuando el usuario no tiene
> datos propios y solo está el dataset base, y también cuando ya acumuló
> cientos de gastos. Son dos escenarios estadísticos distintos y **ningún
> algoritmo gana en los dos**.
>
> Naive Bayes multinomial rinde bien con pocos datos porque asume independencia
> entre términos: no sobreajusta. El SVM lineal busca el hiperplano de máximo
> margen, y eso necesita volumen — pero con más de cien ejemplos propios supera
> claramente a Naive Bayes en este dominio.
>
> Lo que hace que esto sea Strategy y no un `if` suelto es que **el resto del
> código no sabe cuál se usó**. La función que clasifica pide un pipeline y lo
> usa. Los dos algoritmos son intercambiables detrás de la misma interfaz.
>
> La alternativa era fijar uno solo. La descarté porque medí los dos: con el
> dataset base gana Naive Bayes, con datos de usuario gana el SVM. Elegir uno
> era aceptar el peor caso en la mitad de los escenarios."

#### Patrón 2 — Adapter (capa anticorrupción), en la importación

**Abrí:** `app/services/csv_service.py:41`

> "Nueve bancos, nueve formas de llamar a la misma columna: `Fecha`,
> `Fecha Mov.`, `Fecha de Operación`, `F. Mov`. Algunos usan débito y crédito
> separados, otros un importe con signo.
>
> El patrón traduce ese caos externo a **un modelo interno único** antes de que
> toque la lógica de negocio. El resto del sistema conoce un solo movimiento,
> con fecha, descripción, monto y tipo. Y el mapeo es **declarativo**: agregar
> un décimo banco es agregar un sinónimo a una lista, sin tocar lógica.
>
> La alternativa era un parser por banco. No escala: cada banco nuevo es código
> nuevo, y los bancos cambian sus exportaciones sin avisar. La segunda
> alternativa era que el usuario mapeara las columnas a mano — pero eso elimina
> el valor de la funcionalidad: si le tengo que explicar qué columna es cuál, ya
> perdí."

#### Patrón 3 — Cache-Aside + Chain of Responsibility, en la clasificación

**Abrí:** `app/services/ia_service.py:276`

> "Clasificar un gasto es una cadena de tres eslabones, en este orden:
>
> **Uno:** ¿el usuario ya corrigió *esta misma descripción* antes? Si sí,
> devuelvo su corrección con confianza 1.0. Es dato real aportado por el dueño
> de la información: **no hay nada que predecir**.
>
> **Dos:** si no, invoco el modelo local.
>
> **Tres:** si la confianza está por debajo del umbral, devuelvo 'Otros' y marco
> el gasto para revisión manual.
>
> El primer eslabón es Cache-Aside y responde a algo simple: si el usuario ya me
> dijo que 'Adobe Photoshop' es Software, volver a equivocarme en esa misma
> descripción es inaceptable. Y la comparación usa una forma canónica —sin
> tildes, sin mayúsculas, sin espacios de más— para que las variaciones
> tipográficas coincidan igual.
>
> El tercero es una decisión de producto: **cuando el modelo duda, lo dice.**"

---

### 5.3 · Seguridad y soberanía de datos (30:00 – 32:00) · 2'

**Abrí:** `app/services/auth.py` y `app/dependencies.py`.

> "Dos planos: control de acceso y política de datos.
>
> Las contraseñas **nunca** se guardan en texto plano: se convierten con bcrypt,
> que es una función de derivación de clave adaptable en costo, con un valor
> único por usuario. Ni ante una filtración completa de la base se podrían
> recuperar las originales.
>
> Validadas las credenciales, el sistema emite un token firmado con **HMAC-SHA256**
> y vigencia de siete días; la clave de firma vive en una variable de entorno,
> fuera del código fuente.
>
> Hay dos decisiones que quiero señalar porque no son obvias.
>
> La primera: ante un correo inexistente o una contraseña incorrecta, el sistema
> devuelve **siempre el mismo mensaje genérico**. Es deliberado: si dijera
> 'usuario no encontrado' contra 'contraseña incorrecta', le estaría dando a un
> atacante una forma de **enumerar qué cuentas existen**.
>
> La segunda, y es el principio transversal del diseño: **el identificador del
> usuario se obtiene siempre del token, nunca del cuerpo de la petición.** Así
> un cliente no puede manipular a quién pertenecen los datos. El aislamiento
> entre cuentas se garantiza en cada operación, no en la interfaz."

**Y el cierre del bloque, la soberanía de datos:**

> "Sobre los datos: el clasificador **se entrena y se ejecuta dentro del mismo
> entorno donde vive la base**. La descripción de un gasto puede revelar
> clientes, proveedores y hábitos: nunca sale hacia un tercero.
>
> El único servicio externo es la interfaz de inferencia de Groq, y está acotada
> por diseño a **una sola función**: redactar el resumen mensual. Y se le envían
> únicamente **totales numéricos agregados** — nunca texto libre ni datos
> identificables. Además, si esa clave no está configurada, el resumen se arma
> con un fallback determinístico local y **la aplicación funciona igual**.
>
> Esto tiene un beneficio de auditabilidad que me parece el argumento más fuerte:
> verificar la política de privacidad de este sistema se reduce a **inspeccionar
> el único punto del código donde se invoca al servicio externo.**"

---

### 5.4 · Lo más difícil (32:00 – 33:00) · 1'

> **IDEA FUERZA:** mostrá un problema que te costó y cómo lo resolviste. Es lo
> que más credibilidad da, y suele adelantarse a una pregunta del tribunal.

**Abrí:** `app/services/ml_service.py:826` (`_confianza_svm`)

> "Si me preguntan qué fue lo más difícil, no fue entrenar el modelo. Fue
> **medir cuánta confianza tenerle**.
>
> El SVM lineal no devuelve probabilidades: devuelve distancias al hiperplano.
> Mi primer intento fue aplicar softmax sobre esas distancias, que es lo que
> uno hace por reflejo. **No funciona con doce clases**: reparte la densidad
> entre todas y hasta las predicciones correctas quedaban alrededor de 0,20, por
> debajo de cualquier umbral razonable. El sistema mandaba todo a revisión
> manual.
>
> La solución fue cambiar la pregunta. En vez de '¿qué probabilidad tiene esta
> clase?', **'¿cuánto le saca la primera a la segunda?'**. Esa brecha vale cero
> cuando dos categorías empatan —que es exactamente cuando el modelo duda— y
> crece cuando hay una dominante. La mapeo al intervalo cero-uno con una función
> monótona y acotada.
>
> Ese cambio de enfoque es lo que hizo que el umbral de revisión manual
> funcionara."

---

# 6 · Cierre: resultados y trabajo futuro (33:00 – 35:00) · 2'

**En pantalla:** slide de resultados (métricas del clasificador).

> **IDEA FUERZA:** los objetivos se cumplieron, y lo digo con números medidos,
> no con adjetivos. Incluyendo lo que **no** salió bien.

> "Para cerrar, los resultados contra los objetivos.
>
> El objetivo del clasificador era **70 %** de exactitud sobre doce categorías.
> El resultado medido es **76 %**, por validación cruzada de cinco particiones
> sobre un conjunto balanceado de **600 ejemplos**, cincuenta por categoría. El
> balanceo es deliberado: con clases desbalanceadas la exactitud global se
> vuelve engañosa.
>
> Y quiero ser honesto con la distribución, porque el promedio esconde cosas.
> Las categorías con vocabulario propio andan muy bien: **Monotributo 0,96**,
> **Impuestos 0,91**, **Transporte 0,88**. Las que peor andan son **Marketing,
> con 0,58**, y **Servicios, con 0,63** — y el motivo es claro: comparten
> vocabulario con otras categorías. 'Diseño de logo' puede ser Marketing o
> Servicios, y honestamente hasta una persona dudaría.
>
> Por eso el umbral de revisión manual **no es un parche, es parte del diseño**:
> el sistema conoce sus propios límites y le devuelve la decisión al usuario en
> los casos donde realmente no puede resolver.
>
> Los otros tres objetivos también se cumplieron: el motor de predicción a seis
> meses con su estrategia de arranque en frío, el módulo fiscal con monitoreo de
> la categoría, y la auditoría automatizada con cinco detectores. Todo sobre una
> arquitectura que preserva la soberanía de los datos del usuario.
>
> Como trabajo futuro identifico tres líneas: la integración con el sistema de
> facturación electrónica del organismo recaudador, la conciliación bancaria
> contra cuentas reales mediante interfaces de banca abierta, y ampliar el
> dataset de entrenamiento con datos reales de usuarios para levantar el
> desempeño de las categorías que hoy se confunden.
>
> Cierro con lo que dije al principio, porque es el límite del trabajo y lo
> sostengo: **el sistema informa, proyecta y alerta. La decisión y el
> asesoramiento siguen siendo de un profesional y del propio usuario.**
>
> Muchas gracias. Quedo a disposición para las preguntas."

---

# Trampas y protocolos de emergencia

### Si la demo se rompe en vivo

**No improvises. Tenés tres niveles, en este orden:**

1. **Recargá la página** (`Cmd+R`). Resuelve el 80 % de los casos.
2. **Pasá al siguiente módulo** y decí: *"acá tengo un problema de entorno, sigo
   con el próximo y vuelvo al final si da el tiempo"*. Seguí adelante sin
   dramatizar.
3. **Volvé al video**, que quedó minimizado: *"lo tengo grabado, se los muestro
   desde el video"*.

**Lo que NO hay que hacer:** quedarse tocando la aplicación en silencio. Treinta
segundos de silencio con algo roto en pantalla es lo peor que puede pasar.

### Discrepancias entre el documento y el código — tené la respuesta lista

| Si notan… | Respondé |
|---|---|
| La tesis dice **Llama 3.3 70B** y el sistema usa otro modelo | "Correcto. El proveedor dio de baja ese modelo después del cierre del documento. Cambiar de modelo fue **cambiar una variable de entorno**: el código lee el nombre del modelo de la configuración, no lo tiene fijo. Es el mismo principio que la escala de ARCA — lo que cambia por afuera no debería obligar a tocar código." |
| La escala de Monotributo es la de **agosto 2026** | "Sí, es el riesgo R2 de la matriz de riesgos, que se materializó. Las dos escalas están versionadas en el proyecto y la carga fue solo de datos." |

### Dos frases para memorizar literalmente

Estas dos son las únicas que conviene tener palabra por palabra, porque son las
que el tribunal va a estar esperando:

> **1.** "FreelanceControl informa, proyecta y alerta sobre la base de los datos
> que el usuario carga. No constituye asesoramiento contable, fiscal ni
> financiero, y no reemplaza la intervención de un profesional matriculado."

> **2.** "El identificador del usuario se obtiene siempre del token, nunca del
> cuerpo de la petición."

### Números que tenés que saber de memoria

| Dato | Valor |
|---|---|
| Exactitud del clasificador | **76 %** (meta: 70 %) |
| Dataset de evaluación | **600 ejemplos**, 50 por categoría, 5-fold |
| Mejor / peor categoría (F1) | Monotributo **0,96** / Marketing **0,58** |
| Categorías | **12** |
| Pruebas automatizadas | **115** |
| Historias de usuario | **17** |
| Sprints / duración | **8 sprints** / 4 meses |
| Pantallas | **13** |
| Bancos soportados | **9** |
| Detectores de auditoría | **5** |
| Horizonte de proyección | **6 meses** |
| Vigencia del token | **7 días** |
| Costo de desarrollo | **$4.400.000** |
| Trabajo por cuenta propia (INDEC 2025) | **24,5 %** del empleo · 3,3 M de personas |
