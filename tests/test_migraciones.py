"""
El modelo del código tiene que coincidir con lo que crean las migraciones
(HU-15). Si no, una migración autogenerada a partir del modelo propondría
cambios que nadie pidió, como borrar los índices de la migración 0005.
"""

import importlib.util
from pathlib import Path

from app.database import Base
import app.models  # noqa: F401  registra todas las tablas en Base.metadata

VERSIONES = Path(__file__).resolve().parent.parent / "alembic" / "versions"


def _migracion(prefijo: str):
    archivo = next(VERSIONES.glob(f"{prefijo}_*.py"))
    spec = importlib.util.spec_from_file_location(archivo.stem, archivo)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def test_el_modelo_declara_los_indices_de_la_migracion_0005():
    for nombre, tabla, columnas in _migracion("0005").INDICES:
        indices = {i.name: [c.name for c in i.columns] for i in Base.metadata.tables[tabla].indexes}
        assert indices.get(nombre) == columnas, f"{tabla} no declara el índice {nombre}"


def test_columnas_obligatorias_del_modelo_del_clasificador():
    tabla = Base.metadata.tables["modelos_clasificador"]
    for columna in ("n_ejemplos", "fecha_entrenamiento", "activo"):
        assert tabla.c[columna].nullable is False, columna
