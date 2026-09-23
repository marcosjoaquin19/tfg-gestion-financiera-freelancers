"""
Categorías válidas de ingreso.

Única fuente de verdad del backend para clasificar un ingreso. El schema
IngresoCreate valida contra esta lista, de modo que la API rechaza cualquier
categoría que no esté acá, venga de la pantalla o de una llamada directa.

Por qué una lista cerrada: los totales por categoría alimentan el Dashboard,
el resumen mensual y el reporte en PDF. Con texto libre, tres grafías de lo
mismo ("Desarrollo", "desarrollo", "Desarrolo") se cuentan como tres rubros
distintos y los totales dejan de cerrar.

La lista de la pantalla (frontend/src/pages/Ingresos.js) es un espejo de esta:
si se agrega una categoría hay que tocar los dos lados.

Nota: el clasificador de ML trabaja con categorías de GASTO, que son otras.
Un ingreso importado desde un extracto entra siempre como "Otros" y el
usuario lo recategoriza (ver csv_service.clasificar_movimientos).
"""

CATEGORIAS_INGRESO = [
    "Desarrollo",
    "Desarrollo Web",
    "Desarrollo Mobile",
    "Diseño",
    "Consultoría",
    "Marketing Digital",
    "Redacción y Contenido",
    "Soporte y Mantenimiento",
    "Capacitación",
    "Servicios",
    "Otros",
]

# Categorías de versiones anteriores del prototipo que quedaron en datos ya
# cargados. La migración 0009 las reescribe a su equivalente de la lista para
# que esos registros sigan siendo editables.
EQUIVALENCIAS_HISTORICAS = {
    "Software": "Desarrollo",
    "Mantenimiento": "Soporte y Mantenimiento",
    "Soporte": "Soporte y Mantenimiento",
    "Infraestructura": "Servicios",
}
