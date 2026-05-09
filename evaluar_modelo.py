"""
Evalúa el modelo base con cross-validation 5-fold.

Reporta accuracy global, métricas por categoría y matriz de confusión. Se
usa para diagnosticar qué categorías están fallando antes de ampliar el
dataset, y para confirmar que la mejora funcionó después.

Ejecutar (desde Docker):
    docker compose exec api python evaluar_modelo.py
"""
from app.database import SessionLocal
from app.services import ml_service


def main():
    db = SessionLocal()
    try:
        resultado = ml_service.evaluar_modelo_base(db)

        print("=" * 78)
        print(f"  EVALUACIÓN DEL MODELO BASE — algoritmo: {resultado['algoritmo']}")
        print(f"  Total de ejemplos: {resultado['n_ejemplos_total']}")
        print(f"  Accuracy global: {resultado['accuracy_global']:.4f}  "
              f"({resultado['accuracy_global'] * 100:.2f}%)")
        print("=" * 78)

        # Métricas por categoría, ordenadas por f1 ascendente para ver primero las peores.
        print("\n── Métricas por categoría (ordenadas de peor a mejor f1) ──")
        print(f"  {'Categoría':<18} {'Precision':>10} {'Recall':>10} {'F1':>10} {'N':>4}")
        print(f"  {'-' * 56}")
        items = sorted(
            resultado["por_categoria"].items(),
            key=lambda kv: kv[1]["f1"],
        )
        for cat, m in items:
            print(f"  {cat:<18} {m['precision']:>10.3f} {m['recall']:>10.3f} "
                  f"{m['f1']:>10.3f} {m['support']:>4d}")

        # Matriz de confusión: las filas son la categoría real, las columnas la predicción.
        # Leer la matriz: mirar la diagonal (aciertos) y los off-diagonal (confusiones).
        print("\n── Matriz de confusión (filas=real, columnas=predicho) ──")
        labels = resultado["matriz_confusion"]["labels"]
        matriz = resultado["matriz_confusion"]["matriz"]

        # Encabezado con etiquetas truncadas
        print(f"  {'real \\ pred':<18}", end="")
        for lbl in labels:
            print(f"{lbl[:5]:>6}", end="")
        print()

        for i, lbl in enumerate(labels):
            print(f"  {lbl:<18}", end="")
            for j in range(len(labels)):
                val = matriz[i][j]
                # Diagonal en negrita visual con paréntesis si quisiéramos.
                marker = "" if i != j else "*"
                print(f"{val:>5}{marker:<1}", end="")
            print()
        print()
        print("(* indica aciertos, valores fuera de la diagonal son confusiones)")

    finally:
        db.close()


if __name__ == "__main__":
    main()
