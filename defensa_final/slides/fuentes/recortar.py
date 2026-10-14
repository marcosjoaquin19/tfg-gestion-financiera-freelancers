"""Recorta las capturas del 14/10 para las filminas. Coordenadas en píxeles de pantalla
(viewport 1336×758 a 2x → se multiplican por 2). Tapa las fechas que pone la base al guardar
(la simulación corrió el 6/10 con el reloj de la API en el 14/10)."""
from PIL import Image, ImageDraw
SRC = "capturas"; DST = "/Users/marcosjoaquin/proyecto-tfg/defensa_final/slides/capturas"
K = 2672 / 2000   # las coordenadas las medí sobre la vista de 2000 px de ancho

def caja(c): return tuple(round(v * K) for v in c)
def tapar(im, zonas, muestra):
    d = ImageDraw.Draw(im); color = im.getpixel(caja(muestra))
    for z in zonas: d.rectangle(caja(z), fill=color)
def guardar(nombre, origen, recorte, zonas=(), muestra=None, ancho=None):
    im = Image.open(f"{SRC}/{origen}").convert("RGB")
    if zonas: tapar(im, zonas, muestra)
    im = im.crop(caja(recorte))
    if ancho and im.width > ancho:
        im = im.resize((ancho, round(im.height * ancho / im.width)), Image.LANCZOS)
    im.save(f"{DST}/{nombre}.png", optimize=True); print(nombre, im.size)

FECHA_ML = [(680, 240, 1000, 272)]               # "Último entrenamiento: 6/10/2026"
guardar("dashboard", "04_dashboard_despues.png", (300, 72, 2000, 900), ancho=2000)
guardar("aviso_alcance", "16_monotributo.png", (336, 824, 1965, 948))
guardar("importacion_vista_previa", "02_import_preview.png", (300, 72, 2000, 1135), ancho=2000)
guardar("importacion_resultado", "03_import_resultado.png", (520, 105, 1500, 845))
for origen, nombre in [("06_jetbrains.png", "clasif_jetbrains"), ("21_mostaza_antes.png", "clasif_mostaza"),
                       ("20_mostaza_palermo_antes.png", "clasif_mostaza_palermo_antes"),
                       ("23_mostaza_corregido.png", "clasif_mostaza_corregido"),
                       ("24_mostaza_palermo_despues.png", "clasif_mostaza_palermo_despues")]:
    guardar(nombre, origen, (373, 540, 1197, 1071))
guardar("clasif_modelo_propio", "12_clasificador_estado_final.png", (336, 172, 1234, 351), FECHA_ML, (1100, 300))
# Auditoría: la fecha de alta de cada alerta (gris, debajo del monto)
FECHAS_AUD = [(552, y - 14, 690, y + 14) for y in (510, 655, 800, 945, 1090)]
guardar("auditoria", "15_auditoria.png", (300, 72, 2000, 1135), FECHAS_AUD, (1000, 530), ancho=2000)
guardar("monotributo", "16_monotributo.png", (300, 72, 2000, 960), ancho=2000)
guardar("monotributo_semaforo", "16_monotributo.png", (336, 205, 1965, 652))
CALCULADA = [(1600, 210, 1950, 255)]
guardar("proyecciones", "17_proyecciones.png", (300, 72, 2000, 1060), CALCULADA, (1500, 200), ancho=2000)
guardar("proyecciones_grafico", "17_proyecciones.png", (336, 444, 1965, 1056))
guardar("recomendaciones", "18_recomendaciones.png", (300, 72, 2000, 1135), ancho=2000)
guardar("recomendacion_por_que", "18_recomendaciones.png", (336, 512, 1384, 791))
guardar("recomendaciones_dos", "18_recomendaciones.png", (336, 185, 1384, 791))
for i in (1, 2):
    hoja = Image.open(f"{SRC}/19_pdf-{i}.png").convert("RGBA")      # sips deja el fondo transparente
    im = Image.new("RGB", hoja.size, "white"); im.paste(hoja, mask=hoja.split()[3]); im.save(f"{DST}/reporte_pdf_{i}.png", optimize=True); print("reporte_pdf", i, im.size)
