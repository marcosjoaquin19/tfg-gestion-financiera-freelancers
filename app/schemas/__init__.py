"""
Paquete de schemas (Pydantic).

Define los modelos de entrada y salida de la API: validan los datos que llegan
en cada request y dan forma al JSON que se devuelve. Separan la capa HTTP de los
modelos de base de datos (app.models).

Cómo leer un schema:
  - Cada atributo de la clase es un campo con su tipo (str, float, datetime):
    si llega un texto donde va un número, Pydantic lo rechaza solo.
  - Field(max_length=200) agrega límites al campo.
  - @field_validator("campo") es una función que revisa UN campo: si algo está
    mal lanza ValueError con el mensaje que ve el usuario; si está bien,
    devuelve el valor (a veces limpio, por ejemplo sin espacios en los bordes).
  - @model_validator(mode="after") revisa varios campos juntos, ya validados
    uno por uno (por ejemplo, que el vencimiento no sea anterior a la emisión).
  - Los "...Response" definen qué se devuelve: lo que no está en el molde
    (como el hash de la contraseña) nunca sale de la API.
Si alguna validación falla, la API responde 422 con el mensaje en castellano.
"""
