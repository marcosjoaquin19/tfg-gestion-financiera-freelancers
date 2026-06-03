"""Genera docs/HANDOFF.pdf a partir de HANDOFF.md — versión legible en la carpeta.
Reproducible: python3 docs/gen_handoff_pdf.py
Parser Markdown mínimo (headings, tablas, listas, código, negrita) con ReportLab.
"""
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

SRC = "/Users/marcosjoaquin/proyecto-tfg/HANDOFF.md"
OUT = "/Users/marcosjoaquin/proyecto-tfg/docs/HANDOFF.pdf"

AZUL = colors.HexColor("#0D2B45")
AZUL2 = colors.HexColor("#1565c0")
TEAL = colors.HexColor("#1C7293")
GRIS = colors.HexColor("#37474f")
GRIS_CL = colors.HexColor("#f0f3f7")
BORDE = colors.HexColor("#c4ccd4")

st = getSampleStyleSheet()
st.add(ParagraphStyle("H1x", parent=st["Heading1"], fontSize=17, textColor=AZUL,
    spaceBefore=14, spaceAfter=7, fontName="Helvetica-Bold"))
st.add(ParagraphStyle("H2x", parent=st["Heading2"], fontSize=13, textColor=AZUL2,
    spaceBefore=10, spaceAfter=5, fontName="Helvetica-Bold"))
st.add(ParagraphStyle("H3x", parent=st["Heading3"], fontSize=11, textColor=TEAL,
    spaceBefore=8, spaceAfter=3, fontName="Helvetica-Bold"))
st.add(ParagraphStyle("Bodyx", parent=st["Normal"], fontSize=9.5, leading=14,
    alignment=TA_JUSTIFY, spaceAfter=5, fontName="Helvetica"))
st.add(ParagraphStyle("Bul", parent=st["Normal"], fontSize=9.5, leading=13.5,
    leftIndent=14, spaceAfter=2, fontName="Helvetica"))
st.add(ParagraphStyle("Codex", parent=st["Code"], fontSize=8, leading=11.5,
    backColor=GRIS_CL, borderPadding=6, leftIndent=4, spaceAfter=6))
st.add(ParagraphStyle("Quote", parent=st["Normal"], fontSize=9, leading=13,
    leftIndent=10, textColor=GRIS, fontName="Helvetica-Oblique", spaceAfter=5,
    backColor=colors.HexColor("#fbf8ee"), borderPadding=6))
st.add(ParagraphStyle("Cell", parent=st["Normal"], fontSize=8, leading=11, fontName="Helvetica"))
st.add(ParagraphStyle("CellH", parent=st["Normal"], fontSize=8, leading=11,
    fontName="Helvetica-Bold", textColor=colors.white))


def inline(t):
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`(.+?)`", r'<font face="Courier" size="8.5">\1</font>', t)
    t = re.sub(r"⭐", "(*)", t)
    return t


def cellpara(t, header=False):
    return Paragraph(inline(t), st["CellH"] if header else st["Cell"])


def build():
    with open(SRC) as f:
        lines = f.readlines()

    story = []
    i = 0
    code_buf = []
    in_code = False
    para_buf = []

    def flush_para():
        if para_buf:
            txt = " ".join(para_buf).strip()
            if txt:
                story.append(Paragraph(inline(txt), st["Bodyx"]))
            para_buf.clear()

    while i < len(lines):
        ln = lines[i].rstrip("\n")
        s = ln.strip()

        # bloques de código
        if s.startswith("```"):
            if in_code:
                story.append(Paragraph("<br/>".join(
                    c.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace(" ","&nbsp;")
                    for c in code_buf), st["Codex"]))
                code_buf = []
                in_code = False
            else:
                flush_para()
                in_code = True
            i += 1
            continue
        if in_code:
            code_buf.append(ln)
            i += 1
            continue

        # tablas
        if s.startswith("|") and i+1 < len(lines) and re.match(r"^\|[\s:|-]+\|", lines[i+1].strip()):
            flush_para()
            rows = []
            header = [c.strip() for c in s.strip("|").split("|")]
            rows.append(header)
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                rows.append(cells)
                i += 1
            ncol = len(header)
            avail = 17.0
            cw = [avail/ncol]*ncol
            data = [[cellpara(c, r==0) for c in row] for r,row in enumerate(rows)]
            t = Table(data, colWidths=[c*cm for c in cw], repeatRows=1)
            t.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,0),AZUL),
                ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, GRIS_CL]),
                ("GRID",(0,0),(-1,-1),0.4,BORDE),
                ("VALIGN",(0,0),(-1,-1),"TOP"),
                ("LEFTPADDING",(0,0),(-1,-1),4),("RIGHTPADDING",(0,0),(-1,-1),4),
                ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),
            ]))
            story.append(t)
            story.append(Spacer(1,5))
            continue

        # headings
        if s.startswith("# "):
            flush_para(); story.append(Paragraph(inline(s[2:]), st["H1x"]))
        elif s.startswith("## "):
            flush_para()
            story.append(HRFlowable(width="100%", thickness=0.6, color=BORDE, spaceAfter=3, spaceBefore=4))
            story.append(Paragraph(inline(s[3:]), st["H1x"]))
        elif s.startswith("### "):
            flush_para(); story.append(Paragraph(inline(s[4:]), st["H2x"]))
        elif s.startswith("> "):
            flush_para(); story.append(Paragraph(inline(s[2:]), st["Quote"]))
        elif re.match(r"^[-*] ", s):
            flush_para(); story.append(Paragraph("• "+inline(s[2:]), st["Bul"]))
        elif re.match(r"^- \[.\]", s):
            flush_para(); story.append(Paragraph("☐ "+inline(s[5:].strip()), st["Bul"]))
        elif s == "---" or s == "":
            flush_para()
        else:
            para_buf.append(s)
        i += 1
    flush_para()

    def footer(c, d):
        c.saveState(); c.setFont("Helvetica", 8); c.setFillColor(colors.grey)
        c.drawString(2*cm, 1.0*cm, "FreelanceControl — HANDOFF")
        c.drawRightString(A4[0]-2*cm, 1.0*cm, f"Pág. {d.page}")
        c.restoreState()

    doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm,
        topMargin=1.8*cm, bottomMargin=1.6*cm, title="FreelanceControl — HANDOFF")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print("PDF generado:", OUT)


if __name__ == "__main__":
    build()
