"""
Inserta (o actualiza) las 11 categorías de monotributo (PRESTACIÓN DE SERVICIOS)
en la tabla `categorias_monotributo`. Ejecutar desde la raíz del proyecto:
    python seed_categorias_monotributo.py

Catálogo de escalas
-------------------
Cada escala publicada por ARCA se conserva acá como una constante fechada
(ESCALA_JUNIO_2026, ESCALA_AGOSTO_2026, ...). ESCALAS mapea fecha de vigencia →
valores, y ESCALA_VIGENTE selecciona la más reciente: para cargar una escala
nueva alcanza con agregar su constante al diccionario, sin tocar esta lógica ni
código de la aplicación.

LIMITACIÓN CONOCIDA — la tabla NO puede almacenar dos escalas a la vez: la
columna `letra` tiene un índice ÚNICO global (`ix_categorias_monotributo_letra`,
migración 0002), de modo que solo puede existir una fila por letra. El campo
`fecha_vigencia` documenta qué escala está cargada, pero ninguna consulta de la
app filtra por él (get_categoria/listar_categorias filtran solo por activa=True).
Por eso las escalas históricas se versionan en este archivo y la BD guarda
únicamente la vigente. Para versionarlas dentro de la tabla haría falta cambiar
el esquema (unique compuesto por letra+actividad+fecha_vigencia) y las consultas
de monotributo_service.

Fuentes: escala junio 2026 cruzada entre Ámbito y Estudio Brady; escala agosto
2026 (ajuste 16,8 % por IPC del 1er semestre, vigente desde el 1/8/2026) tomada
de la tabla de ARCA (arca.gob.ar/monotributo/categorias.asp) y cruzada con
Estudio Librán. NOTA: son datos impositivos que ARCA actualiza periódicamente
→ verificar contra arca.gob.ar antes de usar en producción/defensa.

También exporta seed_categorias(db) para reutilizar desde otros seeds
(p. ej. seed_demo.py) sin ejecutar nada al importar el módulo.
"""
from datetime import date
from app.database import SessionLocal
from app.models.categoria_monotributo import CategoriaMonotributo

# Escala anterior. Se conserva como referencia histórica del catálogo: la tabla
# solo puede alojar una escala por vez (ver LIMITACIÓN CONOCIDA arriba).
ESCALA_JUNIO_2026 = [
    {"letra": "A", "limite_anual": 10277988.13,  "cuota_mensual": 42386.74},
    {"letra": "B", "limite_anual": 15058447.71,  "cuota_mensual": 48250.78},
    {"letra": "C", "limite_anual": 21113696.52,  "cuota_mensual": 56501.85},
    {"letra": "D", "limite_anual": 26212853.42,  "cuota_mensual": 72414.10},
    {"letra": "E", "limite_anual": 30833964.37,  "cuota_mensual": 102537.97},
    {"letra": "F", "limite_anual": 38642048.36,  "cuota_mensual": 129045.32},
    {"letra": "G", "limite_anual": 46211109.37,  "cuota_mensual": 197108.23},
    {"letra": "H", "limite_anual": 70113407.33,  "cuota_mensual": 447346.93},
    {"letra": "I", "limite_anual": 78479211.62,  "cuota_mensual": 824802.26},
    {"letra": "J", "limite_anual": 89872640.30,  "cuota_mensual": 999007.65},
    {"letra": "K", "limite_anual": 108357084.05, "cuota_mensual": 1381687.90},
]

# Escala vigente desde el 1/8/2026 (ajuste del 16,8 % sobre la anterior).
# La cuota mensual es el total del régimen de servicios: impuesto integrado +
# aportes al SIPA + aporte a obra social.
ESCALA_AGOSTO_2026 = [
    {"letra": "A", "limite_anual": 12009410.45,  "cuota_mensual": 49527.18},
    {"letra": "B", "limite_anual": 17595182.74,  "cuota_mensual": 56379.08},
    {"letra": "C", "limite_anual": 24670494.31,  "cuota_mensual": 66020.12},
    {"letra": "D", "limite_anual": 30628651.43,  "cuota_mensual": 84612.93},
    {"letra": "E", "limite_anual": 36028231.33,  "cuota_mensual": 119811.45},
    {"letra": "F", "limite_anual": 45151659.41,  "cuota_mensual": 150784.21},
    {"letra": "G", "limite_anual": 53995798.87,  "cuota_mensual": 230312.94},
    {"letra": "H", "limite_anual": 81924660.37,  "cuota_mensual": 522706.68},
    {"letra": "I", "limite_anual": 91699761.90,  "cuota_mensual": 963747.86},
    {"letra": "J", "limite_anual": 105012519.20, "cuota_mensual": 1167299.76},
    {"letra": "K", "limite_anual": 126610838.75, "cuota_mensual": 1614446.04},
]

# Catálogo completo: fecha de vigencia → escala publicada para esa fecha.
ESCALAS = {
    date(2026, 6, 1): ESCALA_JUNIO_2026,
    date(2026, 8, 1): ESCALA_AGOSTO_2026,
}

# La escala que se carga en la BD es siempre la de vigencia más reciente.
FECHA_VIGENCIA = max(ESCALAS)
CATEGORIAS = ESCALAS[FECHA_VIGENCIA]


def seed_categorias(db=None):
    """Inserta o actualiza las 11 categorías. Idempotente.

    Si no se pasa una sesión, abre y cierra una propia. Si se pasa (desde otro
    seed que ya tiene sesión abierta), opera sobre ella y NO la cierra.
    """
    propia = db is None
    if propia:
        db = SessionLocal()
    try:
        insertadas = actualizadas = 0
        for datos in CATEGORIAS:
            existente = db.query(CategoriaMonotributo).filter(
                CategoriaMonotributo.letra == datos["letra"]
            ).first()
            if existente:
                existente.limite_anual = datos["limite_anual"]
                existente.cuota_mensual = datos["cuota_mensual"]
                existente.fecha_vigencia = FECHA_VIGENCIA
                existente.activa = True
                actualizadas += 1
            else:
                db.add(CategoriaMonotributo(
                    letra=datos["letra"],
                    limite_anual=datos["limite_anual"],
                    cuota_mensual=datos["cuota_mensual"],
                    actividad="servicios",
                    fecha_vigencia=FECHA_VIGENCIA,
                    activa=True,
                ))
                insertadas += 1
        db.commit()
        print(
            f"Categorías Monotributo (vigencia {FECHA_VIGENCIA.isoformat()}): "
            f"{insertadas} insertadas, {actualizadas} actualizadas."
        )
    finally:
        if propia:
            db.close()


if __name__ == "__main__":
    seed_categorias()
