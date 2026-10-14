"""
Evalúa el modelo base con cross-validation 5-fold.

Reporta accuracy global, métricas por categoría y matriz de confusión. Se
usa para diagnosticar qué categorías están fallando antes de ampliar el
dataset, y para confirmar que la mejora funcionó después.

Al final suma tres mediciones sobre las mismas cinco particiones: la
comparación con Naive Bayes, la nota de cada vuelta (de dónde sale el
promedio) y qué pasa con los errores frente a la vara de confianza (cuántos
van a revisión en vez de guardarse con la categoría mal).

Ejecutar (desde Docker):
    docker compose exec api python evaluar_modelo.py
Con la versión local del script, sin reconstruir la imagen:
    docker compose exec -T api python - < evaluar_modelo.py
"""
import warnings

import numpy as np
from sklearn.model_selection import StratifiedKFold, cross_val_score

# scikit-learn 1.4 avisa en cada entrenamiento de LinearSVC que el valor por
# defecto de `dual` va a cambiar en la 1.5. No afecta el resultado y llenaba
# la salida de avisos: se silencian solo acá, no en la aplicación.
warnings.filterwarnings("ignore", category=FutureWarning)

from app.database import SessionLocal
from app.services import ml_service
from app.services.ia_service import UMBRAL_CONFIANZA_ML


def comparar_algoritmos(X: list, y: list) -> dict:
    """Exactitud de SVM y de Naive Bayes con las mismas cinco particiones."""
    return {
        algoritmo: float(cross_val_score(ml_service._crear_pipeline(algoritmo), X, y, cv=5).mean())
        for algoritmo in ("svm", "naive_bayes")
    }


def cinco_vueltas(X: list, y: list) -> list[tuple[float, int]]:
    """La nota de cada vuelta de la validación cruzada: (exactitud, cuántos gastos).

    Son las mismas cinco particiones que la exactitud global (StratifiedKFold
    sin mezclar, como cross_val_predict con cv=5): en cada vuelta el modelo
    aprende con cuatro partes y se lo evalúa con la quinta, que no vio. Como
    las cinco partes tienen el mismo tamaño, el promedio es la exactitud global.
    """
    X, y = np.array(X, dtype=object), np.array(y)
    notas = []
    for entreno, prueba in StratifiedKFold(n_splits=5).split(X, y):
        pipeline = ml_service._crear_pipeline("svm").fit(list(X[entreno]), list(y[entreno]))
        notas.append((float(np.mean(pipeline.predict(list(X[prueba])) == y[prueba])), len(prueba)))
    return notas


def medir_revision(X: list, y: list) -> dict:
    """Cruza la validación cruzada con la vara de confianza del clasificador.

    Cada ejemplo lo predice un modelo que no lo vio al entrenar, con las
    mismas cinco particiones que la exactitud (cross_val_predict con cv=5 usa
    StratifiedKFold sin mezclar). Debajo de UMBRAL_CONFIANZA_ML el sistema
    no pone la categoría: la manda a "Otros" para que el usuario la revise.
    """
    X, y = np.array(X, dtype=object), np.array(y)
    conteo = {"acierto_seguro": 0, "acierto_a_revision": 0, "error_a_revision": 0, "error_seguro": 0}
    for entreno, prueba in StratifiedKFold(n_splits=5).split(X, y):
        pipeline = ml_service._crear_pipeline("svm").fit(list(X[entreno]), list(y[entreno]))
        puntajes = pipeline.decision_function(list(X[prueba]))
        for fila, real in zip(puntajes, y[prueba]):
            idx, confianza = ml_service._confianza_svm(fila)
            acierto = "acierto" if pipeline.classes_[idx] == real else "error"
            destino = "seguro" if confianza >= UMBRAL_CONFIANZA_ML else "a_revision"
            conteo[f"{acierto}_{destino}"] += 1
    return conteo


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
        encabezado = "real / pred"
        print(f"  {encabezado:<18}", end="")
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

        X = [desc for desc, _ in ml_service.DATASET_BASE]
        y = [cat for _, cat in ml_service.DATASET_BASE]

        exactitudes = comparar_algoritmos(X, y)
        print("\n── Comparación con Naive Bayes (mismas 5 particiones) ──")
        print(f"  SVM          {exactitudes['svm'] * 100:5.1f} %")
        print(f"  Naive Bayes  {exactitudes['naive_bayes'] * 100:5.1f} %")

        notas = cinco_vueltas(X, y)
        print("\n── Las cinco vueltas: cada una, un examen con gastos que no vio ──")
        for i, (nota, n) in enumerate(notas, 1):
            print(f"  Vuelta {i}   {nota * 100:5.1f} %   ({n} gastos)")
        print(f"  Promedio   {np.mean([nota for nota, _ in notas]) * 100:5.1f} %")

        c = medir_revision(X, y)
        errores = c["error_a_revision"] + c["error_seguro"]
        sin_dudar = c["acierto_seguro"] + c["error_seguro"]
        print(f"\n── Qué pasa con los errores (vara de confianza {UMBRAL_CONFIANZA_ML:.0%}) ──")
        print(f"  Acertó y estaba seguro         {c['acierto_seguro']:>4}")
        print(f"  Acertó, pero pidió revisión    {c['acierto_a_revision']:>4}")
        print(f"  Se equivocó y pidió revisión   {c['error_a_revision']:>4}")
        print(f"  Se equivocó estando seguro     {c['error_seguro']:>4}")
        print(f"  De los {errores} errores, {c['error_a_revision']} "
              f"({c['error_a_revision'] / errores:.0%}) van a revisión en vez de guardarse mal.")
        print(f"  Cuando pone una categoría sin dudar, acierta el "
              f"{c['acierto_seguro'] / sin_dudar:.0%}.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
