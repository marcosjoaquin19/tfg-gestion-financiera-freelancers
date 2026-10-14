# Guion de la demo en vivo — FreelanceControl

*Actualizado el 12 de octubre de 2026 · Marcos Joaquín*

## Cómo leer este guion

Cada módulo tiene siempre las mismas tres partes, así lo repasás rápido y no te perdés en vivo.

- **HACÉ** → lo que tocás en la pantalla (dónde hacés clic).
- **DECÍ** → el texto para leer o contar con tus palabras. Está escrito como hablás vos, no como la tesis.
- **Palabras clave** → si te quedás en blanco, decí esas dos o tres palabras y seguí. Con eso el jurado ya entiende qué hace el módulo.

**Truco para repasar:** leé solo las negritas de corrido. Si con las negritas podés contar la demo entera, estás listo.

## La app en una frase

**FreelanceControl junta la plata del freelancer en un solo lugar, la ordena sola y le avisa antes de que haya un problema.**

Analogía para arrancar: **es un copiloto**. No maneja por vos, pero te avisa que viene una curva.

- **Para quién:** el freelancer que cobra por proyecto (diseñador, programador, consultor) y está en el monotributo.
- **Qué le duele**, en cuatro palabras clave:
    - **Plata irregular:** un mes entra mucho y el otro casi nada.
    - **El tope:** si se pasa del límite de su categoría, lo recategorizan o lo echan del régimen.
    - **Nadie revisa:** gastos repetidos, facturas sin cobrar, la cuota sin pagar.
    - **Todo desparramado:** planillas, mails, PDF y el homebanking.

### La frase que se dice tal cual

La pidió la cátedra. Decila despacio, sin cambiarle una palabra:

> "FreelanceControl informa, proyecta y alerta sobre la base de los datos que el usuario carga. No constituye asesoramiento contable, fiscal ni financiero, y no reemplaza la intervención de un profesional matriculado."

Palabras clave: **informa, proyecta y alerta. No asesora.**

### El mapa de la demo

Cuatro tramos en vivo, con filminas en el medio. La filmina anterior a cada tramo te lo anuncia abajo a la derecha ("Ahora, en vivo: …").

| Tramo | Reloj | Qué abrís | La idea en una frase |
|---|---|---|---|
| 1 | 9:20 – 13:30 | Login → Importar (dos rechazos y el extracto) → Dashboard | Subo el extracto y el sistema lo ordena solo |
| Filminas | 13:30 – 18:15 | Clasificador (con capturas) | Cómo adivina la categoría de cada gasto |
| 2 | 20:15 – 21:30 | Auditoría → Facturas (de pasada) | Revisa todo solo y avisa lo raro |
| 3 | 22:30 – 24:00 | Monotributo → Proyecciones | Te dice cuándo te pasarías del tope y qué viene |
| 4 | 27:45 – 29:15 | Recomendaciones → Dashboard (PDF) | Sugerencias con su porqué y el resumen del mes en PDF |

## En vivo, módulo por módulo

En el orden en que los vas a abrir. Cada módulo arranca con **qué hace en una frase**: si solo decís esa frase, ya cumpliste.

### Tramo 1 · Entrar e importar (9:20 – 13:30)

Los dos rechazos del principio suman unos 25 segundos. **Si vas atrasado, hacé solo el PDF.**

#### Entrar (inicio de sesión)

**Qué hace:** te deja entrar a tu cuenta sin que la base guarde tu contraseña.

**HACÉ:** `demo@freelancecontrol.com` / `demo1234` → Ingresar.

**DECÍ:**

> "Entro con la cuenta de una freelancer de ejemplo. La base no guarda mi contraseña: guarda su hash. El hash sale de pasar la contraseña por una fórmula que va en una sola dirección: de la contraseña se llega al hash, pero del hash no se puede volver a la contraseña. Antes de calcularlo le agrega una sal al azar, distinta para cada usuario, así dos personas con la misma contraseña quedan con hashes distintos. Para dejarme entrar, calcula el hash de lo que escribí con la misma sal y lo compara con el guardado. Si alguien se roba la base, se lleva hashes, no contraseñas. Al entrar, el sistema me da un pase firmado que vence solo."

El hash se cuenta acá, en palabras, mientras entrás (unos 40 segundos): la filmina con los dos hashes ya no está en la exposición. Quedó primera en el anexo, por si preguntan o piden verlo en la base.

Palabras clave: **hash, no contraseña** · **una sola dirección** (del hash no se vuelve) · **sal distinta por usuario** · **pase firmado**.

**Ojo con la palabra:** decí "hasheada", nunca "encriptada". Encriptar se deshace con una llave; el hash no se deshace nunca.

**Si te preguntan:**

- *¿Qué es la sal?* → "Veintidós caracteres al azar que se mezclan con la contraseña antes de calcular el hash, distintos para cada usuario. Se guardan junto al hash: no son secretos, su trabajo es que dos contraseñas iguales no den el mismo hash."
- *¿No se puede adivinar probando?* → "Se puede intentar, pero bcrypt repite el cálculo de cada intento 4.096 veces a propósito: es el costo 12 que se ve en el hash. A mí entrar me lleva una fracción de segundo; probar millones de contraseñas se vuelve lentísimo."
- *¿Y si pongo un correo que no existe?* → "Contesta el mismo mensaje y tarda lo mismo, porque igual compara contra un hash de relleno. Así nadie puede averiguar qué correos están registrados."
- *¿Lo puedo ver en la base?* → Terminal **1 · La contraseña en la base**: clic en la ventana y Enter, porque el comando ya está escrito (ver «En las preguntas: las cuatro terminales»). También está en la primera filmina del anexo, para copiarlo:

    ```bash
    sh defensa_final/demo/ver_usuarios.sh
    ```

    Da exactamente lo de la filmina: la siembra conserva el hash de la cuenta demo, y la cuenta del tribunal (misma contraseña) no se borra. Solo lee la base.
- *¿Qué es el pase?* → "Un token firmado con una clave que solo tiene el servidor. Se puede leer, pero si alguien lo modifica la firma no coincide y deja de servir. Vence a los siete días."

#### Importar CSV

**Qué hace:** lee el extracto que bajás del banco o de la billetera, lo ordena solo y, antes de guardar, te muestra qué va a hacer con cada movimiento.

##### Primero, dos archivos que no son extractos (unos 25 segundos)

Lo pide la tesis (HU-07): un archivo que no sea CSV ni Excel se rechaza antes de procesarlo. Los dos archivos están en la misma carpeta que el extracto, y **no se guarda nada**.

**HACÉ:** menú **Importar CSV** → clic en el recuadro → Escritorio → Defensa_FreelanceControl → 4_Demo → elegí `resumen_banco.pdf`.

- Si el Mac lo muestra en gris y no te deja elegirlo, ese ya es el rechazo: decilo así y cerrá la ventana.
- Si te deja elegirlo, abajo del recuadro aparece en rojo: "Solo se aceptan archivos .csv o .xlsx".

**DECÍ:**

> "Primero, lo que hace mucha gente: subir el PDF del resumen del banco. Lo rechaza antes de procesarlo: un PDF no trae los datos en columnas."

**HACÉ:** clic en el recuadro → elegí `planilla_vacia.xlsx` → **Analizar archivo** → aparece en rojo: "El archivo no tiene movimientos: solo se encontró el encabezado."

**DECÍ:**

> "Un Excel sí lo acepta, pero este tiene solo los títulos. Lo lee, ve que no hay movimientos y me lo dice. No guarda nada."

##### Ahora, el extracto de verdad

**HACÉ:** clic en el recuadro → elegí `extracto_28sep_14oct.csv` → **Analizar archivo**.

**DECÍ (para abrir):**

> "Ahora sí, el extracto del homebanking. En vez de tipear gasto por gasto, lo subo. El sistema reconoce solo cuál columna es la fecha, cuál la descripción y cuál el monto, sin configurar nada. Y antes de guardar me muestra qué va a hacer. Este extracto lo armamos con seis casos difíciles a propósito."

**Lo que tenés que saber de los seis casos.** Los metimos nosotros en el CSV: el sistema no sabe que son trampas, solo aplica sus reglas. Cuatro aparecen marcados en pantalla y dos los señalás vos. La vista previa muestra **solo las primeras 20 filas** (lo pide la tesis), por eso Grupo Delta y la Visa aparecen recién en el Dashboard.

| Caso | Dónde se ve | Qué aparece |
|---|---|---|
| 1. Rappi, Uber y SUBE ya cargados | Vista previa, cartel de arriba | "3 movimientos ya existen…" y la etiqueta **SE OMITE · DUPLICADO** |
| 2. Los $ 200.000 que van y vuelven | Vista previa, cartel de arriba | "⇄ 2 movimientos parecen parte de una transferencia…" y **SE OMITE · TRANSFERENCIA PROPIA** |
| 3. La fecha 31/09 | Vista previa, recuadro rojo | "Fila 22 (DEBITO RECHAZADO REINTEGRO): fecha inexistente" |
| 4. Coworking y Telecentro | Vista previa, columna Categoría | Dice "Otros", sin cartel: **lo señalás vos** |
| 5. Los dos Figma | Al confirmar | "2 movimientos importados parecen repetidos" |
| 6. El 1.850.000 de Grupo Delta | Dashboard, "Últimos movimientos" | + $ 1.850.000,00, sin cartel: **lo señalás vos** |

Frená en cada uno, de arriba abajo. Una frase por cada uno:

1. **Lo que ya estaba** (cartel amarillo y las filas grises de Rappi, Uber y SUBE) → "Estos tres ya los había cargado con otro extracto. Los reconoce y no los guarda de nuevo: si no, septiembre quedaría inflado." Clave: **no carga dos veces**.
2. **La plata que va y vuelve** (cartel ⇄ y las filas grises de los $ 200.000) → "Me mandé plata a mi propia cuenta y volvió. Eso no es un cobro: si lo contara, inflaría lo facturado y me podría cambiar la categoría. Lo deja afuera." Clave: **transferencia propia no es ingreso**.
3. **La fecha imposible** (recuadro rojo) → "El 31 de septiembre no existe. No la adivina ni la corrige: deja la fila afuera y me dice por qué." Clave: **no inventa datos**.
4. **Lo que no reconoce** (el coworking, fila 5, y Telecentro, fila 17: dicen "Otros") → "Fíjense que cada gasto ya trae su categoría: eso es el clasificador trabajando. Los que no reconoce no los adivina: los manda a 'Otros' para que yo los revise." Clave: **ante la duda, Otros**.

**HACÉ:** **Confirmar**.

5. **Dos gastos iguales** (el cartel de abajo: "2 movimientos importados parecen repetidos") → "Son los dos Figma, del 2 y del 4 de octubre. Son nuevos, así que los guardó, pero los marcó como posible repetido. El sistema avisa; decide el usuario." Clave: **avisa, no decide**.

**DECÍ (con el resultado en pantalla):**

> "Guardó solo lo que corresponde, y me dice qué dejó afuera y por qué. Guarda todo junto o nada: no queda nada a medias. Y el archivo nunca salió de esta computadora."

El caso 6, Grupo Delta, lo mostrás en el Dashboard.

Palabras clave: **rechaza lo que no es extracto** · **subo el extracto, no tipeo** · **vista previa antes de guardar** · **seis casos** · **no sale de la compu**.

**Si te preguntan:**

- *¿Por qué no lo conectaron directo al banco?* → "Hoy en Argentina no hay una forma estándar y segura de que una app lea las cuentas de todos los bancos. Lo único que dan todos es el archivo, y para eso no hace falta pedirle ninguna clave al usuario. Quedó como trabajo futuro."
- *¿Qué bancos lee?* → Nueve: Galicia, Santander, BBVA, Macro, Nación, Brubank, ICBC, Mercado Pago y Naranja X.
- *¿Y si subo el mismo archivo dos veces?* → La segunda vez no entra nada nuevo: reconoce todo lo que ya estaba cargado y lo omite.
- *¿Y si a un PDF le cambio el nombre a .csv?* → "Lo rechaza igual: 'No se pudo leer el archivo'. No se fija solo en el nombre: intenta leerlo."
- *¿Por qué los cobros dicen "Otros"?* → "El clasificador es de gastos: conoce las 12 categorías de gastos. Los cobros entran como 'Otros' y el usuario les pone el rubro en Ingresos."
- *¿Por qué la vista previa muestra solo 20 filas?* → "Lo pide la tesis: es una muestra para confirmar. Al confirmar se guardan todas, no solo las 20."

#### Dashboard (panel principal)

**Qué hace:** te muestra la foto del mes de un vistazo.

**HACÉ:** menú **Dashboard**. Recorré con el mouse las cuatro tarjetas, la recomendación, la lista **"Últimos movimientos"** y el aviso de abajo.

**DECÍ:**

> "El panel abre siempre en el mes actual. Antes de importar, octubre estaba vacío; ahora ya muestra lo que cobré, lo que gasté y el balance. La cuarta tarjeta es cuánto espero cobrar el mes que viene. A la derecha, la recomendación más urgente. Y abajo, el aviso de alcance: no está solo en la presentación, está en el producto."

Y señalando "Últimos movimientos":

> "Acá está el último caso del extracto: el cobro de Grupo Delta, un millón ochocientos cincuenta mil. En el archivo venía con puntos de miles, como escribimos acá, y lo leyó bien. En la misma lista está el pago de la tarjeta Visa: ese también lo mandó a 'Otros', porque no supo qué era."

Palabras clave: **la foto del mes** · **abre en el mes actual** · **Grupo Delta, punto de miles** · **el aviso está en el producto**.

**Si te preguntan** *¿por qué octubre muestra un gasto menos de los importados?* → "La comisión del banco es del 30 de septiembre, así que cayó en septiembre. Cada movimiento va al mes de su fecha, no al del día en que lo importé."

Dato a mano: la tarjeta de ingresos de octubre dice **$ 3.460.000**, que son los tres cobros del extracto (980.000 + 630.000 + 1.850.000).

**Volvé a las filminas.**

### Filminas · El clasificador (13:30 – 18:15)

No se toca la app: lo contás con las capturas. Es **el punto más importante de la tesis**, así que acá no apures.

#### Clasificador

**Qué hace:** lee la descripción de cada gasto y le pone la categoría solo, entre 12 posibles.

**Qué dice la tesis aprobada:** la meta es acertar **70 % o más** sobre 12 categorías, y se logró **76 %**. Prevé dos algoritmos: **Naive Bayes para pocos ejemplos y SVM desde cien**. El código hace exactamente eso, y como el modelo siempre parte de 600 ejemplos, corre el SVM.

**El hilo, para no perderte:** lo vieron trabajar → aprende de ejemplos → una planilla de puntos → si duda, pregunta → aprende de tus correcciones → hasta dónde llega. **Si te quedás en blanco:** "Aprende de ejemplos; si duda, pregunta; y aprende de tus correcciones."

**DECÍ, en seis pasos** (uno por filmina, más o menos):

1. **Ya lo vieron trabajar.**

    > "Cuando importé el extracto, cada gasto llegó con su categoría y nadie la eligió: la puso el clasificador, leyendo la descripción. Los que no reconoció, como el coworking o Telecentro, no los inventó: los mandó a 'Otros' para que yo los revise. Ahora les cuento cómo lo hace."

2. **Qué es: aprende de ejemplos, no de reglas.**

    > "Es aprendizaje automático. Nosotros no le escribimos reglas del tipo 'si dice Uber, es Transporte'. Le dimos 600 gastos ya clasificados, 50 de cada una de las 12 categorías, y él solo aprendió a separarlos. El algoritmo se llama SVM, máquina de vectores de soporte: los vectores de soporte son los ejemplos más difíciles, los que quedan pegados a la frontera entre dos categorías, y son los que la definen. La tesis prevé dos algoritmos: Naive Bayes para cuando hay pocos ejemplos y SVM desde cien. Como siempre arranca con esos 600, usa el SVM."

    *Puente:* "¿Y cómo aprende a separarlos?"

3. **Cómo aprendió a separarlas: una planilla de puntos por palabra.**

    > "La computadora no entiende palabras, entiende números. Entonces hace dos cosas. Primero, le da un peso a cada palabra: pesa más una rara, como 'jetbrains', que una que aparece en todos lados, como 'pago'. Segundo, para cada categoría arma una planilla de puntos: palabras que suman y palabras que restan. En la de Transporte suman 'viaje', 'vuelo' o 'peaje', y restan 'compra' o 'impuesto'. Esos puntos no los escribió nadie: el SVM los fue ajustando mirando los 600 ejemplos, hasta que cada uno sumara más en su categoría correcta, y con la mayor ventaja posible. Cuando llega un gasto nuevo, suma sus palabras en las doce planillas, y gana la que más suma."

    La analogía:

    > "Es como alguien nuevo en el correo: nadie le explica las reglas, pero mirando muchas cartas ya separadas aprende qué palabras van a cada caja."

    *Puente:* "Pero ganar no alcanza: también tiene que saber si ganó con seguridad."

    Lo que realmente aprendió, por si piden un ejemplo (sacado del modelo entrenado):

    - **Transporte** suma con *auto, viaje, vuelo, abono, estación* y resta con *compra, monotributo, impuesto*.
    - **Software:** *licencia, antivirus, plugin, photoshop*.
    - **Infraestructura:** *hosting, aws, servidor, ssl, cloud*.
    - **Marketing:** *ads, seo, agencia, campaña, publicidad*.
    - Gasto nuevo "UBER VIAJE": Transporte suma +0,68 y la segunda, Hardware, −0,93. Gana Transporte.

    ¿Por qué ejemplos **parejos**? "Si una categoría tuviera 300 ejemplos y las demás 25, el modelo aprendería a decir siempre esa, y el porcentaje mentiría."

4. **Cuándo duda: si casi empatan, va a Otros.**

    > "La seguridad la medimos como en una elección: no importa cuántos votos sacó el ganador, importa por cuánto le ganó al segundo. En 'uber viaje', Transporte le gana por mucho a la segunda: está seguro y lo guarda. En 'telecentro internet fibra' no conoce ninguna de esas palabras y las dos primeras casi empatan: entonces no adivina, lo manda a 'Otros' para revisar. Es el Telecentro que vieron en la importación. Preferimos una revisión antes que una categoría equivocada."

    *Puente:* "Y cuando el usuario corrige, el sistema aprende."

    Los números, si los piden: en "Uber viaje", Transporte le gana lejos a Hardware y queda con **80 %** de seguridad. En "Telecentro internet fibra", Hardware saca −0,77 y Transporte −0,79: empate técnico, **2 %**, va a "Otros". La vara está en **30 %**.

5. **Cómo aprende: de tus correcciones.**

    > "En el extracto, muchos gastos vienen solo con el nombre del comercio. 'Mostaza' el modelo nunca la vio, así que la manda a 'Otros'. La corrijo a Alimentación, y la corrección vale al instante. Además, de fondo y sin trabar la pantalla, el modelo se vuelve a entrenar. Por eso 'mostaza palermo', que nunca le enseñé, ahora va sola a Alimentación: aprendió la palabra, no solo la frase. Y cada usuario tiene su propio modelo: la base más sus gastos."

    *Puente:* "Y, como pidió la cátedra, hasta dónde llega."

    Los números de las capturas: "mostaza" → **Otros, 1 %**; corregida → **Alimentación, 100 %** ("Corrección tuya"); "mostaza palermo" después del reentrenamiento → **Alimentación, 73 %**, arriba de la vara del 30 %. *¿Por qué 73 y no 100?* → "Es una sola corrección contra casi setecientos ejemplos: el modelo no se da vuelta por un solo dato, y eso es sano. Y sube con cada gasto de Mostaza que cargue: con uno más, 78 %; con dos, 81 %."

    Ojo: por eso, después de importar, la pantalla del Clasificador dice **78 %** y no 76. La usuaria pasó los 20 gastos y el sistema le entrenó su modelo propio: los 600 de base más sus 91 gastos. El 76 es el modelo de base, el de la tesis.

6. **Los desafíos y los límites** (los pidieron el profesor y la cátedra).

    **Desafíos** (la filmina quedó en el anexo; en la exposición nombralos en una frase, antes de los límites: "Llegar a esto costó: pocos ejemplos de base, que supiera cuándo duda y reentrenar sin trabar la pantalla. Si quieren, los tengo en el anexo. Y medirlo de forma honesta, que es lo que les muestro ahora."):

    - **Pocos datos, nuestros, no del usuario.** Con 216 ejemplos (18 por categoría) acertaba el 57 %. Lo ampliamos a 600, 50 por categoría, y llegó al 76 %. Un usuario nuevo **no entrena nada**: desde el primer día usa ese modelo de 600, y a los 20 gastos recibe uno propio que es 600 más los suyos. Nunca arranca de cero.
    - **Medirlo honesto: la validación cruzada.**

        > "No lo medimos con los gastos con los que aprendió, porque esos se los sabe de memoria. Sería como un examen con las mismas preguntas que se dieron en clase: todos se sacan 10. Por eso lo probamos con gastos que nunca había visto. Y para que no fuera suerte, lo hicimos cinco veces, cada vez con otros gastos, y sacamos el promedio. Dio 76 %, y la meta era 70."

        En la exposición esta frase es optativa, al cerrar los límites (20 s). La filmina con las cinco vueltas quedó en el anexo (36), con el comando para correrlo si lo piden (abajo).

    - **Saber cuándo duda.**

        > "El primer intento usó una fórmula estándar que reparte 100 % entre las doce categorías. Aunque una gane clarísimo, las otras once se llevan su parte: 'Uber viaje', un acierto obvio, sacaba 32 %, y algo dudoso como Telecentro, 9 %. Todo quedaba amontonado abajo y casi todo iba a revisión. La solución fue medir por cuánto le gana la primera a la segunda: el recuento de la elección."

    - **Reentrenar sin trabar:** de fondo y de a uno por usuario.

    **Límites:**

    - **Acierta 3 de cada 4.** Por eso existe la revisión: no es un parche, es parte del diseño. Y se puede probar: anexo, filmina 36 (abajo).
    - **Entiende palabras, no contexto.** "Diseño de logo" puede ser Marketing o Servicios.
    - **Las 12 categorías son fijas.** Lo que no encaja va a "Otros".
    - **Los ejemplos de base los armamos nosotros.** Sumar datos reales es trabajo futuro.

#### Probar cómo se midió el 76 % y que la revisión funciona (anexo, filmina 36)

En la filmina está la salida del script de evaluación y el comando, para copiarlo. La filmina quedó en el anexo: se muestra y se corre **si lo piden**. Para correrlo: terminal **2 · Las cinco vueltas**, clic en la ventana y Enter (el comando ya está escrito). Tarda menos de un segundo, no cambia nada y da exactamente lo de la filmina (verificado el 11/10, con las cinco vueltas; las últimas líneas son las de la filmina):

```bash
docker compose exec -T api python - < evaluar_modelo.py
```

Lo que imprime, y qué decir:

- **"Accuracy global: 0.7600 (76.00%)"** y **"Las cinco vueltas"** (84,2 · 78,3 · 75,8 · 70,0 · 71,7 → promedio 76,0; cada vuelta, 120 gastos que no vio) → la frase del examen:

    > "¿Cómo sabemos que acierta el 76 %? No lo medimos con los gastos con los que aprendió, porque esos se los sabe de memoria. Sería como un examen con las mismas preguntas que se dieron en clase: todos se sacan 10. Por eso lo probamos con gastos que nunca había visto. Y para que no fuera suerte, lo hicimos cinco veces, cada vez con otros gastos, y sacamos el promedio. Dio 76 %, y la meta era 70."

- **"SVM 76.0 % · Naive Bayes 74.0 %"** → "Los dos algoritmos que prevé la tesis, con los mismos ejemplos."
- **"Qué pasa con los errores":**

| De 600 gastos que el modelo no había visto | Cantidad |
|---|---|
| Acertó y estaba seguro | 378 |
| Acertó, pero pidió revisión | 78 |
| **Se equivocó y pidió revisión** | **93** |
| Se equivocó estando seguro | 51 |

> "Acierta 3 de cada 4. Pero de cada 3 errores, 2 no se guardan callados: van a revisión. Y cuando pone una categoría sin dudar, acierta casi 9 de cada 10. Por eso la revisión no es un parche: es lo que vuelve confiable un 76."

Y en la demo ya se vio: de los 26 gastos nuevos del extracto, a 23 les puso categoría y 3 los mandó a "Otros" (el coworking, Telecentro y la Visa).

Palabras clave: **aprende de ejemplos** · **planilla de puntos por palabra** · **elección: por cuánto ganó** · **si duda, Otros** · **2 de cada 3 errores van a revisión** · **corre en tu compu**.

**Si te preguntan:**

- *¿Por qué no usar ChatGPT?* → "Porque habría que mandarle la descripción de cada gasto a una empresa de afuera, y ahí están los clientes, los proveedores y los hábitos del usuario. El SVM corre acá adentro y los datos no salen."
- *¿Y Naive Bayes?* → "La tesis prevé los dos: Naive Bayes para pocos ejemplos y SVM desde cien, y está implementado así. Como el modelo siempre parte de 600 ejemplos, corre el SVM. Con los mismos 600, 76 contra 74; lo puedo correr acá."
- *¿Qué es Naive Bayes?* → "Cuenta qué tan seguido aparece cada palabra en cada categoría y multiplica esas probabilidades como si las palabras no tuvieran relación entre sí; por eso le dicen 'ingenuo'. Anda bien con pocos datos. El SVM busca la frontera que mejor separa, y con más datos gana."
- *¿Un usuario nuevo tiene que entrenarlo?* → "No. Desde el primer día usa el modelo de 600 ejemplos. A los 20 gastos el sistema le entrena uno propio, que es 600 más los suyos. Lo único que hace el usuario es corregir lo que cae en 'Otros'."
- *¿Por qué el Clasificador dice 78 % y no 76?* → "El 76 es el modelo de base, el de la tesis. Después de importar, esta usuaria tiene modelo propio, con sus gastos sumados, y mide 78."
- *¿Lo de los errores que van a revisión está en la tesis?* → "No: es una medición extra sobre los mismos 600 ejemplos y las mismas cinco vueltas. El script la imprime al final."

### Tramo 2 · Auditoría (20:15 – 21:30)

#### Auditoría

**Qué hace:** revisa todos tus registros con cinco controles y te avisa lo que parece raro. **Avisa, no corrige sola.**

Los cinco controles, para nombrarlos de corrido: **gastos repetidos, gastos irregulares, facturas vencidas, cuota del monotributo sin pagar y transferencias entre cuentas propias.**

**HACÉ:** menú **Auditoría** → **Ejecutar auditoría** → aparecen 5 alertas. Recorrelas de arriba abajo.

**DECÍ (para abrir):**

> "La auditoría es la que revisa por mí lo que nadie revisa. No corre sola: corre cuando aprieto este botón. Encontró cinco cosas."

Después, una frase por alerta:

1. **Figma repetido** → "Los dos Figma del extracto: mismo monto, misma categoría y pocos días de diferencia. Puedo eliminar el repetido o, si fueron dos compras de verdad, marcarlo como resuelto, y no vuelve a aparecer." Clave: **posible duplicado**.
2. **Adobe repetido** → "Este es de junio. Lo encuentra aunque sea viejo."
3. **El servidor de julio** → "Un gasto irregular: mucho más alto de lo que esa categoría suele gastar. En la filmina que sigue les explico cómo lo mide." Clave: **gasto irregular**.
4. **Dos facturas vencidas** (Consultora Aurora y Brand Studio) → "Dos facturas vencidas sin cobrar. Brand Studio en realidad pagó, y vino en el extracto. Pero cruzar los cobros del banco con las facturas quedó fuera del alcance: la marca pagada el usuario. Es un límite, y lo digo." Clave: **límite honesto**.
5. **Lo que no aparece** → "No aparece la cuota del monotributo porque vino pagada en el extracto. Ni la transferencia a mi propia cuenta, porque la frenó la importación. Los módulos se hablan entre sí."

**HACÉ:** bajá un poco y señalá el aviso de alcance al pie.

**No toques ningún botón de las alertas** (ni Resolver ni Eliminar): cambia lo que después muestran las Recomendaciones.

Palabras clave: **revisa por vos** · **cinco controles** · **avisa, no corrige** · **los módulos se hablan**.

#### Facturas, de pasada (unos 15 segundos)

**Qué hace:** lleva las facturas que emitiste y te muestra en qué estado está cada una, con su propio semáforo.

**HACÉ:** menú **Facturas**. Señalá los tres colores: verde (las pagadas), amarillo (Tienda Sur y Acme) y rojo (Consultora Aurora y Brand Studio). **No toques "Marcar pagada"**: cambia lo que después muestran las Recomendaciones.

**DECÍ:**

> "Las facturas las cargo a mano: cliente, monto, fecha de emisión y vencimiento. Tienen su propio semáforo: amarilla mientras está en plazo; roja si venció sin cobrarse, y eso lo cambia el sistema solo; y verde cuando la marco pagada. Las rojas son las que acaba de encontrar la auditoría."

Palabras clave: **se cargan a mano** · **amarilla, roja, verde** · **vence sola**.

**Si te preguntan:**

- *¿Marcarla pagada crea un ingreso?* → "No, a propósito: el cobro ya entra con el extracto, y se contaría dos veces."
- *¿Se puede editar una pagada?* → "No: una pagada ya no se edita ni se borra. Lo pide la tesis."

**Volvé a las filminas.**

#### Filmina · Qué es un gasto irregular (21:30 – 22:30)

**DECÍ:**

> "El sistema compara cada gasto con los de su misma categoría de los últimos seis meses. Saca el promedio y cuánto se suelen mover esos gastos alrededor del promedio, que se llama desvío. Si un gasto se pasa del promedio por más de dos desvíos, lo marca como irregular."

La analogía que lo explica todo, **la boleta de luz**:

> "Si tu boleta siempre viene parecida, una un poco más alta te llama la atención. Si tu boleta varía mucho entre invierno y verano, esa misma boleta es normal. Por eso la vara no es fija: se ajusta sola a cada categoría."

Para cerrar:

> "Solo marca gastos más altos de lo normal, y necesita historia: al menos seis gastos de esa categoría. Y en esa alerta no hay botón de borrar, a propósito: un gasto alto puede ser real, como comprar un servidor caro."

Palabras clave: **se compara con su propia categoría** · **la vara se ajusta sola** · **boleta de luz** · **señal, no acusación**.

### Tramo 3 · Monotributo y Proyecciones (22:30 – 24:00)

Este tramo lo pidió el profesor en la 4.ª entrega: **no se recorta nunca**.

#### Monotributo

**Qué hace:** compara cuánto vas a haber facturado a fin de año con el tope de tu categoría, y te lo muestra con un semáforo.

**HACÉ:** menú **Monotributo**. Señalá, de arriba abajo:

1. La franja verde de arriba: la cuota de octubre figura pagada.
2. La barra roja: lo facturado hasta hoy contra el tope de la categoría G.
3. La tarjeta de la derecha: Diciembre 2026.
4. El recuadro rojo: "superarías el límite en diciembre" y la categoría H.
5. El aviso de alcance al pie.

**DECÍ:**

> "Acá está el control del tope. El sistema no mira solo lo que ya cobré: suma lo cobrado más lo que espera cobrar hasta diciembre, y lo compara con el tope de mi categoría. A este ritmo me pasaría en diciembre, y la categoría que cubriría esa facturación es la H. Fíjense que no dice 'te pasaste': dice cuándo te pasarías. Esa es la respuesta a la pregunta del trabajo: anticipar el riesgo, no solo registrarlo."

Y señalando la franja verde y el aviso:

> "La cuota de octubre figura pagada porque vino en el extracto. Y el aviso lo deja claro: la categoría la define ARCA, y la decisión es del usuario con su contador."

**El semáforo, en criollo:** **verde**, lejos del tope · **amarillo**, cerca · **rojo**, a este ritmo te pasarías.

Palabras clave: **semáforo** · **lo cobrado + lo que viene** · **cuándo te pasarías** · **anticipar, no registrar**.

#### Proyecciones

**Qué hace:** estima cuánto vas a cobrar en los próximos seis meses, con un escenario esperado, uno pesimista y uno optimista.

**HACÉ:** menú **Proyecciones**. **Esperá unos 2 segundos** a que se anime el gráfico antes de hablar. Señalá el punto hueco de octubre y después la franja sombreada de noviembre.

**DECÍ:**

> "Acá el sistema mira lo que cobré cada mes cerrado, la línea blanca, y estima los próximos seis, la línea azul. La azul no es el promedio: es hacia dónde vienen yendo mis cobros. No da un solo número: da un rango, entre un escenario pesimista, en rojo, y uno optimista, en verde."

> "Octubre aparece hueco porque el mes no terminó: si lo usara por la mitad, tiraría la proyección para abajo. Y el rango es ancho porque esta freelancer alterna meses muy buenos con meses flojos. El sistema no lo esconde: lo muestra."

Palabras clave: **un rango, no un número** · **la azul es la tendencia, no el promedio** · **mes a medias no cuenta** · **rango ancho = ingresos irregulares**.

**Volvé a las filminas.**

#### Filminas · El semáforo y Prophet (24:00 – 27:45)

**El semáforo**, con la analogía del viaje:

> "El semáforo responde una sola pregunta: ¿cuánto voy a haber facturado el 31 de diciembre? Es como un viaje de Córdoba a Rosario: el largo del viaje es lo que voy a haber facturado a fin de año; lo recorrido es lo que ya cobré. La barra muestra lo recorrido; el semáforo mira el viaje entero."

**El hilo:** separa la historia en capas → con eso arma tres escenarios → y tiene límites claros. **Si te quedás en blanco:** "Mira hacia dónde van mis cobros y me da un rango, no un número."

**Qué es Prophet:**

> "La proyección que vieron en vivo la hace Prophet, una herramienta gratuita de Meta, la empresa de Facebook, pensada para pronosticar números que cambian con el tiempo. Separa la historia en capas, como los instrumentos de una canción: la tendencia, hacia dónde van mis cobros; la estacionalidad, lo que se repite cada año; y el ruido, el sube y baja sin patrón. La estacionalidad Prophet la enciende solo cuando hay dos años de historia; esta freelancer tiene nueve meses, así que trabaja con la tendencia y el ruido."

*Puente:* "Con esas capas arma los tres escenarios."

**Si lo entrenamos y con qué datos:**

> "No viene entrenado de fábrica y no le dimos datos nuestros. Cada vez que cambian los cobros, o empieza un mes, toma los cobros de esta usuaria y se ajusta en el momento, en un segundo, en la computadora. Usa un solo dato: el total cobrado en cada mes cerrado. Nada de gastos, ni inflación, ni datos de otras personas, ni internet."

**Cuánta historia necesita:**

> "Con poca historia, menos de diez cobros o menos de tres meses cerrados, no usa Prophet: proyecta el promedio de los últimos tres meses, una línea plana, y la pantalla lo dice. Esta freelancer tiene 27 cobros en nueve meses, así que corre Prophet."

**Cómo arma los tres escenarios, en criollo:**

- **Esperado (azul):** "La línea que mejor pasa por el medio de mis meses, estirada seis meses: es 'si sigo como vengo'. No es el promedio. El promedio del año es 4,1 millones, pero el esperado de noviembre es 7,1, porque el año arrancó con dos meses flojos y septiembre fue el mejor: la línea viene subiendo."
- **Para los otros dos:** "Mide cuánto se apartó cada mes de esa línea: acá, hasta cuatro millones para arriba o para abajo. Después imagina mil futuros posibles, cada uno con la línea más sacudones del mismo tamaño, y los ordena de peor a mejor."
- **Pesimista (rojo):** "Solo uno de cada diez futuros quedó por debajo. En nueve de cada diez cobro más que esto: sirve para planificar los gastos fijos." Noviembre: 3,6 millones.
- **Optimista (verde):** "Solo uno de cada diez futuros lo supera: no conviene gastar contando con eso." Noviembre: 10,7 millones.
- **El ancho de la franja:** "Es qué tan irregular fui. Un sueldo parejo da una franja finita; esta freelancer, ancha. Es como el pronóstico del tiempo: 'mañana, entre 18 y 26 grados'."

**De dónde salen los datos de la demo** (si lo preguntan):

> "Los cobros de enero a septiembre son ficticios: los armamos nosotros, alternando meses buenos, de 5 a 10 millones, con meses flojos, de 1 a 2, como cobra un freelancer por proyecto. Así hay historia para que corra Prophet, la franja sale ancha y, a ese ritmo, el año pasa el tope en diciembre. A Prophet no le tocamos ninguna perilla: usa sus valores de fábrica. Lo que fijamos nosotros es usar solo meses cerrados, seis meses, nunca menos de cero, y el azar con semilla fija, para que los mismos datos den siempre lo mismo."

**Los límites** (los pidió la cátedra), uno por línea:

- **Rango ancho** cuando los ingresos son irregulares.
- **No contempla la inflación:** son montos tal cual.
- **Necesita historia.** Si no la hay, usa el promedio de los últimos meses y lo dice en pantalla.
- **Seis meses y no más:** más lejos, el error pesa más que la estimación.
- **No sabe lo que no está en tu historia:** si ayer firmaste un contrato grande, no lo sabe.

Palabras clave: **viaje Córdoba–Rosario** · **capas de una canción** · **la línea, no el promedio** · **mil futuros** · **1 de cada 10** · **pronóstico del tiempo**.

**Si te preguntan:**

- *¿Por qué no se movió el porcentaje al importar?* → "Porque lo que cobré en octubre ya estaba previsto. Al importar, esa plata pasó de 'esperada' a 'cobrada', y el total del año quedó igual. Es el viaje: se movió lo recorrido, no el largo del viaje."
- *¿La escala de ARCA se actualiza sola?* → "No, pero tampoco hay que tocar el cálculo: la escala es un dato con su fecha. ARCA no ofrece una forma oficial de leerla con un programa, y cambia dos veces por año. Cargarla lleva minutos, y la de agosto entró así."
- *¿Por qué Prophet y no otro?* → "Porque da el rango además del número, se ajusta solo a cada usuario, se puede explicar y corre en la computadora sin mandar los ingresos afuera."
- *¿Lo entrenaron?* → "No como al clasificador: se ajusta en el momento con los cobros de cada usuario. No hay datos nuestros adentro."
- *¿Por qué espera 7 millones si el promedio es 4?* → "Porque Prophet no mira el promedio, mira hacia dónde va: el año arrancó flojo y septiembre fue el mejor mes, así que la línea sube."
- *¿Por qué el pesimista de abril da 6,2 millones si los meses flojos son de 1,5?* → "Porque el pesimista se mide alrededor de la línea, y la línea viene subiendo. Con nueve meses, Prophet no sabe que los meses flojos se repiten: los toma como vaivén. Por eso proyectamos seis meses y no más, y la decisión es del usuario."
- *¿Sabe que diciembre es temporada alta?* → "Todavía no: para aprender lo que se repite cada año necesita dos años de historia."

### Tramo 4 · Recomendaciones y reporte PDF (27:45 – 29:15)

#### Recomendaciones

**Qué hace:** te sugiere de tres a cinco cosas para mirar, ordenadas por urgencia, y cada una te dice de dónde sale.

**HACÉ:** menú **Recomendaciones**. Leé la primera y señalá su renglón **"Por qué"**. Bajá a la segunda y a la tercera.

**DECÍ:**

> "Las recomendaciones no usan inteligencia artificial: son reglas fijas, ordenadas por urgencia. Y cada una muestra su 'Por qué': el dato exacto del que sale, para que el usuario pueda verificarlo."

> "La primera son las dos facturas vencidas. La segunda es el tope del monotributo, y sugiere consultarlo con el contador. La tercera, las alertas de la auditoría que todavía no revisé. Fíjense cómo están escritas: 'te sugerimos'. Son sugerencias, no órdenes."

Palabras clave: **reglas, no IA** · **cada una con su porqué** · **sugiere, no ordena** · **ordenadas por urgencia**.

#### Reporte PDF

**Qué hace:** arma el resumen del mes cerrado en un PDF, para archivarlo o compartirlo.

**HACÉ:** menú **Dashboard** → arriba a la derecha el selector ya dice **Septiembre 2026** → **Descargar reporte PDF** → abrí el archivo → bajá hasta el pie.

**DECÍ:**

> "Este es el reporte de septiembre, el último mes cerrado. Tiene cuánto entró y salió comparado con el mes anterior, el estado del monotributo, los gastos por categoría, las facturas y las alertas pendientes. Es lo único que sale de la aplicación, y por eso lleva el aviso adentro: no reemplaza el asesoramiento de un contador matriculado."

Palabras clave: **el resumen del mes cerrado** · **lo único que sale** · **el aviso va adentro**.

**Si te preguntan** *¿es un reporte para el contador?* → "No es un documento contable: es el resumen del mes cerrado. La tesis lo plantea para que el usuario lo archive o, si quiere, lo comparta con su contador. Por eso lleva el aviso de que no reemplaza su asesoramiento."

**Volvé a las filminas.**

#### Filminas · Límites de las recomendaciones y cierre (29:15 – 32:00)

**Los límites de las recomendaciones** (los pidió la cátedra):

> "Las recomendaciones solo ven lo que cargó el usuario: no conocen su situación personal, sus deudas ni cuánto riesgo quiere correr. Si sugieren hacer algo con un excedente, el instrumento lo elige el usuario: el sistema no dice en qué invertir."

**El Resumen del mes, en una frase** (no se abre en vivo):

> "El único lugar que usa una inteligencia artificial de afuera es el Resumen del mes, que escribe en castellano cómo te fue. Recibe solo totales, nunca descripciones, clientes ni el correo. Si inventa una cifra, se descarta; y sin internet, usa una plantilla local."

**El cierre:**

1. **Objetivos cumplidos:** clasificar, proyectar, controlar el monotributo y auditar, con el prototipo funcionando. El clasificador superó la meta.
2. **Cómo se hizo:** con Scrum, en etapas cortas, cada una con algo funcionando para revisar.
3. **Trabajo futuro:** facturación electrónica de ARCA, conectar el banco cuando haya reglas para eso, datos reales para el clasificador y más seguridad para producción.
4. **La frase de alcance, otra vez:**

    > "El sistema informa, proyecta y alerta. La decisión y el asesoramiento siguen siendo del usuario y de su contador."

5. "Muchas gracias. Quedo a disposición para las preguntas."

Del 32:00 al 35:00 es colchón. Si sobra tiempo, **no lo llenes**.

## Los módulos que no abrís en vivo

No están en el recorrido para que la demo entre en el tiempo, pero son parte de la app. Si el jurado pregunta, con la frase de la segunda columna alcanza.

| Módulo | Qué hace, en una frase | Si te preguntan |
|---|---|---|
| Registro | Crea la cuenta con correo y contraseña. La contraseña se guarda como hash, nunca tal cual. | "Dos personas con la misma contraseña quedan con hashes distintos: cada una lleva su propia sal, un condimento al azar." |
| Ingresos | Guarda cada cobro con fecha, monto y cliente, y lo muestra mes por mes. Se carga a mano o con el extracto. | *¿Cómo detecta un cobro repetido?* → "Solo si coinciden día, monto y descripción. Es estricto a propósito: un cliente que paga cuotas iguales no es un error." |
| Gastos | Guarda cada gasto con una de 12 categorías, mes por mes. A mano, el sistema te sugiere la categoría; con el extracto, la pone solo. Tiene el filtro "Solo duplicados". | *¿Y si la categoría quedó mal?* → "Se corrige en el Clasificador y el sistema aprende de esa corrección." |
| Clasificador (pantalla) | Escribís una descripción y te dice la categoría más probable y qué tan seguro está. Ahí se corrige y el modelo aprende. | Es la pantalla de las capturas que mostraste en las filminas. Después de importar dice 78 %: es el modelo propio de la usuaria. |
| Estado del modelo (el recuadro de arriba del Clasificador; no tiene entrada propia en el menú) | Muestra qué modelo usa el usuario (el de base o el propio), con cuántos ejemplos aprendió y cuánto acierta. | "Todos arrancan con el modelo de base, de 600 ejemplos. Cuando cargaron 20 gastos, el sistema les entrena uno propio: los 600 más los suyos." |
| Resumen IA | Escribe en castellano cómo te fue en el mes, en un párrafo. Es el único lugar con IA de afuera. | "Recibe solo totales. Si no hay internet, usa una plantilla local y lo dice con la etiqueta 'Sin IA'." |

**Las 12 categorías**, por si te las piden: Software, Hardware, Infraestructura, Marketing, Servicios, Capacitación, Suscripciones, Transporte, Alimentación, Impuestos, Monotributo y Otros.

## Machete: una línea por módulo

Para el repaso final y para tener a mano el día de la defensa. Si te acordás de esta tabla, podés contar la app entera.

| Módulo | Palabras clave | La frase gancho |
|---|---|---|
| Entrar | hash · una sola dirección · sal por usuario · pase firmado | "La base no guarda tu contraseña, guarda su hash." |
| Importar CSV | rechaza lo que no es extracto · vista previa · seis casos | "Antes de guardar, te muestra qué va a hacer con cada movimiento." |
| Dashboard | foto del mes · mes actual · Grupo Delta · aviso en el producto | "El mes de un vistazo." |
| Clasificador | aprende de ejemplos · planilla de puntos · por cuánto ganó · si duda, Otros | "Mejor una revisión que una categoría equivocada." |
| Auditoría | revisa por vos · cinco controles · avisa, no corrige | "Revisa lo que nadie revisa." |
| Facturas | a mano · amarilla, roja, verde · vence sola | "Lo que te deben y desde cuándo." |
| Gasto irregular | su propia categoría · la vara se ajusta · boleta de luz | "Una señal para revisar, no una acusación." |
| Monotributo | semáforo · cobrado + lo que viene · cuándo | "No dice 'te pasaste': dice cuándo te pasarías." |
| Proyecciones | rango, no número · la línea, no el promedio · mil futuros · 1 de cada 10 | "Como el pronóstico del tiempo." |
| Recomendaciones | reglas, no IA · su porqué · sugiere, no ordena | "Cada una te dice de dónde sale." |
| Reporte PDF | resumen del mes cerrado · lo único que sale | "Por eso lleva el aviso adentro." |
| Ingresos | cada cobro · mes por mes | "Lo que entró, ordenado." |
| Gastos | 12 categorías · solo duplicados | "Lo que salió, ya clasificado." |
| Resumen IA | solo totales · única IA de afuera · plantilla sin internet | "Te cuenta el mes en castellano." |

Y la que va arriba de todas: **informa, proyecta y alerta. No asesora.**

## En las preguntas: las cuatro terminales

Si piden ver algo en vivo, no hay que escribir nada: las cuatro terminales quedan abiertas, escalonadas, cada una con su título arriba y **su comando ya escrito en la línea**. Hacés clic en la ventana y apretás **Enter**. Para repetirlo: flecha arriba y Enter. Ninguna cambia los datos de la demo.

Se abren con un solo comando, desde la carpeta del proyecto y con Docker prendido:

```bash
sh defensa_final/demo/terminales/abrir_terminales.sh
```

| Terminal | Cuándo | Filmina | Tarda |
|---|---|---|---|
| **1 · La contraseña en la base** | "¿Cómo se guarda la contraseña?" | 29 | un segundo |
| **2 · Las cinco vueltas** | "¿Cómo se midió el 76 %?" | 36 | unos segundos |
| **3 · Las pruebas de seguridad** | "¿Cómo lo probaste?", si vas justo de tiempo | 37 | unos segundos |
| **4 · Todas las pruebas automáticas** | "¿Cómo lo probaste?" | 37 | unos dos minutos |

Los comandos también están en las filminas, para copiarlos si hiciera falta.

#### Las pruebas automáticas (anexo, filmina 37)

**Qué es:** pequeños programas que usan el sistema como lo usaría una persona y revisan el resultado. En la tesis es la HU-16 ("Suite automatizada de pruebas").

**DECÍ** (mientras corre la terminal 4, que tarda unos dos minutos):

> "Además de probarlo a mano, el sistema tiene pruebas automáticas: pequeños programas que lo usan como lo usaría una persona y revisan el resultado. Por ejemplo, uno entra con una contraseña equivocada y comprueba que no lo deje pasar; otro importa dos extractos que se pisan y comprueba que no guarde dos veces lo repetido. Cada línea es un módulo: auditoría, autenticación, estado fiscal, facturas, gastos, importación… Y cada punto es una prueba que pasó. Corren sobre una base aparte, en memoria, que se crea y se borra en cada prueba: no tocan los datos de la demo. Si una falla, dice el archivo y el nombre del caso. Así, cada vez que cambiaba algo, comprobaba que no se rompiera lo que ya andaba."

Al final tiene que decir **447 passed** en verde (medido el 12/10: 2 minutos 16 segundos).

**Si vas justo de tiempo**, la terminal 3: corre solo las de seguridad, en segundos, y muestra el nombre de cada caso. Cómo leerlos, en criollo:

| Lo que dice la terminal | Qué prueba |
|---|---|
| `register_exitoso` · `email_duplicado` | registrarse bien · un correo ya usado no se acepta |
| `login_password_incorrecto` | con la contraseña equivocada no entra |
| `ruta_privada_sin_token` · `token_manipulado` | sin iniciar sesión, o con un pase adulterado, no entra a ninguna pantalla |
| `aislamiento_entre_usuarios` | nadie ve lo de otro |
| `clave_de_firma_insegura_frena_el_arranque` | si la clave del servidor es débil, el sistema no arranca |
| `login_con_correo_inexistente_tambien_verifica_la_contrasena` | un correo que no existe tarda lo mismo: no se puede averiguar quién está registrado |

Palabras clave: **programas que prueban el sistema** · **cada punto, una prueba** · **base aparte** · **si falla, dice cuál**.

**Si te preguntan:**

- *¿Qué es ese "-p no:warnings"?* → "Apaga los avisos de algunas bibliotecas que anuncian cambios en versiones futuras. No son fallas; los apago para que se lea el resultado."
- *¿Y las pantallas?* → "Tienen sus propias pruebas, aparte: dieciséis."

## Si algo falla en vivo

La regla de oro: **nunca te quedes en silencio tocando la app.** Mientras arreglás, seguí hablando de lo que debería verse.

1. **Recargá la página** (Cmd + R). Resuelve casi todo.
2. Si no vuelve, **pasá al plan B**: al final del deck están las capturas de cada tramo (importación, auditoría, monotributo, proyecciones, recomendaciones y el PDF). Decí:

    > "Tengo un problema de entorno. Les muestro la misma pantalla en captura, y si da el tiempo vuelvo al final."

3. **Si no hay internet:** todo anda igual, porque la app corre en la computadora. Solo el Resumen usa la plantilla local, y no está en el recorrido.
4. **Si tocaste un botón de más** (por ejemplo, resolviste una alerta o marcaste una factura pagada): no lo arregles en vivo. Seguí, y si en Recomendaciones cambia un número, decí "recalcula con cada dato".

**Antes de entrar a la sala**, el checklist de siempre: Docker corriendo, datos sembrados, el navegador en el inicio de sesión sin entrar, las notificaciones en silencio y, en Escritorio → Defensa_FreelanceControl → 4_Demo, los tres archivos: `extracto_28sep_14oct.csv`, `resumen_banco.pdf` y `planilla_vacia.xlsx`. Abrí además las cuatro terminales (`sh defensa_final/demo/terminales/abrir_terminales.sh`): cada una queda con su comando escrito, por si en las preguntas piden ver algo en vivo. **No borres la cuenta del tribunal**: su hash está en la primera filmina del anexo.
