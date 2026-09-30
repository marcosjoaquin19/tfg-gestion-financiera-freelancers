"""
Servicio de Monotributo — cálculos fiscales del monotributo argentino.

Contiene la lógica fiscal: calcular la facturación del año en curso más la
proyección hasta el cierre del ejercicio (HU-10), compararla contra el límite
de la categoría del usuario, estimar el riesgo de recategorización y verificar
si pagó la cuota del mes. Lo usa el router de
monotributo y también el de auditoría (para la alerta de monotributo impago).
"""

import logging
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from sqlalchemy import extract, func
from sqlalchemy.orm import Session
from app.models.usuario import Usuario
from app.models.ingreso import Ingreso
from app.models.gasto import Gasto
from app.models.proyeccion import Proyeccion
from app.models.categoria_monotributo import CategoriaMonotributo
from app.services.prophet_service import asegurar_proyecciones_vigentes, inicio_de_manana, inicio_mes_en_curso

logger = logging.getLogger(__name__)

MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}

CATEGORIAS_ORDEN = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K"]


def get_categoria(db: Session, letra: str) -> CategoriaMonotributo | None:
    """Categoría de la escala VIGENTE (la activa). Para evaluar un período
    pasado se usa escala_vigente_en()."""
    return (
        db.query(CategoriaMonotributo)
        .filter(CategoriaMonotributo.letra == letra.upper(), CategoriaMonotributo.activa == True)
        .order_by(CategoriaMonotributo.fecha_vigencia.desc())
        .first()
    )


def escala_vigente_en(db: Session, fecha, actividad: str = "servicios") -> dict[str, CategoriaMonotributo]:
    """Escala que regía en `fecha`: la de fecha de vigencia más reciente que no
    sea posterior a esa fecha, como {letra: categoría}. Vacía si para esa
    fecha no hay ninguna escala cargada (no se inventa una)."""
    vigencia = (
        db.query(func.max(CategoriaMonotributo.fecha_vigencia))
        .filter(
            CategoriaMonotributo.actividad == actividad,
            CategoriaMonotributo.fecha_vigencia <= fecha,
        )
        .scalar()
    )
    if vigencia is None:
        return {}
    filas = db.query(CategoriaMonotributo).filter(
        CategoriaMonotributo.actividad == actividad,
        CategoriaMonotributo.fecha_vigencia == vigencia,
    ).all()
    return {f.letra: f for f in filas}


def calcular_estado_monotributo(db: Session, usuario_id: int) -> dict | None:
    """Estado fiscal del año en curso (HU-10).

    Acumulado real del año (hasta hoy) + proyección hasta el cierre del
    ejercicio, comparado contra el tope de la categoría:
      - la proyección se regenera sola si quedó vieja (ver
        asegurar_proyecciones_vigentes);
      - el mes en curso suma lo que sea mayor entre lo ya cobrado y lo que se
        espera para un mes (criterio conservador: el mes no terminó);
      - los meses hasta diciembre que el horizonte de 6 meses no alcanza
        (enero a junio) se completan con el promedio proyectado.
    """
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario or not usuario.categoria_monotributo:
        return None

    cat = usuario.categoria_monotributo.upper()
    datos_cat = get_categoria(db, cat)
    if datos_cat is None:
        return None

    limite_anual = float(datos_cat.limite_anual)
    cuota_mensual = float(datos_cat.cuota_mensual)

    # Proyección al día con los ingresos actuales. Si Prophet fallara, el
    # estado fiscal se calcula igual con lo que haya guardado.
    try:
        asegurar_proyecciones_vigentes(db, usuario_id)
    except Exception:
        logger.exception("No se pudo regenerar la proyección del usuario %s", usuario_id)
        db.rollback()

    mes_actual = inicio_mes_en_curso()                      # 1° del mes, sin zona
    inicio_anio = datetime(mes_actual.year, 1, 1, tzinfo=timezone.utc)

    # Facturado real: ingresos del año con fecha hasta hoy (calendario de
    # Argentina). Un cobro cargado con fecha futura todavía no es facturación.
    ingresos_anio = db.query(Ingreso).filter(
        Ingreso.usuario_id == usuario_id,
        Ingreso.fecha >= inicio_anio,
        Ingreso.fecha < inicio_de_manana(),
    ).all()
    facturado_anual = round(float(sum(i.monto for i in ingresos_anio)), 2)
    facturado_mes_en_curso = float(sum(
        i.monto for i in ingresos_anio
        if (i.fecha.year, i.fecha.month) == (mes_actual.year, mes_actual.month)
    ))
    porcentaje_usado = round((facturado_anual / limite_anual * 100), 1) if limite_anual > 0 else 0.0

    # Proyección de los meses que faltan hasta diciembre.
    proyecciones = db.query(Proyeccion).filter(Proyeccion.usuario_id == usuario_id).all()
    por_mes = {
        (p.fecha_proyeccion.year, p.fecha_proyeccion.month): float(p.monto_proyectado)
        for p in proyecciones
        if (p.fecha_proyeccion.year, p.fecha_proyeccion.month) > (mes_actual.year, mes_actual.month)
    }
    promedio_proyectado = sum(por_mes.values()) / len(por_mes) if por_mes else 0.0

    mes_siguiente = mes_actual + relativedelta(months=1)
    esperado_un_mes = por_mes.get((mes_siguiente.year, mes_siguiente.month), promedio_proyectado)
    ajuste_mes_en_curso = max(0.0, esperado_un_mes - facturado_mes_en_curso)

    restantes = []
    meses_estimados_con_promedio = 0
    mes = mes_siguiente
    while mes.year == mes_actual.year:
        clave = (mes.year, mes.month)
        if clave in por_mes:
            restantes.append((mes, por_mes[clave]))
        else:
            restantes.append((mes, promedio_proyectado))
            meses_estimados_con_promedio += 1
        mes += relativedelta(months=1)

    total_proyectado_restante = ajuste_mes_en_curso + sum(monto for _, monto in restantes)
    proyeccion_anual = round(facturado_anual + total_proyectado_restante, 2)
    porcentaje_proyectado = round(proyeccion_anual / limite_anual * 100, 1) if limite_anual > 0 else 0.0

    # Semáforo (HU-10): verde por debajo del 70 %, amarillo entre 70 % y 90 %,
    # rojo por encima del 90 %. Se multiplica antes de dividir y se redondea a
    # 6 decimales para que el 90 % exacto no dé 90,00000000000001 (y rojo).
    pct = round(proyeccion_anual * 100 / limite_anual, 6) if limite_anual > 0 else 0.0
    if pct < 70:
        estado = "verde"
    elif pct <= 90:
        estado = "amarillo"
    else:
        estado = "rojo"

    # ¿En qué mes de ESTE año se cruzaría el tope? El modelo es anual: si no
    # se cruza antes de diciembre, no hay fecha que informar.
    limite_superado = facturado_anual > limite_anual

    # Los porcentajes se muestran con un decimal. Redondeados sin más, 69,99 %
    # se leía "70 %" en verde, 90,01 % "90 %" en rojo y 100,04 % "100 %" con
    # el tope ya superado: se acotan al rango de su color (y del aviso de tope
    # superado) para que el número que se ve nunca contradiga al semáforo.
    if estado == "verde":
        porcentaje_proyectado = min(porcentaje_proyectado, 69.9)
    elif estado == "rojo":
        porcentaje_proyectado = max(porcentaje_proyectado, 90.1)
    if limite_superado:
        porcentaje_usado = max(porcentaje_usado, 100.1)

    meses_para_limite = None
    mes_limite = None
    if limite_superado:
        meses_para_limite = 0
    else:
        acumulado = facturado_anual
        secuencia = [(mes_actual, ajuste_mes_en_curso)] + restantes
        for indice, (mes, monto) in enumerate(secuencia):
            acumulado += monto
            if acumulado > limite_anual:
                meses_para_limite = indice          # 0 = este mes
                mes_limite = f"{MESES_ES[mes.month]} {mes.year}"
                break

    # Categoría inmediata superior (informativa) y, si la proyección supera el
    # tope, la primera categoría que efectivamente la cubre. Si ni la más alta
    # alcanza, hay riesgo de exclusión del régimen.
    idx = CATEGORIAS_ORDEN.index(cat)
    categoria_siguiente = CATEGORIAS_ORDEN[idx + 1] if idx + 1 < len(CATEGORIAS_ORDEN) else None
    categoria_sugerida = None
    excede_regimen = False
    if proyeccion_anual > limite_anual:
        escala = (
            db.query(CategoriaMonotributo)
            .filter(
                CategoriaMonotributo.activa == True,
                CategoriaMonotributo.actividad == datos_cat.actividad,
            )
            .order_by(CategoriaMonotributo.limite_anual.asc())
            .all()
        )
        cubre = next((c for c in escala if float(c.limite_anual) >= proyeccion_anual), None)
        if cubre is not None:
            categoria_sugerida = cubre.letra
        else:
            excede_regimen = True

    return {
        "categoria_actual": cat,
        "limite_anual": limite_anual,
        "cuota_mensual": cuota_mensual,
        "facturado_anual": facturado_anual,
        "porcentaje_usado": porcentaje_usado,
        "limite_superado": limite_superado,
        "proyeccion_anual": proyeccion_anual,
        "porcentaje_proyectado": porcentaje_proyectado,
        "meses_estimados_con_promedio": meses_estimados_con_promedio,
        "estado": estado,
        "meses_para_limite": meses_para_limite,
        "mes_limite": mes_limite,
        "categoria_siguiente": categoria_siguiente,
        "categoria_sugerida": categoria_sugerida,
        "excede_regimen": excede_regimen,
    }


TOLERANCIA_CUOTA = 0.99
# Margen del 1% al comparar el gasto registrado contra la cuota oficial:
# absorbe diferencias de redondeo entre la escala publicada y lo que el
# banco/billetera debita efectivamente (centavos, ajustes).


def verificar_pago_monotributo(db: Session, usuario_id: int) -> dict:
    """Verifica si la cuota del mes en curso está cubierta.

    Antes alcanzaba con que existiera CUALQUIER gasto de categoría
    "Monotributo" en el mes; ahora, si el usuario tiene categoría cargada,
    lo registrado en el mes tiene que cubrir la cuota esperada (con
    tolerancia del 1%). Cuenta la suma: la cuota se puede pagar en más de un
    débito, y con dos pagos que juntos la cubrían se avisaba que no estaba
    paga. Si lo registrado no alcanza es un pago PARCIAL: se informa aparte y
    la auditoría sigue alertando que la cuota no está cubierta.
    """
    mes_actual = inicio_mes_en_curso()
    mes = mes_actual.month
    anio = mes_actual.year

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    cat = usuario.categoria_monotributo if usuario else None
    datos_cat = get_categoria(db, cat) if cat else None
    monto_esperado = float(datos_cat.cuota_mensual) if datos_cat else None

    gastos_mes = db.query(Gasto).filter(
        Gasto.usuario_id == usuario_id,
        Gasto.categoria == "Monotributo",
        extract("month", Gasto.fecha) == mes,
        extract("year", Gasto.fecha) == anio,
    ).all()

    total_registrado = round(sum(float(g.monto) for g in gastos_mes), 2)
    if monto_esperado is None:
        # Sin categoría cargada no hay cuota contra la cual validar:
        # cualquier registro de la categoría cuenta como pago.
        pagado = bool(gastos_mes)
    else:
        pagado = total_registrado >= monto_esperado * TOLERANCIA_CUOTA
    pago_parcial = bool(gastos_mes) and not pagado

    # El registro más alto del mes (si existe), para que el usuario entienda
    # qué se detectó.
    gasto_mostrado = max(gastos_mes, key=lambda g: float(g.monto)) if gastos_mes else None

    gasto_encontrado = None
    if gasto_mostrado:
        gasto_encontrado = {
            "id": gasto_mostrado.id,
            "descripcion": gasto_mostrado.descripcion,
            "monto": float(gasto_mostrado.monto),
            "fecha": str(gasto_mostrado.fecha),
        }

    return {
        "pagado": pagado,
        "pago_parcial": pago_parcial,
        "mes": MESES_ES[mes],
        "anio": anio,
        "monto_esperado": monto_esperado,
        "total_registrado": total_registrado,
        "gasto_encontrado": gasto_encontrado,
    }
