"""
Servicio de Recomendaciones (HU-12) — sugerencias accionables por reglas locales.

Cada recomendación sale de una regla determinística aplicada sobre los datos
que el usuario cargó: no interviene ningún servicio externo ni modelo de
lenguaje. Criterios de la HU-12 que se cumplen acá:
  - entre 3 y 5 sugerencias (MIN/MAX_RECOMENDACIONES);
  - reglas locales sobre datos agregados;
  - considera a la vez alertas activas, tendencia de ingresos y proyecciones
    vigentes (estas últimas a través del estado fiscal, que suma la proyección).

Reglas de redacción: siempre en tono de sugerencia ("te sugerimos", "podrías",
"conviene"), nunca como indicación, y sin cifras que no salgan de los datos.
Cada recomendación trae su "dato": el hecho concreto que la disparó, con
todas las cifras que aparecen en el texto, para que sea trazable (CP-M11-06).
"""

# PATRÓN: Strategy — cada regla es una función independiente que devuelve
# recomendaciones; generar_recomendaciones() las reúne, ordena y recorta.

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from decimal import Decimal
import statistics

from dateutil.relativedelta import relativedelta
from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.models.alerta_auditoria import AlertaAuditoria, TipoAlerta
from app.models.factura import Factura, EstadoFactura
from app.models.gasto import Gasto
from app.models.ingreso import Ingreso
from app.models.usuario import Usuario
from app.services.facturas_estado import marcar_vencidas
from app.services.formato import formato_pesos_ar as pesos
from app.services.monotributo_service import calcular_estado_monotributo, verificar_pago_monotributo
from app.services.prophet_service import inicio_mes_en_curso, serie_mensual

MIN_RECOMENDACIONES = 3
MAX_RECOMENDACIONES = 5          # HU-12: "entre tres y cinco sugerencias"

UMBRAL_TENDENCIA = 0.15          # ±15 % entre los meses recientes y los anteriores
UMBRAL_AUMENTO_GASTO = 0.30      # un rubro que ya supera en 30 % al mes anterior
MESES_VENTANA_AHORRO = 6         # superávit/déficit sobre los últimos 6 meses cerrados

PRIORIDAD_MAX_PRINCIPAL = 5
# Prioridades 1 a 5: problemas y oportunidades detectados en los datos; se
# muestran hasta 5. Prioridad 6 en adelante: sugerencias informativas o de
# uso de la app, que solo se agregan si hace falta llegar a 3.

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


@dataclass(frozen=True)
class Recomendacion:
    prioridad: int      # 1 = más urgente
    regla: str          # identificador estable de la regla que la produjo
    texto: str          # lo que ve el usuario
    dato: str           # el hecho concreto que la disparó (trazabilidad)


# --- Redacción ------------------------------------------------------------------

def _cantidad(n: int, singular: str, plural: str) -> str:
    return f"{n} {singular if n == 1 else plural}"


def _lista(items: list[str]) -> str:
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " y " + items[-1]


def _fecha(d: datetime) -> str:
    return d.strftime("%d/%m/%Y")


def _meses(claves: list[datetime]) -> str:
    """'julio y agosto de 2026' / 'diciembre de 2025 y enero de 2026'."""
    if len({m.year for m in claves}) == 1:
        return f"{_lista([MESES[m.month - 1] for m in claves])} de {claves[0].year}"
    return _lista([f"{MESES[m.month - 1]} de {m.year}" for m in claves])


def _porcentaje(valor: float) -> str:
    return f"{valor:.1f}".replace(".", ",").removesuffix(",0")


# --- Reglas ------------------------------------------------------------------------

def _regla_cobros(db: Session, usuario_id: int) -> list[Recomendacion]:
    marcar_vencidas(db, usuario_id)
    facturas = db.query(Factura).filter(Factura.usuario_id == usuario_id).all()
    vencidas = sorted((f for f in facturas if f.estado == EstadoFactura.VENCIDA), key=lambda f: f.fecha_vencimiento)
    pendientes = sorted((f for f in facturas if f.estado == EstadoFactura.PENDIENTE), key=lambda f: f.fecha_vencimiento)

    def detalle(lista, verbo):
        items = [f"{f.cliente_nombre}, {pesos(f.monto)}, {verbo} el {_fecha(f.fecha_vencimiento)}" for f in lista[:3]]
        if len(lista) > 3:
            items.append(f"y {len(lista) - 3} más")
        return "; ".join(items)

    if vencidas:
        total_v = sum(f.monto for f in vencidas)
        clientes = {f.cliente_nombre for f in vencidas}
        texto = (
            f"Tenés {_cantidad(len(vencidas), 'factura vencida', 'facturas vencidas')} sin cobrar por "
            f"{pesos(total_v)}. Te sugerimos contactar {'a ese cliente' if len(clientes) == 1 else 'a esos clientes'}: "
            f"es dinero que ya debería haberse acreditado."
        )
        dato = f"Vencidas (total {pesos(total_v)}): {detalle(vencidas, 'venció')}."
        if pendientes:
            total_p = sum(f.monto for f in pendientes)
            texto += f" Además tenés {_cantidad(len(pendientes), 'factura pendiente', 'facturas pendientes')} por {pesos(total_p)}."
            dato += f" Pendientes (total {pesos(total_p)}): {detalle(pendientes, 'vence')}."
        return [Recomendacion(1, "facturas_vencidas", texto, dato)]

    if pendientes:
        total_p = sum(f.monto for f in pendientes)
        texto = (
            f"Tenés {_cantidad(len(pendientes), 'factura pendiente', 'facturas pendientes')} de cobro por "
            f"{pesos(total_p)}; la próxima vence el {_fecha(pendientes[0].fecha_vencimiento)}. "
            f"Conviene hacerles seguimiento para sostener tu flujo de caja."
        )
        return [Recomendacion(3, "facturas_pendientes", texto,
                              f"Pendientes (total {pesos(total_p)}): {detalle(pendientes, 'vence')}.")]

    if not facturas:
        return [Recomendacion(
            7, "sin_facturas",
            "Si emitís facturas, te sugerimos cargarlas en la sección Facturas para seguir sus cobros y vencimientos.",
            "No hay facturas registradas.",
        )]
    return []


def _regla_monotributo(db: Session, usuario_id: int) -> list[Recomendacion]:
    """Estado fiscal (usa la proyección vigente de M08/M09) y cuota del mes."""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario or not usuario.categoria_monotributo:
        return [Recomendacion(
            3, "sin_categoria",
            "Te sugerimos cargar tu categoría de monotributo en la sección Monotributo: así el sistema "
            "controla tu tope anual y te avisa con anticipación si te acercás.",
            "No hay una categoría de monotributo cargada.",
        )]

    e = calcular_estado_monotributo(db, usuario_id)
    if e is None:
        return []
    pago = verificar_pago_monotributo(db, usuario_id)

    cat = e["categoria_actual"]
    pct = _porcentaje(e["porcentaje_proyectado"])
    dato = (
        f"Categoría {cat}: tope anual {pesos(e['limite_anual'])}; facturado en el año {pesos(e['facturado_anual'])} "
        f"({_porcentaje(e['porcentaje_usado'])} %); proyección anual {pesos(e['proyeccion_anual'])} ({pct} %)."
    )

    fiscal, prioridad, regla = None, None, None
    if e["excede_regimen"]:
        fiscal = (
            f"Según tu proyección, este año facturarías {pesos(e['proyeccion_anual'])}, más que el tope de la "
            f"categoría más alta del régimen. Te sugerimos consultar con tu contador cuanto antes: hay riesgo "
            f"de exclusión del Monotributo."
        )
        prioridad, regla = 1, "fiscal_exclusion"
    elif e["limite_superado"]:
        fiscal = (
            f"Lo que facturaste este año ({pesos(e['facturado_anual'])}) ya superó el tope de tu categoría {cat} "
            f"({pesos(e['limite_anual'])}). Te sugerimos consultar con tu contador por la recategorización"
            + (f"; según tu proyección, la categoría que cubriría tu facturación es la {e['categoria_sugerida']}."
               if e["categoria_sugerida"] else ".")
        )
        prioridad, regla = 1, "fiscal_tope_superado"
    elif e["estado"] == "rojo":
        fiscal = (
            f"Según tu proyección, este año llegarías al {pct} % del tope de tu categoría {cat}"
            + (f" y lo superarías en {e['mes_limite'].lower()}" if e["mes_limite"] else "")
            + ". Te sugerimos consultar con tu contador si te conviene recategorizarte"
            + (f" (la categoría que cubriría tu proyección es la {e['categoria_sugerida']})" if e["categoria_sugerida"] else "")
            + "."
        )
        prioridad, regla = 1, "fiscal_rojo"
    elif e["estado"] == "amarillo":
        fiscal = (
            f"Según tu proyección, este año llegarías al {pct} % del tope de tu categoría {cat}. "
            f"Conviene seguir de cerca tu facturación antes de la próxima recategorización semestral."
        )
        prioridad, regla = 2, "fiscal_amarillo"
    elif e["facturado_anual"] > 0 or e["proyeccion_anual"] > 0:
        fiscal = (
            f"Tu semáforo fiscal está en verde: según tu proyección, este año usarías el {pct} % del tope "
            f"de tu categoría {cat}."
        )
        prioridad, regla = 6, "fiscal_verde"

    cuota = None
    if not pago["pagado"] and pago["monto_esperado"]:
        mes_cuota = f"{pago['mes'].lower()} {pago['anio']}"
        if pago["pago_parcial"]:
            registrado = pesos(pago["total_registrado"])
            cuota = (f"El pago registrado de la cuota de {mes_cuota} ({registrado}) no cubre los "
                     f"{pesos(pago['monto_esperado'])} de tu categoría.")
            dato += f" Cuota de {mes_cuota}: {pesos(pago['monto_esperado'])}; registrado {registrado}."
        else:
            cuota = (f"No registramos el pago de la cuota de {mes_cuota} ({pesos(pago['monto_esperado'])}): "
                     f"si ya lo hiciste, te sugerimos cargarlo como gasto de categoría Monotributo.")
            dato += f" Cuota de {mes_cuota}: {pesos(pago['monto_esperado'])}; sin pago registrado."

    if cuota is None and fiscal is None:
        return []
    if cuota is None:
        return [Recomendacion(prioridad, regla, fiscal, dato)]
    if fiscal is None:
        return [Recomendacion(2, "monotributo_cuota", cuota, dato)]
    # Las dos cosas en una sola sugerencia, lo más urgente primero.
    texto = f"{fiscal} {cuota}" if prioridad == 1 else f"{cuota} {fiscal}"
    return [Recomendacion(min(prioridad, 2), f"{regla}+cuota", texto, dato)]


def _regla_tendencia_ingresos(db: Session, usuario_id: int) -> list[Recomendacion]:
    """Compara los últimos meses cerrados con los anteriores (misma serie
    mensual que usa la proyección: meses cerrados, huecos intermedios en $0)."""
    ingresos = db.query(Ingreso).filter(Ingreso.usuario_id == usuario_id).all()
    if not ingresos:
        return [Recomendacion(
            3, "sin_ingresos",
            "Todavía no registraste ingresos. Te sugerimos cargar tus cobros o importar el extracto de tu "
            "banco: con ellos el sistema calcula tu balance, tu proyección y tu estado fiscal.",
            "No hay ingresos registrados.",
        )]

    serie, _, _ = serie_mensual(ingresos)
    if len(serie) < 2:
        return [Recomendacion(
            6, "historial_corto",
            "Te sugerimos registrar tus cobros de cada mes: con al menos dos meses cerrados, el sistema "
            "puede mostrarte la tendencia de tus ingresos.",
            f"Meses cerrados con ingresos: {len(serie)}.",
        )]

    k = min(3, len(serie) // 2)
    recientes, anteriores = serie[-k:], serie[-2 * k:-k]
    prom_rec = statistics.mean(t for _, t in recientes)
    prom_ant = statistics.mean(t for _, t in anteriores)
    if prom_ant == 0:
        return []
    variacion = (prom_rec - prom_ant) / prom_ant
    pct = _porcentaje(round(abs(variacion) * 100, 1))
    meses_rec = _meses([m for m, _ in recientes])
    meses_ant = _meses([m for m, _ in anteriores])
    dato = (
        "Totales mensuales: " + "; ".join(f"{MESES[m.month - 1]} de {m.year} {pesos(t)}" for m, t in anteriores + recientes)
        + f". Promedio de {meses_rec}: {pesos(prom_rec)}; de {meses_ant}: {pesos(prom_ant)}; "
        f"variación {'+' if variacion >= 0 else '−'}{pct} %."
    )

    if variacion <= -UMBRAL_TENDENCIA:
        texto = (
            f"Tus ingresos vienen bajando: en {meses_rec} promediaron {pesos(prom_rec)} por mes, un {pct} % "
            f"menos que en {meses_ant} ({pesos(prom_ant)}). Te sugerimos revisar tus gastos fijos y cuidar tu "
            f"reserva mientras se recupera la facturación."
        )
        return [Recomendacion(2, "ingresos_en_baja", texto, dato)]
    if variacion >= UMBRAL_TENDENCIA:
        texto = (
            f"Tus ingresos vienen creciendo: en {meses_rec} promediaron {pesos(prom_rec)} por mes, un {pct} % "
            f"más que en {meses_ant} ({pesos(prom_ant)}). Si la tendencia se mantiene, conviene seguir de "
            f"cerca tu semáforo fiscal en la sección Monotributo."
        )
        return [Recomendacion(4, "ingresos_en_alza", texto, dato)]
    texto = (
        f"Tus ingresos se mantienen estables: en {meses_rec} promediaron {pesos(prom_rec)} por mes, "
        f"frente a {pesos(prom_ant)} en {meses_ant}."
    )
    return [Recomendacion(6, "ingresos_estables", texto, dato)]


def _regla_resultado(db: Session, usuario_id: int) -> list[Recomendacion]:
    """Superávit o déficit promedio de los últimos meses cerrados. El mes en
    curso no entra: todavía no terminó y bajaría el promedio."""
    mes_actual = inicio_mes_en_curso()
    hasta = mes_actual.replace(tzinfo=timezone.utc)
    desde = (mes_actual - relativedelta(months=MESES_VENTANA_AHORRO)).replace(tzinfo=timezone.utc)

    ingresos = db.query(Ingreso).filter(
        Ingreso.usuario_id == usuario_id, Ingreso.fecha >= desde, Ingreso.fecha < hasta).all()
    gastos = db.query(Gasto).filter(
        Gasto.usuario_id == usuario_id, Gasto.fecha >= desde, Gasto.fecha < hasta).all()
    meses_con_mov = sorted({datetime(x.fecha.year, x.fecha.month, 1) for x in ingresos + gastos})
    if not meses_con_mov:
        return []

    primero = meses_con_mov[0]
    ultimo = mes_actual - relativedelta(months=1)
    n = (ultimo.year - primero.year) * 12 + ultimo.month - primero.month + 1
    # Decimal() también sobre la suma vacía (0 entero): así ingresos y gastos
    # son siempre del mismo tipo y la resta no falla.
    total_ing = Decimal(sum(i.monto for i in ingresos))
    total_gas = Decimal(sum(g.monto for g in gastos))
    prom_ing, prom_gas = total_ing / n, total_gas / n
    saldo = prom_ing - prom_gas
    if n == 1:
        periodo = f"En {_meses([ultimo])}"
    elif primero.year == ultimo.year:
        periodo = f"Entre {MESES[primero.month - 1]} y {MESES[ultimo.month - 1]} de {ultimo.year}"
    else:
        periodo = f"Entre {MESES[primero.month - 1]} de {primero.year} y {MESES[ultimo.month - 1]} de {ultimo.year}"
    dato = (
        f"{_cantidad(n, 'mes cerrado', 'meses cerrados')}: ingresos {pesos(total_ing)} ({pesos(prom_ing)} por mes), "
        f"gastos {pesos(total_gas)} ({pesos(prom_gas)} por mes)."
    )

    if saldo > 0 and n == 1:
        texto = (
            f"{periodo} te quedó un superávit de {pesos(saldo)} (cobraste {pesos(prom_ing)} y gastaste "
            f"{pesos(prom_gas)}). Podrías destinar ese excedente, o una parte, a ahorro o "
            f"inversión en el instrumento que prefieras —por ejemplo plazo fijo, fondos comunes de inversión o "
            f"acciones—, según tu perfil de riesgo."
        )
        return [Recomendacion(4, "resultado_superavit", texto, dato + f" Superávit {pesos(saldo)}.")]
    if saldo > 0:
        texto = (
            f"{periodo} te quedó un superávit promedio de {pesos(saldo)} por mes (cobraste {pesos(prom_ing)} y "
            f"gastaste {pesos(prom_gas)} en promedio). Podrías destinar ese excedente, o una parte, a ahorro o "
            f"inversión en el instrumento que prefieras —por ejemplo plazo fijo, fondos comunes de inversión o "
            f"acciones—, según tu perfil de riesgo."
        )
        return [Recomendacion(4, "resultado_superavit", texto, dato + f" Superávit promedio {pesos(saldo)} por mes.")]
    if saldo < 0:
        por_rubro = {}
        for g in gastos:
            por_rubro[g.categoria] = por_rubro.get(g.categoria, 0) + g.monto
        top = sorted(por_rubro.items(), key=lambda x: x[1], reverse=True)[:2]
        if n == 1:
            resultado = (f"{periodo} gastaste {pesos(prom_gas)} y cobraste {pesos(prom_ing)}: un déficit de "
                         f"{pesos(-saldo)}.")
        else:
            resultado = (f"{periodo} gastaste en promedio {pesos(prom_gas)} por mes y cobraste {pesos(prom_ing)}: "
                         f"un déficit de {pesos(-saldo)} por mes.")
        texto = (
            f"{resultado} Te sugerimos revisar tus rubros de mayor gasto ({_lista([c for c, _ in top])}) "
            f"para equilibrar tus números."
        )
        dato += (f" Déficit promedio {pesos(-saldo)} por mes. Rubros de mayor gasto: "
                 + "; ".join(f"{c} {pesos(t)}" for c, t in top) + ".")
        return [Recomendacion(2, "resultado_deficit", texto, dato)]
    return []


def _regla_aumento_gastos(db: Session, usuario_id: int) -> list[Recomendacion]:
    """Rubros cuyo gasto del mes en curso ya supera en 30 % o más al del mes
    anterior completo (si ya lo supera a mitad de mes, el aumento es real)."""
    actual = inicio_mes_en_curso()
    anterior = actual - relativedelta(months=1)

    def por_categoria(mes: datetime) -> dict:
        filas = db.query(Gasto.categoria, func.sum(Gasto.monto)).filter(
            Gasto.usuario_id == usuario_id,
            extract("month", Gasto.fecha) == mes.month,
            extract("year", Gasto.fecha) == mes.year,
        ).group_by(Gasto.categoria).all()
        return {c: t for c, t in filas}

    este, previo = por_categoria(actual), por_categoria(anterior)
    aumentos = []
    for cat, total in este.items():
        base = previo.get(cat, 0)
        if base > 0 and (total - base) / base >= UMBRAL_AUMENTO_GASTO:
            aumentos.append((cat, total, base, float((total - base) / base * 100)))
    if not aumentos:
        return []
    aumentos.sort(key=lambda x: (-x[3], x[0]))
    aumentos = aumentos[:3]
    texto = (
        f"Este mes tus gastos ya superan a los de {MESES[anterior.month - 1]} en "
        + _lista([f"{c} (+{_porcentaje(round(p))} %)" for c, _, _, p in aumentos])
        + ". Te sugerimos revisar si son gastos necesarios o puntuales."
    )
    dato = "; ".join(
        f"{c}: {pesos(t)} en {MESES[actual.month - 1]} contra {pesos(b)} en {MESES[anterior.month - 1]}"
        for c, t, b, _ in aumentos
    ) + "."
    return [Recomendacion(5, "gastos_en_aumento", texto, dato)]


ETIQUETAS_ALERTA = {
    TipoAlerta.GASTO_DUPLICADO: ("posible gasto duplicado", "posibles gastos duplicados"),
    TipoAlerta.ANOMALIA_ESTADISTICA: ("gasto inusualmente alto", "gastos inusualmente altos"),
    TipoAlerta.TRANSFERENCIA_PROPIA: ("posible transferencia entre tus cuentas", "posibles transferencias entre tus cuentas"),
}
# Las de facturas vencidas y monotributo impago no se cuentan acá: ya tienen
# su propia recomendación y se repetirían.
TIPOS_CON_REGLA_PROPIA = {TipoAlerta.DISCREPANCIA_FACTURACION, TipoAlerta.MONOTRIBUTO_IMPAGO}


def _regla_alertas(db: Session, usuario_id: int) -> list[Recomendacion]:
    alertas = db.query(AlertaAuditoria).filter(
        AlertaAuditoria.usuario_id == usuario_id,
        AlertaAuditoria.resuelta == False,
    ).all()
    alertas = [a for a in alertas if a.tipo not in TIPOS_CON_REGLA_PROPIA]
    if not alertas:
        return []

    por_tipo: dict = {}
    for a in alertas:
        por_tipo[a.tipo] = por_tipo.get(a.tipo, 0) + 1
    partes = []
    for tipo, n in sorted(por_tipo.items(), key=lambda x: (-x[1], x[0].value)):
        singular, plural = ETIQUETAS_ALERTA.get(tipo, ("alerta", "alertas"))
        partes.append(_cantidad(n, singular, plural))
    distorsionan = por_tipo.keys() & {TipoAlerta.GASTO_DUPLICADO, TipoAlerta.TRANSFERENCIA_PROPIA}
    texto = (
        f"La auditoría detectó {_lista(partes)} sin revisar. Te sugerimos revisarlas en la sección Auditoría"
        + (": un duplicado o una transferencia entre tus cuentas distorsionan tus totales y tu estado fiscal."
           if distorsionan else ".")
    )
    dato = (f"{_cantidad(len(alertas), 'alerta pendiente', 'alertas pendientes')}: {_lista(partes)} "
            f"(las de facturas y monotributo tienen su propia recomendación).")
    return [Recomendacion(3, "alertas_auditoria", texto, dato)]


def _regla_uso(db: Session, usuario_id: int) -> list[Recomendacion]:
    """Pasos de uso de la app según lo que falta cargar. No diagnostican nada:
    solo se agregan si hace falta llegar al mínimo de 3."""
    n_ing = db.query(func.count(Ingreso.id)).filter(Ingreso.usuario_id == usuario_id).scalar()
    n_gas = db.query(func.count(Gasto.id)).filter(Gasto.usuario_id == usuario_id).scalar()
    recs = []
    if n_gas == 0:
        recs.append(Recomendacion(
            4, "sin_gastos",
            "Todavía no registraste gastos. Te sugerimos cargarlos o importarlos desde el extracto para ver en "
            "qué se va tu dinero y detectar duplicados o montos inusuales.",
            "No hay gastos registrados.",
        ))
    if n_ing + n_gas > 0:
        recs.append(Recomendacion(
            7, "auditoria_periodica",
            "Te sugerimos ejecutar la auditoría después de cada importación de extractos: detecta gastos "
            "duplicados, montos inusuales y transferencias entre tus cuentas.",
            f"Sugerencia de uso: hay {_cantidad(n_ing + n_gas, 'movimiento registrado', 'movimientos registrados')}.",
        ))
    recs.append(Recomendacion(
        8, "registrar_movimientos",
        "Te sugerimos registrar tus movimientos a medida que ocurren: cuanto más completos estén tus datos, "
        "más precisas son la proyección y estas recomendaciones.",
        f"Sugerencia de uso: hay {_cantidad(n_ing + n_gas, 'movimiento registrado', 'movimientos registrados')}.",
    ))
    return recs


REGLAS = [
    _regla_cobros,
    _regla_tendencia_ingresos,
    _regla_monotributo,
    _regla_resultado,
    _regla_alertas,
    _regla_aumento_gastos,
    _regla_uso,
]
# El orden de la lista desempata recomendaciones de igual prioridad.


def generar_recomendaciones(usuario_id: int, db: Session) -> dict:
    candidatas = [r for regla in REGLAS for r in regla(db, usuario_id)]
    orden = {id(r): i for i, r in enumerate(candidatas)}
    candidatas.sort(key=lambda r: (r.prioridad, orden[id(r)]))

    elegidas = [r for r in candidatas if r.prioridad <= PRIORIDAD_MAX_PRINCIPAL][:MAX_RECOMENDACIONES]
    for r in candidatas:
        if len(elegidas) >= MIN_RECOMENDACIONES:
            break
        if r.prioridad > PRIORIDAD_MAX_PRINCIPAL:
            elegidas.append(r)

    return {
        # lista de textos: la usan la pantalla y la tarjeta del Dashboard
        "recomendaciones": [r.texto for r in elegidas],
        # la misma lista con la regla, la prioridad y el dato que la disparó
        "detalle": [asdict(r) for r in elegidas],
        "generado_con_ia": False,
    }
