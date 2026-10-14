# Guion de la defensa

**Marcos Gamaliel Joaquín · Legajo SOF02218 · Ingeniería de Software · Universidad Siglo 21**

Trabajo Final de Grado — Prototipado Tecnológico · Profesor TFG: Alejandro Mainero

**Defensa: 14 de octubre de 2026 · 35 minutos de exposición + 10 de preguntas · el plan termina a las 34:00**

---

## Cómo está armado

- En cada parte tenés **qué hace el sistema**: los datos, para que lo cuentes **con tus palabras**.
- En cada pantalla de la demo, **los casos bisagra van primero**: es lo que trajo el extracto a propósito y cómo lo resuelve el sistema. Frená en cada uno y explicalo.
- Para cada caso: **qué pasa** (el caso), **qué hace el sistema** y **por qué importa**.
- Lo único para decir **tal cual** es la frase de alcance (parte 2 y cierre): la pidió la cátedra.

---

## Mapa del tiempo

| # | Parte | Reloj |
|---|---|---|
| 1 | El problema | 0:00 – 4:00 |
| 2 | La solución y hasta dónde llega | 4:00 – 7:00 |
| 3 | Video | 7:00 – 9:00 |
| 4.1 | Entrar y cómo queda la contraseña | 9:00 – 10:30 |
| 4.2 | Importar el extracto | 10:30 – 14:00 |
| 4.3 | Panel principal | 14:00 – 15:00 |
| 4.4 | Ingresos | 15:00 – 15:45 |
| 4.5 | Gastos | 15:45 – 16:45 |
| 4.6 | Clasificador (y cómo funciona el SVM) | 16:45 – 21:45 |
| 4.7 | Facturas | 21:45 – 23:00 |
| 4.8 | Auditoría | 23:00 – 25:15 |
| 4.9 | Monotributo | 25:15 – 27:45 |
| 4.10 | Proyecciones (y cómo funciona Prophet) | 27:45 – 30:15 |
| 4.11 | Resumen y Recomendaciones | 30:15 – 31:45 |
| 4.12 | Reporte PDF | 31:45 – 32:30 |
| 5 | Cierre | 32:30 – 34:00 |
| — | Colchón | 34:00 – 35:00 |

**No se recortan nunca:** Monotributo (4.9) y Proyecciones (4.10), que los pidió el profesor en la 4ª entrega, y la frase de alcance.

**Cómo leer los recuadros nuevos:**

- **"Respuesta corta"**: lo que decís en 20 segundos si el jurado pregunta.
- **"Si piden más"**: los fundamentos, de a uno, solo si repreguntan.
- **"Slide pendiente"**: la filmina que vamos a armar al final, cuando el guion esté cerrado.

## Lo que pidió la cátedra y dónde lo respondés

| Pedido | Dónde |
|---|---|
| Que el sistema no se presente como asesoramiento contable, fiscal ni financiero | Parte 2 (frase de alcance), el aviso en cada pantalla, el PDF y el cierre |
| Límites del clasificador | 4.6 |
| Límites del motor predictivo | 4.10 |
| Límites de las recomendaciones | 4.11 |
| Prototipo funcionando | Toda la parte 4, en vivo |
| Cifrado de datos y manejo de sesiones (3ª entrega) | 4.1 |
| Desafíos de entrenar Naive Bayes y SVM (3ª entrega) | 4.6 |
| Topes del monotributo y reportes predictivos (4ª entrega) | 4.9 y 4.10 |

---

## Antes de entrar a la sala

- [ ] Abrí **Docker Desktop** y esperá a que diga que está corriendo.
- [ ] En la carpeta del proyecto: `docker compose up -d` y después
      `docker compose exec api python seed_demo_defensa.py` (deja los datos de enero a septiembre).
      **No** importes el extracto ni corras la auditoría antes: son parte de la demo.
- [ ] **Navegador:** `http://localhost:3000`, en la pantalla de inicio de sesión, sin entrar. Zoom al 110 %.
- [ ] **Terminal:** abierta en la carpeta del proyecto, con la letra grande y este comando escrito, sin Enter:
      `sh defensa_final/demo/ver_usuarios.sh`.
- [ ] El extracto a mano: Escritorio → `TFG_Defensa` → `demo` → `extracto_28sep_14oct.csv`.
- [ ] Las slides abiertas, y el video `FreelanceControl_Institucional.mp4` listo.
- [ ] Internet para el Resumen (si no hay, igual anda: usa la plantilla local).
- [ ] Notificaciones en silencio.

---

# 1. El problema (0:00 – 4:00)

**Slides:** portada · "Un segmento grande, y creciendo" · "Cuatro problemáticas concretas" · "Ninguna solución del mercado cubre el núcleo".

### A quién le pasa

- En Argentina, el trabajo por cuenta propia llegó al **24,5 % del empleo** en el tercer trimestre de 2025: **3,3 millones de personas**, un 42,2 % más que en 2016 (INDEC, Encuesta Permanente de Hogares).
- En el mismo período, los inscriptos en el **monotributo crecieron un 35 %** (Secretaría de Trabajo, 2026).
- Son freelancers que prestan servicios y cobran por proyecto: diseñadores, programadores, consultores. Ese es el usuario del sistema.

### Los cuatro problemas

**1. La plata entra irregular.**

- Lo que cobra un freelancer depende de cuándo termina cada trabajo, de cuándo le paga cada cliente y de lo que se pactó en cada proyecto.
- Un mes entra mucho y el siguiente casi nada. En la demo se ve: mayo, $ 8,1 millones; junio, $ 1,2 millones.
- Las apps que existen **registran lo que ya pasó**, pero ninguna te dice qué viene según tu propia historia. Planificar queda "a ojo".

**2. El tope del monotributo.**

- Cada categoría tiene un **límite anual de facturación** que ARCA actualiza cada tanto.
- Si lo pasás, te **recategorizan de forma obligatoria** o, en casos extremos, te **excluyen del régimen**.
- Controlarlo a mano es sumar todo lo facturado y compararlo contra la tabla oficial cada tanto. Es fácil olvidarse, y el olvido termina en sanciones.

**3. Nadie revisa los registros.**

- Un gasto cargado dos veces, un gasto fuera de lo común en un rubro, una factura vencida que nadie cobró, la cuota del monotributo sin pagar.
- Encontrar eso exige cruzar a mano comprobantes, extractos y planillas. Se termina dejando para fin de año, cuando ya es tarde.

**4. Todo está desparramado.**

- Planillas, apps del celular, mails con comprobantes, PDF de facturas y extractos del homebanking. Nada junto, nada consolidado.

### Qué hay en el mercado

- QuickBooks, FreshBooks, Contabilium, Xubio y Colppy facturan e integran con el fisco, pero están pensadas para **pymes con estructura administrativa**, no para una persona sola en el monotributo.
- **Ninguna** clasifica los gastos sola, proyecta los ingresos ni revisa los registros automáticamente.

### La pregunta del trabajo

**¿Puede un software anticipar el riesgo, en vez de solo registrarlo?**

---

# 2. La solución y hasta dónde llega (4:00 – 7:00)

**Slides:** "Qué se propuso este trabajo" · "Lo que el sistema hace — y lo que no" · "No es una nota al pie: está en el producto" · "Qué quedó deliberadamente fuera".

### Qué planteamos

Un sistema web para monotributistas que, además de registrar, trabaje solo:

- **Junta todo en un lugar:** ingresos, gastos y facturas. En vez de tipear, se sube el extracto del banco (CSV o Excel).
- **Clasifica los gastos solo**, leyendo la descripción, con un modelo que se entrena en la propia computadora y aprende de las correcciones del usuario.
- **Proyecta los ingresos** de los próximos 6 meses, con un rango entre un escenario pesimista y uno optimista.
- **Controla la categoría del monotributo:** avisa si, a este ritmo, te pasarías del tope y en qué mes.
- **Revisa los registros solo:** gastos duplicados, gastos irregulares, facturas vencidas, cuota impaga y transferencias entre cuentas propias.
- **Arma un reporte mensual en PDF** para el contador.

*(Opcional, 20 segundos, slide "Tres contenedores": es una aplicación web —pantallas en React, servidor en Python, base de datos PostgreSQL— que corre en la computadora del usuario.)*

### ⚠️ Lo que pidió la cátedra: la frase de alcance

Decila **tal cual**, despacio, con la slide "Lo que el sistema hace — y lo que no":

> **"FreelanceControl informa, proyecta y alerta sobre la base de los datos que el usuario carga. No constituye asesoramiento contable, fiscal ni financiero, y no reemplaza la intervención de un profesional matriculado."**

Tres ejemplos para bajarla a tierra:

- Te dice que a este ritmo **te pasarías del tope en diciembre**, pero **no te dice qué hacer**.
- Marca **dos gastos iguales**, pero **no decide que uno sea un error**.
- **Proyecta** tus ingresos con un rango, pero **no los garantiza**.

El aviso está en **seis pantallas** (Panel, Monotributo, Proyecciones, Recomendaciones, Resumen y Auditoría) y al pie del **PDF**, que es lo único que sale de la aplicación. Lo van a ver en la demo.

### Qué quedó afuera, a propósito

- La facturación electrónica de ARCA.
- La conexión directa con las cuentas del banco (el porqué, si preguntan, está en 4.2).
- La gestión de clientes como algo separado de las facturas.
- La venta de productos: el foco es el freelancer que **presta servicios**.

---

# 3. Video (7:00 – 9:00)

- "Antes de la demo les muestro un video corto con el problema y la solución."
- `FreelanceControl_Institucional.mp4` (1:43), a pantalla completa. **No hables durante el video.**
- Al terminar: "Ahora, el sistema funcionando."

---

# 4. Demo

## 4.1 Entrar y cómo queda la contraseña (9:00 – 10:30)

**Pantalla:** inicio de sesión → `demo@freelancecontrol.com` / `demo1234` → Ingresar. Después, la terminal → Enter en `sh defensa_final/demo/ver_usuarios.sh`.

### Casos bisagra

**Caso: ¿la base guarda la contraseña?**

- **Qué pasa:** la cuenta demo tiene la contraseña `demo1234`.
- **Qué hace el sistema:** en la base no aparece `demo1234`, sino algo como `$2b$12$m74i8jqxUrIkV/kWGr875.bv45hjPwMXsHHlR6lBGG8IhfxodUyiO`. Eso es el **hash**.
- **Por qué importa:** si alguien se roba la base, no ve ninguna contraseña.

**Caso: ¿la contraseña está "encriptada"?**

- **Qué pasa:** es la palabra que todos usan, y está mal.
- **Qué hace el sistema:** la **hashea**. Encriptar se puede deshacer con una llave; un hash no se deshace nunca, ni siquiera el sistema puede recuperar la contraseña.
- **Por qué importa:** es justo lo que pidió profundizar el profesor (cifrado). Decí "hasheada", nunca "encriptada".

**Caso: contraseña equivocada o correo que no existe**

- **Qué pasa:** alguien prueba entrar con datos falsos.
- **Qué hace el sistema:** responde siempre lo mismo, "Email o contraseña incorrectos", y tarda lo mismo en los dos casos.
- **Por qué importa:** si respondiera distinto, o tardara distinto, se podría averiguar qué correos están registrados.

### Qué hace el sistema

- **Hash con bcrypt:** una "licuadora" de una sola vía. La contraseña entra y sale un "jugo"; del jugo no se puede volver a la fruta.
- **Cómo se lee lo que ves:**
    - `$2b$` es la versión de bcrypt.
    - `12` es el costo: licúa 2¹² veces, más de cuatro mil vueltas, para que probar contraseñas sea lento a propósito.
    - Los 22 caracteres siguientes son la **sal**: un condimento al azar, distinto para cada usuario. Dos personas con la misma contraseña quedan con hashes distintos.
    - El resto es el hash.
    - El comando separa esas partes solo para leerlas: en la base es una sola cadena.
- **Para dejarte entrar:** toma la sal de esa cadena, licúa lo que escribiste y compara los resultados.
- **La sesión (una línea, lo pidió el profesor):** al entrar, el sistema te da un pase **firmado** que vence a los 7 días. Se puede leer, pero si alguien lo modifica, la firma no coincide y deja de servir.

---

## 4.2 Importar el extracto (10:30 – 14:00)

**Pantalla:** Importar → subir `extracto_28sep_14oct.csv` → **Analizar archivo** → mirar la vista previa → **Confirmar**.

### Casos bisagra (están en el CSV a propósito)

**Caso 1: movimientos que ya estaban cargados**

- **Qué pasa:** el extracto trae Rappi ($ 18.500, 28/09), Uber ($ 9.800, 29/09) y SUBE ($ 5.000, 30/09), que ya se habían cargado con un extracto anterior.
- **Qué hace el sistema:** compara fecha, monto, descripción y tipo con lo que ya está en la base. Si coinciden, avisa "3 movimientos ya existen y se omitirán" y no los guarda.
- **Por qué importa:** si los guardara, los gastos de septiembre aparecerían inflados.

**Caso 2: transferencia entre cuentas propias**

- **Qué pasa:** el 3/10 salen $ 200.000 a mi propia cuenta de Mercado Pago, y el 4/10 vuelven.
- **Qué hace el sistema:** busca un débito y un crédito del **mismo monto**, con **un día o menos** de diferencia, y que hablen de transferencia o de cuenta propia. Los marca ("parecen parte de una transferencia entre tus propias cuentas") y no los importa.
- **Por qué importa:** si contara la vuelta como un cobro, **inflaría lo facturado**, y de lo facturado depende la categoría del monotributo. Si la descripción no menciona una transferencia, no la marca: podría ser un cobro real del mismo monto.

**Caso 3: una fecha que no existe**

- **Qué pasa:** una fila, "Débito rechazado reintegro", tiene fecha **31/09/2026**.
- **Qué hace el sistema:** no la corrige ni la adivina. La deja afuera y dice cuál fila es y por qué: "fecha inexistente".
- **Por qué importa:** inventar una fecha sería meter un dato falso.

**Caso 4: montos con punto de miles**

- **Qué pasa:** el cobro de Grupo Delta viene como "1.850.000".
- **Qué hace el sistema:** lo lee como **un millón ochocientos cincuenta mil**. Conoce el punto de miles y la coma decimal; "15,000" también lo lee como quince mil.
- **Por qué importa:** al principio "15.000" entraba como 15 pesos. Lo detectamos en las pruebas y lo corregimos.

**Caso 5: gastos que el modelo no sabe clasificar**

- **Qué pasa:** el coworking ($ 85.000), Telecentro ($ 32.900) y el pago de la tarjeta Visa ($ 186.450).
- **Qué hace el sistema:** como su seguridad es baja, los pone en **"Otros"** para que el usuario los revise. No inventa una categoría.
- **Por qué importa:** es mejor una revisión que una categoría equivocada. Y la tarjeta entra como un solo pago, como viene en el banco: importar el resumen compra por compra la contaría dos veces (quedó fuera del alcance).

**Caso 6: dos gastos iguales que son nuevos**

- **Qué pasa:** Figma, $ 21.000, el 2/10 y el 4/10. No estaban en la base.
- **Qué hace el sistema:** los importa, pero los **marca como posible repetido**: mismo monto y categoría, con 3 días o menos de diferencia. Al confirmar avisa "2 movimientos importados parecen repetidos".
- **Por qué importa:** puede ser un cobro doble. El sistema avisa; decide el usuario.

**Caso 7: ¿y si cargo dos extractos del mismo mes?** (no se ve en la demo: contalo)

- **El mismo extracto dos veces:** compara cada fila con lo que ya está guardado: fecha, monto, descripción (sin importar mayúsculas, tildes ni espacios de más) y si es ingreso o gasto. Si ya existe, avisa "ya existe y se omitirá". Importar dos veces el mismo archivo da **cero movimientos nuevos**. Es lo mismo que hizo con Rappi, Uber y SUBE.
- **Dos compras iguales de verdad, el mismo día** (dos cafés de $ 9.600): cuenta cuántas hay guardadas. Si el archivo trae dos y en la base hay una, omite una e importa la otra.
- **Extractos de dos cuentas distintas** (el banco y Mercado Pago): importa los dos. Una transferencia entre esas cuentas aparece como gasto en un archivo y como ingreso en el otro; como vienen separados, la importación no los puede emparejar. Los empareja la **auditoría**: alerta de "transferencia entre cuentas propias", con un botón **"Descartar transferencia"** que borra las dos patas.
- **Si el banco escribe distinto la descripción** entre una descarga y otra: no coincide exacto y lo importa. Si es un **gasto**, igual lo marca como **posible duplicado** (mismo monto y categoría con 3 días o menos) y aparece en la auditoría. En los **cobros** la regla es más estricta (mismo día, monto y descripción) para no confundir las cuotas iguales de un cliente con un error; el precio es que un cobro repetido con la descripción escrita distinto puede pasar.

**Repregunta probable: "¿Por qué no lo conectaron directo a la cuenta, con la API del banco o de Mercado Pago?"**

> **Respuesta corta:** "Porque hoy en Argentina no hay una forma estándar y segura de que una aplicación lea las cuentas de todos los bancos. Lo único que dan los nueve bancos y billeteras es el archivo de movimientos, y para eso no hace falta pedirle ninguna clave al usuario. Por eso la conexión directa quedó fuera del alcance y es trabajo futuro. Y el sistema ya está preparado para sumarla."

*Palabra nueva:* una **API** es una "ventanilla" que una empresa abre para que otro programa le pida datos de forma automática, sin pasar por la pantalla.

**Si piden más, los fundamentos de a uno:**

1. **Los bancos no tienen una ventanilla abierta para otras aplicaciones.**
    - Que una app lea tu cuenta con tu permiso se llama **finanzas abiertas** (o *open banking*). Brasil y Europa lo tienen funcionando y obligatorio.
    - En Argentina se creó por decreto en mayo de 2025 (Decreto 353/2025), pero todavía no funciona: el Banco Central no publicó las reglas técnicas, así que **los bancos no están obligados a ofrecerla**.
    - Sin esas reglas, conectar cada banco sería un acuerdo distinto con cada uno.
    - Lo relevamos en la tesis (proceso P3): los bancos entregan los movimientos **"exclusivamente en archivos exportados"**, cada uno con su formato. Ese fue el problema que resolvimos: leer esos archivos sin configurar nada.
2. **La alternativa sería pedirle la clave del homebanking, y eso es inaceptable.**
    - Algunas aplicaciones entran al homebanking con el usuario y la clave de la persona, y copian lo que muestra la pantalla.
    - Eso obliga a **guardar la llave de la cuenta bancaria** del usuario. El sistema no guarda ni siquiera su propia contraseña (la hashea, lo vieron en 4.1): guardar la del banco va contra todo el diseño de seguridad. Y los bancos piden no compartirla con nadie.
3. **Mercado Pago sí tiene API, pero no alcanza.**
    - Cubre **1 de las 9** entidades: las otras 8 seguirían con archivo, y habría que mantener dos caminos.
    - Habría que registrar la aplicación en Mercado Pago, que el usuario la autorice, y guardar un permiso de acceso a una cuenta con plata: sería **el dato más sensible** de todo el sistema.
    - Está pensada sobre todo para comercios que cobran con Mercado Pago, y sus reportes de movimientos **igual se generan como un archivo**: lo mismo que el usuario descarga desde la app.
4. **El archivo tiene ventajas propias.**
    - Una sola pieza sirve para los nueve.
    - **El usuario decide qué entra:** lo ve en la vista previa antes de guardar.
    - El archivo no sale de la computadora, y la importación no depende de internet ni de que otra empresa cambie su API.
5. **Queda preparado.** La importación convierte cualquier formato en el mismo molde: fecha, descripción, monto y si es ingreso o gasto. Una conexión futura sería **otra entrada al mismo molde**: los duplicados, la transferencia propia, el clasificador y la auditoría se reaprovechan tal cual.

**Para cerrar, si hace falta:** "No fue por no saber conectar una API: el sistema ya usa una, la del Resumen. Fue una decisión de seguridad y de alcance."

*Slide pendiente (anexo, para preguntas):* "¿Por qué archivo y no conexión directa?", con los puntos 1 a 3 y el molde único del punto 5.

**Caso 8: cargué hasta el 14, ¿cómo completo el mes?** (no se ve en la demo: contalo)

- **Qué hacés:** a fin de mes bajás el extracto **completo** de octubre, del 1 al 31, y lo importás. No hace falta recortarlo.
- **Qué hace el sistema:** lo del 1 al 14 ya está guardado, así que lo omite como repetido, y guarda **solo lo nuevo**, del 15 al 31. La transferencia propia y la fila del 31/09 las vuelve a frenar igual.
- **Qué se actualiza solo:** el panel, los ingresos y los gastos al instante; lo facturado en Monotributo; y el modelo del clasificador, que se reentrena si entraron 10 gastos nuevos o más.
- **Qué se actualiza después:** octubre entra al cálculo de Proyecciones recién cuando el mes termina. La auditoría hay que volver a ejecutarla con su botón: no corre sola (las alertas que ya resolviste no vuelven).

### Qué hace la importación

- Reconoce sola cuál columna es la fecha, cuál la descripción y cuáles el débito y el crédito, **sin configurar nada**.
- Sirve para nueve bancos y billeteras: Galicia, Santander, BBVA, Macro, Nación, Brubank, ICBC, Mercado Pago y Naranja X.
- Antes de guardar muestra todo en una vista previa, con la categoría de cada gasto y los avisos.
- Al confirmar, guarda todo junto o nada: si un registro falla, no queda nada a medias.
- El archivo **no sale de la computadora**.
- **Resultado:** 34 filas → **29 importados** (3 cobros y 26 gastos), 3 omitidos por duplicado, 2 por transferencia propia y 1 fila omitida.
- Como la usuaria ya tenía más de 20 gastos, al guardar estos el sistema **le entrena su propio modelo de clasificación**, de fondo. Se ve en el Clasificador.

---

## 4.3 Panel principal (14:00 – 15:00)

### Casos bisagra

**Caso: el mes recién empieza**

- **Qué pasa:** antes de importar, octubre estaba en cero.
- **Qué hace el sistema:** el panel abre siempre en el mes actual. Ahora octubre muestra lo importado.
- **Por qué importa:** ves el mes en curso sin buscarlo.

**Caso: importé 26 gastos y octubre muestra 25**

- **Qué pasa:** parece que falta uno.
- **Qué hace el sistema:** la comisión del banco es del **30 de septiembre**, así que la puso en septiembre.
- **Por qué importa:** cada movimiento cae en el mes de su fecha, no en el del día que lo importaste.

### Qué muestra

- Ingresos, gastos y balance del mes; la estimación del mes que viene; la recomendación más urgente.
- **Datos:** octubre, **$ 3.460.000** cobrados. Noviembre estimado en **unos $ 7,1 millones** (cómo lo calcula: en Proyecciones, 4.10). Recomendación: **2 facturas vencidas por $ 1.410.000**.

---

## 4.4 Ingresos (15:00 – 15:45)

### Casos bisagra

**Caso: la transferencia propia no está**

- **Qué pasa:** los $ 200.000 que fueron y volvieron de Mercado Pago no aparecen.
- **Qué hace el sistema:** los frenó en la importación.
- **Por qué importa:** lo facturado del año no se infla; eso se ve después en Monotributo.

**Caso: el millón ochocientos cincuenta mil**

- **Qué pasa:** el cobro de Grupo Delta figura por $ 1.850.000.
- **Qué hace el sistema:** lo leyó bien con el punto de miles.

### Qué registra

- Cada cobro, con fecha, monto y cliente o descripción.
- **Datos de octubre:** Brand Studio $ 980.000 (9/10), Acme $ 630.000 (10/10) y Grupo Delta $ 1.850.000 (13/10).

---

## 4.5 Gastos (15:45 – 16:45)

### Casos bisagra

**Caso: los dos Figma**

- **Qué pasa:** aparecen con la marca de **duplicado**. Hay un filtro "Solo duplicados" para verlos juntos.
- **Qué hace el sistema:** los marcó al importarlos, sin esperar a la auditoría.

**Caso: los tres "Otros"**

- **Qué pasa:** el coworking, Telecentro y la tarjeta esperan revisión.
- **Qué hace el sistema:** si les cambiás la categoría, el sistema **aprende de esa corrección** y vuelve a entrenar el modelo de fondo.

### Qué registra

- Cada gasto con fecha, monto, descripción y una de **12 categorías**: Software, Hardware, Infraestructura, Marketing, Servicios, Capacitación, Suscripciones, Transporte, Alimentación, Impuestos, Monotributo y Otros.
- Se cargan a mano (con la categoría sugerida) o con el extracto.

---

## 4.6 Clasificador y cómo funciona el SVM (16:45 – 21:45) — pedidos del profesor: límites y desafíos del entrenamiento

**Pantalla:** Clasificador. Después, las slides del clasificador: "Con 216 ejemplos no llegaba a la meta" · "Dos algoritmos, una misma interfaz" · "No fue entrenar el modelo: fue medir la confianza" · "Cada usuario termina con su propio modelo" · "Dónde se confunde, y por qué".

### Casos bisagra (los escribís en vivo)

**Caso 1: una descripción clara**

- **Qué escribís:** `licencia jetbrains anual`.
- **Qué hace el sistema:** **Software, 82 %** de seguridad.

**Caso 2: una palabra suelta**

- **Qué escribís:** `servicio`.
- **Qué hace el sistema:** **Otros, 6 %**, y pide revisión.
- **Por qué importa:** cuando la seguridad es **menor a 30 %**, no adivina: lo manda a "Otros" y avisa.

**Caso 3: la corrección**

- **Qué escribís:** `servicio mensual` → **Otros, 25 %**. Lo corregís a **Servicios** y lo volvés a clasificar.
- **Qué hace el sistema:** ahora da **Servicios, 100 %**, "corrección del usuario". La corrección se aplica **al instante**, y además el modelo se vuelve a entrenar con ella, **de fondo**.
- **Por qué importa:** si el usuario ya le dijo qué es, equivocarse de nuevo en lo mismo sería inaceptable. Funciona aunque lo escribas con mayúsculas o espacios de más.

**Caso 4: aprendió**

- **Qué escribís:** `servicio` otra vez.
- **Qué hace el sistema:** ahora da **Servicios, 51 %**. Hace un minuto daba 6 %.
- **Por qué importa:** corregiste **otra** frase y el modelo, reentrenado, ya entiende esta.

**Caso 5: el modelo propio**

- **Qué mirás:** el recuadro de arriba del Clasificador (estado del modelo) → **modelo propio**, SVM, **692 ejemplos**, exactitud **77 %**.
- **Qué hace el sistema:** cada usuario tiene su propio modelo: los 600 ejemplos de base, más sus 65 gastos anteriores, los 26 del extracto y tu corrección.
- **Si preguntan por qué 77 y no 76:** 76 % es el modelo base de la tesis; 77 % es el de esta usuaria, medido igual pero con sus gastos.

### Qué es el SVM

- **SVM** son las siglas de *Support Vector Machine* ("máquina de vectores de soporte"). Es un algoritmo de **aprendizaje automático**.
- No se le programan reglas del tipo "si dice Uber, es Transporte". Se le dan **ejemplos ya clasificados** y **aprende solo** a separar las categorías.
- En este sistema aprende de 600 descripciones de gastos, 50 por cada una de las 12 categorías, más los gastos del usuario.

### Cómo funciona, paso a paso

1. **Pasa el texto a números.** La computadora no entiende palabras, entiende números. Cada descripción se convierte en una lista de números, uno por cada palabra o par de palabras. Pesa más la palabra **rara y distintiva** ("jetbrains") que la común ("de", "pago"). Esto se llama **TF-IDF**.
    - Ejemplo real, en "licencia jetbrains anual": "licencia jetbrains" pesa 0,60, "jetbrains" 0,57, "licencia" 0,42 y "anual" 0,37.
2. **Aprende fronteras.** Con los ejemplos, el SVM traza **fronteras entre las categorías**, dejando el mayor margen posible entre unas y otras.
    - Analogía: es como dibujar en un mapa los límites entre barrios, lo más lejos posible de las casas de cada uno, para que una casa nueva caiga claramente de un lado.
3. **Clasifica uno nuevo.** La descripción nueva se pasa a números, y el SVM le da a cada categoría un **puntaje**: cuánto cae dentro de su territorio. Gana la de puntaje más alto.
4. **Mide cuán seguro está.** La seguridad es **cuánto le saca la primera categoría a la segunda**: si empatan, la seguridad es cero; si una gana lejos, es alta.
    - "licencia jetbrains anual": Software +0,83 contra Suscripciones −0,69. Le saca 1,52 → **78 %** con el modelo base.
    - "servicio mensual": le saca 0,25 → **22 %**. Menos de 30 % → "Otros" y revisión.

### Por qué usamos SVM

- Es de los métodos clásicos que **mejor funcionan con textos cortos y muchas palabras distintas**, y **entrena en segundos en la propia computadora**.
- **Lo comparamos.** La tesis planteó usar **Naive Bayes** (otro algoritmo, más simple, que calcula probabilidades palabra por palabra) cuando hay menos de 100 ejemplos, y SVM desde 100.
    - Medidos sobre los mismos 600 ejemplos: **SVM 76 %, Naive Bayes 74 %**.
    - Con solo 96 ejemplos, en 50 sorteos distintos, también ganó SVM: 46 % contra 44 %.
    - Como el modelo siempre parte de los 600 de base, en la práctica corre SVM.
- **No usamos un modelo tipo ChatGPT** porque habría que mandarle la descripción de cada gasto a una empresa externa: ahí están los clientes, los proveedores y los hábitos del usuario. El SVM corre adentro, y los datos no salen.

### Los desafíos del entrenamiento (lo pidió el profesor)

1. **Pocos datos.**
    - Con 216 ejemplos (18 por categoría) acertaba el **57 %**: lejos de la meta.
    - Lo ampliamos a 600, **parejos: 50 por categoría**, y llegó al **76 %**.
    - Parejo importa: si una categoría tiene muchos más ejemplos, el modelo aprende a decir siempre esa y el porcentaje engaña.
2. **Medirlo de forma honesta.** No se le toma examen con lo que ya estudió. Se parten los 600 en 5 grupos: se entrena con 4 y se evalúa con el que quedó afuera, cinco veces. El 76 % es el promedio. Esto se llama **validación cruzada**.
3. **Que supiera cuándo duda.** Lo más difícil.
    - El SVM no da probabilidades, da puntajes. El primer intento fue convertirlos con una fórmula estándar (softmax), y con 12 categorías hasta los aciertos claros quedaban en 20 %: **todo iba a revisión**.
    - Lo resolvimos midiendo la **diferencia entre la primera y la segunda**, como se vio arriba.
4. **Reentrenar sin trabar la aplicación.**
    - A los **20 gastos** el usuario recibe su modelo propio, y después se reentrena **cada 10 gastos nuevos o con cada corrección**.
    - Corre **de fondo**: la pantalla no espera.
    - Se entrena **de a uno por usuario**, para que nunca queden dos modelos activos.

### Los límites (los pidió la cátedra)

- **Acierta 3 de cada 4.** Por eso existe la revisión: no es un parche, es parte del diseño.
- **Entiende palabras, no contexto.** "Diseño de logo" puede ser Marketing o Servicios: comparten vocabulario, y ahí es donde más se confunde (Marketing es la categoría más floja).
- **Las 12 categorías son fijas.** Lo que no encaja va a "Otros".
- **Los 600 ejemplos los armamos nosotros.** Sumar datos reales de usuarios es trabajo futuro.

---

## 4.7 Facturas (21:45 – 23:00)

### Casos bisagra

**Caso: Brand Studio pagó, pero la factura figura vencida**

- **Qué pasa:** la factura de Brand Studio ($ 980.000) venció el **8/10**. La transferencia llegó el **9/10** y vino en el extracto.
- **Qué hace el sistema:** no la marca pagada solo. Cruzar los movimientos del banco con las facturas (la conciliación bancaria) **quedó fuera del alcance**.
- **Qué hacés:** Brand Studio → **Marcar pagada** → la fecha viene en hoy: cambiala a **09/10/2026** → **Confirmar**.
- **Por qué importa:** muestra el límite con honestidad. Acme también pagó (el 10/10) y su factura sigue pendiente por el mismo motivo.

**Caso: una factura que vence hoy (si preguntan)**

- **Qué hace el sistema:** sigue **pendiente** todo el día y pasa a vencida recién mañana. El cambio a vencida lo hace el sistema solo, por fecha.

### Qué registra

- Las facturas emitidas, con cliente, monto, fecha de emisión, vencimiento y estado: **pendiente, vencida o pagada**.
- **Datos:** 4 pagadas, 2 pendientes (Tienda Sur y Acme) y 2 vencidas (Consultora Aurora y Brand Studio).

---

## 4.8 Auditoría (23:00 – 25:15)

**Pantalla:** Auditoría → **Ejecutar auditoría** → **4 alertas**. La auditoría corre cuando apretás ese botón; la marca de duplicado en Gastos, en cambio, aparece al instante.

### Casos bisagra

**Caso 1: duplicado que vino en el extracto**

- **Qué pasa:** Figma, $ 21.000, el 2/10 y el 4/10.
- **Qué hace el sistema:** alerta de **gasto duplicado**: mismo monto y misma categoría con 3 días o menos de diferencia.
- **Qué podés hacer** (no es solo informativa):
    - **"Eliminar duplicado":** borra el gasto repetido (el más nuevo del par), le saca la marca al otro y deja la alerta resuelta.
    - **"Resolver":** si eran dos compras reales, la marcás como revisada. No se borra nada, y la próxima auditoría no la vuelve a mostrar.
    - **Ignorarla:** queda pendiente y suma en Recomendaciones como "alerta sin revisar".

**Caso 2: duplicado viejo**

- **Qué pasa:** Adobe, $ 38.000, el 3/06 y el 5/06.
- **Qué hace el sistema:** la misma alerta. Lo encuentra aunque sea de junio.

**Caso 3: un gasto irregular**

- **Qué pasa:** un servidor de **$ 900.000** en julio. Los otros 9 gastos de Infraestructura de los últimos 6 meses van de $ 35.000 a $ 118.000 (rondan los $ 89.000).
- **Qué es un gasto irregular, en una frase:** un gasto **mucho más alto de lo que esa categoría suele moverse**. El sistema no lo compara con un número fijo, sino con la costumbre de la misma categoría.

> **Para decir (tu versión, corregida):** "Para detectar un gasto irregular, el sistema compara cada gasto con los de su misma categoría de los últimos 6 meses. Calcula el promedio y cuánto suelen apartarse esos gastos del promedio, que se llama **desvío**. Si un gasto supera el promedio en **más de 2 desvíos**, lo marca como irregular. Este servidor quedó **2,8 desvíos** arriba del promedio de Infraestructura. Y funciona cuando ya hay historia: hacen falta al menos 6 gastos de esa categoría."

- **Lo que había que corregir de tu versión:**
    - **La regla es 2, no 2,8.** El 2,8 es lo que dio este servidor; la vara es 2 desvíos.
    - **No es "veces el promedio", es "desvíos".** El servidor es 5,3 veces el promedio, pero el sistema no mira eso: mira cuánto se aparta comparado con lo que la categoría suele moverse.
    - **La categoría es "Alimentación"**, no "comida": usá los nombres de las 12 categorías.

**Cómo lo calcula, con los números de la demo:**

1. Junta los gastos de **Infraestructura** de los últimos 6 meses: son **10**, contando el servidor.
2. **Promedio:** $ 170.100.
3. **Desvío** (cuánto se mueve la categoría, en promedio, alrededor de ese número): $ 258.358.
4. **Pone la vara:** promedio + 2 desvíos = 170.100 + 2 × 258.358 = **$ 686.816**. Cualquier gasto de Infraestructura por encima de esa vara es irregular.
5. **Compara:** el servidor ($ 900.000) pasa la vara: está **2,8 desvíos** arriba. El AWS de octubre ($ 118.000) queda muy por debajo: normal.

**¿Por qué "desvíos" y no "el doble del promedio"?** La analogía de la boleta de luz:

- Si tu boleta **siempre** viene entre $ 30.000 y $ 35.000, una de $ 50.000 te llama la atención.
- Si tu boleta va de $ 10.000 en otoño a $ 60.000 en verano, una de $ 50.000 es normal.
- El promedio es parecido en los dos casos (unos $ 33.000). Lo que cambia es **cuánto se mueve**, y eso es lo que mide el desvío.
- Con la regla "el doble del promedio", la vara sería $ 66.000 en los dos casos, y la boleta rara de $ 50.000 pasaría sin aviso. Con desvíos, **la vara se ajusta sola a cada categoría**: en una que se mueve poco, salta un gasto apenas más alto; en una que se mueve mucho, solo uno muy alto.

**Por qué 2 desvíos:** es una regla estadística clásica. Cuando los gastos se comportan normalmente, casi todos (alrededor de 95 de cada 100) caen a menos de 2 desvíos del promedio: lo que queda afuera llama la atención.

**¿Desde cuándo funciona? (usuarios nuevos):**

- Hacen falta **al menos 6 gastos de esa categoría** en los últimos 6 meses. Con menos, no marca nada: con tan pocos datos, el promedio no dice nada.
- **Se cuenta por categoría,** no por usuario: alguien con 50 gastos de Transporte y 3 de Hardware ya tiene control en Transporte, pero todavía no en Hardware.
- **Si te muestran el código y dice 5:** el mínimo programado es 5, pero con 5 gastos es matemáticamente imposible pasar los 2 desvíos, porque el propio gasto alto sube el promedio y el desvío (el máximo posible es 1,79). En la práctica, el primero aparece con 6.

**Cuidados:**

- Solo marca gastos **más altos** de lo normal, no más bajos.
- Si todos los gastos de una categoría son iguales (el desvío es cero), no marca ninguno.

**Qué podés hacer:** **"Resolver"**, si el gasto es real (compraste un servidor caro), y no vuelve a aparecer. Si estaba mal cargado, lo corregís o lo borrás en **Gastos**, y en la próxima auditoría ya no sale. No hay botón de borrar en la alerta, a propósito: un gasto alto puede ser real, y el sistema no decide que sea un error.

**Por qué importa:** es una señal para revisar, no una acusación de error.

*Slide pendiente:* "¿Qué es un gasto irregular?": los 10 gastos de Infraestructura como barras, la línea del promedio ($ 170.100), la vara punteada ($ 686.816) y el servidor pasándola. Abajo, la boleta de luz.

**Caso 4: factura vencida**

- **Qué pasa:** Consultora Aurora, $ 430.000, venció el 20/08.
- **Qué hace el sistema:** alerta de factura vencida sin cobrar. **Brand Studio ya no aparece**: la marcaste pagada.

**Lo que no aparece, y por qué:**

- **La cuota del monotributo:** vino **pagada en el extracto**, el 7/10. Los módulos se hablan entre sí.
- **Las transferencias propias:** las frenó la importación.

**Caso: alerta resuelta (si preguntan)**

- Si marcás una alerta como resuelta, la próxima vez **no vuelve a aparecer**. Si no, la auditoría sería puro ruido. Con **"Reabrir"** vuelve a pendiente.
- **"Limpiar resueltas"** las borra del historial; si el problema sigue existiendo, reaparece en la próxima auditoría.
- Dos cuotas iguales en meses distintos **no** son duplicado: hay más de 3 días entre ellas.

> En la demo, **no** elimines ni resuelvas alertas antes de Recomendaciones: cambia el conteo de "alertas sin revisar". Si lo querés mostrar, hacelo al final.

### Qué hace

- Revisa todos los registros con **5 controles**: gastos duplicados, gastos irregulares, facturas vencidas, cuota del monotributo sin cubrir y transferencias entre cuentas propias.
- **Avisa, no corrige nada sola.** Señalá el aviso al pie (si no se ve, bajá un poco).

---

## 4.9 Monotributo (25:15 – 27:45) — pedido del profesor, no se recorta

### Casos bisagra

**Caso 1: todavía no me pasé, pero me voy a pasar**

- **Qué pasa:** lo facturado real del año es el **75,5 %** del tope ($ 40.760.000).
- **Qué hace el sistema:** suma lo facturado más lo que espera hasta diciembre. Llega al **109,4 % → rojo**. Dice: **"a este ritmo te pasarías en diciembre"**, y que la categoría que cubriría esa facturación es la **H**.
- **Por qué importa:** no dice "te pasaste", dice **cuándo te pasarías**. Esa es la respuesta a la pregunta del trabajo.

**Caso 2: la cuota de octubre**

- **Qué pasa:** el extracto trajo el pago del monotributo, $ 230.312,94, el 7/10.
- **Qué hace el sistema:** la cuota figura **pagada**. Si no estuviera, aparece el botón **"Registrar pago ahora"** con el monto exacto.

**Caso 3: importé $ 3,46 millones y el 109,4 % no se movió**

- **Qué pasa:** antes de importar, el semáforo decía 109,4 %. Importaste $ 3,46 millones de cobros de octubre y sigue diciendo 109,4 %. Parece que lo importado no contó.
- **La idea en una frase:** el 109,4 % **ya contaba con que en octubre ibas a cobrar**. Lo importado no es plata nueva para el cálculo: es plata que **ya estaba prevista** y ahora está **confirmada**.

> **Respuesta corta:** "No se suma de más porque ya estaba prevista. El sistema esperaba cobrar unos 7,1 millones en octubre. Al importar, 3,46 pasaron de 'esperado' a 'cobrado', y el total del año quedó igual. Lo que sí subió es lo facturado real, de 69 a 75 %."

**La analogía del viaje:**

- Vas de Córdoba a Rosario: 400 km. Antes de salir, el viaje mide 400 km.
- A mitad de camino hiciste 200 km. El viaje **sigue midiendo 400**: lo que cambió es cuánto ya recorriste.
- En el semáforo: **109,4 % es el largo del viaje** (cuánto vas a haber facturado el 31 de diciembre). **75,5 % es lo que ya recorriste** (lo facturado de verdad). Al importar se movió lo recorrido, no el largo del viaje.

**Las cuentas, en tres renglones:**

1. El semáforo pregunta: **"¿cuánto vas a haber facturado el 31 de diciembre?"** Respuesta: lo que ya cobraste + lo que falta cobrar.
2. Para octubre, el sistema espera un mes de unos **7,1 M** (usa lo que Prophet estima para un mes completo).
3. **Antes** de importar, de octubre habías cobrado 0, así que faltaban 7,1. **Después**, cobraste 3,46, así que faltan 3,64. **En los dos casos, octubre suma 7,1.**

| | Antes de importar | Después de importar |
|---|---|---|
| Ya cobrado de enero a septiembre | 37,3 M | 37,3 M |
| Octubre: ya cobrado | 0 | **3,46 M** |
| Octubre: lo que falta cobrar | 7,1 M | **3,64 M** |
| *Octubre en total* | *7,1 M* | *7,1 M* |
| Noviembre (estimado) | 7,1 M | 7,1 M |
| Diciembre (estimado) | 7,6 M | 7,6 M |
| **Total del año** | **59,1 M** | **59,1 M** |
| **Contra el tope de la G ($ 54,0 M)** | **109,4 %** | **109,4 %** |
| Lo facturado de verdad (la otra barra) | 37,3 M → **69,1 %** | 40,76 M → **75,5 %** |

**Cuándo se mueve el 109,4 %:**

- **Si en octubre cobrás más de 7,1 M.** Por ejemplo, con 8 M cobrados en octubre, el total pasa a unos 60 M: **111,1 %**.
- **El 1 de noviembre,** cuando octubre se cierra: entra al cálculo con lo que realmente cobraste y Prophet recalcula todo. Si octubre terminó flojo, recién ahí el porcentaje baja.

**Por qué está hecho así:**

- Si el sistema tomara solo lo cobrado del mes en curso, **cada día 1 el riesgo "bajaría"** (octubre valdría cero) y volvería a subir a fin de mes.
- Un semáforo que mejora todos los principios de mes sería una **falsa tranquilidad** justo en el dato fiscal.
- Prefiere equivocarse para el lado prudente: suponer que el mes se completa y avisar antes.

*Slide pendiente:* "¿Por qué no se movió el 109,4 %?": dos barras iguales de 59,1 M, "antes" y "después", con octubre partido en "cobrado" y "por cobrar", y la línea del tope de la G en 54,0 M.

**Caso 4: las transferencias propias no suman**

- **Qué hace el sistema:** como no entraron, lo facturado no se infló con los $ 200.000 que fueron y volvieron.

**Caso 5: la escala nueva de ARCA** (pregunta probable del jurado)

- **Qué pasa:** ARCA cambió la escala el 1/8/2026, durante el desarrollo (subió un 16,8 % los topes y las cuotas). Era el riesgo **R2** de la tesis.
- **¿Se actualiza sola?** **No.** Pero **tampoco hay que tocar el cálculo**: la escala es un **dato**. Es un catálogo con las 11 categorías (tope anual y cuota de cada una) y la **fecha desde la que rige**.
- **Lo dice la tesis:** la prevención del riesgo R2 es un "catálogo de categorías del régimen versionado en la base de datos con fecha de vigencia, actualizable por carga de datos sin modificar el código". Y se cumplió: la escala de agosto se cargó así.
- **Cada escala queda guardada con su fecha:** un reporte de mayo se sigue calculando con la escala que regía en mayo.

**Repregunta: "¿Por qué no se actualiza sola? ¿Cuál fue el impedimento?"**

> **Respuesta corta:** "Porque ARCA no ofrece ninguna forma oficial de que un programa consulte la escala: la publica como una tabla en su página web, pensada para personas. Leer esa página con un programa es frágil, y un tope mal leído da un semáforo equivocado sin que nadie se entere. Como la escala cambia dos veces por año, en fechas que fija la ley, cargarla y verificarla lleva minutos. Y está probado: la de agosto entró así, sin tocar el cálculo."

**Si piden más, el impedimento punto por punto:**

1. **ARCA no tiene una ventanilla para programas que entregue la escala.**
    - ARCA tiene servicios web (las "ventanillas" que usan los sistemas de facturación), pero son para operar con un CUIT: emitir facturas, consultar los datos de un contribuyente. Piden un certificado digital asociado a ese CUIT.
    - **En el catálogo oficial de servicios de ARCA no hay ninguno que devuelva la tabla de categorías.**
    - La escala se publica como una **página web** (arca.gob.ar/monotributo/categorias.asp). Así la relevamos en la tesis: documento D3, formato "Web", actualización semestral.
2. **Leer la página con un programa es frágil.**
    - Eso se llama *scraping*: un programa "lee" la página como lo haría una persona, buscando los números en el diseño.
    - Si ARCA cambia el diseño, el programa puede leer mal **sin avisar**. Y cambia: en 2024 AFIP pasó a llamarse ARCA y cambió de dirección web.
    - El tope es el número más delicado del sistema: si se lee mal, el semáforo da verde cuando es rojo. **Un error silencioso en el dato fiscal es peor que una carga manual verificada.**
3. **Cambia poco y en fechas conocidas.**
    - Por ley (Ley 27.743, de 2024), la escala se actualiza **dos veces por año** según la inflación del semestre que mide el INDEC: rige desde el **1 de febrero** y desde el **1 de agosto**.
    - Automatizar algo que pasa dos veces por año no justifica el riesgo de un error que nadie ve.
4. **Conectarse con ARCA quedó fuera del alcance** de la tesis (Límites). Es la primera línea de trabajo futuro.

**Repregunta: "¿Es fácil actualizarla?"** Sí: **tres pasos, unos minutos.**

1. **Copiar los 22 números** de la tabla oficial de ARCA (11 topes y 11 cuotas) al catálogo de escalas, con la fecha desde la que rige. Por ejemplo, la próxima sería "escala de febrero de 2027, rige desde el 1/2/2027".
2. **Correr un comando:** `docker compose exec api python seed_categorias_monotributo.py`.
3. **Verificar** en la pantalla de Monotributo que el tope de la categoría coincida con el de ARCA.

- **Qué hace el comando solo:** guarda la escala nueva como **vigente** y deja la anterior como **histórica**, sin borrarla. Si se corre dos veces, no duplica nada.
- **Qué no se toca:** el cálculo del semáforo, el control de la cuota en la auditoría y el PDF. Todos leen la escala de la base.
- **Se hizo de verdad:** la escala de agosto entró así. Hoy en la base conviven las dos de 2026. Por ejemplo, la categoría G:

| Categoría G | Tope anual | Cuota mensual | Estado |
|---|---|---|---|
| Desde el 1/2/2026 | $ 46.211.109,37 | $ 197.108,23 | histórica |
| Desde el 1/8/2026 | $ 53.995.798,87 | $ 230.312,94 | vigente |

**¿Lo mostramos en vivo?** No hay que actualizar una escala durante la defensa:

- **La próxima escala real (febrero de 2027) todavía no existe.** Habría que inventar los números, y en la demo no se muestra ningún dato inventado.
- **Cambiar el tope a mitad de la demo cambia todo lo que viene después:** el 109,4 %, las recomendaciones y el PDF.
- **Lo que sí podés hacer, si preguntan:** mostrar las dos escalas que conviven en la base (la tabla de arriba). Es real y no cambia nada. *(Pendiente: armar un comando de solo lectura, como el de los usuarios.)*

**Si insisten: "¿y ese catálogo no es código?"** → "Es un archivo de datos del proyecto: una lista con los 11 topes y cuotas de cada escala, con su fecha. La lógica que calcula el semáforo no se toca. En producción, eso sería una pantalla de administración o la integración con ARCA."

*Slide pendiente (anexo, para preguntas):* "¿Cómo se actualiza la escala de ARCA?": por qué no sola (los puntos 1 a 3), los tres pasos y la tabla de la categoría G.

**Si preguntan:** el 90 % justo es **amarillo**; rojo es "más de 90 %".

### Qué hace

- Compara lo facturado en el año, más lo que se espera facturar hasta diciembre, con el **tope de tu categoría**.
- **Semáforo:** verde por debajo de 70 %, amarillo de 70 a 90 %, rojo por encima de 90 %.
- **Señalá el aviso al pie:** el cálculo se basa en la escala de ARCA y en lo que cargó el usuario; **la categoría la define ARCA**, y la decisión es del usuario con su contador.

---

## 4.10 Proyecciones y cómo funciona Prophet (27:45 – 30:15) — pedidos del profesor, no se recorta

**Pantalla:** Proyecciones. El gráfico tarda unos 2 segundos en animarse: esperá antes de hablar.

**Orden para decirlo (2:30):**

1. Los casos bisagra en la pantalla: octubre hueco y el rango ancho (40 s).
2. Qué es Prophet y qué datos usa (40 s).
3. Cómo arma los tres escenarios (50 s).
4. Por qué Prophet, en una frase, y los límites (20 s). La comparación con otros modelos queda para las preguntas.

### Casos bisagra

**Caso 1: octubre no entra**

- **Qué pasa:** octubre aparece como un **punto hueco**.
- **Qué hace el sistema:** como el mes no terminó, lo muestra aparte y **no lo usa** para calcular.
- **Por qué importa:** un mes por la mitad tiraría la proyección para abajo.

**Caso 2: un rango ancho**

- **Qué pasa:** para noviembre, entre **$ 3,6 y $ 10,7 millones** (el valor esperado es $ 7,1 M).
- **Qué hace el sistema:** muestra el rango en vez de un solo número.
- **Por qué importa:** esta freelancer alterna meses grandes y flojos. Con nueve meses de historia ve la tendencia, pero no puede saber si noviembre trae un proyecto grande, y lo dice.

**Caso 3: un usuario nuevo, con poca historia (si preguntan)**

- **Qué hace el sistema:** con menos de 10 cobros o menos de 3 meses cerrados, no usa Prophet: proyecta con el **promedio de los últimos 3 meses** y lo dice en pantalla. Con un solo mes, usa un margen de ±20 %.
- **Por qué importa:** el que recién empieza también ve algo, y sabe cómo se calculó.

### Qué hace

- Estima los ingresos de los **próximos 6 meses** con **Prophet**.
- Para cada mes muestra tres escenarios: **esperado**, **pesimista** y **optimista**.

### Qué es Prophet, en criollo

- Una herramienta **gratuita y de código abierto** que creó **Meta** (la empresa de Facebook) para pronosticar números que cambian con el tiempo: ventas, visitas, ingresos.
- La hicieron para que alguien que no es estadístico pueda hacer un pronóstico razonable **sin ajustar perillas a mano**. La tesis la fundamenta con el trabajo de sus autores (Taylor y Letham, 2018).
- **Cómo mira la historia:** la separa en tres capas, como separar una canción en sus instrumentos:
    1. **Tendencia:** hacia dónde va (sube, baja, se frena).
    2. **Estacionalidad:** lo que se repite todos los años (un diciembre siempre alto, un enero siempre flojo).
    3. **Ruido:** el sube y baja que no sigue ningún patrón.
- **Cómo pronostica:** estira la tendencia, le suma la estacionalidad y, con el ruido, calcula cuánto se puede equivocar.

### ¿En qué se basa? Los datos que usa

> **Respuesta corta:** "Solo en lo que cobró esta usuaria cada mes. Prophet traza la tendencia de esa historia y la estira: ese es el escenario esperado. Después simula mil futuros con el mismo vaivén que tuvo la historia: el pesimista y el optimista son los límites donde caen 8 de cada 10."

- **Un solo dato: el total cobrado en cada mes cerrado**, sacado de Ingresos. Nueve números:

    | Ene | Feb | Mar | Abr | May | Jun | Jul | Ago | Sep |
    |---|---|---|---|---|---|---|---|---|
    | 1,4 | 1,9 | 6,3 | 1,6 | 8,1 | 1,2 | 5,7 | 1,8 | 9,3 |

    (en millones; promedio, 4,1). Octubre no entra porque no terminó.

- **Lo que no usa:** los gastos, las facturas pendientes, la inflación, datos de otras personas ni nada de internet.
- **¿Qué entrenamiento previo tiene?** Ninguno de afuera. No viene entrenado "de fábrica": se ajusta **cada vez con los cobros de esta usuaria**, en su computadora. Y no es un entrenamiento con ejemplos, como el clasificador, sino un ajuste estadístico sobre su propia historia.
- Se recalcula solo cuando cambian los cobros, y con los mismos datos **da siempre el mismo resultado** (la simulación usa una semilla fija).

### Cómo arma los tres escenarios

1. **Busca las tres capas.** Con 9 meses **no puede ver estacionalidad**: para saber si diciembre siempre es alto necesita al menos dos años de historia, así que la deja afuera sola. Quedan la tendencia y el ruido.
2. **Escenario esperado = la tendencia estirada.**
    - La tendencia es la línea que mejor pasa entre los 9 puntos. Los meses altos vienen subiendo (6,3 → 8,1 → 5,7 → 9,3), así que la línea sube unos **$ 490.000 por mes**: arranca en 2,2 M en enero y llega a 6,1 M en septiembre.
    - Estirada: octubre 6,6 · **noviembre 7,1** · diciembre 7,6.
3. **Mide el vaivén:** cuánto se apartó cada mes real de la línea.
    - Junio cobró 1,2 cuando la línea marcaba 4,6: **3,4 abajo**. Septiembre cobró 9,3 contra 6,1: **3,2 arriba**.
    - Lo típico es que un mes se aparte unos **2,7 millones** de la línea, para arriba o para abajo.
4. **Escenarios pesimista y optimista = mil futuros simulados.**
    - Prophet arma **1.000 noviembres posibles**. En cada uno, la tendencia puede doblar un poco (como dobló en el pasado) y el mes se sacude con el mismo vaivén de la historia.
    - Los ordena de menor a mayor:
        - **Pesimista:** el que queda en el puesto 100. Solo 1 de cada 10 futuros es peor: **$ 3,6 M**.
        - **Optimista:** el del puesto 900. Solo 1 de cada 10 es mejor: **$ 10,7 M**.
    - Entre los dos caen **8 de cada 10 futuros**. Esa es la banda.
5. **En pantalla, noviembre:** esperado **7,1 M**, pesimista **3,6 M**, optimista **10,7 M**.

**La analogía del pronóstico del tiempo:** "mañana, entre 18 y 26 grados". No sabe la temperatura exacta, pero te da un rango en el que casi seguro cae. Acá es igual: la línea dice "unos 7,1"; el vaivén de tu historia dice "puede ser bastante menos o bastante más", y el sistema muestra las dos cosas.

**Si preguntan "¿y si el pesimista da negativo?":** se muestra como cero: no se puede cobrar menos que nada.

### ¿Para qué es bueno Prophet?

- Para **series de negocio** (ventas, ingresos) con una tendencia que cambia y patrones que se repiten cada año.
- **Tolera meses raros:** un mes enorme o uno vacío no lo descalabra.
- **Da un rango, no solo un número:** el esperado, el pesimista y el optimista.
- **Es automático:** no hay que ajustarlo a mano para cada usuario. Clave, porque cada usuario tiene su propia historia.
- **Es explicable:** se puede mostrar la línea, la estacionalidad y la banda, como recién.
- **Corre en la computadora del usuario:** los ingresos no salen a ningún servicio externo.

### ¿Por qué Prophet y no otro?

> **Respuesta corta:** "Porque da el rango además del número, se ajusta solo a la historia de cada usuario, se puede explicar y corre en la computadora sin mandar los ingresos afuera. Con poca historia se comporta como una línea con su banda; cuando el usuario tenga dos años, suma solo lo que se repite cada año, sin tocar el código."

| Opción | Qué haría con esta usuaria | Por qué no |
|---|---|---|
| **El promedio de los meses** | 4,1 M para todos los meses que vienen | No ve que viene creciendo. Lo usamos como **plan B** para usuarios nuevos (arranque en frío). |
| **Una recta común** (regresión lineal) | Hoy, casi lo mismo que Prophet | Se queda en recta para siempre: no ve cuando el negocio se frena ni lo que se repite cada año. Y la banda hay que armarla aparte. |
| **ARIMA** (un modelo estadístico clásico) | Podría andar | Hay que elegir sus parámetros según cómo es cada serie, y supone una historia más larga y pareja que la de un freelancer. Con un modelo por usuario, no es práctico. |
| **Redes neuronales o una IA** | Con 9 datos se "aprende de memoria" el ruido | Necesitan cientos o miles de datos, no se puede explicar por qué dio 7,1 y, si es una IA externa, habría que mandar los ingresos afuera. |

**Si dicen "entonces es una regresión lineal":** "Hoy, con nueve meses, se comporta como una: el número de noviembre da parecido. La diferencia es que Prophet trae la banda calculada de forma estándar, detecta si la tendencia dobla y, con dos años de historia, suma la estacionalidad sola. Elegimos una herramienta que crece con el usuario."

### Qué no ve

- Que esta freelancer alterna un mes grande y uno flojo. Ese vaivén no es estacionalidad anual, así que no lo predice: lo refleja en lo ancho de la banda.
- **El futuro del negocio:** si ayer firmaste un contrato grande, no lo sabe. Solo estira tu historia.

### Los límites (los pidió la cátedra)

- El rango es ancho cuando los ingresos son irregulares.
- Son montos **nominales**: no contempla la inflación.
- Necesita historia: 10 cobros y 3 meses cerrados. Si no los hay, usa el promedio.
- Proyecta **6 meses** y no más: más lejos, el error pasa a dominar la estimación.

*Slides pendientes:*

- "Prophet en criollo": las tres capas (tendencia, estacionalidad, ruido) y los 9 números que usa.
- "De dónde salen los tres escenarios": las 9 barras, la línea de tendencia estirada hasta diciembre y la banda de noviembre (3,6 · 7,1 · 10,7).
- Anexo, para preguntas: "¿Por qué Prophet?", con la tabla de comparación.

---

## 4.11 Resumen y Recomendaciones (30:15 – 31:45) — pedido de la cátedra: límites de las recomendaciones

### Casos bisagra

**Caso 1: el panel decía 2 facturas vencidas, y acá dice 1**

- **Qué hace el sistema:** recalcula con cada dato. Como marcaste pagada a Brand Studio, ahora queda solo Aurora ($ 430.000).

**Caso 2: si la IA inventa un número (si preguntan)**

- **Qué hace el sistema:** compara cada cifra del texto con las que le mandó. Si aparece una que no mandó, descarta el texto, reintenta una vez y, si vuelve a fallar, usa la plantilla local.

**Caso 3: sin internet (si preguntan)**

- **Qué hace el sistema:** el Resumen sale de una plantilla local, con la etiqueta "Sin IA". El resto del sistema no usa internet.

### Qué hace

**Resumen** (Resumen → septiembre → generar):

- Una IA externa (Groq) escribe en castellano cómo te fue en el mes.
- Recibe **solo totales**: nunca descripciones, clientes ni el correo.
- Es el **único lugar** del sistema que usa IA externa.

**Recomendaciones:**

- **No usan IA.** Son **reglas fijas**: de 3 a 5, ordenadas por urgencia.
- Cada una muestra su **"Por qué"**: el dato exacto que la disparó.
- **Datos:** 1 factura vencida (Aurora, $ 430.000); lo facturado proyectado llega al 109,4 % del tope; 3 alertas sin revisar; los ingresos crecieron un 54,1 %; hay superávit promedio.

### Los límites (los pidió la cátedra)

- Solo ven **lo que cargó el usuario**. No conocen su situación personal, sus deudas ni cuánto riesgo quiere correr.
- Si sugieren destinar el superávit a algún instrumento (plazo fijo, fondos, acciones), **lo elige el usuario**: el sistema no dice en qué invertir.
- Señalá el aviso al pie.

---

## 4.12 Reporte PDF (31:45 – 32:30)

**Pantalla:** Panel → reporte → **septiembre** (viene elegido) → abrir → bajar hasta el pie.

### Casos bisagra

**Caso: un mes con escala vieja (si preguntan)**

- **Qué hace el sistema:** un reporte de mayo usa la escala del monotributo que regía en mayo, no la de agosto.

**Caso: un mes que no terminó (si preguntan)**

- **Qué hace el sistema:** el mes en curso sale marcado como "datos parciales". Un mes que todavía no empezó, lo rechaza.

### Qué hace

- El resumen del mes para el contador: comparación con el mes anterior, estado del monotributo, gastos por categoría, facturas y alertas pendientes.
- Al pie: **"no reemplaza el asesoramiento de un contador matriculado"**. Es lo único que sale de la aplicación, por eso lleva el aviso adentro.

---

# 5. Cierre (32:30 – 34:00)

**Slides:** resultados · trabajo futuro · gracias.

- **Los objetivos se cumplieron:** registrar y juntar todo en un lugar, clasificar los gastos solo, controlar el monotributo y auditar los registros, y proyectar los ingresos con su reporte. El clasificador superó la meta que nos habíamos puesto.
- **Cómo se construyó:** con Scrum, en etapas cortas, cada una con algo funcionando para revisar.
- **Trabajo futuro:**
    - Integrar la facturación electrónica de ARCA.
    - Conectar las cuentas del banco.
    - Sumar datos reales al clasificador.
    - Llevarlo a producción con más seguridad: base cifrada, HTTPS y sesiones más cortas.
- **Repetí la frase de alcance:** el sistema **informa, proyecta y alerta**; la decisión y el asesoramiento siguen siendo del usuario y de su contador.
- "Muchas gracias. Quedo a disposición para las preguntas."

De 34:00 a 35:00 queda un minuto de colchón. Si sobra, no lo llenes.

---

# Si algo falla en vivo

1. **Recargá la página** (`Cmd+R`): resuelve casi todo.
2. **Pasá a la pantalla siguiente:** "tengo un problema de entorno, sigo y vuelvo al final si da el tiempo".
3. **Sin internet:** todo anda local; solo el Resumen usa la plantilla y lo dice.
4. **Si la terminal no responde:** explicá el hash con el ejemplo de 4.1 y seguí con la demo.

**Nunca** te quedes en silencio tocando la aplicación.
