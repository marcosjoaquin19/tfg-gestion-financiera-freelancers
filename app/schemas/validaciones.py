"""
Validaciones compartidas por los esquemas de entrada: montos y fechas.

Las usan la carga manual y la edición de ingresos, gastos y facturas, y la
confirmación de una importación. Tenerlas en un solo lugar evita que una vía
acepte lo que otra rechaza.
"""

from datetime import datetime

MONTO_MINIMO = 0.01
MONTO_MAXIMO = 10 ** 10

# Mismo rango de años que aceptan los filtros por mes de los listados: una
# fecha fuera de él (un año 0026 o 1026 por un error de tipeo) se guardaba
# pero después no se podía filtrar, y estiraba la serie de la proyección con
# siglos de meses en $0.
ANIO_MINIMO = 2000
ANIO_MAXIMO = 2100


def validar_monto(v: float) -> float:
    if v <= 0:
        raise ValueError("El monto debe ser mayor a cero")
    if v < MONTO_MINIMO:
        # Los montos se guardan con dos decimales: $ 0,001 terminaba en $ 0,00.
        raise ValueError("El monto mínimo es $ 0,01")
    if v >= MONTO_MAXIMO:
        raise ValueError("El monto supera el máximo admitido (10.000.000.000)")
    return v


def fecha_en_rango(fecha: datetime) -> bool:
    return ANIO_MINIMO <= fecha.year <= ANIO_MAXIMO


def validar_fecha(v: datetime) -> datetime:
    if not fecha_en_rango(v):
        raise ValueError(f"La fecha tiene que estar entre los años {ANIO_MINIMO} y {ANIO_MAXIMO}")
    return v
