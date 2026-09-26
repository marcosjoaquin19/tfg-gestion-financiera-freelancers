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

# PATRÓN: Adapter / Capa anticorrupción — traduce 9 formatos de homebanking a un movimiento interno único.
# PATRÓN: Diccionario de sinónimos como tabla de mapeo: agregar un banco no toca la lógica.
# Justificación y alternativas descartadas: docs/ARQUITECTURA_Y_PATRONES.md

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

logger = logging.getLogger(__name__)


# ── Diccionario de sinónimos de columnas (homebanking argentino) ─────────────
# Cada lista contiene fragmentos esperables en los encabezados. Se compara
# contra el nombre de columna normalizado (sin tildes, minúsculas, alfanumérico).

SINONIMOS_FECHA = [
    "fecha", "fechamov", "fechamovimiento", "fechaoperacion", "fechavalor",
    "fmov", "fechadeoperacion", "fechaoperac", "fechacontabilizacion",
]
SINONIMOS_DESCRIPCION = [
    "concepto", "descripcion", "detalle", "descripciondelmovimiento",
    "descripcionoperacion", "movimiento",
]
# Nombres que A VECES traen la descripción, pero que en muchos extractos son
# un número de comprobante o un código. Solo se usan si no hay ninguna
# columna de descripción propiamente dicha: con "Comprobante" y "Descripción
# de la operación" en el mismo archivo, antes ganaba el comprobante y cada
# gasto se llamaba "000123".
SINONIMOS_DESCRIPCION_DEBILES = [
    "referencia", "comprobante", "operacion", "tipodemovimiento",
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


def _buscar_columna(
    columnas_norm: dict[str, str], sinonimos: list[str], usadas: set | None = None,
) -> str | None:
    """Devuelve el nombre original de la columna que matchee algún sinónimo.

    columnas_norm: dict {nombre_normalizado: nombre_original}
    usadas: columnas ya asignadas a otro campo, que no se vuelven a considerar.
    Sin esto, "Fecha Movimiento" contiene "movimiento" y la misma columna
    terminaba siendo a la vez la fecha y la descripción.
    Estrategia: primero match exacto, luego match por contains (más permisivo).
    """
    usadas = usadas or set()
    candidatas = {n: o for n, o in columnas_norm.items() if o not in usadas}
    for sin in sinonimos:
        if sin in candidatas:
            return candidatas[sin]
    for nombre_norm, nombre_orig in candidatas.items():
        for sin in sinonimos:
            if sin in nombre_norm:
                return nombre_orig
    return None


# ── Lectura de archivos ──────────────────────────────────────────────────────
# Centralizamos acá la decisión de qué motor de pandas usar según la extensión.
# Si después agregamos otro formato (ej: .ods) basta con sumar un branch.

# Cuántas filas de cabecera inspeccionamos como mucho buscando el encabezado
# real. Los preámbulos de homebanking rara vez pasan de unas pocas líneas;
# 30 deja margen de sobra sin recorrer archivos enteros.
MAX_FILAS_PREAMBULO = 30


def _fila_es_encabezado(tokens: list) -> bool:
    """Indica si una fila parece el encabezado real de la tabla de movimientos.

    Criterio: contiene una columna de fecha y al menos una de descripción,
    monto, débito o crédito. Reutiliza los mismos diccionarios de sinónimos
    que la detección de columnas, así que es consistente con ella.
    """
    normalizados = [_normalizar(t) for t in tokens]
    tiene_fecha = any(
        any(sin in norm for sin in SINONIMOS_FECHA) for norm in normalizados
    )
    otros = (SINONIMOS_DESCRIPCION + SINONIMOS_DESCRIPCION_DEBILES
             + SINONIMOS_MONTO + SINONIMOS_DEBITO + SINONIMOS_CREDITO)
    tiene_otro = any(
        any(sin in norm for sin in otros) for norm in normalizados
    )
    return tiene_fecha and tiene_otro


def leer_dataframe(contenido_bytes: bytes, extension: str) -> pd.DataFrame | None:
    """Devuelve un DataFrame leído desde el contenido bruto del archivo.

    Acepta extensiones .csv y .xlsx. La extensión se compara en minúsculas
    con punto incluido. Si pandas no puede interpretar el contenido, devuelve
    None y el llamador decide cómo reportarlo al usuario.

    Muchos exports reales (Galicia, Santander Río, BBVA, Macro, Nación)
    anteponen filas de metadata (titular, CBU, período) antes de la tabla.
    Antes de leer buscamos la fila que realmente parece el encabezado y
    descartamos lo de arriba; si no hay preámbulo, arrancamos en la fila 0
    igual que siempre.
    """
    extension = (extension or "").lower()
    try:
        if extension == ".csv":
            # Algunos bancos exportan en latin-1; intentamos utf-8 primero
            # y caemos a latin-1 si falla la decodificación.
            try:
                # utf-8-sig descarta la marca invisible (BOM) que agrega Excel
                # al guardar como "CSV UTF-8"; sin ella, el encabezado quedaba
                # como "\ufeffFecha".
                texto = contenido_bytes.decode("utf-8-sig")
            except UnicodeDecodeError:
                texto = contenido_bytes.decode("latin-1")

            # Detectamos el preámbulo separando cada línea por los delimitadores
            # típicos del homebanking argentino (; , o tab) y buscando la
            # primera que tenga pinta de encabezado.
            lineas = texto.splitlines()
            inicio = 0
            for i, linea in enumerate(lineas[:MAX_FILAS_PREAMBULO]):
                if _fila_es_encabezado(re.split(r"[;,\t]", linea)):
                    inicio = i
                    break
            if inicio > 0:
                texto = "\n".join(lineas[inicio:])

            # sep=None + engine='python' auto-detecta coma, punto-coma y tabulación.
            # Cubre Galicia (;), Brubank (\t), y extractos genéricos (,).
            # dtype=str: pandas no interpreta los números por su cuenta. Si lo
            # hiciera, leería "15.000" (quince mil, con punto de miles) como
            # 15.0 y "1.250.000" como texto ilegible. Los montos los convierte
            # _parse_monto, que conoce el formato argentino. keep_default_na
            # evita que una celda vacía se convierta en el texto "nan".
            return pd.read_csv(
                io.StringIO(texto), sep=None, engine="python",
                dtype=str, keep_default_na=False,
            )
        if extension == ".xlsx":
            # openpyxl es la dependencia que pandas usa por debajo para .xlsx.
            # Leemos primero sin encabezado para poder localizar el preámbulo,
            # y recién después re-leemos saltando las filas que sobran.
            crudo = pd.read_excel(
                io.BytesIO(contenido_bytes), engine="openpyxl", header=None
            )
            inicio = 0
            for i in range(min(MAX_FILAS_PREAMBULO, len(crudo))):
                if _fila_es_encabezado(crudo.iloc[i].tolist()):
                    inicio = i
                    break
            return pd.read_excel(
                io.BytesIO(contenido_bytes), engine="openpyxl", skiprows=inicio
            )
    except Exception as e:
        logger.error(f"Error leyendo archivo ({extension}): {e}")
        return None

    logger.warning(f"Extensión no soportada en leer_dataframe: {extension}")
    return None


def contar_hojas_excel(contenido_bytes: bytes) -> int:
    """Cantidad de hojas de un .xlsx (0 si no se puede leer)."""
    try:
        return len(pd.ExcelFile(io.BytesIO(contenido_bytes), engine="openpyxl").sheet_names)
    except Exception:
        return 0


def _detectar_formato_fecha(serie: pd.Series) -> str:
    """Infiere el formato de fecha del archivo, priorizando los argentinos.

    Se elige el primer formato que sirve para TODAS las fechas del archivo (se
    miran hasta 500). Con solo las primeras 5, un extracto con fechas mes/día
    ("09/20/2026") se leía mezclado: las filas ambiguas como día/mes y el
    resto como mes/día, dentro del mismo archivo. Mes/día va después de
    día/mes: "03/04/2026" se sigue leyendo como 3 de abril.
    """
    formatos = [
        "%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%Y/%m/%d",
        "%d/%m/%y", "%d-%m-%y", "%m/%d/%Y", "%m-%d-%Y",
    ]
    muestras = [m for m in serie.dropna().astype(str).str.strip().tolist() if m][:500]
    if not muestras:
        return "%d/%m/%Y"

    # Si traen hora ("20/09/2026 14:35"), el formato se decide con la fecha.
    solo_fecha = [m.split(" ")[0].split("T")[0] for m in muestras]
    mejor, mejor_validas = "%d/%m/%Y", -1
    for fmt in formatos:
        validas = pd.to_datetime(pd.Series(solo_fecha), format=fmt, errors="coerce").notna().sum()
        if validas == len(solo_fecha):
            return fmt
        # Si ninguno sirve para todas (por ejemplo, hay una fila "Total"), se
        # queda con el que más fechas interpreta.
        if validas > mejor_validas:
            mejor, mejor_validas = fmt, validas
    return mejor


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

    # Cada columna se asigna a un solo campo. El orden importa: primero lo
    # más reconocible (fecha), después la descripción y al final los montos.
    usadas: set = set()

    def asignar(sinonimos):
        col = _buscar_columna(columnas_norm, sinonimos, usadas)
        if col is not None:
            usadas.add(col)
        return col

    col_fecha = asignar(SINONIMOS_FECHA)
    col_desc = asignar(SINONIMOS_DESCRIPCION) or asignar(SINONIMOS_DESCRIPCION_DEBILES)
    col_debito = asignar(SINONIMOS_DEBITO)
    col_credito = asignar(SINONIMOS_CREDITO)
    col_monto = asignar(SINONIMOS_MONTO)

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


# Largo máximo de la descripción en la base (columna String(255)).
MAX_DESCRIPCION = 255
# Tope de importe: la columna es Numeric(12, 2), igual que en la carga manual.
MONTO_MAXIMO = 10 ** 10


def _celda_vacia(valor) -> bool:
    return valor is None or (isinstance(valor, float) and pd.isna(valor)) or str(valor).strip() == ""


def procesar_csv(
    df: pd.DataFrame,
    mapeo: dict,
    omitidas: list | None = None,
    compras_tarjeta: bool = False,
) -> list[dict]:
    """Convierte cada fila del DataFrame en un movimiento normalizado.

    Recibe el DataFrame ya leído (por leer_dataframe) más el mapeo de columnas
    detectado por detectar_columnas_csv. La salida es una lista de dicts con
    las claves fecha, descripción, monto y tipo, lista para clasificar.

    Si se pasa la lista `omitidas`, se le agrega una entrada por cada fila que
    no se pudo convertir ({"fila", "descripcion", "motivo"}), para mostrarle
    al usuario qué quedó afuera. Antes esas filas se descartaban en silencio.

    compras_tarjeta: el resumen de una tarjeta de crédito usa el signo al
    revés que un extracto bancario: las compras figuran en positivo (es lo
    que se debe) y el pago del resumen o una devolución, en negativo. En este
    modo lo positivo se toma como gasto y lo negativo se omite, informado: el
    pago de la tarjeta ya figura como débito en el extracto del banco, y
    contarlo acá sería registrar dos veces las mismas compras.
    """
    def omitir(numero, descripcion, motivo):
        if omitidas is not None:
            omitidas.append({"fila": numero, "descripcion": descripcion, "motivo": motivo})

    if df is None or df.empty:
        return []

    col_fecha = mapeo.get("columna_fecha")
    col_desc = mapeo.get("columna_descripcion")
    col_monto = mapeo.get("columna_monto")
    col_debito = mapeo.get("columna_debito")
    col_credito = mapeo.get("columna_credito")
    fmt_fecha = mapeo.get("formato_fecha", "%d/%m/%Y")

    movimientos = []

    for numero, (_, row) in enumerate(df.iterrows(), start=1):
        # numero: posición del movimiento en la tabla (1 = primera fila de datos).
        descripcion = ""
        try:
            desc_raw = row.get(col_desc) if col_desc else None
            descripcion = "Sin descripción" if _celda_vacia(desc_raw) else str(desc_raw).strip()
            # La columna admite 255 caracteres; un concepto bancario más largo
            # se recorta en lugar de hacer fallar toda la importación.
            descripcion = descripcion[:MAX_DESCRIPCION]

            fecha_raw = row.get(col_fecha) if col_fecha else None
            if _celda_vacia(fecha_raw):
                omitir(numero, descripcion, "sin fecha")
                continue
            try:
                texto_fecha = str(fecha_raw).strip().split(" ")[0].split("T")[0]
                fecha = pd.to_datetime(texto_fecha, format=fmt_fecha)
            except (ValueError, TypeError):
                fecha = None
            if fecha is None or pd.isna(fecha):
                # Según el texto, pandas a veces devuelve "fecha vacía" (NaT)
                # en lugar de dar error: los dos casos van por acá.
                # dayfirst: si una fila no sigue el formato detectado, se
                # prioriza igual el orden día/mes que usan los bancos locales.
                fecha = pd.to_datetime(str(fecha_raw), errors="coerce", dayfirst=True)
                if pd.isna(fecha):
                    omitir(numero, descripcion, f"fecha ilegible: '{fecha_raw}'")
                    continue

            if col_debito and col_credito:
                debito_raw, credito_raw = row.get(col_debito), row.get(col_credito)
                debito = _parse_monto(debito_raw)
                credito = _parse_monto(credito_raw)
                if credito is None and not _celda_vacia(credito_raw):
                    omitir(numero, descripcion, f"importe ilegible: '{credito_raw}'")
                    continue
                if debito is None and not _celda_vacia(debito_raw):
                    omitir(numero, descripcion, f"importe ilegible: '{debito_raw}'")
                    continue
                # Algunos bancos anotan el débito con signo menos: se toma el valor absoluto.
                credito = abs(credito) if credito else None
                debito = abs(debito) if debito else None
                if credito and debito:
                    # Antes se tomaba el crédito y el débito se perdía sin aviso.
                    omitir(numero, descripcion, "tiene débito y crédito en la misma fila")
                    continue
                if credito:
                    monto, tipo = credito, "ingreso"
                elif debito:
                    monto, tipo = debito, "gasto"
                else:
                    omitir(numero, descripcion, "sin importe")
                    continue
            elif col_monto:
                monto_raw = row.get(col_monto)
                monto_val = _parse_monto(monto_raw)
                if monto_val is None and not _celda_vacia(monto_raw):
                    omitir(numero, descripcion, f"importe ilegible: '{monto_raw}'")
                    continue
                if not monto_val:
                    omitir(numero, descripcion, "sin importe")
                    continue
                if monto_val > 0:
                    monto, tipo = monto_val, "ingreso"
                else:
                    monto, tipo = abs(monto_val), "gasto"
            else:
                continue

            if monto >= MONTO_MAXIMO:
                # Mismo tope que la carga manual. Si pasaba al preview, después
                # hacía fallar la importación completa al confirmar.
                omitir(numero, descripcion, "importe fuera de rango (máximo $10.000 millones)")
                continue

            if compras_tarjeta:
                if tipo == "gasto":
                    omitir(numero, descripcion,
                           "monto negativo en un resumen de tarjeta (pago del resumen o devolución): no es una compra")
                    continue
                tipo = "gasto"

            movimientos.append({
                "fecha": fecha.strftime("%Y-%m-%dT00:00:00"),
                "descripcion": descripcion,
                "monto": round(float(monto), 2),
                "tipo": tipo,
            })

        except Exception as e:
            logger.warning(f"Fila ignorada por error: {e}")
            omitir(numero, descripcion, "no se pudo leer la fila")
            continue

    return movimientos


_MILES_CON_PUNTO = re.compile(r"^\d{1,3}(\.\d{3})+$")


def _parse_monto(valor) -> float | None:
    """Convierte un importe del extracto a número. Devuelve None si no se puede.

    Los bancos argentinos escriben "1.234,56": punto de miles y coma decimal.
    Otros exportan "1234.56" o "1,234.56". La regla:
      - Si hay punto y coma, el separador que aparece ÚLTIMO es el decimal.
      - Si hay solo comas: una sola es decimal ("3500,50"); varias son de
        miles ("1,250,000").
      - Si hay solo puntos: varios son de miles ("1.250.000"), y uno solo
        seguido de exactamente tres dígitos también ("15.000" = quince mil).
        Un importe bancario nunca tiene tres decimales.
    También acepta el negativo entre paréntesis "(1.234,56)" y con el signo
    al final "1.234,56-", que usan algunos homebanking.
    """
    if valor is None or isinstance(valor, bool):
        return None
    if isinstance(valor, (int, float)):
        # Excel ya entrega números reales: no hay formato que interpretar.
        return None if pd.isna(valor) else float(valor)

    s = str(valor).strip().replace("$", "").replace(" ", "").replace("\u00a0", "")
    if not s:
        return None

    negativo = False
    if s.startswith("(") and s.endswith(")"):
        negativo, s = True, s[1:-1]
    if s.endswith("-"):
        negativo, s = True, s[:-1]
    if s.startswith("-"):
        negativo, s = not negativo, s[1:]
    elif s.startswith("+"):
        s = s[1:]

    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")   # 1.234,56
        else:
            s = s.replace(",", "")                     # 1,234.56
    elif "," in s:
        s = s.replace(",", "") if s.count(",") > 1 else s.replace(",", ".")
    elif "." in s and (s.count(".") > 1 or _MILES_CON_PUNTO.match(s)):
        s = s.replace(".", "")

    try:
        numero = float(s)
    except ValueError:
        return None
    if numero != numero or numero in (float("inf"), float("-inf")):
        return None
    return -numero if negativo else numero


def clasificar_movimientos(movimientos: list, db: Session, usuario_id: int = 0) -> list:
    """Clasifica cada movimiento usando exclusivamente el ML local.

    La descripción del movimiento permanece dentro de la infraestructura del
    sistema y nunca se transmite a terceros.

    Trabaja en LOTE: el pipeline de sklearn se deserializa una única vez y las
    correcciones previas del usuario se traen en una sola consulta. Clasificar
    fila por fila (como hace clasificar_gasto para un gasto individual)
    implicaría decodificar el modelo desde la BD por cada movimiento, algo
    prohibitivo para un extracto bancario de cientos de filas.
    """
    import numpy as np
    from app.models.cache_clasificacion import CacheClasificacion
    from app.services import ml_service
    from app.services.ia_service import UMBRAL_CONFIANZA_ML

    resultado: list[dict | None] = [None] * len(movimientos)

    # El clasificador está entrenado con categorías de GASTO (Software,
    # Suscripciones, Transporte...). Aplicárselo a un ingreso le asignaría
    # una categoría que no existe en el módulo de ingresos y rompería sus
    # filtros, así que los ingresos entran como "Otros" y el usuario los
    # recategoriza si quiere.
    indices_gasto = []
    for idx, mov in enumerate(movimientos):
        if mov.get("tipo") != "gasto":
            resultado[idx] = {**mov, "categoria": "Otros"}
        else:
            indices_gasto.append(idx)

    if not indices_gasto:
        return resultado

    # Paso 1: correcciones explícitas previas del usuario (ground truth).
    # Misma prioridad que aplica ia_service.clasificar_gasto, pero resuelta
    # con una única query en lugar de una por fila.
    correcciones = {
        c.descripcion_normalizada: c.categoria
        for c in db.query(CacheClasificacion).filter(
            CacheClasificacion.usuario_id == usuario_id,
        ).all()
    }

    pendientes = []
    for idx in indices_gasto:
        desc_norm = ml_service.normalizar_descripcion(movimientos[idx].get("descripcion", ""))
        if desc_norm in correcciones:
            resultado[idx] = {**movimientos[idx], "categoria": correcciones[desc_norm]}
        else:
            pendientes.append(idx)

    # Paso 2: predicción en lote con el modelo del usuario (o el base).
    # Mismo umbral de confianza que la clasificación individual: por debajo
    # se sugiere "Otros" para que el usuario revise.
    if pendientes:
        try:
            pipeline, algoritmo, _es_propio = ml_service.obtener_o_crear_modelo(db, usuario_id)
            descripciones = [movimientos[i].get("descripcion", "") for i in pendientes]
            clases = pipeline.classes_

            categorias = []
            if algoritmo == "svm":
                scores = np.asarray(pipeline.decision_function(descripciones), dtype=float)
                if scores.ndim == 1:
                    scores = scores.reshape(-1, 1)  # caso binario: un margen por fila
                for fila in scores:
                    idx_clase, confianza = ml_service._confianza_svm(fila.ravel())
                    categorias.append(clases[idx_clase] if confianza >= UMBRAL_CONFIANZA_ML else "Otros")
            else:
                probas = pipeline.predict_proba(descripciones)
                for fila in probas:
                    idx_clase = int(np.argmax(fila))
                    confianza = float(fila[idx_clase])
                    categorias.append(clases[idx_clase] if confianza >= UMBRAL_CONFIANZA_ML else "Otros")

            for i, categoria in zip(pendientes, categorias):
                resultado[i] = {**movimientos[i], "categoria": categoria}
        except Exception as e:
            logger.error(f"Error clasificando lote de importación (usuario {usuario_id}): {e}")
            for i in pendientes:
                if resultado[i] is None:
                    resultado[i] = {**movimientos[i], "categoria": "Otros"}

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
) -> tuple[list[dict], int, int]:
    """Devuelve (movimientos_a_importar, omitidos_por_duplicado, omitidos_por_transferencia).

    Pensada para el endpoint /confirmar: aplica la misma detección que /preview
    como red de seguridad y descarta duplicados y transferencias entre cuentas
    propias antes de persistir.
    """
    marcados = detectar_posibles_duplicados(db, usuario_id, movimientos)
    marcados = detectar_transferencias_propias_en_lote(marcados)
    a_importar = [
        m for m in marcados
        if not m.get("posible_duplicado") and not m.get("posible_transferencia_propia")
    ]
    omitidos_dup = sum(1 for m in marcados if m.get("posible_duplicado"))
    omitidos_transf = sum(
        1 for m in marcados
        if m.get("posible_transferencia_propia") and not m.get("posible_duplicado")
    )
    return a_importar, omitidos_dup, omitidos_transf


# ── Transferencias entre cuentas propias ─────────────────────────────────────
# Un freelancer opera con varias cuentas (banco + Mercado Pago + billeteras).
# Una transferencia entre sus propias cuentas aparece como débito en un
# extracto y como crédito en el otro: si ambas patas se importan como
# gasto + ingreso, el "ingreso" infla la facturación de 12 meses que evalúa
# la categoría de Monotributo. Detectamos el patrón: mismo monto, fechas a
# ≤1 día y al menos una descripción con vocabulario de transferencia.
#
# Hay dos capas de defensa:
#   1. Acá (import): si AMBAS patas vienen en el mismo lote, se marcan con
#      posible_transferencia_propia y /confirmar las omite.
#   2. Auditoría (detector 5): cubre el caso real de patas repartidas entre
#      archivos de bancos distintos ya persistidos, con acción de descarte.

PATRON_TRANSFERENCIA = re.compile(
    r"transf|enviaste|recibiste|dinero retirado|retiro de dinero|retiraste"
    r"|cuenta propia|cuentas propias|mismo titular|misma titularidad|entre cuentas"
)


def es_descripcion_transferencia(descripcion: str) -> bool:
    """Indica si la descripción tiene vocabulario típico de transferencia.

    Se evalúa sobre la forma normalizada (minúsculas, sin tildes), así
    "TRANSFERENCIA", "Transf." y "transferís" matchean igual. Es un guardia
    contra falsos positivos: un ingreso y un gasto que casualmente coinciden
    en monto y fecha NO se marcan si ninguno menciona una transferencia.
    """
    return bool(PATRON_TRANSFERENCIA.search(_normalizar_descripcion(descripcion)))


def _fechas_cercanas(fecha_a: str, fecha_b: str, max_dias: int = 1) -> bool:
    try:
        da = datetime.fromisoformat(fecha_a).date()
        db_ = datetime.fromisoformat(fecha_b).date()
    except (ValueError, TypeError):
        return False
    return abs((da - db_).days) <= max_dias


def detectar_transferencias_propias_en_lote(movimientos: list[dict]) -> list[dict]:
    """Marca pares (ingreso, gasto) del MISMO lote que parecen transferencia.

    Emparejamiento voraz: cada ingreso se aparea con a lo sumo un gasto libre
    de igual monto, fecha a ≤1 día y vocabulario de transferencia en alguna
    de las dos descripciones. Ambas patas quedan con la flag
    posible_transferencia_propia = True; el resto queda en False.
    """
    resultado = [{**m, "posible_transferencia_propia": False} for m in movimientos]

    idx_ingresos = [i for i, m in enumerate(resultado) if m.get("tipo") == "ingreso"]
    idx_gastos = [i for i, m in enumerate(resultado) if m.get("tipo") == "gasto"]

    gastos_usados: set[int] = set()
    for i in idx_ingresos:
        ing = resultado[i]
        monto_ing = round(float(ing.get("monto", 0)), 2)
        for j in idx_gastos:
            if j in gastos_usados:
                continue
            gasto = resultado[j]
            if round(float(gasto.get("monto", 0)), 2) != monto_ing:
                continue
            if not _fechas_cercanas(ing.get("fecha", ""), gasto.get("fecha", "")):
                continue
            if not (
                es_descripcion_transferencia(ing.get("descripcion", ""))
                or es_descripcion_transferencia(gasto.get("descripcion", ""))
            ):
                continue
            resultado[i]["posible_transferencia_propia"] = True
            resultado[j]["posible_transferencia_propia"] = True
            gastos_usados.add(j)
            break

    return resultado
