"""Formato de moneda argentina, compartido entre servicios.

Centralizado acá para que las descripciones de alertas (auditoria) y las
tablas del reporte PDF (reportes_service) usen exactamente la misma
convención: separador de miles con punto, decimales con coma.
"""


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
