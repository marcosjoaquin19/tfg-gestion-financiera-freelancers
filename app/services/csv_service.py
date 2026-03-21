import os
import json
import logging
import io
import pandas as pd
from groq import Groq
from sqlalchemy.orm import Session
from app.services.ia_service import clasificar_gasto

logger = logging.getLogger(__name__)

PROMPT_DETECCION = """Analizá este CSV de un banco argentino.
Identificá exactamente qué columna contiene:
- la fecha del movimiento
- la descripción o concepto
- el monto (puede estar en una o dos columnas: débito/crédito o una sola con signo)
- si hay columna de tipo (ingreso/egreso)

Respondé SOLO con JSON válido así:
{{
  "columna_fecha": "nombre_exacto_columna",
  "columna_descripcion": "nombre_exacto_columna",
  "columna_monto": "nombre_exacto_columna_o_null",
  "columna_debito": null,
  "columna_credito": null,
  "columna_tipo": null,
  "formato_fecha": "DD/MM/YYYY"
}}

Donde columna_monto es null si hay columnas separadas de débito/crédito, y columna_debito/columna_credito son null si hay una sola columna de monto.
Sin explicaciones, solo el JSON.

CSV:
{csv_muestra}"""


def detectar_columnas_csv(contenido_csv: str, db: Session) -> dict | None:
    try:
        df = pd.read_csv(io.StringIO(contenido_csv), nrows=5)

        # Privacidad y ahorro de tokens: enviamos a Groq solo las primeras 5 columnas.
        # CSVs bancarios suelen incluir CUIT, número de cuenta, nombre del titular y saldo,
        # datos que no aportan al mapeo de columnas pero exponen PII innecesariamente.
        # Limitamos a 5 columnas para reducir la superficie de exposición y el tamaño del prompt.
        if df.shape[1] > 5:
            df = df.iloc[:, :5]

        csv_muestra = df.to_csv(index=False)
    except Exception as e:
        logger.error(f"Error leyendo CSV para detección: {e}")
        return None

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None

    try:
        client = Groq(api_key=api_key)
        model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": PROMPT_DETECCION.format(csv_muestra=csv_muestra)}],
            max_tokens=300,
            temperature=0,
        )
        texto = response.choices[0].message.content.strip()

        # Extraer el JSON aunque venga envuelto en markdown
        if "```" in texto:
            texto = texto.split("```")[1]
            if texto.startswith("json"):
                texto = texto[4:]

        mapeo = json.loads(texto)
        return mapeo

    except Exception as e:
        logger.error(f"Error Groq detectar_columnas_csv: {e}")
        return None


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

    # Normalizar formato de fecha para pandas
    fmt_pandas = fmt_fecha.replace("DD", "%d").replace("MM", "%m").replace("YYYY", "%Y").replace("YY", "%y")

    movimientos = []

    for _, row in df.iterrows():
        try:
            # Fecha
            fecha_raw = row.get(col_fecha) if col_fecha else None
            if pd.isna(fecha_raw) if fecha_raw is not None else True:
                continue
            try:
                fecha = pd.to_datetime(str(fecha_raw), format=fmt_pandas)
            except Exception:
                fecha = pd.to_datetime(str(fecha_raw), infer_datetime_format=True)

            # Descripción
            descripcion = str(row.get(col_desc, "Sin descripción")).strip()

            # Monto y tipo
            if col_debito and col_credito:
                debito_raw  = row.get(col_debito, 0)
                credito_raw = row.get(col_credito, 0)
                debito  = _parse_monto(debito_raw)
                credito = _parse_monto(credito_raw)

                if credito and credito > 0:
                    monto = credito
                    tipo = "ingreso"
                elif debito and debito > 0:
                    monto = debito
                    tipo = "gasto"
                else:
                    continue
            elif col_monto:
                monto_raw = row.get(col_monto, 0)
                monto_val = _parse_monto(monto_raw)
                if not monto_val or monto_val == 0:
                    continue
                if monto_val > 0:
                    monto = monto_val
                    tipo = "ingreso"
                else:
                    monto = abs(monto_val)
                    tipo = "gasto"
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
        # Limpiar formato argentino: "1.234,56" → 1234.56
        s = str(valor).strip().replace("$", "").replace(" ", "")
        # Si tiene punto y coma, el punto es separador de miles
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".")
        elif "," in s:
            s = s.replace(",", ".")
        return float(s)
    except Exception:
        return None


def clasificar_movimientos(movimientos: list, db: Session) -> list:
    resultado = []
    for mov in movimientos:
        try:
            categoria = clasificar_gasto(mov["descripcion"], db)
        except Exception:
            categoria = "Otros"
        resultado.append({**mov, "categoria": categoria})
    return resultado
