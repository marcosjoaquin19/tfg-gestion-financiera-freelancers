"""Genera docs/roadmap_final.png — mapa visual de lo que falta para terminar el TFG.

Reproducible: python3 docs/gen_roadmap.py
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

W, H = 16, 13
fig, ax = plt.subplots(figsize=(W, H))
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.axis("off")

# Paleta
C_DONE = "#2e7d32"   # verde
C_NOW = "#1565c0"    # azul
C_NEXT = "#5e35b1"   # violeta
C_FINAL = "#c62828"  # rojo
C_OPT = "#757575"    # gris
TXT = "white"


def caja(x, y, w, h, color, titulo, items):
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.05,rounding_size=0.15",
        linewidth=1.5, edgecolor=color, facecolor=color, alpha=0.93,
    )
    ax.add_patch(box)
    ax.text(x + w / 2, y + h - 0.30, titulo, ha="center", va="top",
            color=TXT, fontsize=11, fontweight="bold")
    for i, txt in enumerate(items):
        ax.text(x + 0.18, y + h - 0.75 - i * 0.28, txt,
                ha="left", va="top", color=TXT, fontsize=8.5)


def flecha(x1, y1, x2, y2, color="#37474f"):
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2), arrowstyle="->",
        mutation_scale=15, linewidth=1.4, color=color,
    ))


# Título
ax.text(W / 2, 12.55, "TFG FreelanceControl — Roadmap hasta la defensa",
        ha="center", fontsize=16, fontweight="bold", color="#263238")
ax.text(W / 2, 12.15, "Estado al 28-05-2026 · 97 tests verdes · 13/13 HU · 17/17 PB",
        ha="center", fontsize=10, color="#546e7a", style="italic")

# ─── SEMANA 2 ──────────────────────────────────────────────────────────────
y_s2 = 9.0
H_s2 = 1.8
ax.text(0.2, y_s2 + H_s2 + 0.25,
        "SEMANA 2 — Integración y pruebas del prototipo (en curso)",
        fontsize=11.5, fontweight="bold", color=C_NOW)

caja(0.2, y_s2, 3.0, H_s2, C_DONE, "S2.1 ✓ Prophet ↔ Monotributo",
     ["• Cold start verde",
      "• Prophet → semáforo rojo",
      "• meses_para_limite ok",
      "• Cambio categoría D→verde"])
caja(3.4, y_s2, 3.0, H_s2, C_DONE, "S2.2 ✓ Loop clasificador",
     ["• Cortocircuito conf 1.0",
      "• Tolerancia tipográfica",
      "• Reentreno background",
      "• fuente=correccion_usuario"])
caja(6.6, y_s2, 3.0, H_s2, C_DONE, "S2.3 ✓ Importación bancos",
     ["• Galicia (;)",
      "• Santander / Brubank",
      "• 4 edge cases (413, .pdf…)",
      "• Auto-detect separador"])
caja(9.8, y_s2, 3.0, H_s2, C_DONE, "S2.4 ✓ PDF denso",
     ["• 6 secciones rendering",
      "• Formato $AR consistente",
      "• 6 alertas reales",
      "• Bug formato corregido"])
caja(13.0, y_s2, 2.8, H_s2, C_NOW, "S2.5 ▶ Demo path",
     ["• Verificar seed_demo.py",
      "• Escribir DEMO.md",
      "• Guión paso a paso",
      "• Capturas reproducibles"])

# Flechas horizontales semana 2
for x in [3.2, 6.4, 9.6, 12.8]:
    flecha(x, y_s2 + H_s2 / 2, x + 0.18, y_s2 + H_s2 / 2,
           C_DONE if x < 12.8 else C_NOW)

# ─── SEMANA 3 ──────────────────────────────────────────────────────────────
y_s3 = 5.7
H_s3 = 2.0
ax.text(0.2, y_s3 + H_s3 + 0.25,
        "SEMANA 3 — Informe final de tesis",
        fontsize=11.5, fontweight="bold", color=C_NEXT)

caja(0.2, y_s3, 3.7, H_s3, C_NEXT, "Capítulos pendientes",
     ["• Implementación (decisiones)",
      "• Pruebas (suite + smoke)",
      "• Conclusiones",
      "• Trabajos futuros",
      "• Bibliografía actualizada"])
caja(4.1, y_s3, 3.7, H_s3, C_NEXT, "Métricas reales clasificador",
     ["• Correr evaluar_modelo.py",
      "• Accuracy / precision / recall",
      "• Matriz de confusión",
      "• Cross-validation k=5",
      "• Análisis por categoría"])
caja(8.0, y_s3, 3.7, H_s3, C_NEXT, "Manual de usuario",
     ["• Instalación (docker)",
      "• Onboarding (registro→cat)",
      "• Importar extractos",
      "• Interpretar semáforo",
      "• FAQ + troubleshooting"])
caja(11.9, y_s3, 3.9, H_s3, C_OPT, "Mejoras opcionales (no bloquean)",
     ["• Filtros por rango fechas",
      "• Endpoint stats/totales",
      "• Healthcheck BD compose",
      "• Logging estructurado",
      "• Paginación total_count"])

# ─── SEMANA 4 ──────────────────────────────────────────────────────────────
y_s4 = 2.0
H_s4 = 2.0
ax.text(0.2, y_s4 + H_s4 + 0.25,
        "SEMANA 4 — Defensa final",
        fontsize=11.5, fontweight="bold", color=C_FINAL)

caja(0.2, y_s4, 3.7, H_s4, C_FINAL, "Slides",
     ["• Problema + solución",
      "• Arquitectura + stack",
      "• Decisiones clave (ML local)",
      "• Métricas reales",
      "• Demo en vivo (5 min)"])
caja(4.1, y_s4, 3.7, H_s4, C_FINAL, "Demo guionada",
     ["• Login con seed_demo",
      "• Importar CSV banco",
      "• Clasificar + corregir",
      "• Auditoría 4 tipos",
      "• PDF descargable"])
caja(8.0, y_s4, 3.7, H_s4, C_FINAL, "Video backup",
     ["• Grabación demo (mp4)",
      "• Por si falla la red",
      "• Subtitulado opcional",
      "• Backup local + cloud",
      "• 5–7 min total"])
caja(11.9, y_s4, 3.9, H_s4, C_FINAL, "Preguntas anticipadas",
     ["• ¿Por qué ML local y no Groq?",
      "• ¿Cómo validás el clasificador?",
      "• ¿Escalabilidad multi-usuario?",
      "• ¿Qué pasa con AFIP real?",
      "• ¿Cómo manejás privacidad?"])

# ─── Flechas verticales entre semanas ──────────────────────────────────────
flecha(W / 2, y_s2 - 0.1, W / 2, y_s3 + H_s3 + 0.10)
flecha(W / 2, y_s3 - 0.1, W / 2, y_s4 + H_s4 + 0.10)

# ─── Leyenda ──────────────────────────────────────────────────────────────
leyenda = [
    (C_DONE, "Completado"),
    (C_NOW, "En curso / próximo"),
    (C_NEXT, "Pendiente — Semana 3"),
    (C_FINAL, "Pendiente — Semana 4"),
    (C_OPT, "Opcional / no bloquea"),
]
for i, (col, lbl) in enumerate(leyenda):
    rect = mpatches.Rectangle((0.4 + i * 3.0, 0.65), 0.35, 0.28, color=col, alpha=0.92)
    ax.add_patch(rect)
    ax.text(0.85 + i * 3.0, 0.79, lbl, fontsize=9, va="center", color="#263238")

ax.text(W / 2, 0.2,
        "Cada caja es un entregable concreto. Las flechas marcan dependencia temporal (semana 2 → 3 → 4).",
        ha="center", fontsize=8.7, color="#546e7a", style="italic")

plt.tight_layout()
plt.savefig("/Users/marcosjoaquin/proyecto-tfg/docs/roadmap_final.png",
            dpi=160, bbox_inches="tight", facecolor="white")
print("OK: docs/roadmap_final.png")
