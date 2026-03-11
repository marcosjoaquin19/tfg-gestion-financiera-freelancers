from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.gasto import Gasto
from app.models.factura import Factura, EstadoFactura
from app.models.alerta_auditoria import AlertaAuditoria, TipoAlerta
import statistics


# -------------------------------------------------------------------
# CONSTANTES DE CONFIGURACIÓN
# -------------------------------------------------------------------
VENTANA_DUPLICADOS_DIAS = 3
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
    db: Session,
    usuario_id: int,
    tipo: TipoAlerta,
    descripcion: str,
    monto: float | None = None,
) -> None:
    alerta = AlertaAuditoria(
        usuario_id=usuario_id,
        tipo=tipo,
        descripcion=descripcion,
        monto_involucrado=monto,
    )
    db.add(alerta)


# -------------------------------------------------------------------
# DETECTOR 1: GASTOS DUPLICADOS
# Busca gastos con mismo monto y categoría dentro de la ventana de días
# -------------------------------------------------------------------
def detectar_gastos_duplicados(db: Session, usuario_id: int) -> list[tuple[Gasto, Gasto]]:
    gastos = (
        db.query(Gasto)
        .filter(Gasto.usuario_id == usuario_id)
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
    gastos = db.query(Gasto).filter(Gasto.usuario_id == usuario_id).all()

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
# FUNCIÓN PRINCIPAL
# Ejecuta los tres detectores y guarda las alertas en la BD
# -------------------------------------------------------------------
def ejecutar_auditoria(db: Session, usuario_id: int) -> dict:
    # Borramos las alertas no resueltas antes de regenerarlas
    # así evitamos duplicar alertas si la auditoría se corre múltiples veces
    db.query(AlertaAuditoria).filter(
        AlertaAuditoria.usuario_id == usuario_id,
        AlertaAuditoria.resuelta == False,
    ).delete()

    conteo = {"gastos_duplicados": 0, "anomalias": 0, "discrepancias": 0}

    # --- DETECTOR 1: duplicados ---
    duplicados = detectar_gastos_duplicados(db, usuario_id)
    ids_marcados: set[int] = set()

    for gasto_a, gasto_b in duplicados:
        # marcamos ambos gastos como duplicados en la tabla gastos
        for g in (gasto_a, gasto_b):
            if g.id not in ids_marcados:
                g.es_duplicado = True
                ids_marcados.add(g.id)

        _crear_alerta(
            db,
            usuario_id,
            TipoAlerta.GASTO_DUPLICADO,
            f"Posible gasto duplicado: ${gasto_a.monto:.2f} en '{gasto_a.categoria}' "
            f"registrado el {gasto_a.fecha.date()} y el {gasto_b.fecha.date()}",
            monto=gasto_a.monto,
        )
        conteo["gastos_duplicados"] += 1

    # --- DETECTOR 2: anomalías ---
    anomalias = detectar_anomalias_estadisticas(db, usuario_id)

    for gasto, media, desviacion in anomalias:
        _crear_alerta(
            db,
            usuario_id,
            TipoAlerta.ANOMALIA_ESTADISTICA,
            f"Gasto inusualmente alto: ${gasto.monto:.2f} en '{gasto.categoria}' "
            f"(promedio de la categoría: ${media:.2f}, desviación: ${desviacion:.2f})",
            monto=gasto.monto,
        )
        conteo["anomalias"] += 1

    # --- DETECTOR 3: discrepancias ---
    facturas_vencidas = detectar_discrepancias_facturacion(db, usuario_id)

    for factura in facturas_vencidas:
        _crear_alerta(
            db,
            usuario_id,
            TipoAlerta.DISCREPANCIA_FACTURACION,
            f"Factura vencida sin cobrar: ${factura.monto:.2f} a '{factura.cliente_nombre}' "
            f"(venció el {factura.fecha_vencimiento.date()})",
            monto=factura.monto,
        )
        conteo["discrepancias"] += 1

    db.commit()
    return conteo
