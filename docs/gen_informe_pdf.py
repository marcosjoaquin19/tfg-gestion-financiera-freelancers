"""
Genera el PDF de los capítulos de cierre del informe (Implementación, Pruebas,
Conclusiones) con los gráficos de métricas embebidos como anexo.
"""
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image,
    HRFlowable, Table, TableStyle
)

OUT = "/Users/marcosjoaquin/proyecto-tfg/docs/FreelanceControl_Informe_Capitulos.pdf"
MD = "/Users/marcosjoaquin/proyecto-tfg/docs/informe_capitulos.md"
DOCS = "/Users/marcosjoaquin/proyecto-tfg/docs"

AZUL = colors.HexColor("#1a237e")
AZUL_MED = colors.HexColor("#1565c0")
GRIS = colors.HexColor("#37474f")

s = getSampleStyleSheet()
s.add(ParagraphStyle("Tit", parent=s["Title"], fontSize=26, textColor=AZUL,
    alignment=TA_CENTER, spaceAfter=6))
s.add(ParagraphStyle("Sub", parent=s["Normal"], fontSize=13, textColor=GRIS,
    alignment=TA_CENTER, spaceAfter=4))
s.add(ParagraphStyle("Cap", parent=s["Heading1"], fontSize=19, textColor=AZUL,
    spaceBefore=16, spaceAfter=10, fontName="Helvetica-Bold"))
s.add(ParagraphStyle("Sec", parent=s["Heading2"], fontSize=13, textColor=AZUL_MED,
    spaceBefore=12, spaceAfter=6, fontName="Helvetica-Bold"))
s.add(ParagraphStyle("Cuerpo", parent=s["Normal"], fontSize=10.5, leading=16,
    alignment=TA_JUSTIFY, spaceAfter=8, fontName="Helvetica"))
s.add(ParagraphStyle("Cap2", parent=s["Heading1"], fontSize=19, textColor=AZUL,
    spaceBefore=16, spaceAfter=10, fontName="Helvetica-Bold", alignment=TA_CENTER))
s.add(ParagraphStyle("PieFig", parent=s["Normal"], fontSize=8.5, textColor=GRIS,
    alignment=TA_CENTER, spaceBefore=4, spaceAfter=12, fontName="Helvetica-Oblique"))

story = []

# Portada
story.append(Spacer(1, 5*cm))
story.append(Paragraph("FreelanceControl", s["Tit"]))
story.append(Paragraph("Informe final — Capítulos de cierre", s["Sub"]))
story.append(Spacer(1, 0.3*cm))
story.append(Paragraph("Implementación · Pruebas · Conclusiones", s["Sub"]))
story.append(Spacer(1, 1.5*cm))
story.append(HRFlowable(width="60%", thickness=1.2, color=AZUL_MED))
story.append(Spacer(1, 0.5*cm))
story.append(Paragraph("Trabajo Final de Grado — Ingeniería en Sistemas de Información",
    s["Sub"]))
story.append(Paragraph(f"Versión al {datetime.now().strftime('%d/%m/%Y')}", s["Sub"]))
story.append(PageBreak())

# Parsear el Markdown de forma sencilla
def render_md(path):
    elems = []
    with open(path) as f:
        lineas = f.readlines()
    buffer_parrafo = []

    def flush():
        if buffer_parrafo:
            texto = " ".join(buffer_parrafo).strip()
            if texto:
                # negritas **x** -> <b>x</b>
                import re
                texto = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", texto)
                elems.append(Paragraph(texto, s["Cuerpo"]))
            buffer_parrafo.clear()

    for linea in lineas:
        l = linea.rstrip("\n")
        ls = l.strip()
        if ls.startswith("> ") or ls == ">":
            continue  # saltar blockquote del encabezado del borrador
        if ls.startswith("# "):
            continue  # título del documento, ya tenemos portada
        if ls == "---":
            flush()
            continue
        if ls.startswith("## "):
            flush()
            titulo = ls[3:].strip()
            elems.append(PageBreak())
            elems.append(Paragraph(titulo, s["Cap"]))
            elems.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#bdbdbd"),
                spaceAfter=8))
            continue
        if ls.startswith("### "):
            flush()
            elems.append(Paragraph(ls[4:].strip(), s["Sec"]))
            continue
        if ls == "":
            flush()
            continue
        buffer_parrafo.append(ls)
    flush()
    return elems

story += render_md(MD)

# Anexo con gráficos
story.append(PageBreak())
story.append(Paragraph("Anexo — Métricas del clasificador", s["Cap2"]))
story.append(Spacer(1, 0.4*cm))
story.append(Paragraph(
    "Resultados de la evaluación del modelo base mediante validación cruzada de "
    "cinco particiones sobre 600 ejemplos etiquetados. Exactitud global: 76,00%.",
    s["Cuerpo"]))
story.append(Spacer(1, 0.5*cm))

img1 = Image(f"{DOCS}/metricas_f1_por_categoria.png", width=15*cm, height=10.9*cm)
story.append(img1)
story.append(Paragraph("Figura 1. Precision, recall y F1-score por categoría.", s["PieFig"]))

story.append(PageBreak())
story.append(Paragraph("Anexo — Matriz de confusión", s["Cap2"]))
story.append(Spacer(1, 0.4*cm))
img2 = Image(f"{DOCS}/metricas_matriz_confusion.png", width=15*cm, height=13*cm)
story.append(img2)
story.append(Paragraph(
    "Figura 2. Matriz de confusión (filas = categoría real, columnas = predicción). "
    "El color indica la proporción por fila; la diagonal verde marca los aciertos.",
    s["PieFig"]))

def pie(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(2*cm, 1.2*cm, "FreelanceControl — Informe final")
    canvas.drawRightString(A4[0]-2*cm, 1.2*cm, f"Página {doc.page}")
    canvas.restoreState()

doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=2.2*cm, rightMargin=2.2*cm,
    topMargin=2*cm, bottomMargin=2*cm,
    title="FreelanceControl — Informe final (capítulos de cierre)")
doc.build(story, onFirstPage=pie, onLaterPages=pie)
print("PDF generado:", OUT)
