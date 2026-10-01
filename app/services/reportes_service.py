"""
Genera el reporte financiero mensual en PDF.

Uso ReportLab y no WeasyPrint a propósito: WeasyPrint depende de un motor
de renderizado HTML/CSS y no escala bien en Docker. ReportLab arma el PDF
de forma totalmente programática, lo que también permite explicar línea
por línea cómo se construye cada sección durante la defensa.
"""

# PATRÓN: Builder — cada _seccion_*() aporta un fragmento y generar_pdf_mensual() ensambla el documento.
# PATRÓN: Template Method — _pie_pagina() lo invoca ReportLab en cada página (onFirstPage/onLaterPages).
# Justificación y alternativas descartadas: docs/ARQUITECTURA_Y_PATRONES.md

from io import BytesIO
from datetime import date, datetime
from decimal import Decimal
from xml.sax.saxutils import escape
from zoneinfo import ZoneInfo

from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app.models.usuario import Usuario
from app.models.ingreso import Ingreso
from app.models.gasto import Gasto
from app.models.factura import Factura, EstadoFactura
from app.services.facturas_estado import marcar_vencidas
from app.models.alerta_auditoria import AlertaAuditoria, TipoAlerta
from app.services.formato import formato_pesos_ar


MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}

ZONA_AR = ZoneInfo("America/Argentina/Buenos_Aires")

MAX_ALERTAS_DETALLE = 20

ETIQUETA_ALERTA = {
    TipoAlerta.GASTO_DUPLICADO: "Posible gasto duplicado",
    TipoAlerta.ANOMALIA_ESTADISTICA: "Gasto inusualmente alto",
    TipoAlerta.DISCREPANCIA_FACTURACION: "Factura vencida",
    TipoAlerta.MONOTRIBUTO_IMPAGO: "Monotributo impago",
    TipoAlerta.TRANSFERENCIA_PROPIA: "Transferencia entre cuentas propias",
    TipoAlerta.RIESGO_RECATEGORIZACION: "Riesgo de recategorización",
    TipoAlerta.FACTURA_IMPAGA: "Factura impaga",
    TipoAlerta.COMISION_EXCESIVA: "Comisión excesiva",
}


def ahora_ar() -> datetime:
    """Hora de Argentina para lo que ve el usuario (el servidor corre en UTC)."""
    return datetime.now(ZONA_AR)


def _texto(valor) -> str:
    """Texto cargado por el usuario, listo para un Paragraph de ReportLab.

    Paragraph interpreta "<" y "&" como marcas de formato: sin escapar, el
    nombre "Pérez & Hijos <SRL>" salía como "Pérez & Hijos" y el cliente
    "A&B <Consultores>" como "A&B; ". En un documento para el contador el
    texto tiene que salir exactamente como se cargó.
    """
    return escape(str(valor or ""))


# ── Recolección de datos ─────────────────────────────────────────────────────
# Estas funciones consultan la BD y devuelven dicts simples. La idea es
# separar la consulta del armado visual: si después cambia el layout, no hay
# que tocar SQL.

def _totales_mes(db: Session, usuario_id: int, mes: int, anio: int) -> dict:
    ingresos = db.query(Ingreso).filter(
        Ingreso.usuario_id == usuario_id,
        extract("month", Ingreso.fecha) == mes,
        extract("year", Ingreso.fecha) == anio,
    ).all()

    gastos = db.query(Gasto).filter(
        Gasto.usuario_id == usuario_id,
        extract("month", Gasto.fecha) == mes,
        extract("year", Gasto.fecha) == anio,
    ).all()

    total_ingresos = sum((i.monto for i in ingresos), Decimal("0"))
    total_gastos = sum((g.monto for g in gastos), Decimal("0"))

    return {
        "total_ingresos": total_ingresos,
        "cant_ingresos": len(ingresos),
        "total_gastos": total_gastos,
        "cant_gastos": len(gastos),
        "balance": total_ingresos - total_gastos,
    }


def _gastos_por_categoria(db: Session, usuario_id: int, mes: int, anio: int) -> list[dict]:
    # Agrupado por SQL para no traer todos los registros a memoria.
    rows = db.query(
        Gasto.categoria,
        func.sum(Gasto.monto).label("total"),
        func.count(Gasto.id).label("cantidad"),
    ).filter(
        Gasto.usuario_id == usuario_id,
        extract("month", Gasto.fecha) == mes,
        extract("year", Gasto.fecha) == anio,
    ).group_by(Gasto.categoria).all()

    total_general = sum((r.total for r in rows), Decimal("0")) or Decimal("1")

    resultado = [
        {
            "categoria": r.categoria,
            "monto": r.total,
            "cantidad": r.cantidad,
            "porcentaje": float(r.total / total_general * 100),
        }
        for r in rows
    ]
    # Mayor a menor para que los más relevantes queden arriba en la tabla.
    resultado.sort(key=lambda x: x["monto"], reverse=True)
    return resultado


def _facturacion_mes(db: Session, usuario_id: int, mes: int, anio: int) -> dict:
    marcar_vencidas(db, usuario_id)
    facturas = db.query(Factura).filter(
        Factura.usuario_id == usuario_id,
        extract("month", Factura.fecha_emision) == mes,
        extract("year", Factura.fecha_emision) == anio,
    ).all()

    pagadas = [f for f in facturas if f.estado == EstadoFactura.PAGADA]
    pendientes = [f for f in facturas if f.estado == EstadoFactura.PENDIENTE]
    vencidas = [f for f in facturas if f.estado == EstadoFactura.VENCIDA]

    return {
        "emitidas": (len(facturas), sum((f.monto for f in facturas), Decimal("0"))),
        "pagadas": (len(pagadas), sum((f.monto for f in pagadas), Decimal("0"))),
        "pendientes": (len(pendientes), sum((f.monto for f in pendientes), Decimal("0"))),
        "vencidas": (len(vencidas), sum((f.monto for f in vencidas), Decimal("0"))),
    }


def _estado_fiscal_periodo(db: Session, usuario_id: int, mes: int, anio: int) -> dict:
    """Estado fiscal evaluado con la escala que regía en el período.

    No se llama a monotributo_service.verificar_pago_monotributo porque esa
    consulta siempre el mes corriente con la escala vigente; sí se reusa su
    regla, cuota_cubierta. Para un mes anterior a un cambio de escala (por
    ejemplo, mayo de 2026, antes del ajuste del 1/8/2026) la cuota y el tope
    tienen que ser los de ese momento.
    """
    from app.services.monotributo_service import cuota_cubierta, escala_vigente_en

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario or not usuario.categoria_monotributo:
        return {"tiene_categoria": False}

    letra = usuario.categoria_monotributo.upper()
    inicio = date(anio, mes, 1)
    datos_cat = escala_vigente_en(db, inicio).get(letra)
    if datos_cat is None:
        return {"tiene_categoria": True, "categoria": letra, "sin_escala": True}

    cuota = Decimal(datos_cat.cuota_mensual)
    gastos_mes = db.query(Gasto).filter(
        Gasto.usuario_id == usuario_id,
        Gasto.categoria == "Monotributo",
        extract("month", Gasto.fecha) == mes,
        extract("year", Gasto.fecha) == anio,
    ).all()
    # La misma regla que la pantalla Monotributo y la auditoría
    # (monotributo_service.cuota_cubierta), con la cuota de la escala del
    # período. Si lo registrado no alcanza, es un pago parcial.
    registrado = sum((Decimal(g.monto) for g in gastos_mes), Decimal("0"))
    if not gastos_mes:
        estado_cuota, registrado = "sin_registrar", None
    elif cuota_cubierta(registrado, cuota):
        estado_cuota = "pagada"
    else:
        estado_cuota = "parcial"

    # El reporte es la foto del mes: no incluye el facturado anual acumulado
    # ni el % consumido del tope (decisión de diseño). Ese panorama anual,
    # con la proyección y el semáforo, vive en la pantalla Monotributo.
    return {
        "tiene_categoria": True,
        "categoria": letra,
        "vigencia": datos_cat.fecha_vigencia,
        "limite_anual": Decimal(datos_cat.limite_anual),
        "cuota_mensual": cuota,
        "estado_cuota": estado_cuota,
        "registrado": registrado,
    }


def _alertas_pendientes(db: Session, usuario_id: int) -> list[AlertaAuditoria]:
    # Las alertas no están atadas a un mes en particular: muestro las pendientes
    # al momento de generar el reporte. Ordeno por tipo para agrupar visualmente.
    return (
        db.query(AlertaAuditoria)
        .filter(
            AlertaAuditoria.usuario_id == usuario_id,
            AlertaAuditoria.resuelta == False,
        )
        .order_by(AlertaAuditoria.tipo, AlertaAuditoria.fecha_deteccion.desc())
        .all()
    )


# ── Helpers de formato ───────────────────────────────────────────────────────

def _fmt_pesos(valor) -> str:
    # Formato argentino centralizado en services.formato (compartido con auditoria).
    return formato_pesos_ar(valor)


def _fmt_porcentaje(valor: float) -> str:
    # Coma decimal, como los importes: "24,5 %".
    return f"{valor:.1f}".replace(".", ",") + " %"


def _variacion(actual: Decimal, anterior: Decimal) -> str:
    # Si no hay base para comparar, no inventamos una variación.
    if anterior is None or anterior == 0:
        return "—"
    # Se divide por el valor absoluto: con un balance anterior negativo, pasar
    # de −$100 a +$100 es una mejora (+200 %), no "−200 %".
    delta = float((actual - anterior) / abs(anterior) * 100)
    signo = "+" if delta >= 0 else "−"
    return f"{signo}{_fmt_porcentaje(abs(delta))}"


# ── Construcción del documento ───────────────────────────────────────────────

def _estilos():
    base = getSampleStyleSheet()
    base.add(ParagraphStyle(
        name="Titulo",
        parent=base["Title"],
        fontSize=18,
        spaceAfter=6,
        textColor=colors.HexColor("#1f3a5f"),
    ))
    base.add(ParagraphStyle(
        name="Subtitulo",
        parent=base["Normal"],
        fontSize=10,
        textColor=colors.grey,
        spaceAfter=18,
    ))
    base.add(ParagraphStyle(
        name="Seccion",
        parent=base["Heading2"],
        fontSize=13,
        spaceBefore=14,
        spaceAfter=8,
        textColor=colors.HexColor("#1f3a5f"),
        # El título va en la misma página que su tabla: sin esto, en el reporte
        # de septiembre del demo "Auditoría" quedaba solo al pie de la página 1.
        keepWithNext=1,
    ))
    base.add(ParagraphStyle(
        name="Celda",
        parent=base["Normal"],
        fontSize=8,
        leading=10,
    ))
    base.add(ParagraphStyle(
        name="Nota",
        parent=base["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.grey,
        spaceBefore=4,
    ))
    base.add(ParagraphStyle(
        name="Aviso",
        parent=base["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#8a5a00"),
        backColor=colors.HexColor("#fff4d6"),
        borderPadding=6,
        spaceAfter=12,
    ))
    base.add(ParagraphStyle(
        name="Pie",
        parent=base["Normal"],
        fontSize=8,
        textColor=colors.grey,
        alignment=1,
    ))
    return base


def _tabla_estandar(datos: list[list], col_widths: list = None) -> Table:
    # Mismo estilo para todas las tablas del reporte: encabezado azul,
    # filas alternadas, bordes finos. Centralizo acá para no repetir.
    tabla = Table(datos, colWidths=col_widths)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3a5f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f6fa")]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return tabla


def _seccion_encabezado(usuario: Usuario, mes: int, anio: int, generado: datetime, en_curso: bool, estilos) -> list:
    titulo = Paragraph("FreelanceControl — Reporte mensual", estilos["Titulo"])
    sub = Paragraph(
        f"{_texto(usuario.nombre)} &nbsp;·&nbsp; "
        f"Período: {MESES_ES[mes]} {anio} &nbsp;·&nbsp; "
        f"Generado: {generado.strftime('%d/%m/%Y %H:%M')} (hora de Argentina)",
        estilos["Subtitulo"],
    )
    partes = [titulo, sub]
    if en_curso:
        partes.append(Paragraph(
            f"<b>Período en curso:</b> datos parciales al {generado.strftime('%d/%m/%Y')}. "
            f"El reporte del mes completo se genera una vez cerrado el período.",
            estilos["Aviso"],
        ))
    return partes


def _seccion_resumen_ejecutivo(actual: dict, previo: dict, estilos) -> list:
    encabezado = Paragraph("Resumen ejecutivo", estilos["Seccion"])

    # La comparativa contra el mes anterior es lo más informativo del resumen,
    # por eso va en una columna propia y no como nota al pie.
    filas = [
        ["Indicador", "Período", "vs mes anterior"],
        ["Total ingresos", _fmt_pesos(actual["total_ingresos"]),
         _variacion(actual["total_ingresos"], previo["total_ingresos"])],
        ["Total gastos", _fmt_pesos(actual["total_gastos"]),
         _variacion(actual["total_gastos"], previo["total_gastos"])],
        ["Balance", _fmt_pesos(actual["balance"]),
         _variacion(actual["balance"], previo["balance"])],
        ["Movimientos", f"{actual['cant_ingresos'] + actual['cant_gastos']}", "—"],
    ]
    tabla = _tabla_estandar(filas, col_widths=[6 * cm, 5 * cm, 5 * cm])
    return [encabezado, tabla]


def _seccion_monotributo(fiscal: dict, estilos) -> list:
    encabezado = Paragraph("Estado fiscal — Monotributo", estilos["Seccion"])

    if not fiscal.get("tiene_categoria"):
        nota = Paragraph("El usuario no tiene cargada una categoría de Monotributo.", estilos["Normal"])
        return [encabezado, nota]

    if fiscal.get("sin_escala"):
        nota = Paragraph(
            f"Categoría declarada: {fiscal['categoria']}. No hay una escala de categorías cargada para "
            f"este período, por lo que no se evalúan la cuota ni el tope.",
            estilos["Normal"],
        )
        return [encabezado, nota]

    if fiscal["estado_cuota"] == "pagada":
        cuota_periodo = f"Pagada ({_fmt_pesos(fiscal['registrado'])})"
    elif fiscal["estado_cuota"] == "parcial":
        cuota_periodo = f"Parcial: {_fmt_pesos(fiscal['registrado'])} de {_fmt_pesos(fiscal['cuota_mensual'])}"
    else:
        cuota_periodo = "Sin registrar"

    filas = [
        ["Concepto", "Valor"],
        ["Categoría declarada (actual)", fiscal["categoria"]],
        ["Escala aplicada", f"vigente desde el {fiscal['vigencia'].strftime('%d/%m/%Y')}"],
        ["Tope anual de la categoría", _fmt_pesos(fiscal["limite_anual"])],
        ["Cuota mensual", _fmt_pesos(fiscal["cuota_mensual"])],
        ["Cuota del período", cuota_periodo],
    ]
    tabla = _tabla_estandar(filas, col_widths=[7 * cm, 9 * cm])
    tabla.setStyle(TableStyle([("ALIGN", (0, 1), (0, -1), "LEFT")]))
    nota = Paragraph(
        "La cuota y el tope corresponden a la escala que regía en el período. La categoría es la "
        "declarada hoy en la aplicación.",
        estilos["Nota"],
    )
    return [encabezado, tabla, nota]


def _seccion_categorias(rows: list[dict], estilos) -> list:
    encabezado = Paragraph("Distribución de gastos por categoría", estilos["Seccion"])

    if not rows:
        return [encabezado, Paragraph("Sin gastos registrados en el período.", estilos["Normal"])]

    filas = [["Categoría", "Monto", "% del total", "Movimientos"]]
    for r in rows:
        filas.append([
            r["categoria"],
            _fmt_pesos(r["monto"]),
            _fmt_porcentaje(r["porcentaje"]),
            str(r["cantidad"]),
        ])
    tabla = _tabla_estandar(filas, col_widths=[6 * cm, 4.5 * cm, 3 * cm, 2.5 * cm])
    # Primera columna alineada a la izquierda — el resto sigue centrado/derecha
    # del estilo base. La alineación específica va acá porque depende de la tabla.
    tabla.setStyle(TableStyle([("ALIGN", (0, 1), (0, -1), "LEFT")]))
    return [encabezado, tabla]


def _seccion_facturacion(fact: dict, estilos) -> list:
    encabezado = Paragraph("Facturación del período", estilos["Seccion"])

    filas = [["Estado", "Cantidad", "Monto"]]
    for clave, etiqueta in [
        ("emitidas", "Emitidas"),
        ("pagadas", "Pagadas"),
        ("pendientes", "Pendientes"),
        ("vencidas", "Vencidas"),
    ]:
        cant, monto = fact[clave]
        filas.append([etiqueta, str(cant), _fmt_pesos(monto)])

    tabla = _tabla_estandar(filas, col_widths=[6 * cm, 4 * cm, 6 * cm])
    tabla.setStyle(TableStyle([("ALIGN", (0, 1), (0, -1), "LEFT")]))
    return [encabezado, tabla]


def _seccion_auditoria(alertas: list[AlertaAuditoria], estilos) -> list:
    encabezado = Paragraph("Auditoría — alertas pendientes al generar el reporte", estilos["Seccion"])

    if not alertas:
        return [encabezado, Paragraph("Sin alertas pendientes al momento de generar el reporte.", estilos["Normal"])]

    def etiqueta(tipo):
        return ETIQUETA_ALERTA.get(tipo, tipo.value.replace("_", " ").capitalize())

    # Conteo por tipo para el bloque resumen.
    conteo: dict = {}
    for a in alertas:
        conteo[etiqueta(a.tipo)] = conteo.get(etiqueta(a.tipo), 0) + 1
    resumen_lineas = [["Tipo", "Cantidad"]] + [[t, str(c)] for t, c in conteo.items()]
    tabla_resumen = _tabla_estandar(resumen_lineas, col_widths=[10 * cm, 4 * cm])
    tabla_resumen.setStyle(TableStyle([("ALIGN", (0, 1), (0, -1), "LEFT")]))

    # Listado detallado: las descripciones son visibles porque el PDF es para
    # el dueño de los datos. La política de no exponer texto libre aplica solo
    # a transmisiones a servicios externos.
    detalle_lineas = [["Tipo", "Detalle", "Monto"]]
    for a in alertas[:MAX_ALERTAS_DETALLE]:
        # Paragraph (no string plano) para que ReportLab haga wrap dentro de
        # la columna: un string largo desborda la celda y pisa la de Monto.
        detalle_lineas.append([
            Paragraph(_texto(etiqueta(a.tipo)), estilos["Celda"]),
            Paragraph(_texto(a.descripcion), estilos["Celda"]),
            _fmt_pesos(a.monto_involucrado) if a.monto_involucrado else "—",
        ])
    tabla_detalle = _tabla_estandar(detalle_lineas, col_widths=[4 * cm, 9 * cm, 3 * cm])
    tabla_detalle.setStyle(TableStyle([
        ("ALIGN", (0, 1), (1, -1), "LEFT"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))

    partes = [encabezado, tabla_resumen, Spacer(1, 0.3 * cm), tabla_detalle]
    restantes = len(alertas) - MAX_ALERTAS_DETALLE
    if restantes > 0:
        partes.append(Paragraph(
            f"Y {restantes} alerta{'s' if restantes != 1 else ''} más: el detalle completo está en la "
            f"sección Auditoría de la aplicación.",
            estilos["Nota"],
        ))
    return partes


def _seccion_pie(estilos) -> list:
    # Descargo de alcance. Va en el PDF además de en la pantalla porque el
    # reporte es justamente el artefacto que sale de la aplicación y circula
    # fuera de ella (el usuario se lo envía al contador o lo imprime): tiene
    # que llevar el límite de responsabilidad consigo. Mismo enunciado que el
    # componente frontend/src/components/AvisoAlcance.js, con la frase exacta
    # del criterio de la HU-13: "no reemplaza el asesoramiento de un contador
    # matriculado".
    texto = (
        "Documento generado automáticamente por FreelanceControl a partir de los datos "
        "cargados por el usuario. El sistema informa, proyecta y alerta: no constituye "
        "asesoramiento contable, fiscal ni financiero, y no reemplaza el asesoramiento de "
        "un contador matriculado. Las cifras deben verificarse contra la documentación "
        "respaldatoria antes de su presentación ante organismos de control."
    )
    return [Spacer(1, 0.6 * cm), Paragraph(texto, estilos["Pie"])]


# ── Punto de entrada ─────────────────────────────────────────────────────────

def generar_pdf_mensual(db: Session, usuario_id: int, mes: int, anio: int) -> bytes:
    """Devuelve el PDF como bytes listo para enviar en la respuesta HTTP."""

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if usuario is None:
        # Casi imposible que pase porque el endpoint ya filtra por current_user,
        # pero si llega acá es preferible un error explícito que un PDF vacío.
        raise ValueError("Usuario no encontrado")

    # Mes anterior, ajustando el año si arrancamos en enero.
    if mes == 1:
        mes_prev, anio_prev = 12, anio - 1
    else:
        mes_prev, anio_prev = mes - 1, anio

    generado = ahora_ar()
    hoy = generado.date()
    en_curso = (anio, mes) == (hoy.year, hoy.month)

    actual = _totales_mes(db, usuario_id, mes, anio)
    previo = _totales_mes(db, usuario_id, mes_prev, anio_prev)
    cats = _gastos_por_categoria(db, usuario_id, mes, anio)
    fact = _facturacion_mes(db, usuario_id, mes, anio)
    fiscal = _estado_fiscal_periodo(db, usuario_id, mes, anio)
    alertas = _alertas_pendientes(db, usuario_id)

    # SimpleDocTemplate escribe a un buffer en memoria; después devolvemos
    # los bytes para que el router los meta en una StreamingResponse.
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"Reporte {MESES_ES[mes]} {anio}",
        author="FreelanceControl",
    )

    estilos = _estilos()

    historia = []
    historia += _seccion_encabezado(usuario, mes, anio, generado, en_curso, estilos)
    historia += _seccion_resumen_ejecutivo(actual, previo, estilos)
    historia += _seccion_monotributo(fiscal, estilos)
    historia += _seccion_categorias(cats, estilos)
    historia += _seccion_facturacion(fact, estilos)
    historia += _seccion_auditoria(alertas, estilos)
    historia += _seccion_pie(estilos)

    doc.build(historia, onFirstPage=_pie_pagina, onLaterPages=_pie_pagina)
    return buffer.getvalue()


def _pie_pagina(canvas, doc):
    # Numeración al pie en cada página. Lo hago con onFirstPage/onLaterPages
    # porque ReportLab no tiene un footer "global" en SimpleDocTemplate.
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Página {doc.page}")
    canvas.restoreState()
