"""
Servicio de Auditoría — detección de inconsistencias y anomalías.

Contiene la lógica que recorre los datos del usuario y genera alertas. Tiene
cinco detectores:
  1. gastos duplicados (mismo monto y categoría con 3 días o menos de diferencia);
  2. anomalías estadísticas (un gasto mucho más alto que lo normal en su categoría);
  3. discrepancias de facturación (facturas vencidas sin cobrar);
  4. monotributo impago (la cuota del mes no está cubierta);
  5. transferencias entre cuentas propias (un ingreso y un gasto que son la
     misma plata pasando de una cuenta del usuario a otra).
Lo usa la ruta /alertas (pantalla Auditoría): ejecutar_auditoria() corre los
cinco detectores y guarda las alertas encontradas.

Son reglas fijas y explicables, no un modelo de IA: cada alerta dice qué dato
la disparó, y el usuario decide si la resuelve.
"""

# PATRÓN: Strategy — cada detector es una función independiente con la misma firma; ejecutar_auditoria() las orquesta.
# PATRÓN: Factory Method — _crear_alerta() centraliza la construcción de alertas
#         (todas se arman en un solo lugar, así ninguna queda con un campo de menos).
# PATRÓN: Idempotencia por huella — _huella_alerta() evita regenerar alertas ya resueltas por el usuario.
#         (Idempotente = correr la auditoría dos veces da el mismo resultado que una.)
# Justificación y alternativas descartadas: defensa_final/02_ARQUITECTURA_Y_PATRONES.md

from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models.gasto import Gasto
from app.models.ingreso import Ingreso
from app.models.factura import Factura, EstadoFactura
from app.services.facturas_estado import inicio_de_hoy, marcar_vencidas
from app.models.alerta_auditoria import AlertaAuditoria, TipoAlerta
from app.services.monotributo_service import verificar_pago_monotributo
from app.services.formato import formato_fecha_ar, formato_pesos_ar
import statistics


# -------------------------------------------------------------------
# CONSTANTES DE CONFIGURACIÓN
# -------------------------------------------------------------------
VENTANA_DUPLICADOS_DIAS = 3
# Dos gastos se consideran duplicados si tienen el mismo monto y la misma
# categoría y sus fechas están a 3 días o menos. Dos cobros iguales separados
# por más tiempo son, por lo general, cuotas o abonos mensuales, no un error.

MESES_VENTANA = 6
# Solo analizamos los últimos 6 meses (6 × 30 = 180 días) para que la
# detección sea relevante y rápida: un duplicado de hace un año ya no se corrige.

UMBRAL_ANOMALIA_DESVIACIONES = 2.0
# Un gasto es anómalo si supera el promedio de su categoría en más de 2
# desviaciones estándar. La desviación estándar mide cuánto se alejan, en
# general, los gastos del promedio. Regla estadística clásica: en datos
# "normales" casi todo (alrededor de 95 de cada 100) cae a menos de 2
# desviaciones del promedio, así que lo que queda por encima (~2,5 %) llama la atención.

MIN_GASTOS_PARA_ESTADISTICA = 5
# Necesitamos al menos 5 gastos por categoría (la tesis dice "al menos cinco"):
# con menos datos, el promedio y la desviación no son confiables.
# Dato fino: con exactamente 5 gastos ningún gasto puede quedar a más de 1,79
# desviaciones (es el máximo matemático para 5 datos: (n-1)/√n), así que en la
# práctica la primera anomalía puede aparecer desde el sexto gasto.


# A qué contador del resumen suma cada tipo de alerta (el resumen es lo que
# muestra la pantalla Auditoría después de correrla: "2 duplicados, 1 anomalía...").
CLAVE_CONTEO = {
    TipoAlerta.GASTO_DUPLICADO: "gastos_duplicados",
    TipoAlerta.ANOMALIA_ESTADISTICA: "anomalias",
    TipoAlerta.DISCREPANCIA_FACTURACION: "discrepancias",
    TipoAlerta.MONOTRIBUTO_IMPAGO: "monotributo_impago",
    TipoAlerta.TRANSFERENCIA_PROPIA: "transferencias_propias",
}


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
    """Arma una alerta (todavía sin guardar) con los datos que la identifican.

    gasto_id_duplicado e ingreso_id_relacionado apuntan a los registros
    involucrados, para que las acciones de la pantalla ("eliminar duplicado",
    "descartar transferencia") sepan exactamente sobre cuál actuar.
    """
    return AlertaAuditoria(
        usuario_id=usuario_id,
        tipo=tipo,
        descripcion=descripcion,
        monto_involucrado=monto,
        gasto_id_duplicado=gasto_id_duplicado,
        ingreso_id_relacionado=ingreso_id_relacionado,
    )


def _huella_alerta(alerta: AlertaAuditoria) -> tuple:
    """Identidad de la condición concreta que marca una alerta, para no
    regenerar las que el usuario ya resolvió.

    Tiene que distinguir situaciones distintas: con solo (tipo, monto), resolver
    un duplicado de $5.000 en Software silenciaba cualquier otro duplicado de
    $5.000, y resolver el monotributo de un mes silenciaba todos los siguientes
    (la cuota es la misma). Por eso:
      - anomalía: el gasto señalado (su descripción varía entre corridas porque
        incluye el promedio y la desviación de la categoría);
      - el resto: los registros referenciados más la descripción, que es estable
        y ya nombra fechas, categoría, cliente o mes según el tipo.
    """
    if alerta.tipo == TipoAlerta.ANOMALIA_ESTADISTICA:
        return (alerta.tipo, alerta.gasto_id_duplicado)
    return (
        alerta.tipo,
        alerta.gasto_id_duplicado,
        alerta.ingreso_id_relacionado,
        alerta.descripcion,
    )


# -------------------------------------------------------------------
# DETECTOR 1: GASTOS DUPLICADOS
# Busca gastos con mismo monto y categoría dentro de la ventana de días
# -------------------------------------------------------------------
def detectar_gastos_duplicados(db: Session, usuario_id: int) -> list[tuple[Gasto, Gasto]]:
    """Devuelve los pares de gastos que parecen cargados dos veces.

    Regla: mismo monto, misma categoría y 3 días o menos de diferencia. Se
    comparan los gastos de a pares, ordenados por fecha: para cada gasto se
    miran solo los siguientes y se deja de mirar apenas uno queda a más de 3
    días (como están ordenados, los que siguen están todavía más lejos).

    Es la misma regla que se aplica al cargar cada gasto (duplicados_gasto.py);
    acá se repasa todo junto y, además, se genera la alerta.
    """
    fecha_limite = datetime.now(timezone.utc) - timedelta(days=MESES_VENTANA * 30)
    gastos = (
        db.query(Gasto)
        .filter(Gasto.usuario_id == usuario_id, Gasto.fecha >= fecha_limite)
        .order_by(Gasto.fecha.asc())
        .all()
    )

    duplicados = []
    for i, gasto_a in enumerate(gastos):
        for gasto_b in gastos[i + 1:]:   # solo los gastos posteriores a gasto_a
            # Les quitamos la zona horaria a las dos fechas para poder restarlas:
            # Python no deja comparar una fecha con zona y otra sin zona.
            fecha_a = gasto_a.fecha.replace(tzinfo=None) if gasto_a.fecha.tzinfo else gasto_a.fecha
            fecha_b = gasto_b.fecha.replace(tzinfo=None) if gasto_b.fecha.tzinfo else gasto_b.fecha

            # Diferencia en días (86.400 segundos = 1 día).
            diferencia_dias = abs((fecha_b - fecha_a).total_seconds()) / 86400

            if diferencia_dias > VENTANA_DUPLICADOS_DIAS:
                # Como están ordenados por fecha, si este ya quedó fuera de la
                # ventana, los siguientes también: cortamos y pasamos al próximo gasto_a.
                break

            if gasto_a.monto == gasto_b.monto and gasto_a.categoria == gasto_b.categoria:
                duplicados.append((gasto_a, gasto_b))

    return duplicados


# -------------------------------------------------------------------
# DETECTOR 2: ANOMALÍAS ESTADÍSTICAS
# Detecta gastos inusualmente altos comparados al promedio de su categoría
# -------------------------------------------------------------------
def detectar_anomalias_estadisticas(db: Session, usuario_id: int) -> list[tuple[Gasto, float, float]]:
    """Devuelve los gastos inusualmente altos para su categoría (puntaje z > 2).

    El puntaje z dice a cuántas desviaciones estándar está un gasto del
    promedio de su categoría:  z = (monto - promedio) / desviación.
    Ejemplo: en Software el promedio es $10.000 y la desviación $2.000; un gasto
    de $15.000 tiene z = (15.000 - 10.000) / 2.000 = 2,5 → es anomalía.

    Cada categoría se compara solo consigo misma: $50.000 puede ser normal en
    Hardware y rarísimo en Transporte. Solo se marcan los gastos ALTOS (z
    positivo): gastar menos de lo habitual no es un problema a revisar.

    Devuelve (gasto, promedio, desviación) para poder explicarlo en la alerta.
    """
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
        media = statistics.mean(montos)        # promedio de la categoría
        desviacion = statistics.stdev(montos)  # desviación estándar de la categoría

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
    """Devuelve las facturas cuyo vencimiento ya pasó y siguen sin cobrarse.

    "Discrepancia" porque hay una diferencia entre lo facturado y lo cobrado:
    se emitió la factura, venció, y la plata no está registrada como cobrada.
    """
    # Primero se actualiza el estado: las pendientes con vencimiento pasado
    # pasan a "vencida" (ver facturas_estado.py).
    marcar_vencidas(db, usuario_id)

    facturas_vencidas = (
        db.query(Factura)
        .filter(
            Factura.usuario_id == usuario_id,
            # marcar_vencidas() ya pasó a VENCIDA las pendientes atrasadas;
            # se mantienen los dos estados en el filtro por robustez: en
            # ambos casos la factura sigue sin cobrarse.
            Factura.estado.in_([EstadoFactura.PENDIENTE, EstadoFactura.VENCIDA]),
            Factura.fecha_vencimiento < inicio_de_hoy(),
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
    transferencia ("transf", "enviaste", "recibiste", "cuenta propia", etc.) en al menos una de las
    descripciones; es el mismo control que usa la importación (ver
    csv_service.es_descripcion_transferencia). El emparejamiento es "voraz":
    para cada ingreso se toma el primer gasto que cumple y ese gasto ya no
    se ofrece a otro ingreso, así cada gasto participa de un solo par.

    Ejemplo: sale $200.000 de Galicia el 3/9 ("TRANSF A MERCADO PAGO") y entran
    $200.000 en Mercado Pago el 3/9 → un par: no es facturación nueva.
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

    # Para cada ingreso se busca un gasto que cumpla las tres condiciones; cada
    # "continue" descarta el gasto y pasa al siguiente.
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
            # Cumple todo: es un par. El gasto queda usado y se pasa al próximo ingreso.
            pares.append((ingreso, gasto))
            gastos_usados.add(gasto.id)
            break

    return pares


# -------------------------------------------------------------------
# FUNCIÓN PRINCIPAL
# Ejecuta los detectores y guarda las alertas en la BD
# -------------------------------------------------------------------
def ejecutar_auditoria(db: Session, usuario_id: int) -> dict:
    """Corre los cinco detectores, guarda las alertas y devuelve cuántas hubo de cada tipo.

    La llama el botón "Ejecutar auditoría" (POST /alertas/ejecutar-auditoria). Pasos:
      1. Borra las alertas pendientes anteriores (se vuelven a calcular de cero).
      2. Anota las "huellas" de las alertas que el usuario ya resolvió.
      3. Corre los cinco detectores y arma una alerta por cada hallazgo.
      4. Descarta las que coinciden con una huella resuelta (no se repiten).
      5. Guarda las que quedan y devuelve el conteo por tipo.
    """
    # Paso 1: borramos las alertas no resueltas antes de regenerarlas; así no
    # se duplican alertas si la auditoría se corre varias veces.
    db.query(AlertaAuditoria).filter(
        AlertaAuditoria.usuario_id == usuario_id,
        AlertaAuditoria.resuelta == False,
    ).delete()

    # Paso 2: huellas de las alertas YA RESUELTAS (ver _huella_alerta).
    resueltas = db.query(AlertaAuditoria).filter(
        AlertaAuditoria.usuario_id == usuario_id,
        AlertaAuditoria.resuelta == True,
    ).all()
    huellas_resueltas = {_huella_alerta(a) for a in resueltas}

    conteo = {
        "gastos_duplicados": 0, "anomalias": 0, "discrepancias": 0,
        "monotributo_impago": 0, "transferencias_propias": 0,
    }
    alertas: list[AlertaAuditoria] = []

    # Paso 3: los cinco detectores.
    # --- DETECTOR 1: duplicados ---
    duplicados = detectar_gastos_duplicados(db, usuario_id)
    ids_marcados: set[int] = set()

    for gasto_a, gasto_b in duplicados:
        # Marcamos ambos gastos como duplicados en la tabla gastos (es la marca
        # que usa el filtro "Solo duplicados" de la pantalla Gastos).
        for g in (gasto_a, gasto_b):
            if g.id not in ids_marcados:
                g.es_duplicado = True
                ids_marcados.add(g.id)

        alertas.append(_crear_alerta(
            usuario_id,
            TipoAlerta.GASTO_DUPLICADO,
            f"Posible gasto duplicado: {formato_pesos_ar(gasto_a.monto)} en '{gasto_a.categoria}' "
            f"registrado el {formato_fecha_ar(gasto_a.fecha)} y el {formato_fecha_ar(gasto_b.fecha)}",
            monto=gasto_a.monto,
            # referencia directa al gasto repetido (el más reciente del par):
            # permite que "eliminar duplicado" borre exactamente este gasto,
            # sin ambigüedad si otro par comparte el mismo monto.
            gasto_id_duplicado=gasto_b.id,
        ))

    # --- DETECTOR 2: anomalías ---
    anomalias = detectar_anomalias_estadisticas(db, usuario_id)

    for gasto, media, desviacion in anomalias:
        alertas.append(_crear_alerta(
            usuario_id,
            TipoAlerta.ANOMALIA_ESTADISTICA,
            f"Gasto inusualmente alto: {formato_pesos_ar(gasto.monto)} en '{gasto.categoria}' "
            f"(promedio de la categoría: {formato_pesos_ar(media)}, desviación: {formato_pesos_ar(desviacion)})",
            monto=gasto.monto,
            # el gasto señalado: identifica la alerta aunque cambien el
            # promedio y la desviación de la categoría entre corridas
            gasto_id_duplicado=gasto.id,
        ))

    # --- DETECTOR 3: discrepancias ---
    facturas_vencidas = detectar_discrepancias_facturacion(db, usuario_id)

    for factura in facturas_vencidas:
        alertas.append(_crear_alerta(
            usuario_id,
            TipoAlerta.DISCREPANCIA_FACTURACION,
            f"Factura vencida sin cobrar: {formato_pesos_ar(factura.monto)} a '{factura.cliente_nombre}' "
            f"(venció el {formato_fecha_ar(factura.fecha_vencimiento)})",
            monto=factura.monto,
        ))

    # --- DETECTOR 4: monotributo impago ---
    _, alerta_mono = detectar_monotributo_impago(db, usuario_id)
    if alerta_mono:
        alertas.append(alerta_mono)

    # --- DETECTOR 5: transferencias entre cuentas propias ---
    transferencias = detectar_transferencias_propias(db, usuario_id)

    for ingreso, gasto in transferencias:
        alertas.append(_crear_alerta(
            usuario_id,
            TipoAlerta.TRANSFERENCIA_PROPIA,
            f"Posible transferencia entre cuentas propias: {formato_pesos_ar(ingreso.monto)} "
            f"ingresó el {formato_fecha_ar(ingreso.fecha)} ('{ingreso.descripcion[:60]}') y salió el "
            f"{formato_fecha_ar(gasto.fecha)} ('{gasto.descripcion[:60]}'). Si es un movimiento entre tus "
            f"cuentas, no representa facturación real: descartalo para no inflar tu monotributo.",
            monto=ingreso.monto,
            gasto_id_duplicado=gasto.id,
            ingreso_id_relacionado=ingreso.id,
        ))

    # Paso 4: una condición que el usuario ya marcó como resuelta no se vuelve
    # a generar aunque siga existiendo: así "Resolver" es efectivo.
    alertas = [a for a in alertas if _huella_alerta(a) not in huellas_resueltas]
    for alerta in alertas:
        conteo[CLAVE_CONTEO[alerta.tipo]] += 1

    # Paso 5: guardar todo junto.
    db.add_all(alertas)
    db.commit()
    return conteo


# -------------------------------------------------------------------
# DETECTOR 4: MONOTRIBUTO IMPAGO
# Avisa si la cuota del mes en curso no está cubierta por los gastos de
# categoría "Monotributo" registrados en el mes.
# -------------------------------------------------------------------
def detectar_monotributo_impago(db: Session, usuario_id: int) -> tuple:
    """Devuelve (1, alerta) si la cuota del mes no está cubierta, o (0, None) si está bien.

    La regla de "cuota pagada" vive en monotributo_service (verificar_pago_monotributo
    y cuota_cubierta): la misma que usa la pantalla Monotributo, así nunca
    se contradicen. Si el usuario no cargó su categoría no hay cuota contra la
    cual comparar y no se genera alerta.
    """
    estado = verificar_pago_monotributo(db, usuario_id)
    if not estado["pagado"] and estado["monto_esperado"] is not None:
        detalle = (
            f"No se registró el pago del monotributo de {estado['mes']} {estado['anio']}. "
            f"Cuota esperada: {formato_pesos_ar(estado['monto_esperado'], decimales=0)}"
        )
        # Si hubo registros que no llegan a cubrir la cuota, lo aclaramos:
        # ayuda a distinguir "me olvidé de pagar" de "pagué de menos".
        if estado.get("pago_parcial"):
            detalle += (
                f". Lo registrado en el mes ({formato_pesos_ar(estado['total_registrado'], decimales=0)}) "
                f"no cubre la cuota"
            )
        alerta = _crear_alerta(
            usuario_id,
            TipoAlerta.MONOTRIBUTO_IMPAGO,
            detalle,
            monto=estado["monto_esperado"],
        )
        return 1, alerta
    return 0, None
