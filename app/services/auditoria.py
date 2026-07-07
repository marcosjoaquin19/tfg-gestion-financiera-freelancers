"""
Servicio de Auditoría — detección de inconsistencias y anomalías.

Contiene la lógica que recorre los datos del usuario y genera alertas. Detecta
gastos duplicados, montos atípicos (anomalías estadísticas), facturas impagas,
monotributo sin pagar y riesgo de recategorización. Lo usa el router de alertas:
ejecutar_auditoria() corre todas las reglas y persiste las alertas encontradas.
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models.gasto import Gasto
from app.models.ingreso import Ingreso
from app.models.factura import Factura, EstadoFactura
from app.models.alerta_auditoria import AlertaAuditoria, TipoAlerta
from app.services.monotributo_service import verificar_pago_monotributo
from app.services.formato import formato_pesos_ar
import statistics


# -------------------------------------------------------------------
# CONSTANTES DE CONFIGURACIÓN
# -------------------------------------------------------------------
VENTANA_DUPLICADOS_DIAS = 3

MESES_VENTANA = 6
# solo analizamos los últimos 6 meses para mantener la detección relevante y eficiente
# dos gastos se consideran duplicados si tienen mismo monto y categoría
# y fueron registrados con menos de 3 días de diferencia

UMBRAL_ANOMALIA_DESVIACIONES = 2.0
# un gasto es anómalo si supera la media de su categoría en más de 2 desviaciones estándar
# equivale a estar en el top ~2.5% de gastos para esa categoría

MIN_GASTOS_PARA_ESTADISTICA = 5
# necesitamos al menos 5 gastos por categoría para que la estadística sea significativa
# con menos datos la desviación estándar no es confiable


# -------------------------------------------------------------------
# FUNCIÓN AUXILIAR
# -------------------------------------------------------------------
def _crear_alerta(
    usuario_id: int,
    tipo: TipoAlerta,
    descripcion: str,
    monto: float | None = None,
    gasto_id_duplicado: int | None = None,
    ingreso_id_relacionado: int | None = None,
) -> AlertaAuditoria:
    return AlertaAuditoria(
        usuario_id=usuario_id,
        tipo=tipo,
        descripcion=descripcion,
        monto_involucrado=monto,
        gasto_id_duplicado=gasto_id_duplicado,
        ingreso_id_relacionado=ingreso_id_relacionado,
    )


def _huella_alerta(tipo: TipoAlerta, monto) -> tuple:
    """Identidad de una condición, para no regenerar alertas que el usuario
    ya marcó como resueltas. Usamos (tipo, monto) porque es estable entre
    corridas (la descripción de algunas alertas varía: promedios, desviaciones)."""
    monto_norm = round(float(monto), 2) if monto is not None else None
    return (tipo, monto_norm)


# -------------------------------------------------------------------
# DETECTOR 1: GASTOS DUPLICADOS
# Busca gastos con mismo monto y categoría dentro de la ventana de días
# -------------------------------------------------------------------
def detectar_gastos_duplicados(db: Session, usuario_id: int) -> list[tuple[Gasto, Gasto]]:
    fecha_limite = datetime.now(timezone.utc) - timedelta(days=MESES_VENTANA * 30)
    gastos = (
        db.query(Gasto)
        .filter(Gasto.usuario_id == usuario_id, Gasto.fecha >= fecha_limite)
        .order_by(Gasto.fecha.asc())
        .all()
    )

    duplicados = []
    for i, gasto_a in enumerate(gastos):
        for gasto_b in gastos[i + 1:]:
            fecha_a = gasto_a.fecha.replace(tzinfo=None) if gasto_a.fecha.tzinfo else gasto_a.fecha
            fecha_b = gasto_b.fecha.replace(tzinfo=None) if gasto_b.fecha.tzinfo else gasto_b.fecha
            # normalizamos a naive para poder comparar sin importar el timezone guardado

            diferencia_dias = abs((fecha_b - fecha_a).total_seconds()) / 86400

            if diferencia_dias > VENTANA_DUPLICADOS_DIAS:
                # como están ordenados por fecha, si superamos la ventana podemos cortar
                break

            if gasto_a.monto == gasto_b.monto and gasto_a.categoria == gasto_b.categoria:
                duplicados.append((gasto_a, gasto_b))

    return duplicados


# -------------------------------------------------------------------
# DETECTOR 2: ANOMALÍAS ESTADÍSTICAS
# Detecta gastos inusualmente altos comparados al promedio de su categoría
# -------------------------------------------------------------------
def detectar_anomalias_estadisticas(db: Session, usuario_id: int) -> list[tuple[Gasto, float, float]]:
    fecha_limite = datetime.now(timezone.utc) - timedelta(days=MESES_VENTANA * 30)
    gastos = db.query(Gasto).filter(
        Gasto.usuario_id == usuario_id,
        Gasto.fecha >= fecha_limite,
    ).all()

    # agrupamos los gastos por categoría
    por_categoria: dict[str, list[Gasto]] = {}
    for gasto in gastos:
        por_categoria.setdefault(gasto.categoria, []).append(gasto)

    anomalias = []
    for categoria, lista in por_categoria.items():
        if len(lista) < MIN_GASTOS_PARA_ESTADISTICA:
            # con pocos datos no podemos hacer estadística confiable
            continue

        montos = [g.monto for g in lista]
        media = statistics.mean(montos)
        desviacion = statistics.stdev(montos)

        if desviacion == 0:
            # todos los gastos tienen el mismo monto, ninguno es anómalo
            continue

        for gasto in lista:
            z_score = (gasto.monto - media) / desviacion
            # z_score → cuántas desviaciones estándar está el gasto por encima de la media
            if z_score > UMBRAL_ANOMALIA_DESVIACIONES:
                anomalias.append((gasto, media, desviacion))

    return anomalias


# -------------------------------------------------------------------
# DETECTOR 3: DISCREPANCIAS DE FACTURACIÓN
# Detecta facturas que vencieron sin ser cobradas
# -------------------------------------------------------------------
def detectar_discrepancias_facturacion(db: Session, usuario_id: int) -> list[Factura]:
    ahora = datetime.now(timezone.utc)

    facturas_vencidas = (
        db.query(Factura)
        .filter(
            Factura.usuario_id == usuario_id,
            Factura.estado == EstadoFactura.PENDIENTE,
            Factura.fecha_vencimiento < ahora,
            # pendiente + fecha de vencimiento pasada = no se cobró a tiempo
        )
        .all()
    )

    return facturas_vencidas


# -------------------------------------------------------------------
# DETECTOR 5: TRANSFERENCIAS ENTRE CUENTAS PROPIAS
# Un freelancer con varias cuentas (banco + Mercado Pago + billeteras) que
# importa los extractos de todas ve cada transferencia entre sus cuentas como
# un gasto en un extracto Y un ingreso en el otro. Ese "ingreso" no es
# facturación real e infla el cálculo del límite anual de Monotributo.
# -------------------------------------------------------------------
def detectar_transferencias_propias(db: Session, usuario_id: int) -> list[tuple[Ingreso, Gasto]]:
    """Empareja ingresos y gastos que parecen las dos patas de una transferencia.

    Criterio: mismo monto exacto, fechas a ≤1 día y vocabulario de
    transferencia en al menos una de las descripciones (mismo guardia que usa
    la importación, ver csv_service.es_descripcion_transferencia). El
    emparejamiento es voraz: cada gasto participa de un solo par.
    """
    from app.services.csv_service import es_descripcion_transferencia

    fecha_limite = datetime.now(timezone.utc) - timedelta(days=MESES_VENTANA * 30)
    ingresos = db.query(Ingreso).filter(
        Ingreso.usuario_id == usuario_id, Ingreso.fecha >= fecha_limite,
    ).order_by(Ingreso.fecha.asc()).all()
    gastos = db.query(Gasto).filter(
        Gasto.usuario_id == usuario_id, Gasto.fecha >= fecha_limite,
    ).order_by(Gasto.fecha.asc()).all()

    pares: list[tuple[Ingreso, Gasto]] = []
    gastos_usados: set[int] = set()

    for ingreso in ingresos:
        fecha_ing = ingreso.fecha.replace(tzinfo=None) if ingreso.fecha.tzinfo else ingreso.fecha
        for gasto in gastos:
            if gasto.id in gastos_usados:
                continue
            if gasto.monto != ingreso.monto:
                continue
            fecha_gas = gasto.fecha.replace(tzinfo=None) if gasto.fecha.tzinfo else gasto.fecha
            if abs((fecha_gas - fecha_ing).days) > 1:
                continue
            if not (
                es_descripcion_transferencia(ingreso.descripcion)
                or es_descripcion_transferencia(gasto.descripcion)
            ):
                continue
            pares.append((ingreso, gasto))
            gastos_usados.add(gasto.id)
            break

    return pares


# -------------------------------------------------------------------
# FUNCIÓN PRINCIPAL
# Ejecuta los detectores y guarda las alertas en la BD
# -------------------------------------------------------------------
def ejecutar_auditoria(db: Session, usuario_id: int) -> dict:
    # Borramos las alertas no resueltas antes de regenerarlas
    # así evitamos duplicar alertas si la auditoría se corre múltiples veces
    db.query(AlertaAuditoria).filter(
        AlertaAuditoria.usuario_id == usuario_id,
        AlertaAuditoria.resuelta == False,
    ).delete()

    # Huellas de las alertas YA RESUELTAS: una condición que el usuario marcó
    # como resuelta NO se vuelve a generar aunque siga existiendo. Así "Resolver"
    # es efectivo y no reaparece la misma alerta al re-ejecutar la auditoría.
    resueltas = db.query(AlertaAuditoria).filter(
        AlertaAuditoria.usuario_id == usuario_id,
        AlertaAuditoria.resuelta == True,
    ).all()
    huellas_resueltas = {_huella_alerta(a.tipo, a.monto_involucrado) for a in resueltas}

    conteo = {
        "gastos_duplicados": 0, "anomalias": 0, "discrepancias": 0,
        "monotributo_impago": 0, "transferencias_propias": 0,
    }
    alertas: list[AlertaAuditoria] = []

    # --- DETECTOR 1: duplicados ---
    duplicados = detectar_gastos_duplicados(db, usuario_id)
    ids_marcados: set[int] = set()

    for gasto_a, gasto_b in duplicados:
        # marcamos ambos gastos como duplicados en la tabla gastos
        for g in (gasto_a, gasto_b):
            if g.id not in ids_marcados:
                g.es_duplicado = True
                ids_marcados.add(g.id)

        if _huella_alerta(TipoAlerta.GASTO_DUPLICADO, gasto_a.monto) in huellas_resueltas:
            continue  # el usuario ya resolvió esta condición → no repetir

        alertas.append(_crear_alerta(
            usuario_id,
            TipoAlerta.GASTO_DUPLICADO,
            f"Posible gasto duplicado: {formato_pesos_ar(gasto_a.monto)} en '{gasto_a.categoria}' "
            f"registrado el {gasto_a.fecha.date()} y el {gasto_b.fecha.date()}",
            monto=gasto_a.monto,
            # referencia directa al gasto repetido (el más reciente del par):
            # permite que "eliminar duplicado" borre exactamente este gasto,
            # sin ambigüedad si otro par comparte el mismo monto.
            gasto_id_duplicado=gasto_b.id,
        ))
        conteo["gastos_duplicados"] += 1

    # --- DETECTOR 2: anomalías ---
    anomalias = detectar_anomalias_estadisticas(db, usuario_id)

    for gasto, media, desviacion in anomalias:
        if _huella_alerta(TipoAlerta.ANOMALIA_ESTADISTICA, gasto.monto) in huellas_resueltas:
            continue
        alertas.append(_crear_alerta(
            usuario_id,
            TipoAlerta.ANOMALIA_ESTADISTICA,
            f"Gasto inusualmente alto: {formato_pesos_ar(gasto.monto)} en '{gasto.categoria}' "
            f"(promedio de la categoría: {formato_pesos_ar(media)}, desviación: {formato_pesos_ar(desviacion)})",
            monto=gasto.monto,
        ))
        conteo["anomalias"] += 1

    # --- DETECTOR 3: discrepancias ---
    facturas_vencidas = detectar_discrepancias_facturacion(db, usuario_id)

    for factura in facturas_vencidas:
        if _huella_alerta(TipoAlerta.DISCREPANCIA_FACTURACION, factura.monto) in huellas_resueltas:
            continue
        alertas.append(_crear_alerta(
            usuario_id,
            TipoAlerta.DISCREPANCIA_FACTURACION,
            f"Factura vencida sin cobrar: {formato_pesos_ar(factura.monto)} a '{factura.cliente_nombre}' "
            f"(venció el {factura.fecha_vencimiento.date()})",
            monto=factura.monto,
        ))
        conteo["discrepancias"] += 1

    # --- DETECTOR 4: monotributo impago ---
    mono_count, alerta_mono = detectar_monotributo_impago(db, usuario_id)
    if alerta_mono and _huella_alerta(TipoAlerta.MONOTRIBUTO_IMPAGO, alerta_mono.monto_involucrado) not in huellas_resueltas:
        conteo["monotributo_impago"] = mono_count
        alertas.append(alerta_mono)

    # --- DETECTOR 5: transferencias entre cuentas propias ---
    transferencias = detectar_transferencias_propias(db, usuario_id)

    for ingreso, gasto in transferencias:
        if _huella_alerta(TipoAlerta.TRANSFERENCIA_PROPIA, ingreso.monto) in huellas_resueltas:
            continue
        alertas.append(_crear_alerta(
            usuario_id,
            TipoAlerta.TRANSFERENCIA_PROPIA,
            f"Posible transferencia entre cuentas propias: {formato_pesos_ar(ingreso.monto)} "
            f"ingresó el {ingreso.fecha.date()} ('{ingreso.descripcion[:60]}') y salió el "
            f"{gasto.fecha.date()} ('{gasto.descripcion[:60]}'). Si es un movimiento entre tus "
            f"cuentas, no representa facturación real: descartalo para no inflar tu monotributo.",
            monto=ingreso.monto,
            gasto_id_duplicado=gasto.id,
            ingreso_id_relacionado=ingreso.id,
        ))
        conteo["transferencias_propias"] += 1

    db.add_all(alertas)
    db.commit()
    return conteo


def detectar_monotributo_impago(db: Session, usuario_id: int) -> tuple:
    estado = verificar_pago_monotributo(db, usuario_id)
    if not estado["pagado"] and estado["monto_esperado"] is not None:
        detalle = (
            f"No se registró el pago del monotributo de {estado['mes']} {estado['anio']}. "
            f"Cuota esperada: {formato_pesos_ar(estado['monto_esperado'], decimales=0)}"
        )
        # Si hubo un registro que no llega a cubrir la cuota, lo aclaramos:
        # ayuda a distinguir "me olvidé de pagar" de "pagué de menos".
        if estado.get("pago_parcial") and estado.get("gasto_encontrado"):
            detalle += (
                f". Se encontró un registro de {formato_pesos_ar(estado['gasto_encontrado']['monto'], decimales=0)} "
                f"que no cubre la cuota"
            )
        alerta = _crear_alerta(
            usuario_id,
            TipoAlerta.MONOTRIBUTO_IMPAGO,
            detalle,
            monto=estado["monto_esperado"],
        )
        return 1, alerta
    return 0, None
