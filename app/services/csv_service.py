"""
Procesamiento de archivos de homebanking (CSV y Excel).

El módulo se llama csv_service por razones históricas. En la práctica acepta
también archivos .xlsx, ya que los bancos argentinos (Galicia, Santander,
BBVA, Macro, Nación, Brubank, ICBC, Mercado Pago, Naranja X) exportan en
ambos formatos según el plan o canal del usuario. La detección de columnas
se hace una sola vez sobre un DataFrame de pandas, sin importar de qué
formato vino el archivo.

Política de soberanía de datos del TFG: la detección del formato del archivo
se realiza íntegramente con heurísticas locales basadas en un diccionario de
sinónimos relevados sobre los bancos arriba mencionados. En ningún caso se
transmite el contenido del archivo a servicios externos.
"""

import io
import logging
import re
import unicodedata
from collections import defaultdict
from datetime import datetime, time

import pandas as pd
from sqlalchemy.orm import Session

from app.models.ingreso import Ingreso
from app.models.gasto import Gasto
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


# ── Lectura de archivos ──────────────────────────────────────────────────────
# Centralizamos acá la decisión de qué motor de pandas usar según la extensión.
# Si después agregamos otro formato (ej: .ods) basta con sumar un branch.

def leer_dataframe(contenido_bytes: bytes, extension: str) -> pd.DataFrame | None:
    """Devuelve un DataFrame leído desde el contenido bruto del archivo.

    Acepta extensiones .csv y .xlsx. La extensión se compara en minúsculas
    con punto incluido. Si pandas no puede interpretar el contenido, devuelve
    None y el llamador decide cómo reportarlo al usuario.
    """
    extension = (extension or "").lower()
    try:
        if extension == ".csv":
            # Algunos bancos exportan en latin-1; intentamos utf-8 primero
            # y caemos a latin-1 si falla la decodificación.
            try:
                texto = contenido_bytes.decode("utf-8")
            except UnicodeDecodeError:
                texto = contenido_bytes.decode("latin-1")
            # sep=None + engine='python' auto-detecta coma, punto-coma y tabulación.
            # Cubre Galicia (;), Brubank (\t), y extractos genéricos (,).
            return pd.read_csv(io.StringIO(texto), sep=None, engine="python")
        if extension == ".xlsx":
            # openpyxl es la dependencia que pandas usa por debajo para .xlsx.
            return pd.read_excel(io.BytesIO(contenido_bytes), engine="openpyxl")
    except Exception as e:
        logger.error(f"Error leyendo archivo ({extension}): {e}")
        return None

    logger.warning(f"Extensión no soportada en leer_dataframe: {extension}")
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


def detectar_columnas_csv(df: pd.DataFrame, db: Session = None) -> dict | None:
    """Detecta la estructura del archivo mediante heurísticas locales.

    Recibe un DataFrame ya parseado (por leer_dataframe). El nombre conserva
    el sufijo csv por compatibilidad histórica, pero opera igual sobre Excel.
    Devuelve None si no logra identificar las columnas mínimas (fecha y
    descripción), para que el endpoint pueda informar el problema al usuario.
    """
    if df is None or df.empty or df.shape[1] == 0:
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


def procesar_csv(df: pd.DataFrame, mapeo: dict) -> list[dict]:
    """Convierte cada fila del DataFrame en un movimiento normalizado.

    Recibe el DataFrame ya leído (por leer_dataframe) más el mapeo de columnas
    detectado por detectar_columnas_csv. La salida es una lista de dicts con
    las claves fecha, descripción, monto y tipo, lista para clasificar.
    """
    if df is None or df.empty:
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
        # El clasificador está entrenado con categorías de GASTO (Software,
        # Suscripciones, Transporte...). Aplicárselo a un ingreso le asignaría
        # una categoría que no existe en el módulo de ingresos y rompería sus
        # filtros, así que los ingresos entran como "Otros" y el usuario los
        # recategoriza si quiere.
        if mov.get("tipo") != "gasto":
            resultado.append({**mov, "categoria": "Otros"})
            continue
        try:
            clasificacion = clasificar_gasto(mov["descripcion"], db, usuario_id)
            categoria = clasificacion.get("categoria_sugerida", "Otros")
        except Exception:
            categoria = "Otros"
        resultado.append({**mov, "categoria": categoria})
    return resultado


# ── Detección de duplicados por conteo de instancias ─────────────────────────
# El problema: si comparamos solo "existe ya un movimiento igual en BD", falla
# en casos legítimos como "dos cafés del mismo día" — el segundo café se
# marcaría como duplicado del primero.
#
# La estrategia es comparar la CANTIDAD de instancias por clave (fecha+monto+
# descripción+tipo) que vienen en el CSV contra las que ya están persistidas:
#
#   csv_count == 0  → no hay nada que comparar
#   csv_count <= bd_count  → todas las del CSV ya están cubiertas → marcar todas
#   csv_count >  bd_count  → marcar las primeras bd_count, dejar el resto pasar
#
# Esto distingue correctamente entre re-importar el mismo archivo (mismas
# cantidades en CSV y BD) y agregar nuevas instancias legítimas (CSV trae más
# que BD).


def _normalizar_descripcion(desc: str) -> str:
    """Limpia la descripción para comparar: minúsculas, sin tildes, sin espacios extra."""
    if not desc:
        return ""
    nfkd = unicodedata.normalize("NFKD", desc)
    sin_tildes = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sin_tildes.lower().strip())


def _clave_movimiento(mov: dict) -> tuple:
    """Tupla canónica para agrupar movimientos equivalentes.

    No usamos hash criptográfico porque la clave nunca sale del proceso —
    la usamos como llave de diccionario y nada más. Una tupla hashable alcanza.
    """
    fecha_str = mov.get("fecha", "")
    try:
        fecha_obj = datetime.fromisoformat(fecha_str).date()
    except (ValueError, TypeError):
        # Fechas inválidas no se pueden agrupar; las tratamos como únicas
        # para no marcarlas erróneamente como duplicado.
        fecha_obj = None
    monto = round(float(mov.get("monto", 0)), 2)
    desc = _normalizar_descripcion(mov.get("descripcion", ""))
    tipo = mov.get("tipo", "")
    return (fecha_obj, monto, desc, tipo)


def _contar_instancias_en_bd(
    db: Session,
    usuario_id: int,
    fecha_obj,
    monto: float,
    desc_norm: str,
    tipo: str,
) -> int:
    """Cuenta movimientos del usuario en BD que matchean la clave del CSV.

    La descripción tiene que compararse normalizada, pero la BD guarda el
    texto original. Por eso traemos los candidatos por fecha+monto y
    filtramos en Python con la misma normalización que aplicamos al CSV.
    Para el rango de fechas usamos el día completo (00:00 a 23:59:59) porque
    distintos exports pueden traer la hora con valores diferentes.
    """
    if fecha_obj is None:
        return 0

    Modelo = Ingreso if tipo == "ingreso" else Gasto

    inicio = datetime.combine(fecha_obj, time.min)
    fin = datetime.combine(fecha_obj, time.max)

    candidatos = db.query(Modelo).filter(
        Modelo.usuario_id == usuario_id,
        Modelo.monto == monto,
        Modelo.fecha >= inicio,
        Modelo.fecha <= fin,
    ).all()

    return sum(
        1 for m in candidatos
        if _normalizar_descripcion(m.descripcion) == desc_norm
    )


def detectar_posibles_duplicados(
    db: Session,
    usuario_id: int,
    movimientos: list[dict],
) -> list[dict]:
    """Marca cada movimiento con la flag posible_duplicado: bool.

    El criterio se documenta arriba en este mismo archivo. La función no
    decide nada ni omite filas — solo agrega información para que el cliente
    (frontend o el endpoint /confirmar) sepa qué desactivar por defecto.
    """
    if not movimientos:
        return []

    # Agrupamos los índices del CSV por clave canónica.
    grupos = defaultdict(list)
    for idx, mov in enumerate(movimientos):
        clave = _clave_movimiento(mov)
        grupos[clave].append(idx)

    # Arrancamos con la flag en False para todos.
    resultado = [{**mov, "posible_duplicado": False} for mov in movimientos]

    # Cache local para no preguntarle a la BD lo mismo dos veces si hay
    # varias claves que cuentan la misma fecha+monto+desc.
    cache_bd: dict[tuple, int] = {}

    for clave, indices in grupos.items():
        if clave in cache_bd:
            bd_count = cache_bd[clave]
        else:
            fecha_obj, monto, desc_norm, tipo = clave
            bd_count = _contar_instancias_en_bd(
                db, usuario_id, fecha_obj, monto, desc_norm, tipo,
            )
            cache_bd[clave] = bd_count

        # Solo marcamos las primeras bd_count instancias del CSV. Si el CSV
        # trae más que las que ya hay en BD, las "extras" quedan como nuevas.
        n_marcar = min(len(indices), bd_count)
        for i in indices[:n_marcar]:
            resultado[i]["posible_duplicado"] = True

    return resultado


def filtrar_no_duplicados(
    db: Session,
    usuario_id: int,
    movimientos: list[dict],
) -> tuple[list[dict], int]:
    """Devuelve (movimientos_a_importar, omitidos_por_duplicado).

    Pensada para el endpoint /confirmar: aplica la misma detección que /preview
    como red de seguridad y descarta los duplicados antes de persistir.
    """
    marcados = detectar_posibles_duplicados(db, usuario_id, movimientos)
    a_importar = [m for m in marcados if not m.get("posible_duplicado")]
    omitidos = len(marcados) - len(a_importar)
    return a_importar, omitidos
