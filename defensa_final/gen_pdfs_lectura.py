"""
Genera versiones en PDF de los documentos de la defensa, para leerlos cómodo
(en papel, en el iPad, o anotándolos) sin depender de un editor de Markdown.

    python defensa_final/gen_pdfs_lectura.py

Salida: defensa_final/lectura/*.pdf

Los .md siguen siendo la fuente de verdad: estos PDF son una copia para lectura
y hay que regenerarlos cada vez que se toca un documento.
"""

import subprocess
import sys
from pathlib import Path

import markdown

RAIZ = Path(__file__).resolve().parent
SALIDA = RAIZ / "lectura"

# Documentos a convertir: archivo fuente → título que se imprime en la portada.
DOCUMENTOS = [
    ("README.md", "Defensa final — índice del material"),
    ("01_GUION_DEFENSA_35MIN.md", "Guion de defensa oral — 35 minutos"),
    ("02_ARQUITECTURA_Y_PATRONES.md", "Arquitectura y patrones de diseño"),
]

# Tipografía grande y medidas de lectura cómodas: estos documentos se leen
# enteros y varias veces, no se consultan salteado.
CSS = """
@page { size: A4; margin: 20mm 18mm 18mm 18mm; }
* { box-sizing: border-box; }
body {
  font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
  font-size: 11.5pt; line-height: 1.65; color: #16222E; margin: 0;
}
h1 { font-size: 22pt; color: #0D2B45; margin: 0 0 4pt; line-height: 1.25;
     border-bottom: 2.5pt solid #02C39A; padding-bottom: 6pt; }
h1 + p em, h1 + p strong { color: #4A5A68; }
h2 { font-size: 16pt; color: #0D2B45; margin: 24pt 0 8pt; line-height: 1.3;
     border-bottom: 0.75pt solid #DCE4EC; padding-bottom: 4pt;
     page-break-after: avoid; }
h3 { font-size: 13pt; color: #1C7293; margin: 18pt 0 6pt; page-break-after: avoid; }
h4 { font-size: 11.5pt; color: #1C7293; margin: 14pt 0 4pt; page-break-after: avoid; }
p { margin: 0 0 9pt; }
ul, ol { margin: 0 0 9pt; padding-left: 20pt; }
li { margin-bottom: 4pt; }
strong { color: #0D2B45; }

/* Las citas del guion son lo que efectivamente se dice en voz alta:
   van destacadas para poder encontrarlas de un vistazo al ensayar. */
blockquote {
  margin: 10pt 0; padding: 9pt 14pt; background: #F4F7FB;
  border-left: 3pt solid #1C7293; color: #2A3A48;
  page-break-inside: avoid;
}
blockquote p { margin: 0 0 6pt; }
blockquote p:last-child { margin-bottom: 0; }

code { font-family: "SF Mono", Menlo, Consolas, monospace; font-size: 9.5pt;
       background: #EDF2F7; padding: 1pt 4pt; border-radius: 3px; color: #14395E; }
pre { background: #0B1B2B; color: #CADCFC; padding: 10pt 12pt; border-radius: 5px;
      overflow-x: auto; page-break-inside: avoid; }
pre code { background: none; color: inherit; font-size: 9.5pt; padding: 0; }

table { border-collapse: collapse; width: 100%; margin: 10pt 0; font-size: 9.5pt;
        page-break-inside: avoid; }
th { background: #0D2B45; color: #fff; text-align: left; padding: 5pt 7pt; font-weight: 600; }
td { border-bottom: 0.5pt solid #DCE4EC; padding: 5pt 7pt; vertical-align: top; }
tr:nth-child(even) td { background: #F7FAFC; }

hr { border: none; border-top: 0.75pt solid #DCE4EC; margin: 20pt 0; }
a { color: #1C7293; text-decoration: none; }

/* Espacio en el margen derecho para anotar a mano sobre el papel. */
.portada { margin-bottom: 24pt; }
.portada .meta { color: #8FA3B5; font-size: 9.5pt; margin-top: 4pt; }
"""

PLANTILLA = """<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<title>{titulo}</title><style>{css}</style></head>
<body>
<div class="portada">
  <div class="meta">FreelanceControl · Defensa TFG · Marcos Gamaliel Joaquín · Legajo SOF02218</div>
</div>
{cuerpo}
</body></html>
"""


def convertir(origen: Path, destino: Path, titulo: str) -> None:
    texto = origen.read_text(encoding="utf-8")
    cuerpo = markdown.markdown(
        texto,
        extensions=["tables", "fenced_code", "sane_lists", "attr_list"],
    )
    html = PLANTILLA.format(titulo=titulo, css=CSS, cuerpo=cuerpo)

    tmp_html = destino.with_suffix(".html")
    tmp_html.write_text(html, encoding="utf-8")

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        navegador = p.chromium.launch()
        pagina = navegador.new_page()
        pagina.goto(tmp_html.as_uri())
        pagina.pdf(
            path=str(destino),
            format="A4",
            print_background=True,
            margin={"top": "18mm", "bottom": "16mm", "left": "16mm", "right": "16mm"},
            display_header_footer=True,
            header_template="<div></div>",
            footer_template=(
                '<div style="width:100%;font-size:8pt;color:#8FA3B5;'
                'font-family:-apple-system,Helvetica,Arial,sans-serif;'
                'padding:0 16mm;display:flex;justify-content:space-between;">'
                f"<span>{titulo}</span>"
                '<span class="pageNumber"></span></div>'
            ),
        )
        navegador.close()

    tmp_html.unlink()


def main() -> int:
    SALIDA.mkdir(exist_ok=True)
    for nombre, titulo in DOCUMENTOS:
        origen = RAIZ / nombre
        if not origen.exists():
            print(f"  ! falta {nombre}, lo salteo")
            continue
        destino = SALIDA / (origen.stem + ".pdf")
        convertir(origen, destino, titulo)
        kb = destino.stat().st_size // 1024
        print(f"  ✓ {destino.relative_to(RAIZ.parent)}  ({kb} KB)")

    # La presentación ya es un .pptx; se exporta a PDF con LibreOffice si está.
    pptx = RAIZ / "slides" / "FreelanceControl_Defensa_Final.pptx"
    if pptx.exists():
        try:
            subprocess.run(
                ["soffice", "--headless", "--convert-to", "pdf",
                 "--outdir", str(SALIDA), str(pptx)],
                check=True, capture_output=True, timeout=300,
            )
            print(f"  ✓ defensa_final/lectura/{pptx.stem}.pdf  (slides)")
        except Exception as e:
            print(f"  ! no pude exportar las slides a PDF ({e.__class__.__name__})")

    print(f"\nListo. Los PDF están en {SALIDA}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
