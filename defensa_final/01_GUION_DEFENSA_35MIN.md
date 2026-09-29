# Guion de la defensa — versión simple

**Marcos Gamaliel Joaquín · Legajo SOF02218 · Ingeniería de Software · Universidad Siglo 21**

Trabajo Final de Grado — Prototipado Tecnológico · Profesor TFG: Alejandro Mainero

**Defensa: 14 de octubre de 2026 · 35 minutos de exposición + 10 de preguntas**

---

## Cómo leer este guion

- **Lo que está en recuadro (>) es lo que decís en voz alta.** Está escrito
  simple a propósito: decilo con tus palabras, no lo recites.
- **"Para vos"** es la explicación en criollo, para que entiendas lo que estás
  diciendo. Eso no se le dice al tribunal.
- **Idea fuerza:** una sola frase por bloque. Es lo único que conviene
  memorizar. Si te perdés, volvé a ella.
- **Casos bisagra:** las preguntas de "¿y si…?" que probamos en los tests (el
  valor justo en el borde de una regla, o un dato raro). Respuesta corta: una o
  dos frases. Si repreguntan, el detalle está en `docs/PREGUNTAS_ANTICIPADAS.md`.
- ⏱ marca dónde tenés que estar en el reloj.

---

## Lo que pidió la cátedra y dónde lo respondés

Este cuadro es el corazón de la defensa. Cada pedido tiene su momento y su frase.

| # | Qué pidieron | Cuándo lo pidieron | Dónde lo respondés | Frase clave |
|---|---|---|---|---|
| 1 | Que el sistema **no** se presente como asesoramiento contable, fiscal ni financiero | Corrección final | Bloque 2, el aviso en cada pantalla de la demo, el PDF y el cierre | "Informa, proyecta y alerta. No asesora." |
| 2 | Explicar los **límites del clasificador** | Corrección final | 4.2 y 5.4 | "Acierta 3 de cada 4, y cuando duda lo dice." |
| 3 | Explicar los **límites del motor predictivo** | Corrección final | 4.6 | "Proyecta con una banda, no promete." |
| 4 | Explicar los **límites de las recomendaciones** | Corrección final | 4.7 | "Son reglas fijas: sugieren, no deciden." |
| 5 | Tener el **prototipo funcionando** | Corrección final | Todo el bloque 4, en vivo | — |
| 6 | Profundizar en **cifrado de datos y manejo seguro de sesiones** (Seguridad quedó en "Bueno", la nota más baja) | 3ª entrega | 5.3: **3 minutos**, el tramo técnico más largo | "La contraseña se licúa, la sesión se firma y el usuario sale siempre del token." |
| 7 | Detallar los **desafíos de entrenar Naive Bayes y SVM** | 3ª entrega | 5.4 | "Lo difícil no fue entrenar: fue saber cuándo el modelo duda." |
| 8 | Enfocar la demo en los **topes del monotributo** y los **reportes predictivos** | 4ª entrega | 4.5 y 4.6: **no se recortan nunca** | "No dice que te pasaste: dice cuándo te pasarías." |

---

## Palabras que vas a usar (en criollo)

| Palabra | Qué es |
|---|---|
| **Hash (bcrypt)** | Una licuadora de una sola vía: de la contraseña sale un "jugo" y del jugo no se puede volver a la fruta. Para verificar, se licúa lo que escribiste y se comparan los jugos. |
| **Sal** | Un condimento al azar, distinto por usuario, que se agrega antes de licuar: dos personas con la misma contraseña quedan con jugos distintos. |
| **Cifrar** | Guardar algo en una caja con llave: con la llave se abre y se recupera el original. **Hashear no es cifrar**: el hash no se abre nunca. |
| **Token JWT** | La pulsera del boliche: te la ponen en la entrada (el login) y con ella pasás a cada lugar sin volver a mostrar el DNI. Vence a los 7 días. |
| **Firma HS256** | El sello de la pulsera: cualquiera puede leer lo que dice, pero nadie la puede falsificar sin el sello, que solo tiene el servidor (la `SECRET_KEY`). |
| **HTTPS** | El sobre cerrado para lo que viaja por internet. |
| **API** | La ventanilla del backend: la pantalla pide y la API responde. |
| **Contenedor (Docker)** | Una caja con todo lo que el programa necesita, para que ande igual en cualquier computadora. |
| **TF-IDF** | Convierte un texto en números según las palabras que tiene y qué tan raras son: "jetbrains" pesa mucho más que "de". |
| **Naive Bayes y SVM** | Dos formas de aprender a separar categorías a partir de esos números. El SVM traza "fronteras" entre categorías. |
| **Validación cruzada (5 partes)** | Partir los 600 ejemplos en 5 grupos: se entrena con 4 y se toma examen con el que quedó afuera, 5 veces. Nadie rinde con las preguntas que ya estudió. |
| **Confianza y umbral 0,30** | Cuánto le saca la categoría ganadora a la segunda. Si es menos de 0,30, el sistema dice "no estoy seguro". |
| **Prophet** | Un modelo de pronóstico que separa la historia en tendencia (para dónde va), estacionalidad (lo que se repite) y ruido. |
| **Banda (intervalo de confianza)** | El rango entre un escenario pesimista y uno optimista. |
| **Media móvil** | El promedio de los últimos 3 meses: el plan B cuando hay poca historia. |
| **Puntaje z** | Cuántos "pasos típicos" se aleja un gasto del promedio de su rubro. Más de 2 = raro. |
| **Migración** | Un cambio de la estructura de la base, numerado, que se aplica en orden: la base queda igual en cualquier máquina. |

---

## Mapa de los 35 minutos

| # | Bloque | Reloj | Dura | Soporte |
|---|---|---|---|---|
| 1 | El problema | 0:00 – 3:00 | 3' | Slides 1–4 |
| 2 | La propuesta y sus **límites** | 3:00 – 6:00 | 3' | Slides 5–9 |
| 3 | Videos | 6:00 – 10:00 | 4' | Video |
| 4 | **Demo en vivo** | 10:00 – 24:00 | 14' | App |
| 5 | Código, **seguridad** y **ML** | 24:00 – 33:00 | 9' | Editor + slides 12–23 |
| 6 | Cierre | 33:00 – 35:00 | 2' | Slides 24–27 |

**Regla de oro del reloj:** si a los 10:00 no arrancaste la demo, cortá lo que
falte y arrancá igual. **Lo que nunca se recorta:** 4.5 Monotributo y 4.6
Proyecciones (lo pidió el corrector de la 4ª entrega) y 5.3 Seguridad (fue la
nota más baja de la 3ª).

---

# Bloque 1 · El problema (0:00 – 3:00)

**Pantalla:** portada → slides 2 a 4.

> **IDEA FUERZA:** el monotributista no tiene un problema de desorden. Tiene un
> problema **fiscal**: se entera tarde de que se pasó de categoría.

> "Buenos días. Soy Marcos Gamaliel Joaquín, legajo SOF02218, y presento
> FreelanceControl, un sistema de gestión financiera para monotributistas
> argentinos.
>
> Según el INDEC, en 2025 el trabajo por cuenta propia llegó al **24,5 % del
> empleo**: **3,3 millones de personas**. Y esas personas tienen cuatro
> problemas."

Enumerá los cuatro, sin apurarte (están en la slide):

1. **La plata entra irregular.** Depende de cuándo termina cada trabajo y de
   cuándo paga cada cliente. Las apps registran lo que pasó, pero no proyectan
   lo que viene.
2. **La categoría del monotributo tiene un tope anual.** Si lo pasás, te
   recategorizan o te pueden excluir del régimen. Controlarlo a mano es sumar
   todo lo facturado y compararlo con la tabla de ARCA.
3. **Nadie audita.** Un gasto cargado dos veces, una factura vencida, la cuota
   sin pagar: se descubre al cierre del año.
4. **Todo está desparramado.** Planillas, apps, mails, PDFs y extractos del banco.

> "Contabilium, Xubio, Colppy, QuickBooks: están pensadas para empresas con
> estructura administrativa, y ninguna clasifica gastos sola, proyecta ingresos
> ni audita automáticamente. La pregunta del trabajo fue: **¿puede un software
> anticipar el riesgo, en vez de solo registrarlo?**"

**Casos bisagra (si aparecen en las preguntas):**

- *¿Por qué no alcanza con una planilla?* → "La planilla registra. No te avisa
  que vas a pasar el tope en diciembre ni que cargaste algo dos veces."
- *¿De dónde sale el 24,5 %?* → "De la Encuesta Permanente de Hogares del INDEC,
  tercer trimestre de 2025. Está citada en la tesis."

> ⏱ **3:00**

---

# Bloque 2 · La propuesta y sus límites (3:00 – 6:00)

**Pantalla:** slides 5 a 9.

> **IDEA FUERZA:** el sistema **informa, proyecta y alerta. No asesora.** Y eso
> está adentro del producto, no solo escrito en la tesis.

> "El objetivo fue un sistema web con cuatro piezas automáticas: un
> clasificador de gastos que se entrena en la propia máquina, un motor que
> proyecta los ingresos, un control de la categoría del monotributo y una
> auditoría automática de los registros.
>
> Los cuatro objetivos se cumplieron. El único con meta numérica era el
> clasificador: **70 % de aciertos sobre 12 categorías. Dio 76 %.**
>
> Lo construí con Scrum: 17 historias de usuario, 8 sprints, 4 meses."

### ⚠️ El minuto más importante de la defensa (pedido 1)

**Pantalla:** slide 7, "Lo que el sistema hace y lo que NO hace". Despacio,
mirando al tribunal:

> "**FreelanceControl informa, proyecta y alerta sobre la base de los datos que
> el usuario carga. No constituye asesoramiento contable, fiscal ni
> financiero, y no reemplaza la intervención de un profesional matriculado.**
>
> Tres ejemplos. Puede decir que, a este ritmo, pasarías el tope en diciembre:
> **no te dice qué hacer**. Puede marcar dos gastos iguales en tres días: **no
> decide que uno sea un error**. Puede proyectar tus ingresos con un rango: **no
> los garantiza**.
>
> Y no quedó solo escrito. El aviso está en **seis pantallas** —Dashboard,
> Monotributo, Proyecciones, Recomendaciones, Resumen y Auditoría— y en el pie
> del **reporte PDF**, que es lo único que sale de la aplicación y llega al
> contador."

**Después, los límites del prototipo** (slide 9):

> "Quedaron afuera a propósito: la facturación electrónica de ARCA, la conexión
> directa con cuentas bancarias, la gestión de clientes como algo separado de
> las facturas y la venta de productos. El foco es el freelancer que presta
> servicios."

**Para vos:** el tribunal escucha esa frase buscando si realmente la creés. Por
eso la decís dos veces: acá y en el cierre. Y en la demo **señalá el aviso con
el mouse** en Monotributo, Proyecciones, Recomendaciones y el PDF: que lo vean,
no solo que lo escuchen.

**Casos bisagra:**

- *Si el semáforo está en rojo, ¿me tengo que recategorizar?* → "No lo decide el
  sistema. Informa que a este ritmo pasarías el tope; la categoría la determina
  ARCA y la decisión es del usuario con su contador."
- *¿Por qué no integraste ARCA?* → "Quedó fuera del alcance definido en la tesis.
  Es la primera línea de trabajo futuro."
- *¿Y en Ingresos, Gastos o Facturas no hay aviso?* → "Ahí solo se cargan y
  listan datos: no hay nada que se pueda confundir con un consejo."

> ⏱ **6:00** — arrancan los videos.

---

# Bloque 3 · Videos (6:00 – 10:00)

**Pantalla:** video a pantalla completa, volumen al máximo. Dos videos seguidos,
los dos en el Escritorio:

1. `FreelanceControl_Institucional.mp4` (1:43) — el problema, la solución y el alcance.
2. `FreelanceControl_Demo_TFG_v2.mp4` (1:41) — el recorrido por la aplicación.

> "Antes de la demo en vivo les muestro dos videos cortos: uno del problema y
> la solución, y otro con el recorrido de la aplicación."

**Durante los videos no hables:** tienen narración propia. Usá esos tres
minutos y medio para respirar, tomar agua y mirar el reloj. Es a propósito que
estén antes del tramo más largo.

Al terminar:

> "Eso es lo grabado. Ahora, lo mismo en vivo."

**Para vos:** si preferís pasar uno solo, pasá el institucional. Los dos
minutos que sobran van al clasificador (4.2), que es lo que más le interesa
al tribunal.

> ⏱ **10:00**

---

# Bloque 4 · Demo en vivo (10:00 – 24:00)

> **IDEA FUERZA DE TODA LA DEMO:** cada pantalla resuelve uno de los cuatro
> problemas del bloque 1. **Nombrá el problema antes de mostrar la solución.**

### Antes de entrar a la sala

- [ ] Esa mañana: `docker compose up -d` y esperar los tres contenedores sanos.
- [ ] `docker compose exec api python seed_demo_defensa.py` → deja los datos
      exactos del ensayo (enero a septiembre). **No** importes el extracto ni
      corras la auditoría antes: son parte de la demo.
- [ ] Login en `http://localhost:3000` con `demo@freelancecontrol.com` / `demo1234`.
- [ ] Pestañas abiertas: Dashboard · Gastos · Importar · Auditoría · Monotributo ·
      Proyecciones · Resumen · Recomendaciones.
- [ ] El extracto a mano: Escritorio → `TFG_Defensa` → `demo` → `extracto_28sep_14oct.csv`.
- [ ] Zoom del navegador al 110 %. Notificaciones en silencio.
- [ ] Internet (Wi-Fi o el celular compartido) para el Resumen. Si no hay, igual
      funciona: cae a la plantilla local y lo explicás (ver 4.7).
- [ ] Los dos videos abiertos y minimizados: son el plan B.
- [ ] El editor abierto en el proyecto, con estas pestañas para el bloque 5:
      `app/services/auth.py`, `app/dependencies.py`, `app/services/ml_service.py`,
      `app/services/csv_service.py`, `app/services/ia_service.py`.

---

### 4.1 · Dashboard (10:00 – 10:30) · 30"

> **IDEA FUERZA:** una sola pantalla para lo que hoy está en cinco lugares.

> "Este es el panel principal: ingresos, gastos y balance del mes, la
> proyección del mes que viene y la recomendación principal. Responde al cuarto
> problema, la dispersión.
>
> Hoy es 14 de octubre: el mes recién empieza y todavía no cargué nada, por eso
> octubre está en cero. En unos minutos lo lleno con el extracto del banco."

No te quedes. Treinta segundos y seguís.

---

### 4.2 · Clasificador de gastos (10:30 – 13:00) · 2'30" — pedido 2

**Problema:** cargar y categorizar cada gasto a mano.

> **IDEA FUERZA:** clasifica solo, **dice cuánta confianza tiene** y **aprende
> cuando lo corregís**.

**Hacé:**

1. Gastos → nuevo gasto → `licencia jetbrains anual` → sugiere **Software** (≈ 81 %).
   > "No elegí la categoría: la sugirió el modelo leyendo el texto."
2. Nuevo gasto → `servicio mensual` → confianza baja → pide revisar.
   > "Y acá está el límite, a la vista: 'servicio mensual' puede ser muchas
   > cosas. Cuando el modelo duda, no inventa: lo manda a 'Otros' y le pide al
   > usuario que lo revise."
3. Clasificador → corregir `servicio mensual` a la categoría correcta → volver a
   clasificarla → sale con la corrección.
   > "Corregí una vez. Desde ahora esa descripción usa mi corrección, que es un
   > dato real, y además queda como ejemplo para reentrenar mi modelo personal."
4. Estado ML → ahora dice **modelo propio**, con unos **666 ejemplos**.
   > "Cuando cargué el primer gasto, como la usuaria ya tenía más de veinte
   > gastos propios, el sistema le entrenó su modelo personal en segundo plano.
   > No toqué nada."

**Los límites, en voz alta (pedido 2 — no los saltees):**

> "Tres límites claros. **Uno:** acierta el 76 %, o sea que **uno de cada
> cuatro** se equivoca; por eso existe la revisión. **Dos:** entiende
> **palabras, no contexto**: 'diseño de logo' puede ser Marketing o Servicios, y
> ahí es donde más falla —Marketing es la categoría más floja, con 0,58—.
> **Tres:** las **12 categorías son fijas**; lo que no encaja va a 'Otros'."

**Para vos:** la "confianza" no es una probabilidad. Es cuánto le gana la
primera categoría a la segunda: si empatan, vale 0. Lo explicás en 5.4.

> ⚠️ **Trampa:** no digas "se reentrena al instante". **La corrección** se aplica
> al instante; **el reentrenamiento** corre de fondo y la pantalla no lo espera.

**Casos bisagra:**

- *¿Qué pasa justo en 0,30?* → "Con 0,30 o más, clasifica. Con menos, va a
  'Otros' y pide revisión."
- *La misma descripción, ¿da lo mismo para todos los usuarios?* → "No: cada uno
  tiene su modelo. Lo probamos: la misma frase dio 0,323 con el modelo de un
  usuario que ya había entrenado —clasifica— y 0,292 con el modelo base —pide
  revisión—."
- *¿Y si corrijo con la descripción vacía?* → "La rechaza. Antes se guardaba la
  regla 'vacío = Software' y lo corregimos."
- *¿Y si mando una categoría que no existe?* → "La rechaza: la lista es cerrada.
  En las pruebas, una categoría inventada había llegado a entrar al
  entrenamiento como una clase número 13."
- *¿Cuándo se entrena el modelo propio?* → "La primera vez al llegar a 20 gastos
  propios; después, cada 10 gastos nuevos o ante cada corrección. De a uno por
  usuario."
- *¿Mi corrección le cambia el modelo a otro usuario?* → "No, cada uno tiene el
  suyo. Hay una prueba automática de aislamiento."

---

### 4.3 · Importación de extractos (13:00 – 15:15) · 2'15"

**Problema:** pasar el extracto del banco a mano.

> **IDEA FUERZA:** 9 bancos, 9 formatos, **cero configuración** y **cero datos
> enviados afuera**.

**Hacé:**

1. Importar → subir `extracto_28sep_14oct.csv` → **Analizar archivo**.
2. Frená en la vista previa:
   > "Detectó solo cuál columna es la fecha, cuál la descripción y cuál el
   > importe. Usa un diccionario de nombres de columnas que armé revisando nueve
   > bancos: Galicia, Santander, BBVA, Macro, Nación, Brubank, ICBC, Mercado Pago
   > y Naranja X. Todo local: el archivo no sale de la máquina."
3. Señalá los avisos de arriba (son las trampas que puse a propósito en el archivo):
   > "Antes de guardar me avisa tres cosas. Tres movimientos ya los había
   > importado con el extracto anterior: no los duplica. Dos son una
   > transferencia a mi propia cuenta de Mercado Pago y su vuelta: no es
   > facturación, no la cuenta. Y una fila dice 31 de septiembre, una fecha que
   > no existe: no la inventa, me dice cuál es y por qué quedó afuera."
4. Señalá los que quedaron en "Otros" (coworking, Telecentro, el pago de la
   tarjeta): "cuando no está seguro, no inventa".
5. Confirmar → **29 movimientos** (3 cobros y 26 gastos).
6. Dashboard (15"): octubre ya tiene **$ 3.460.000** de ingresos. "Esto antes era
   una tarde de planilla."

**El remate:**

> "Detectar las columnas de un archivo desconocido es justo lo que hoy se le
> pide a una IA. Decidí no hacerlo: un extracto tiene los clientes, los
> proveedores y los hábitos de una persona. Mandarlo a un tercero para
> ahorrarme un diccionario no valía la pena."

**Casos bisagra:**

- *¿Cómo lee "1.250.000"?* → "Como un millón doscientos cincuenta mil. Antes
  '15.000' entraba como 15 pesos; lo corregimos: el sistema conoce el punto de
  miles y la coma decimal."
- *¿Y si importo el mismo extracto dos veces?* → "Reconoce los repetidos y no
  los duplica." (Lo acabás de mostrar.)
- *¿Una fila rota en el medio del archivo?* → "En el análisis te dice cuál y por
  qué. Al confirmar, si algún registro es inválido no se guarda ninguno: todo o
  nada."
- *¿Y el resumen de la tarjeta de crédito?* → "Avisa. La tarjeta ya entra por el
  banco como 'PAGO TARJETA'; importarla compra por compra la contaría dos
  veces. Está fuera del alcance: es trabajo futuro."
- *Cargué un gasto a mano y después importé el extracto: ¿queda doble?* →
  "Queda marcado como posible duplicado, con la misma regla que la carga manual."

---

### 4.4 · Auditoría automatizada (15:15 – 17:15) · 2'

**Problema:** nadie revisa los registros hasta fin de año.

> **IDEA FUERZA:** un control continuo, con cinco detectores, que no molesta dos
> veces con lo mismo.

**Hacé:** Auditoría → **Ejecutar auditoría**. Nombrá los cinco a medida que
aparecen:

1. **Duplicados** — mismo monto y categoría con hasta 3 días de diferencia:
   Adobe en junio y **Figma, cobrado el 2 y el 4 de octubre** (vino en el extracto).
2. **Anomalías** — un gasto muy lejos del promedio de su rubro en los últimos
   6 meses: el servidor de **$ 900.000** de julio.
3. **Facturas vencidas** — Consultora Aurora y Brand Studio.
4. **Cuota del monotributo** — la de octubre **no aparece**, porque vino pagada
   en el extracto, el día 7. "Los módulos se hablan entre sí."
5. **Transferencias propias** — las vieron recién en la importación.
   > "Es el detector más propio del dominio. Si paso plata del banco a Mercado
   > Pago y el sistema lo cuenta como un cobro, me infla la facturación, y de
   > ese número depende mi categoría. Detectarlo evita un error con
   > consecuencias impositivas."

**Si sobran 30":** Facturas → Brand Studio → **Marcar pagada** (su
transferencia vino el 9 de octubre) → volver a ejecutar → la alerta desaparece.

> "Y si marco una alerta como resuelta, la próxima corrida no la vuelve a
> mostrar. Si no, la auditoría sería puro ruido."

Señalá el aviso al pie de la pantalla.

**Para vos:** "anomalía" es un puntaje z mayor a 2: el gasto está a más de dos
"pasos típicos" del promedio de su rubro. Es una señal para revisar, no una
acusación de error.

**Casos bisagra:**

- *Dos cuotas iguales de un plan de pago, en meses distintos: ¿duplicado?* → "No.
  Duplicado es mismo monto y categoría con hasta 3 días; las cuotas caen en
  fechas distintas."
- *¿Tres gastos iguales en tres días?* → "Tres alertas, una por cada par. Es a
  propósito."
- *Con 5 gastos en un rubro, ¿puede detectar una anomalía?* → "No, y es
  matemática: con 5 datos, el z más alto posible es 1,79, menor que 2. La
  primera anomalía posible aparece con 6 gastos."
- *Una factura que vence hoy, ¿figura vencida?* → "No: vence cuando la fecha
  **ya pasó**. Hoy sigue pendiente todo el día, contando el día de Argentina,
  porque el servidor trabaja en hora universal."
- *¿"Eliminar duplicado" puede borrar el gasto equivocado?* → "No: la alerta
  guarda el identificador exacto del repetido, el más nuevo del par."

---

### 4.5 · Estado fiscal del Monotributo (17:15 – 19:45) · 2'30" — pedido 8, NO SE RECORTA

**Problema:** ¿cuándo me paso del tope?

> **IDEA FUERZA:** no dice "te pasaste". Dice **cuándo te pasarías**, a este ritmo.

> "Esta es la pantalla que responde la pregunta que originó el trabajo.
>
> Arriba, la categoría —la G— y lo facturado en el año contra su tope. Pero el
> semáforo no mira solo el pasado: suma lo facturado hasta hoy **más la
> proyección hasta diciembre**, y lo compara con el tope. Verde por debajo del
> 70 %, amarillo hasta el 90 %, rojo por encima del 90 %.
>
> Hoy da **rojo: 109,4 %**. Ojo: todavía no me pasé; lo facturado real es el
> 75,5 %. Lo que dice es que **a este ritmo me pasaría en diciembre**, y que la
> categoría que cubriría esa facturación es la **H**."

**Mostrá también:** la cuota de octubre figura **pagada** (vino en el extracto).
Si no estuviera, el botón **"Registrar pago ahora"** precarga el gasto con el
monto exacto de la cuota.

**Señalá el aviso al pie (pedido 1):**

> "Y el pie dice que el cálculo se basa en la escala publicada por ARCA y en lo
> que el usuario cargó, y que **la categorización definitiva la determina
> ARCA**. El sistema alerta; la decisión es del usuario con su contador."

**Para vos:** hay tres números y no hay que mezclarlos. Lo facturado real hasta
hoy (75,5 %), lo proyectado a fin de año (109,4 %), y el color, que sale del
proyectado.

**Casos bisagra:**

- *¿El 90 % exacto es amarillo o rojo?* → "Amarillo: rojo es 'por encima del
  90 %', como dice la historia de usuario. Y el 70 % exacto ya es amarillo."
- *¿Por qué año calendario, si ARCA mira los últimos 12 meses?* → "Porque la
  HU-10 lo define así: año en curso más la proyección al cierre. Los 12 meses
  móviles también se calculan, aparte. Por eso el aviso dice que decide ARCA."
- *Importaste $ 3,46 millones y el porcentaje casi no se movió. ¿Por qué?* → "El
  mes en curso cuenta lo mayor entre lo cobrado y lo esperado para un mes. Se
  esperaban unos $ 7,1 millones: hasta cobrar más que eso, manda lo esperado.
  Es conservador, que en un riesgo fiscal es lo correcto."
- *¿Y si ya superé el tope?* → "Dice 'ya superaste el límite anual' y qué
  categoría cubriría lo facturado. Si ni la K alcanza, advierte el riesgo de
  exclusión del régimen."
- *¿Un cobro con fecha futura suma?* → "No como facturado real: todavía no pasó."
- *¿Y si pagué la cuota de menos?* → "Cuenta como pago parcial y la auditoría
  sigue avisando."

---

### 4.6 · Proyección de ingresos (19:45 – 21:45) · 2' — pedidos 3 y 8, NO SE RECORTA

**Problema:** la plata entra irregular.

> **IDEA FUERZA:** proyecta con una **banda**, no con una promesa, y funciona
> también para el que recién empieza.

> ⚠️ El gráfico tarda unos 2 segundos en animarse: **esperá antes de hablar**.

> "Proyección a seis meses con Prophet, un modelo que separa la historia en
> tendencia, estacionalidad y ruido. La línea del histórico es lo real; la
> azul, lo proyectado; las punteadas, el escenario pesimista y el optimista. El
> punto hueco es octubre: el mes no terminó, se muestra aparte y no entra en el
> cálculo."

**Los límites, en voz alta (pedido 3):**

> "Y quiero mostrar sus límites. **Uno:** miren el ancho de la banda, va de 3,6
> a 10,7 millones. Esta freelancer alterna meses de proyecto grande y meses
> flojos; con nueve meses de historia el modelo ve la tendencia, pero no puede
> saber si noviembre trae un proyecto grande, y lo dice. **Dos:** son montos
> nominales, no contempla la inflación. **Tres:** necesita historia: al menos
> diez cobros y tres meses ya cerrados.
>
> ¿Y si no los hay? No bloqueo la pantalla: **cambio de estrategia**. Proyecto
> con el promedio de los últimos tres meses y un margen, y la pantalla dice con
> qué método se calculó. El usuario nuevo, que es el que más necesita entender
> la herramienta, siempre ve algo."

**Para vos:** Prophet con dos meses es como trazar una recta por dos puntos:
siempre "encaja" y se dispara. Por eso pide tres.

**Casos bisagra:**

- *9 cobros en meses cerrados y 3 en el mes actual: son 12. ¿Usa Prophet?* → "No:
  para el mínimo cuentan solo los meses cerrados. Usa el promedio."
- *¿Con un solo mes de datos?* → "Promedio con una banda de ±20 %: con un solo
  dato no hay desvío, y una banda de ancho cero sería una falsa certeza."
- *¿Puede proyectar ingresos negativos?* → "Prophet sí; los recortamos a cero."
- *¿Y si Prophet falla?* → "Pasa al promedio y lo informa. La pantalla no se cae."
- *¿Por qué seis meses y no un año?* → "Es lo que fija la HU-09. Más lejos, el
  error pesa más que la tendencia."

---

### 4.7 · Resumen y Recomendaciones (21:45 – 23:00) · 1'15" — pedido 4

**Resumen (30"):** Resumen → **septiembre** → generar.

> "Este es el único lugar donde uso un modelo de lenguaje externo, Groq: redacta
> en castellano cómo me fue en el mes. Le mando **solo totales** —nunca
> descripciones, clientes ni mi email— y el sistema **verifica cada cifra** que
> escribe contra las que le mandé: si inventa un número, el texto se descarta."

Si no hay internet, sale el resumen de la plantilla local con la etiqueta
"Sin IA" y el motivo: decí "sin conexión, el sistema sigue andando con su
plantilla local" y seguí.

**Recomendaciones (45"):**

> **IDEA FUERZA:** son **reglas fijas**, y cada una muestra **de dónde sale**.
> Sugieren, no deciden.

> "Las recomendaciones, en cambio, no usan ninguna IA: salen de reglas fijas
> sobre los datos. Son siempre entre tres y cinco, ordenadas por urgencia."
> *(Tocá "Por qué" en una.)* "Cada una muestra la regla y el dato exacto que la
> disparó: la factura vencida, el 109,4 % del tope, los ingresos que crecieron
> un 54,1 %."

**Los límites, en voz alta (pedido 4):**

> "Sus límites: solo ven lo que el usuario cargó. No conocen su situación
> personal, sus deudas ni cuánto riesgo está dispuesto a correr. Si hay
> superávit, sugieren que podría destinarlo al instrumento que prefiera —plazo
> fijo, fondos, acciones— **a elección del usuario**: no le digo en qué
> invertir. Y abajo está el aviso de alcance."

**Casos bisagra:**

- *¿Las recomendaciones las hace Groq?* → "No, reglas locales. La HU-12 dice
  justamente 'reglas aplicadas de forma local, sin intervención de servicios
  externos'. Mismos datos, misma respuesta: hay pruebas que lo verifican."
- *¿Qué recibe un usuario sin datos?* → "Pasos para empezar, como 'registrá tus
  ingresos'. Nunca un diagnóstico inventado."
- *¿Qué diferencia hay entre el Resumen y las Recomendaciones?* → "El resumen
  cuenta cómo te fue en un mes: describe. Las recomendaciones sugieren qué mirar
  ahora. Uno con IA sobre totales; las otras con reglas."
- *¿Cómo sabés que la IA no inventa números?* → "No le creo: el sistema extrae
  cada monto del texto y lo compara con los que le mandé. Si aparece uno que no
  mandé, lo descarta, reintenta una vez y, si vuelve a fallar, usa la plantilla."
- *¿Y si Groq da de baja el modelo?* → "Ya pasó. Se cambió una variable de
  entorno, sin tocar código."

---

### 4.8 · Reporte PDF (23:00 – 24:00) · 1'

> **IDEA FUERZA:** lo que el usuario le lleva al contador. Es lo único que sale
> del sistema, por eso lleva el aviso adentro.

**Hacé:** Dashboard → reporte → **septiembre** (el último mes cerrado, ya viene
elegido) → abrir → bajar hasta el final.

> "Resumen del mes con la comparación contra el anterior, estado del
> monotributo con la escala que regía ese mes, gastos por categoría,
> facturación por estado y alertas pendientes. Y al pie: **no reemplaza el
> asesoramiento de un contador matriculado**."

**Casos bisagra:**

- *¿Un reporte de mayo usa la escala nueva de agosto?* → "No: usa la que regía
  en mayo. Las dos escalas están guardadas con su fecha de vigencia."
- *¿Por qué no trae el semáforo ni la proyección?* → "Es la foto del mes. Lo que
  mira hacia adelante vive en las pantallas."
- *¿Puedo pedir un mes que no empezó?* → "No, lo rechaza. El mes en curso sale
  marcado como 'datos parciales'."

> ⏱ **24:00** — cerrá el navegador y pasá al editor.

---

# Bloque 5 · Código, seguridad y ML (24:00 – 33:00)

> **IDEA FUERZA:** cada decisión tuvo una alternativa que descarté por una razón.

> "Hasta acá mostré qué hace el sistema. Ahora, cómo está hecho y por qué."

---

### 5.1 · Arquitectura (24:00 – 25:30) · 1'30"

**Pantalla:** slides 12 a 15 y el árbol de carpetas en el editor.

> "Son tres contenedores: React para las pantallas, FastAPI con Python para la
> lógica y PostgreSQL para los datos. Adentro del backend hay una regla: **el
> router no calcula nada.** Recibe el pedido, lo valida y llama a un servicio.
> Toda la lógica —clasificador, auditoría, monotributo, proyecciones— vive en
> `services/`.
>
> Eso me dio dos cosas. Pruebas: **414 automáticas**, que corren contra una base
> en memoria, sin tocar la real. Y reutilización: la función que verifica la
> cuota del monotributo la usan el módulo fiscal y la auditoría, sin duplicarla."

**Para vos:** el router es el mozo (toma el pedido), el service es la cocina
(hace el plato), el model es la heladera (los datos) y el schema es la carta
(qué se puede pedir y cómo).

**Casos bisagra:**

- *¿Probar sobre una base en memoria no es una debilidad?* → "Las pruebas miden
  la lógica, rápido y aisladas, como pide la HU-16. Además, la verificación
  final la hice en vivo contra PostgreSQL, sobre un clon limpio del repositorio."
- *¿Escala a muchos usuarios?* → "Es un prototipo. La separación en capas y en
  contenedores permite escalar la API por separado, pero no lo medí con carga:
  es trabajo futuro."

---

### 5.2 · Patrones de diseño (25:30 – 27:00) · 1'30"

**Pantalla:** slides 16 a 19. **No recorras todos:** tres, una frase cada uno.

> "Cada decisión de diseño está marcada en el código con la palabra `PATRÓN`."
> *(Buscala en el editor y mostrá la lista de resultados: cinco segundos.)*

1. **Strategy**, en el clasificador: dos algoritmos intercambiables detrás de la
   misma interfaz. Lo desarrollo en 5.4.
2. **Adapter**, en la importación (`csv_service.py:42`): traduce nueve formatos
   de banco a un único movimiento interno. Agregar un banco es agregar un
   sinónimo. Descarté escribir un lector por banco (no escala) y que el usuario
   eligiera las columnas a mano (le saca el valor a la función).
3. **Cache-Aside y cadena de responsabilidad**, en la clasificación
   (`ia_service.py:409`): primero mira si el usuario ya corrigió esa
   descripción; si no, pregunta al modelo; si el modelo duda, "Otros".
   > "Si el usuario ya me dijo que 'Adobe Photoshop' es Software, equivocarme de
   > nuevo en eso sería inaceptable."

---

### 5.3 · Seguridad: cifrado y sesiones (27:00 – 30:00) · 3' — pedido 6, NO SE RECORTA

**Para vos, antes de hablar:** en la 3ª entrega, Seguridad fue la nota más
baja ("Bueno"). El profesor pidió profundizar en **cifrado de datos** y
**manejo seguro de sesiones**. Este tramo es la respuesta, en cuatro preguntas:
cómo guardo la contraseña, cómo manejo la sesión, quién ve qué, y cómo viajan y
dónde quedan los datos. Al final decís **lo que no hace**: eso suma, no resta.

**Pantalla:** slides 20 y 21, y `app/services/auth.py` en el editor.

**1. La contraseña: no se cifra, se hashea** (`auth.py:100`)

> "La contraseña nunca se guarda. Se guarda su hash con bcrypt: una función de
> una sola vía, con una sal aleatoria por usuario y un costo de 12, es decir,
> cada intento de adivinarla exige miles de vueltas a propósito. No la cifro,
> porque cifrar supone una llave para volver atrás, y no quiero que exista
> ninguna forma de recuperarla, ni siquiera para mí. Si alguien se roba la base,
> se lleva hashes que no se pueden revertir."

**2. La sesión: un token firmado** (`auth.py:123` y `dependencies.py:40`)

> "Al iniciar sesión, el servidor entrega un token firmado con HMAC-SHA256.
> Adentro lleva solo dos datos: el número de usuario y el vencimiento, a los
> siete días. **Firmado no es cifrado**: el contenido se puede leer, por eso no
> lleva nada sensible; pero no se puede modificar, porque la firma deja de
> coincidir y el servidor responde 'no autorizado'.
>
> La clave de firma vive solo en la configuración del entorno, fuera del código.
> La API **no arranca** si falta, si quedó la de ejemplo o si tiene menos de 32
> caracteres.
>
> En cada pedido el servidor verifica la firma, el vencimiento y que la cuenta
> siga activa: si se desactiva una cuenta, su token deja de servir en el pedido
> siguiente. Y cuando la sesión vence, la aplicación te lleva al inicio de
> sesión y te avisa por qué."

**3. Quién ve qué: el usuario sale del token**

> "Un principio que atraviesa todo el sistema: **el identificador del usuario se
> obtiene siempre del token, nunca del cuerpo de la petición.** Si alguien manda
> el número de otro usuario, se ignora. Si pide un dato ajeno, recibe 'no
> encontrado', que ni siquiera confirma que existe. Y si se equivoca al iniciar
> sesión, el mensaje es siempre el mismo, para no revelar qué correos están
> registrados; y tarda lo mismo: si el correo no existe, igual se hace el
> cálculo de bcrypt contra una contraseña de relleno. Si no, midiendo cuánto
> tarda la respuesta se sabría qué cuentas existen."

**4. Los datos: por dónde viajan y dónde quedan**

> "El prototipo corre completo en la máquina del usuario: el tráfico entre la
> pantalla, la API y la base no sale a internet, y ni siquiera a la red: los
> puertos se abren solo para esta computadora. La clave de la base está en el
> archivo de entorno de cada instalación, no en el código. Lo único que sale es el pedido
> del resumen a Groq, por HTTPS, y lleva **solo totales**. El clasificador se
> entrena y corre adentro."

**Lo que no hace (decilo, suma honestidad):**

> "Y los límites de seguridad del prototipo, que en producción cambiaría: la
> base no está cifrada en disco; un token no se puede anular antes de que
> venza, salvo desactivando la cuenta; el navegador lo guarda en su
> almacenamiento local; y no hay un límite de intentos de inicio de sesión. Para
> producción: HTTPS con certificado, base cifrada en reposo, tokens de vida
> corta con renovación en cookies protegidas y límite de intentos. Están en
> trabajo futuro."

**Para vos:** tres verbos que no hay que mezclar nunca.
**Hashear** = licuadora, no vuelve (las contraseñas).
**Firmar** = sello, se lee pero no se falsifica (el token).
**Cifrar** = caja con llave, se abre con la llave (HTTPS hacia Groq; la base, en producción).

**Casos bisagra:**

- *¿Si alguien cambia una letra del token?* → "La firma no coincide: 'no
  autorizado'. Hay una prueba que altera el contenido del token."
- *¿Y si me roban el token?* → "Sirve hasta que vence, a los 7 días, como fija
  la tesis. Desactivar la cuenta lo corta. Anular un token puntual es trabajo
  futuro."
- *¿Una contraseña de 100 caracteres?* → "Se rechaza por encima de 72 bytes:
  bcrypt solo mira los primeros 72, y con una más larga entraría cualquier otra
  que empezara igual."
- *¿"Demo@…" y "demo@…" son dos cuentas distintas?* → "No: el correo se guarda
  en minúsculas, es la misma cuenta."
- *¿Se puede averiguar si un correo existe midiendo cuánto tarda el login?* →
  "No: tarda lo mismo. Lo medí: antes eran 2 milisegundos con un correo
  inexistente contra 170 con uno registrado, y lo corregí haciendo el cálculo
  de bcrypt en los dos casos. Ahora son 168 contra 168."
- *¿La clave de la base está en GitHub?* → "No. Docker la toma del archivo de
  entorno, que no se sube, y el lanzador genera una al azar en cada
  instalación. Además la base solo acepta conexiones desde la misma
  computadora."
- *¿Por qué "no encontrado" y no "prohibido" ante un dato ajeno?* → "'Prohibido'
  confirmaría que ese dato existe."
- *¿Si se roban la base?* → "Las contraseñas no se recuperan. Los movimientos sí
  quedarían legibles, porque la base no está cifrada en disco en el prototipo:
  por eso lo pongo como lo primero a cambiar en producción."

---

### 5.4 · Los desafíos del ML (30:00 – 32:30) · 2'30" — pedidos 7 y 2

**Pantalla:** slide 22 y `app/services/ml_service.py` en el editor.

> **IDEA FUERZA:** lo difícil no fue entrenar el modelo: fue **saber cuándo duda**.

Cuatro desafíos, en este orden:

**1. Pocos datos**

> "Arranqué con 216 ejemplos, 18 por categoría, y el modelo acertaba el 57 %:
> lejos de la meta. Lo resolví ampliando a 600 ejemplos, **50 por categoría,
> balanceados**. Balanceados es importante: si una categoría tiene muchos más
> ejemplos, el modelo aprende a decir siempre esa y el porcentaje engaña. Con
> eso llegué al 76 %, medido con validación cruzada de cinco partes: cada
> ejemplo se evalúa con un modelo que nunca lo vio."

**2. Naive Bayes o SVM** (`ml_service.py:727`)

> "La tesis define la estrategia: Naive Bayes para conjuntos chicos, de menos de
> 100 ejemplos, y SVM lineal desde 100. Los medí a los dos sobre el mismo
> conjunto de 600: **SVM 76 %, Naive Bayes 74 %**. Por eso el modelo base usa
> SVM, y como el modelo personal siempre incluye esos 600, en la práctica corre
> SVM. Lo que hace que sea el patrón Strategy es que el resto del código no sabe
> cuál se usó: los dos se usan igual."

**3. La confianza del SVM** (`ml_service.py:831`)

> "El SVM no da probabilidades: da distancias a las fronteras entre categorías.
> Mi primer intento fue convertirlas con softmax, que es lo habitual, y con doce
> categorías hasta los aciertos claros quedaban en 0,20: todo iba a revisión
> manual. Cambié la pregunta. En vez de '¿qué probabilidad tiene?', **'¿cuánto
> le saca la primera a la segunda?'**. Si empatan vale cero —justo cuando el
> modelo duda— y crece cuando hay una clara. Con eso el umbral de 0,30 empezó a
> funcionar."

**4. Reentrenar sin trabar la aplicación**

> "Cada corrección, o cada diez gastos nuevos, reentrena el modelo del usuario.
> Si eso pasara mientras el usuario espera, la pantalla se colgaría: corre **en
> segundo plano**, como pide la HU-05, y de a uno por usuario, para que dos
> entrenamientos a la vez no dejen dos modelos activos. Y cada ejemplo se valida
> contra la lista cerrada de doce categorías."

**Cerrá con los límites (pedido 2):** "acierta 3 de cada 4; Marketing y
Servicios comparten vocabulario; entiende palabras y no contexto; las 12
categorías son fijas; y los 600 ejemplos los armé yo, no salen de usuarios
reales: ampliarlos con datos reales es trabajo futuro".

**Casos bisagra:**

- *¿76 % no es poco?* → "La meta era 70. Y un sistema que acierta 3 de 4 y avisa
  cuando duda sirve más que uno que acierta más pero nunca avisa."
- *¿Por qué no un modelo de lenguaje, tipo ChatGPT, para clasificar?* → "Porque
  tendría que mandar la descripción de cada gasto a un tercero, y eso rompe la
  soberanía de los datos."
- *¿Con pocos datos no gana Naive Bayes?* → "Es lo que sugiere la literatura y
  por eso la tesis lo prevé. En mi conjunto lo medí con 96 ejemplos y tampoco:
  SVM 46 %, Naive Bayes 42 %. Como el modelo siempre tiene los 600 de base,
  Naive Bayes no llega a activarse y no cambia ningún resultado."
- *¿El 76 % se puede reproducir?* → "Sí: el script `evaluar_modelo.py` da
  exactamente 76,00 %, con la tabla por categoría del Anexo A."
- *¿Por qué balanceado?* → "Con desbalance, un modelo que dice siempre la
  categoría más común parece bueno y no sirve para nada."

---

### 5.5 · Un riesgo que se cumplió (32:30 – 33:00) · 30"

**Pantalla:** slide 23.

> "En la matriz de riesgos puse el R2: que ARCA cambiara la escala durante el
> desarrollo. Pasó: el 1 de agosto de 2026 salió una escala nueva. La incorporé
> **cargando datos, sin tocar código**, y las dos quedaron guardadas con su
> fecha: un reporte de mayo se sigue evaluando con la escala de febrero, que
> era la que regía."

> ⏱ **33:00**

---

# Bloque 6 · Cierre (33:00 – 35:00)

**Pantalla:** slides 24 a 27.

> **IDEA FUERZA:** los objetivos se cumplieron, con números medidos. Incluido lo
> que no salió tan bien.

> "Para cerrar. El clasificador tenía como meta el 70 % y dio 76 %, con
> validación cruzada sobre 600 ejemplos balanceados. Anda muy bien donde el
> vocabulario es propio —Monotributo 0,96, Impuestos 0,91— y peor donde se
> comparte —Marketing 0,58, Servicios 0,63—. Por eso la revisión manual no es
> un parche: es parte del diseño.
>
> También se cumplieron la proyección a seis meses con su plan B para usuarios
> nuevos, el control del monotributo y la auditoría con cinco detectores, todo
> sin sacar los datos del usuario de su máquina.
>
> Como trabajo futuro: integrar la facturación electrónica de ARCA, conectar
> cuentas bancarias reales, ampliar el conjunto de entrenamiento con datos
> reales y, en seguridad, lo que dije: cifrado en reposo, HTTPS y sesiones de
> vida corta para llevarlo a producción.
>
> Y termino con lo mismo que empecé: **el sistema informa, proyecta y alerta.
> La decisión y el asesoramiento siguen siendo del usuario y de su contador.**
>
> Muchas gracias. Quedo a disposición para las preguntas."

---

# Si algo falla en vivo

Tres pasos, en este orden:

1. **Recargá la página** (`Cmd+R`). Resuelve casi todo.
2. **Pasá al módulo siguiente:** "tengo un problema de entorno, sigo y vuelvo al
   final si da el tiempo".
3. **Mostralo en el video**, que quedó minimizado: "lo tengo grabado".

**Nunca:** quedarte en silencio tocando la aplicación. Treinta segundos de
silencio con algo roto en pantalla es lo peor que puede pasar.

**Sin internet:** todo funciona local (base, clasificador, proyección,
auditoría, PDF). Solo el Resumen pasa a la plantilla en unos 3 segundos y la
pantalla dice por qué.

---

# Diferencias entre la tesis y el código — tené la respuesta lista

| Si notan… | Respondé |
|---|---|
| La tesis nombra **Llama 3.3 70B** y el sistema usa otro modelo | "Groq dio de baja ese modelo después de entregar la tesis. Cambiarlo fue editar una variable de entorno: el código no tiene el nombre del modelo fijo." |
| La escala del monotributo es la de **agosto de 2026** | "Es el riesgo R2 de la matriz, que se cumplió. Las dos escalas están guardadas con su fecha y la carga fue solo de datos." |
| En algunos capítulos la tesis dice que Groq genera **resúmenes y recomendaciones** | "La HU-12 dice que las recomendaciones se construyen con 'reglas aplicadas de forma local, sin intervención de servicios externos', y el sprint 7 registra la separación entre el resumen generado y las recomendaciones determinísticas. La IA externa quedó en una sola función: sale menos información, nunca más." |
| La HU-09 dice "diez o más ingresos → Prophet" y el código pide además **tres meses cerrados** | "Con menos de diez, siempre media móvil, como dice la HU. Agregué un piso más porque con dos meses Prophet traza una recta que se dispara: con 1 y 3 millones proyectaba 13 millones a seis meses." |
| La HU-10 dice que sugiere "la categoría **siguiente**" y el sistema puede sugerir otra | "Sugiere la primera categoría que cubre la proyección. Si sugiriera la letra de al lado y tampoco alcanzara, el dato no le serviría al usuario." |
| ARCA mira los **últimos 12 meses** y el semáforo mira el año calendario | "El semáforo sigue la HU-10: año en curso más la proyección al cierre. Los 12 meses móviles se calculan aparte, como complemento." |

---

# Si no sabés la respuesta

> "Es una buena observación, no lo evalué en profundidad para este prototipo.
> Mi intuición es [X], pero lo honesto es decir que habría que medirlo antes de
> afirmarlo."

Mejor reconocer el límite que inventar: el tribunal valora la honestidad
técnica más que una respuesta forzada.

---

# Las dos frases para saber de memoria

> **1.** "FreelanceControl informa, proyecta y alerta sobre la base de los datos
> que el usuario carga. No constituye asesoramiento contable, fiscal ni
> financiero, y no reemplaza la intervención de un profesional matriculado."

> **2.** "El identificador del usuario se obtiene siempre del token, nunca del
> cuerpo de la petición."

---

# Números de memoria

| Dato | Valor |
|---|---|
| Exactitud del clasificador | **76 %** (meta: 70 %) |
| Conjunto de evaluación | **600 ejemplos**, 50 por categoría, validación cruzada de 5 partes |
| SVM contra Naive Bayes (600 ejemplos) | **76 % contra 74 %** |
| Punto de partida del conjunto | 216 ejemplos → 57 % |
| Mejor y peor categoría (F1) | Monotributo **0,96** · Marketing **0,58** |
| Categorías | **12** |
| Umbral de confianza | **0,30** |
| Modelo propio | a los **20** gastos; después cada **10** o ante una corrección |
| Anomalía | puntaje z **mayor a 2**, últimos 6 meses (la primera posible, con 6 gastos) |
| Duplicado | mismo monto y categoría, hasta **3 días** |
| Semáforo | verde < 70 % · amarillo 70–90 % · rojo > 90 % |
| Prophet | **10** cobros y **3** meses cerrados; si no, media móvil de 3 meses |
| Horizonte de proyección | **6 meses** |
| Contraseñas | bcrypt, costo **12**, hasta 72 bytes, mínimo 8 caracteres |
| Token | HMAC-SHA256, vence a los **7 días**; clave de al menos **32** caracteres |
| Pruebas automatizadas | **414** del backend + 8 de pantalla |
| Historias de usuario | **17** |
| Sprints y duración | **8 sprints**, 4 meses |
| Pantallas | **13** |
| Bancos soportados | **9** |
| Detectores de auditoría | **5** |
| Costo de desarrollo | **$ 4.400.000** |
| Trabajo por cuenta propia (INDEC 2025) | **24,5 %** del empleo · 3,3 millones de personas |

Cifras de la demo (simulación del 14/10): 29 movimientos importados (3 cobros y
26 gastos), $ 3.460.000 cobrados en octubre, semáforo rojo 109,4 % con lo
facturado real en 75,5 %, supera en diciembre, sugiere la H, banda de 3,6 a
10,7 millones, ingresos +54,1 %.
