"""
Genera el reporte financiero mensual en PDF.

Uso ReportLab y no WeasyPrint a propósito: WeasyPrint depende de un motor
de renderizado HTML/CSS y no escala bien en Docker. ReportLab arma el PDF
de forma totalmente programática, lo que también permite explicar línea
por línea cómo se construye cada sección durante la defensa.
"""

from io import BytesIO
from datetime import datetime
from decimal import Decimal

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
from app.models.alerta_auditoria import AlertaAuditoria
from app.models.categoria_monotributo import CategoriaMonotributo
from app.services.formato import formato_pesos_ar


MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}


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


def _pago_monotributo(db: Session, usuario_id: int, mes: int, anio: int) -> dict:
    # No reuso monotributo_service.verificar_pago_monotributo porque ese siempre
    # consulta el mes corriente. Acá necesitamos un mes/año arbitrario para que
    # el reporte de cualquier período sea coherente.
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario or not usuario.categoria_monotributo:
        return {"tiene_categoria": False}

    cat_letra = usuario.categoria_monotributo.upper()
    datos_cat = db.query(CategoriaMonotributo).filter(
        CategoriaMonotributo.letra == cat_letra,
        CategoriaMonotributo.activa == True,
    ).first()

    if datos_cat is None:
        return {"tiene_categoria": False}

    gasto_pago = db.query(Gasto).filter(
        Gasto.usuario_id == usuario_id,
        Gasto.categoria == "Monotributo",
        extract("month", Gasto.fecha) == mes,
        extract("year", Gasto.fecha) == anio,
    ).first()

    return {
        "tiene_categoria": True,
        "categoria": cat_letra,
        "limite_anual": float(datos_cat.limite_anual),
        "cuota_mensual": float(datos_cat.cuota_mensual),
        "pagado": gasto_pago is not None,
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
    return f"{valor:.1f}%"


def _variacion(actual: Decimal, anterior: Decimal) -> str:
    # Si no hay base para comparar, no inventamos una variación.
    if anterior is None or anterior == 0:
        return "—"
    delta = float((actual - anterior) / anterior * 100)
    signo = "+" if delta >= 0 else ""
    return f"{signo}{delta:.1f}%"


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


def _seccion_encabezado(usuario: Usuario, mes: int, anio: int, estilos) -> list:
    titulo = Paragraph("FreelanceControl — Reporte mensual", estilos["Titulo"])
    sub = Paragraph(
        f"{usuario.nombre} &nbsp;·&nbsp; "
        f"Período: {MESES_ES[mes]} {anio} &nbsp;·&nbsp; "
        f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        estilos["Subtitulo"],
    )
    return [titulo, sub]


def _seccion_resumen_ejecutivo(actual: dict, previo: dict, estilos) -> list:
    encabezado = Paragraph("Resumen ejecutivo", estilos["Seccion"])

    # La comparativa contra el mes anterior es lo más informativo del resumen,
    # por eso va en una columna propia y no como nota al pie.
    filas = [
        ["Indicador", "Mes actual", "vs mes anterior"],
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


def _seccion_monotributo(pago: dict, estilos) -> list:
    encabezado = Paragraph("Estado fiscal — Monotributo", estilos["Seccion"])

    if not pago.get("tiene_categoria"):
        nota = Paragraph(
            "El usuario no tiene cargada una categoría de Monotributo.",
            estilos["Normal"],
        )
        return [encabezado, nota]

    estado_pago = "Pagada" if pago["pagado"] else "Sin registrar"
    filas = [
        ["Concepto", "Valor"],
        ["Categoría actual", pago["categoria"]],
        ["Límite anual de la categoría", _fmt_pesos(pago["limite_anual"])],
        ["Cuota mensual", _fmt_pesos(pago["cuota_mensual"])],
        ["Cuota del período", estado_pago],
    ]
    tabla = _tabla_estandar(filas, col_widths=[8 * cm, 8 * cm])
    return [encabezado, tabla]


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
    encabezado = Paragraph("Auditoría — alertas pendientes", estilos["Seccion"])

    if not alertas:
        return [encabezado, Paragraph("Sin alertas pendientes al momento de generar el reporte.", estilos["Normal"])]

    # Conteo por tipo para el bloque resumen.
    from collections import Counter
    conteo = Counter(a.tipo.value for a in alertas)
    resumen_lineas = [["Tipo", "Cantidad"]] + [[t, str(c)] for t, c in conteo.items()]
    tabla_resumen = _tabla_estandar(resumen_lineas, col_widths=[10 * cm, 4 * cm])

    # Listado detallado: las descripciones son visibles porque el PDF es para
    # el dueño de los datos. La política de no exponer texto libre aplica solo
    # a transmisiones a servicios externos.
    detalle_lineas = [["Tipo", "Detalle", "Monto"]]
    for a in alertas[:20]:  # cap visual razonable: si hay más, se ve en la app.
        descripcion = a.descripcion or ""
        if len(descripcion) > 90:
            descripcion = descripcion[:87] + "..."
        detalle_lineas.append([
            a.tipo.value,
            descripcion,
            _fmt_pesos(a.monto_involucrado) if a.monto_involucrado else "—",
        ])
    tabla_detalle = _tabla_estandar(detalle_lineas, col_widths=[4 * cm, 9 * cm, 3 * cm])
    tabla_detalle.setStyle(TableStyle([
        ("ALIGN", (0, 1), (1, -1), "LEFT"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
    ]))

    return [encabezado, tabla_resumen, Spacer(1, 0.3 * cm), tabla_detalle]


def _seccion_pie(estilos) -> list:
    texto = (
        "Documento generado automáticamente por FreelanceControl. "
        "No reemplaza el asesoramiento de un contador matriculado."
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

    actual = _totales_mes(db, usuario_id, mes, anio)
    previo = _totales_mes(db, usuario_id, mes_prev, anio_prev)
    cats = _gastos_por_categoria(db, usuario_id, mes, anio)
    fact = _facturacion_mes(db, usuario_id, mes, anio)
    pago = _pago_monotributo(db, usuario_id, mes, anio)
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
    historia += _seccion_encabezado(usuario, mes, anio, estilos)
    historia += _seccion_resumen_ejecutivo(actual, previo, estilos)
    historia += _seccion_monotributo(pago, estilos)
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
