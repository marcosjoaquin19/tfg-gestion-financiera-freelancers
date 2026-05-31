"""Genera los gráficos de métricas del clasificador para el informe.

Datos REALES tomados de evaluar_modelo.py (cross-validation 5-fold sobre el
modelo base SVM de 600 ejemplos). Ver docs/metricas_clasificador.txt.

Produce:
  - docs/metricas_f1_por_categoria.png  (barras horizontales de F1)
  - docs/metricas_matriz_confusion.png  (heatmap)

Reproducible: python3 docs/gen_graficos_metricas.py
"""
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

OUT_DIR = "/Users/marcosjoaquin/proyecto-tfg/docs"

# ── Datos reales (de docs/metricas_clasificador.txt) ─────────────────────────
ACCURACY = 0.76
N_EJEMPLOS = 600

# (categoria, precision, recall, f1)  — ordenadas peor→mejor f1
METRICAS = [
    ("Otros",           0.500, 0.480, 0.489),
    ("Servicios",       0.604, 0.580, 0.592),
    ("Hardware",        0.681, 0.640, 0.660),
    ("Infraestructura", 0.760, 0.760, 0.760),
    ("Capacitación",    0.745, 0.760, 0.752),
    ("Software",        0.787, 0.740, 0.763),
    ("Marketing",       0.820, 0.820, 0.820),
    ("Suscripciones",   0.787, 0.820, 0.803),
    ("Transporte",      0.880, 0.880, 0.880),
    ("Alimentación",    0.843, 0.860, 0.851),
    ("Impuestos",       0.860, 0.860, 0.860),
    ("Monotributo",     0.860, 0.920, 0.889),
]

LABELS = ["Software", "Hardware", "Infraestructura", "Marketing", "Servicios",
          "Capacitación", "Suscripciones", "Transporte", "Alimentación",
          "Impuestos", "Monotributo", "Otros"]

# Matriz de confusión real (filas=real, columnas=predicho), mismo orden que LABELS
MATRIZ = [
    [37, 1, 3, 0, 2, 1, 2, 0, 0, 0, 0, 4],
    [2, 32, 3, 1, 1, 1, 1, 1, 0, 1, 0, 7],
    [1, 2, 38, 0, 1, 0, 1, 0, 0, 1, 0, 6],
    [0, 0, 0, 41, 3, 1, 1, 0, 0, 0, 0, 4],
    [2, 1, 1, 2, 29, 3, 0, 1, 2, 2, 1, 6],
    [1, 0, 0, 1, 2, 38, 2, 0, 0, 0, 0, 6],
    [1, 0, 1, 1, 0, 1, 41, 0, 0, 0, 1, 4],
    [0, 1, 0, 0, 1, 0, 0, 44, 1, 0, 0, 3],
    [0, 0, 0, 0, 1, 0, 0, 2, 43, 0, 0, 4],
    [0, 0, 0, 0, 1, 0, 0, 0, 1, 43, 2, 3],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 46, 2],
    [3, 2, 2, 1, 4, 2, 3, 2, 2, 1, 0, 24],
]


def grafico_f1():
    cats = [m[0] for m in METRICAS]
    f1 = [m[3] for m in METRICAS]
    precision = [m[1] for m in METRICAS]
    recall = [m[2] for m in METRICAS]

    y = np.arange(len(cats))
    h = 0.26

    fig, ax = plt.subplots(figsize=(11, 8))
    # Color por umbral de f1
    def color_f1(v):
        if v >= 0.80: return "#2e7d32"
        if v >= 0.65: return "#f9a825"
        return "#c62828"

    ax.barh(y + h, precision, h, label="Precision", color="#90caf9", edgecolor="white")
    ax.barh(y,     recall,    h, label="Recall",    color="#5e9cd6", edgecolor="white")
    barras_f1 = ax.barh(y - h, f1, h, label="F1-score",
                        color=[color_f1(v) for v in f1], edgecolor="white")

    # Etiquetas de valor en las barras de F1
    for rect, v in zip(barras_f1, f1):
        ax.text(v + 0.01, rect.get_y() + rect.get_height()/2, f"{v:.2f}",
                va="center", ha="left", fontsize=8, fontweight="bold",
                color="#263238")

    ax.set_yticks(y)
    ax.set_yticklabels(cats, fontsize=10)
    ax.set_xlim(0, 1.05)
    ax.set_xlabel("Score", fontsize=11)
    ax.set_title("Métricas del clasificador por categoría\n"
                 f"Modelo base SVM · {N_EJEMPLOS} ejemplos · cross-validation 5-fold · "
                 f"accuracy global {ACCURACY*100:.0f}%",
                 fontsize=12, fontweight="bold", pad=14)
    ax.axvline(0.80, color="#2e7d32", linestyle=":", linewidth=1, alpha=0.6)
    ax.axvline(0.30, color="#c62828", linestyle=":", linewidth=1, alpha=0.5)
    ax.text(0.30, len(cats)-0.3, " umbral de revisión (0.30)", fontsize=7.5,
            color="#c62828", va="top")
    ax.legend(loc="lower right", fontsize=9, framealpha=0.95)
    ax.grid(axis="x", linestyle="--", alpha=0.3)
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/metricas_f1_por_categoria.png", dpi=160,
                bbox_inches="tight", facecolor="white")
    plt.close()
    print("OK: metricas_f1_por_categoria.png")


def grafico_matriz():
    matriz = np.array(MATRIZ)
    n = len(LABELS)
    # Normalizar por fila (recall visual) para el color, pero mostrar conteos
    matriz_norm = matriz / matriz.sum(axis=1, keepdims=True)

    fig, ax = plt.subplots(figsize=(11, 9.5))
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "azul", ["#ffffff", "#bbdefb", "#1565c0", "#0d3c75"])
    im = ax.imshow(matriz_norm, cmap=cmap, vmin=0, vmax=1, aspect="auto")

    ax.set_xticks(np.arange(n))
    ax.set_yticks(np.arange(n))
    ax.set_xticklabels(LABELS, rotation=45, ha="right", fontsize=9)
    ax.set_yticklabels(LABELS, fontsize=9)
    ax.set_xlabel("Predicho", fontsize=11, fontweight="bold")
    ax.set_ylabel("Real", fontsize=11, fontweight="bold")
    ax.set_title("Matriz de confusión del clasificador\n"
                 f"Modelo base SVM · {N_EJEMPLOS} ejemplos · color = proporción por fila (recall)",
                 fontsize=12, fontweight="bold", pad=14)

    # Anotar cada celda con el conteo
    for i in range(n):
        for j in range(n):
            val = matriz[i][j]
            if val == 0:
                continue
            color = "white" if matriz_norm[i][j] > 0.5 else "#263238"
            peso = "bold" if i == j else "normal"
            ax.text(j, i, str(val), ha="center", va="center",
                    fontsize=8, color=color, fontweight=peso)

    # Resaltar la diagonal con un borde
    for i in range(n):
        ax.add_patch(plt.Rectangle((i-0.5, i-0.5), 1, 1, fill=False,
                                    edgecolor="#2e7d32", linewidth=1.8))

    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Proporción por categoría real", fontsize=9)

    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/metricas_matriz_confusion.png", dpi=160,
                bbox_inches="tight", facecolor="white")
    plt.close()
    print("OK: metricas_matriz_confusion.png")


if __name__ == "__main__":
    grafico_f1()
    grafico_matriz()
