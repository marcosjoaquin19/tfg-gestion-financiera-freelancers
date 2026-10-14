"""
Servicio de Proyecciones — predicción de ingresos con Prophet.

Usa la librería Prophet (modelo de series temporales de Meta) para predecir los
ingresos futuros del freelancer a partir de su historial. Devuelve, por período,
el monto estimado y el rango (inferior/superior) del intervalo de confianza.
Con pocos datos no usa Prophet: recurre a una media móvil (arranque en frío).
Solo se entrena con meses cerrados y siempre se proyecta desde el mes que viene.

Cómo leer este archivo:
  1. serie_mensual() convierte los ingresos sueltos en una lista de totales
     por mes (la "serie temporal": un valor por cada mes, en orden).
  2. _generar_proyecciones() decide el método según cuánta historia hay:
     Prophet, media móvil, estimación con el mes en curso o "sin datos".
  3. El resultado se guarda en la tabla proyecciones con una "firma" de los
     ingresos usados; asegurar_proyecciones_vigentes() la compara para saber
     si hay que recalcular (la usa el semáforo del monotributo).

Prophet en criollo: separa la historia en tres capas, la tendencia (hacia dónde
va), la estacionalidad (lo que se repite todos los años) y el ruido (lo que no
se puede explicar). Para pronosticar, estira la tendencia, le suma la
estacionalidad y con el ruido calcula una banda: un mínimo y un máximo entre
los que cae el resultado 8 de cada 10 veces (el 80 % que Prophet usa por
defecto). Para ver estacionalidad anual necesita al menos dos años de historia;
con menos, Prophet la deja afuera solo y queda la tendencia con su banda.
"""

# PATRÓN: Strategy + Degradación elegante — Prophet si hay historial suficiente, media móvil si no.
# (Degradación elegante: si falta algo, el sistema sigue andando con un método
# más simple en lugar de mostrar un error.)
# Justificación y alternativas descartadas: defensa_final/02_ARQUITECTURA_Y_PATRONES.md

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import hashlib
import logging
import statistics
import threading
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
import numpy as np
import pandas as pd
# cmdstanpy es el motor de cálculo que Prophet usa por dentro para ajustar el
# modelo. Debe importarse antes que Prophet para que use CMDSTANPY.
# ("noqa: F401" le avisa al revisor de estilo que el import sin usar es a propósito.)
import cmdstanpy  # noqa: F401
from prophet import Prophet
from app.models.ingreso import Ingreso
from app.models.proyeccion import Proyeccion

logger = logging.getLogger(__name__)

MIN_INGRESOS_PROPHET = 10
# Por debajo de 10 cobros en meses cerrados, Prophet no tiene suficientes datos
# para separar tendencia de ruido → usamos media móvil.

MIN_MESES_PROPHET = 3
# Prophet ajusta una tendencia sobre los totales mensuales. Con dos meses la
# "tendencia" es la recta que pasa por dos puntos: encaja perfecto sin importar
# los datos y se extrapola sin ningún control (1M y 3M → 13M en seis meses).
# Con tres o más meses ya hay algo que ajustar.

HORIZONTE_MAX_MESES = 6
# HU-09: proyección de los próximos seis meses. Más allá, en series cortas e
# irregulares como las de un freelancer, el error pasa a dominar la estimación.

VENTANA_MEDIA_MOVIL = 3
# El arranque en frío promedia los últimos 3 meses cerrados. Media "móvil"
# porque la ventana se corre: el mes que viene promediará otros tres.

# Método con el que se calculó cada proyección (se guarda en la tabla y la
# pantalla Proyecciones lo muestra, para que el usuario sepa de dónde sale el número).
METODO_PROPHET = "prophet"
METODO_MEDIA_MOVIL = "media_movil"
METODO_MES_EN_CURSO = "mes_en_curso"
# solo hay ingresos del mes que todavía no terminó: estimación provisoria
METODO_SIN_DATOS = "sin_datos"
METODO_RESPALDO = "respaldo"
# había historial para Prophet pero falló: la misma media móvil, con otro
# nombre para que la pantalla no lo explique como falta de datos


# Zona horaria de Argentina (UTC-3). El servidor trabaja en UTC, la hora
# universal; sin esta corrección, desde las 21 h de Argentina el sistema ya
# creía estar en el día siguiente.
ZONA_AR = ZoneInfo("America/Argentina/Buenos_Aires")


def inicio_de_manana() -> datetime:
    """Primer instante de mañana según el calendario de Argentina, con la
    convención de las fechas guardadas (día calendario a las 00:00 UTC).

    Un cobro ya pasó si su fecha es anterior a este instante. Comparar contra
    la hora UTC fallaba desde las 21 h: en UTC ya era mañana, así que un cobro
    fechado al día siguiente sumaba como facturado real y, el 31/12 a la
    noche, uno del 1/1 se sumaba al año que terminaba.
    """
    hoy = datetime.now(ZONA_AR)
    return datetime(hoy.year, hoy.month, hoy.day, tzinfo=timezone.utc) + timedelta(days=1)


def inicio_mes_en_curso() -> datetime:
    """Primer día del mes en curso según el calendario de Argentina, sin zona.

    Las fechas se cargan como día calendario (guardado a las 00:00 UTC), así
    que el mes que las agrupa es el del calendario local. Con el reloj en UTC,
    desde las 21 h del último día del mes el sistema ya creía estar en el mes
    siguiente: la cuota recién pagada figuraba impaga y el resumen por
    defecto era de un mes vacío.
    """
    ahora = datetime.now(ZONA_AR)
    return datetime(ahora.year, ahora.month, 1)


def firma_ingresos(ingresos) -> str:
    """Huella de los datos de los que depende la proyección.

    Cambia si se agrega, borra o edita un ingreso (id, monto o mes) y también
    cuando empieza un mes nuevo, porque cambian los meses cerrados. Así se
    detecta una proyección vieja sin comparar resultados.

    SHA-1 funciona como una huella digital: a partir de todo ese texto genera un
    código corto que cambia por completo si cambia aunque sea un dato. Comparar
    dos códigos es mucho más barato que recalcular la proyección para ver si da
    lo mismo. Acá no se usa para seguridad, solo para detectar cambios.
    """
    # Arranca con el mes en curso ("2026-10"): al empezar un mes nuevo, la firma cambia.
    h = hashlib.sha1(inicio_mes_en_curso().strftime("%Y-%m").encode())
    # Después suma cada ingreso, siempre en el mismo orden (por id), así la misma
    # lista de ingresos da siempre la misma firma.
    for ingreso in sorted(ingresos, key=lambda i: i.id):
        h.update(f"|{ingreso.id}:{float(ingreso.monto):.2f}:{ingreso.fecha.year}-{ingreso.fecha.month}".encode())
    return h.hexdigest()


def _clave_mes(fecha: datetime) -> datetime:
    """Lleva cualquier fecha al día 1 de su mes: así se agrupan los cobros por mes."""
    return datetime(fecha.year, fecha.month, 1)


def serie_mensual(ingresos) -> tuple[list[tuple[datetime, float]], float, int]:
    """Totales por mes con los que se entrena, más el parcial del mes en curso.

    Devuelve (serie, total_mes_en_curso, ingresos_en_meses_cerrados).

    - Solo entran los meses CERRADOS: el mes en curso todavía no terminó y,
      tratado como un mes completo, parece una caída brusca que Prophet
      extrapola hacia cero. Tampoco entran fechas futuras.
    - Los meses sin ingresos que quedan ENTRE el primero y el último con datos
      cuentan como $0: para un freelancer, un mes sin cobrar es un dato real.
      No se completa con ceros después del último mes con datos, porque eso
      puede ser un extracto que todavía no se importó.
    """
    mes_actual = inicio_mes_en_curso()
    totales: dict[datetime, float] = {}   # mes → suma de lo cobrado ese mes
    total_en_curso = 0.0
    cantidad_cerrados = 0

    # Se reparte cada cobro en su mes. Los de meses futuros no entran en ningún lado.
    for ingreso in ingresos:
        mes = _clave_mes(ingreso.fecha)
        if mes < mes_actual:
            totales[mes] = totales.get(mes, 0.0) + float(ingreso.monto)
            cantidad_cerrados += 1
        elif mes == mes_actual:
            total_en_curso += float(ingreso.monto)

    if not totales:
        return [], round(total_en_curso, 2), 0

    # Se recorre mes a mes desde el primero hasta el último con datos; los
    # meses del medio sin cobros entran con $0.
    serie = []
    mes = min(totales)
    ultimo = max(totales)
    while mes <= ultimo:
        serie.append((mes, round(totales.get(mes, 0.0), 2)))
        mes += relativedelta(months=1)   # relativedelta suma "un mes" respetando el calendario

    return serie, round(total_en_curso, 2), cantidad_cerrados


def _proyeccion(usuario_id, mes, yhat, lower, upper, metodo) -> Proyeccion:
    """Arma una fila de la tabla proyecciones para un mes.

    yhat es el monto estimado ("y sombrero": así llama Prophet al valor
    predicho), y lower/upper son el piso y el techo de la banda. Ningún valor
    puede quedar negativo (max con 0): un mes no puede tener ingresos menores a
    cero, aunque la banda matemática a veces baje de cero.
    """
    return Proyeccion(
        usuario_id=usuario_id,
        fecha_proyeccion=mes.replace(tzinfo=timezone.utc),
        monto_proyectado=round(max(yhat, 0), 2),
        monto_lower=round(max(lower, 0), 2),
        monto_upper=round(max(upper, 0), 2),
        metodo=metodo,
    )


def _meses_a_proyectar(periodos: int) -> list[datetime]:
    """Siempre desde el mes que viene, aunque el último dato sea viejo: una
    proyección nunca cae sobre un mes que ya pasó."""
    primero = inicio_mes_en_curso() + relativedelta(months=1)
    return [primero + relativedelta(months=k) for k in range(periodos)]


def _proyecciones_media_movil(usuario_id: int, montos: list[float], periodos: int, metodo: str) -> list[Proyeccion]:
    """Arranque en frío ("cold start"): todavía hay pocos datos para Prophet.

    Proyecta, para cada mes futuro, el promedio de los totales mensuales que
    recibe (los últimos 3 meses cerrados). Es el mismo número para todos los
    meses: con tan poca historia no se puede afirmar una tendencia.

    La banda (mínimo y máximo) es el promedio ± 1 desviación estándar. La
    desviación estándar mide cuánto se alejan los meses del promedio: si todos
    los meses se cobró parecido es chica y la banda es angosta; si hubo meses
    muy distintos, la banda se abre. Con un solo dato no hay desviación para
    medir, y se usa ± 20 % del promedio.

    "metodo" dice con qué nombre se guarda (media_movil, mes_en_curso,
    sin_datos o respaldo): el cálculo es el mismo, cambia cómo lo explica la pantalla.
    """
    media = sum(montos) / len(montos) if montos else 0.0
    desviacion = statistics.stdev(montos) if len(montos) >= 2 else media * 0.2

    return [
        _proyeccion(usuario_id, mes, media, media - desviacion, media + desviacion, metodo)
        for mes in _meses_a_proyectar(periodos)
    ]


def _proyecciones_prophet(usuario_id: int, serie, periodos: int) -> list[Proyeccion]:
    """Proyecta con Prophet los próximos meses a partir de la serie mensual.

    Pasos: 1) se arma la tabla que Prophet espera; 2) se entrena (fit) con los
    meses cerrados; 3) se le piden los meses futuros; 4) se guardan solo los
    que corresponden (desde el mes que viene), con su monto y su banda.
    """
    # Paso 1: Prophet exige una tabla (DataFrame de pandas) con dos columnas de
    # nombres fijos: "ds" = la fecha (día 1 de cada mes) e "y" = el total de ese mes.
    df = pd.DataFrame(serie, columns=["ds", "y"])

    meses = _meses_a_proyectar(periodos)
    ultimo_dato = df["ds"].max()
    # Prophet predice a partir del mes siguiente al último dato. Si ese dato es
    # viejo, hay que pedirle también los meses intermedios y descartarlos.
    # Ejemplo: último dato julio, hoy es octubre → se piden ago-sep-oct y los
    # seis siguientes, y después se tiran ago, sep y oct.
    faltan = relativedelta(meses[-1], ultimo_dato)
    pasos = faltan.years * 12 + faltan.months

    # Paso 2: entrenar. stan_backend elige el motor de cálculo (ver el import de cmdstanpy).
    modelo = Prophet(stan_backend="CMDSTANPY")
    modelo.fit(df)
    # Paso 3: la tabla de meses futuros a predecir.
    # freq="MS" → "Month Start": cada predicción es el primer día de cada mes.
    # include_history=False → solo los meses futuros, no los que ya pasaron.
    futuro = modelo.make_future_dataframe(periods=pasos, freq="MS", include_history=False)
    # Prophet calcula la banda (yhat_lower/yhat_upper) simulando muchos futuros
    # posibles al azar (simulación "Monte Carlo") y tomando el rango donde caen
    # 8 de cada 10. Fijamos la semilla del azar para que el resultado sea
    # REPRODUCIBLE: mismos datos → misma proyección, incluida la banda. Clave
    # para poder defender el número: si se recalcula, da lo mismo.
    np.random.seed(42)
    forecast = modelo.predict(futuro)
    # Paso 4: descartar los meses intermedios y quedarse con los pedidos.
    forecast = forecast[forecast["ds"] >= meses[0]].head(periodos)

    return [
        _proyeccion(usuario_id, fila["ds"].to_pydatetime(), fila["yhat"],
                    fila["yhat_lower"], fila["yhat_upper"], METODO_PROPHET)
        for _, fila in forecast.iterrows()
    ]


# Una sola regeneración a la vez. Después de importar, el Dashboard y el
# semáforo piden la proyección al mismo tiempo: sin el candado, los dos
# recalculaban en paralelo, el segundo borraba lo que guardaba el primero (que
# fallaba con un error 500, "error interno del servidor") y la semilla de numpy,
# que es global, se compartía, así que la banda pesimista/optimista salía distinta.
# RLock = candado "reentrante": el mismo pedido que ya lo tiene puede volver a
# tomarlo sin trabarse. Hace falta porque asegurar_proyecciones_vigentes() toma
# el candado y, adentro, llama a generar_proyecciones(), que lo vuelve a pedir.
_candado = threading.RLock()


def generar_proyecciones(db: Session, usuario_id: int, periodos: int = HORIZONTE_MAX_MESES) -> list[Proyeccion]:
    """Calcula y guarda de nuevo las proyecciones del usuario (de 1 a 6 meses).

    La llaman la pantalla Proyecciones (POST /proyecciones/generar) y
    asegurar_proyecciones_vigentes(). Espera su turno con el candado; el
    trabajo real está en _generar_proyecciones().
    """
    with _candado:
        return _generar_proyecciones(db, usuario_id, periodos)


def _generar_proyecciones(db: Session, usuario_id: int, periodos: int) -> list[Proyeccion]:
    """Elige el método según la historia disponible y reemplaza las proyecciones guardadas.

    Árbol de decisión:
      - 10 o más cobros en meses cerrados Y 3 o más meses cerrados → Prophet
        (si Prophet falla, media móvil con el nombre "respaldo");
      - hay algún mes cerrado, pero no alcanza para Prophet → media móvil de
        los últimos 3 meses cerrados;
      - solo hay cobros en el mes en curso (usuario nuevo) → se usa lo cobrado
        este mes como estimación provisoria;
      - no hay ningún cobro → proyección en cero ("sin_datos").
    """
    ingresos = (
        db.query(Ingreso)
        .filter(Ingreso.usuario_id == usuario_id)
        .order_by(Ingreso.fecha.asc())
        .all()
    )

    serie, total_en_curso, cantidad_cerrados = serie_mensual(ingresos)
    montos = [total for _, total in serie]

    if cantidad_cerrados >= MIN_INGRESOS_PROPHET and len(serie) >= MIN_MESES_PROPHET:
        try:
            nuevas = _proyecciones_prophet(usuario_id, serie, periodos)
        except Exception:
            # Si Prophet falla (por ejemplo, el optimizador no converge), la
            # pantalla no se cae: se proyecta con la media móvil, la misma
            # estrategia del arranque en frío, y el método guardado lo dice.
            logger.exception("Prophet falló para el usuario %s; se usa la media móvil", usuario_id)
            nuevas = _proyecciones_media_movil(
                usuario_id, montos[-VENTANA_MEDIA_MOVIL:], periodos, METODO_RESPALDO,
            )
    elif serie:
        nuevas = _proyecciones_media_movil(
            usuario_id, montos[-VENTANA_MEDIA_MOVIL:], periodos, METODO_MEDIA_MOVIL,
        )
    elif total_en_curso > 0:
        # Usuario nuevo con ingresos solo en el mes que todavía no terminó:
        # es un piso, no un promedio, y se informa como estimación provisoria.
        nuevas = _proyecciones_media_movil(usuario_id, [total_en_curso], periodos, METODO_MES_EN_CURSO)
    else:
        nuevas = _proyecciones_media_movil(usuario_id, [], periodos, METODO_SIN_DATOS)

    # Cada proyección guarda la firma de los ingresos con los que se calculó,
    # para saber más adelante si quedó vieja.
    firma = firma_ingresos(ingresos)
    for p in nuevas:
        p.firma = firma

    # Se borran las proyecciones anteriores del usuario y se guardan las nuevas
    # en un mismo commit (guardado): nunca quedan mezcladas viejas y nuevas.
    db.query(Proyeccion).filter(Proyeccion.usuario_id == usuario_id).delete()
    db.add_all(nuevas)
    db.commit()
    for p in nuevas:
        db.refresh(p)

    return nuevas


def asegurar_proyecciones_vigentes(db: Session, usuario_id: int) -> list[Proyeccion]:
    """Devuelve las proyecciones guardadas si siguen correspondiendo a los
    ingresos actuales; si no existen o quedaron viejas, las regenera.

    La usa el estado fiscal: sin esto, el semáforo sumaba una proyección
    calculada antes de la última importación (o ninguna, si el usuario nunca
    abrió Proyecciones).
    """
    with _candado:
        # Se mira recién con el candado tomado: si otro pedido las acaba de
        # regenerar, se usan esas en vez de calcularlas de nuevo.
        actuales = db.query(Proyeccion).filter(Proyeccion.usuario_id == usuario_id).all()
        ingresos = db.query(Ingreso).filter(Ingreso.usuario_id == usuario_id).all()
        firma = firma_ingresos(ingresos)
        if actuales and all(p.firma == firma for p in actuales):
            return actuales
        return generar_proyecciones(db, usuario_id)
