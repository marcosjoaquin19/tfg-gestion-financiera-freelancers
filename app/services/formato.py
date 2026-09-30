"""Formato de moneda y de fechas en argentino, compartido entre servicios.

Centralizado acá para que las descripciones de alertas (auditoria) y las
tablas del reporte PDF (reportes_service) usen exactamente la misma
convención: separador de miles con punto, decimales con coma.
"""

# PATRÓN: Single Source of Truth — un único formateador de moneda para toda la app.
# Justificación y alternativas descartadas: docs/ARQUITECTURA_Y_PATRONES.md


def formato_pesos_ar(valor, decimales: int = 2) -> str:
    """Formatea un número como pesos argentinos.

    ej: 1234567.89 → "$ 1.234.567,89"   (decimales=2)
        56502      → "$ 56.502"         (decimales=0)
    """
    if valor is None:
        return "-"
    n = float(valor)
    # Python usa coma para miles y punto para decimales (formato US);
    # invertimos ambos para obtener el formato argentino.
    s = f"{n:,.{decimales}f}"
    if decimales > 0:
        entero, dec = s.split(".")
        return f"$ {entero.replace(',', '.')},{dec}"
    return f"$ {s.replace(',', '.')}"


def formato_fecha_ar(fecha) -> str:
    """Fecha como la lee el usuario: 29/09/2026 (no 2026-09-29).

    Las fechas se guardan como día calendario a las 00:00 UTC, así que el día
    que se muestra es el de la fecha guardada, sin convertir de zona.
    """
    return fecha.strftime("%d/%m/%Y")
