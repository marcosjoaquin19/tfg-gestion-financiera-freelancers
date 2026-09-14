"""
Paquete de services (lógica de negocio).

Concentra la lógica que no corresponde a los routers: autenticación, auditoría,
clasificador de ML, proyecciones (Prophet), cálculos de monotributo, generación
de reportes, integración con IA e importación de CSV. Los routers la invocan.
"""

# PATRÓN: Facade — los routers hablan con estos servicios, nunca con la lógica interna.
# PATRÓN: Separación de responsabilidades — la regla de negocio vive acá, no en el router.
# Justificación y alternativas descartadas: docs/ARQUITECTURA_Y_PATRONES.md
