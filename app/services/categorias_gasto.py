"""
Categorías válidas de gasto.

Única fuente de verdad del backend para clasificar un gasto. Son las 12 clases
que conoce el clasificador de ML (ml_service), las que valida la corrección
manual (/ml/corregir), las que usa el importador y las que acepta el alta y la
edición de gastos (schema GastoCreate).

Por qué una lista cerrada: además de los totales por categoría del Dashboard,
el resumen y el PDF, los gastos del usuario son los ejemplos con los que se
reentrena su modelo. Una categoría inventada ("Pizza") entraría al
entrenamiento como una clase número 13 y el clasificador empezaría a sugerirla.

La lista de la pantalla (frontend/src/pages/Gastos.js) es un espejo de esta:
si se agrega una categoría hay que tocar los dos lados y reentrenar el modelo
base con ejemplos de la nueva clase.
"""

CATEGORIAS_GASTO = [
    "Software", "Hardware", "Infraestructura", "Marketing", "Servicios",
    "Capacitación", "Suscripciones", "Transporte", "Alimentación",
    "Impuestos", "Monotributo", "Otros",
]
