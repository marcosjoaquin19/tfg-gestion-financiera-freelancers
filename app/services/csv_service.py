"""
Procesamiento de archivos CSV de homebanking.

Política de soberanía de datos del TFG: la detección del formato del archivo
se realiza íntegramente con heurísticas locales basadas en un diccionario de
sinónimos relevados sobre bancos y billeteras argentinas (Galicia, Santander,
BBVA, Macro, Nación, Brubank, ICBC, Mercado Pago, Naranja X). En ningún caso
se transmite el contenido del archivo a servicios externos.
"""

import io
import logging
import re
import unicodedata
import pandas as pd
from sqlalchemy.orm import Session
from app.services.ia_service import clasificar_gasto

logger = logging.getLogger(__name__)


# ── Diccionario de sinónimos de columnas (homebanking argentino) ─────────────
# Cada lista contiene fragmentos esperables en los encabezados. Se compara
# contra el nombre de columna normalizado (sin tildes, minúsculas, alfanumérico).

SINONIMOS_FECHA = [
    "fecha", "fechamov", "fechamovimiento", "fechaoperacion", "fechavalor",
    "fmov", "fechadeoperacion", "fechaoperac", "fechacontabilizacion",
]
SINONIMOS_DESCRIPCION = [
    "concepto", "descripcion", "detalle", "movimiento", "referencia",
    "comprobante", "operacion", "descripciondelmovimiento", "descripcionoperacion",
    "tipodemovimiento",
]
SINONIMOS_DEBITO = [
    "debito", "debitos", "egreso", "egresos", "salida", "importedebito",
    "debe", "debitoars", "debitopesos",
]
SINONIMOS_CREDITO = [
    "credito", "creditos", "ingreso", "ingresos", "entrada", "importecredito",
    "haber", "creditoars", "creditopesos",
]
SINONIMOS_MONTO = [
    "importe", "monto", "valor", "montoars", "importeoperacion",
    "importepesos", "montototal", "importetotal",
]


def _normalizar(texto: str) -> str:
    """Normaliza un nombre de columna: minúsculas, sin tildes, solo alfanuméricos."""
    if texto is None:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(texto))
    sin_tildes = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", sin_tildes.lower())


def _buscar_columna(columnas_norm: dict[str, str], sinonimos: list[str]) -> str | None:
    """Devuelve el nombre original de la columna que matchee algún sinónimo.

    columnas_norm: dict {nombre_normalizado: nombre_original}
    Estrategia: primero match exacto, luego match por contains (más permisivo).
    """
    for sin in sinonimos:
        if sin in columnas_norm:
            return columnas_norm[sin]
    for nombre_norm, nombre_orig in columnas_norm.items():
        for sin in sinonimos:
            if sin in nombre_norm:
                return nombre_orig
    return None


def _detectar_formato_fecha(serie: pd.Series) -> str:
    """Intenta inferir el formato de fecha probando los más comunes en Argentina."""
    formatos = [
        "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%Y/%m/%d",
        "%d/%m/%y", "%d-%m-%y",
    ]
    muestras = serie.dropna().astype(str).head(5).tolist()
    if not muestras:
        return "%d/%m/%Y"

    for fmt in formatos:
        try:
            pd.to_datetime(muestras, format=fmt)
            return fmt
        except (ValueError, TypeError):
            continue
    return "%d/%m/%Y"


def detectar_columnas_csv(contenido_csv: str, db: Session = None) -> dict | None:
    """Detecta la estructura del CSV mediante heurísticas locales.

    Devuelve un mapeo con la misma forma que la versión anterior basada en LLM,
    para mantener compatibilidad con procesar_csv() y el resto del flujo.
    """
    try:
        df = pd.read_csv(io.StringIO(contenido_csv), nrows=5)
    except Exception as e:
        logger.error(f"Error leyendo CSV para detección: {e}")
        return None

    if df.empty or df.shape[1] == 0:
        return None

    columnas_norm = {_normalizar(c): c for c in df.columns}

    col_fecha = _buscar_columna(columnas_norm, SINONIMOS_FECHA)
    col_desc = _buscar_columna(columnas_norm, SINONIMOS_DESCRIPCION)
    col_debito = _buscar_columna(columnas_norm, SINONIMOS_DEBITO)
    col_credito = _buscar_columna(columnas_norm, SINONIMOS_CREDITO)
    col_monto = _buscar_columna(columnas_norm, SINONIMOS_MONTO)

    if col_fecha is None or col_desc is None:
        return None

    # Si hay débito y crédito, ignoramos columna de monto único para evitar
    # sumar dos veces. Si solo hay monto único, lo usamos.
    if col_debito and col_credito:
        col_monto = None
    elif col_monto is None and not (col_debito and col_credito):
        return None

    formato_fecha = _detectar_formato_fecha(df[col_fecha])

    return {
        "columna_fecha": col_fecha,
        "columna_descripcion": col_desc,
        "columna_monto": col_monto,
        "columna_debito": col_debito,
        "columna_credito": col_credito,
        "columna_tipo": None,
        "formato_fecha": formato_fecha,
    }


def procesar_csv(contenido_csv: str, mapeo: dict) -> list[dict]:
    try:
        df = pd.read_csv(io.StringIO(contenido_csv))
    except Exception as e:
        logger.error(f"Error leyendo CSV para procesar: {e}")
        return []

    col_fecha = mapeo.get("columna_fecha")
    col_desc = mapeo.get("columna_descripcion")
    col_monto = mapeo.get("columna_monto")
    col_debito = mapeo.get("columna_debito")
    col_credito = mapeo.get("columna_credito")
    fmt_fecha = mapeo.get("formato_fecha", "%d/%m/%Y")

    movimientos = []

    for _, row in df.iterrows():
        try:
            fecha_raw = row.get(col_fecha) if col_fecha else None
            if fecha_raw is None or (isinstance(fecha_raw, float) and pd.isna(fecha_raw)):
                continue
            try:
                fecha = pd.to_datetime(str(fecha_raw), format=fmt_fecha)
            except (ValueError, TypeError):
                fecha = pd.to_datetime(str(fecha_raw), errors="coerce")
                if pd.isna(fecha):
                    continue

            descripcion = str(row.get(col_desc, "Sin descripción")).strip()

            if col_debito and col_credito:
                debito = _parse_monto(row.get(col_debito, 0))
                credito = _parse_monto(row.get(col_credito, 0))
                if credito and credito > 0:
                    monto, tipo = credito, "ingreso"
                elif debito and debito > 0:
                    monto, tipo = debito, "gasto"
                else:
                    continue
            elif col_monto:
                monto_val = _parse_monto(row.get(col_monto, 0))
                if not monto_val or monto_val == 0:
                    continue
                if monto_val > 0:
                    monto, tipo = monto_val, "ingreso"
                else:
                    monto, tipo = abs(monto_val), "gasto"
            else:
                continue

            movimientos.append({
                "fecha": fecha.strftime("%Y-%m-%dT00:00:00"),
                "descripcion": descripcion,
                "monto": round(float(monto), 2),
                "tipo": tipo,
            })

        except Exception as e:
            logger.warning(f"Fila ignorada por error: {e}")
            continue

    return movimientos


def _parse_monto(valor) -> float | None:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return None
    try:
        # Formato argentino: "1.234,56" → 1234.56
        s = str(valor).strip().replace("$", "").replace(" ", "")
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".")
        elif "," in s:
            s = s.replace(",", ".")
        return float(s)
    except (ValueError, TypeError):
        return None


def clasificar_movimientos(movimientos: list, db: Session, usuario_id: int = 0) -> list:
    """Clasifica cada movimiento usando exclusivamente el ML local.

    La descripción del movimiento permanece dentro de la infraestructura del
    sistema y nunca se transmite a terceros.
    """
    resultado = []
    for mov in movimientos:
        try:
            clasificacion = clasificar_gasto(mov["descripcion"], db, usuario_id)
            categoria = clasificacion.get("categoria_sugerida", "Otros")
        except Exception:
            categoria = "Otros"
        resultado.append({**mov, "categoria": categoria})
    return resultado
