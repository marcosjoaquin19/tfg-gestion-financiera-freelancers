"""
Router de Importación — carga masiva desde extractos bancarios.

Expone bajo /importar la subida de extractos en CSV/XLSX. El flujo: el usuario
sube el archivo, el sistema detecta automáticamente las columnas (fecha, monto,
descripción), clasifica cada movimiento como ingreso o gasto, marca posibles
duplicados y, tras la confirmación del usuario, guarda los movimientos en la BD.
La lógica de parseo y clasificación vive en csv_service.

Los ingresos que entran por acá pasan por la misma revisión de carga repetida
que los cargados a mano (routers/ingresos.py), para que la marca y el filtro
"Solo duplicados" se comporten igual venga el dato de donde venga.
"""

import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel, Field, field_validator, model_validator
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.models.ingreso import Ingreso
from app.models.gasto import Gasto
from app.dependencies import get_current_user
from app.services.duplicados_ingreso import _actualizar_marca_duplicado
from app.services.categorias_ingreso import CATEGORIAS_INGRESO
from app.services.ml_service import CATEGORIAS_VALIDAS as CATEGORIAS_GASTO
from app.services.csv_service import (
    clasificar_movimientos,
    detectar_columnas_csv,
    detectar_posibles_duplicados,
    detectar_transferencias_propias_en_lote,
    filtrar_no_duplicados,
    leer_dataframe,
    procesar_csv,
)
from datetime import datetime

router = APIRouter(prefix="/importar", tags=["Importar"])

# Validación previa del archivo importado (Objetivo Específico 1 — TFG).
# Soportamos CSV (estándar de exportación bancaria) y XLSX (formato moderno
# de Excel). Para .xls antiguo el usuario tiene que convertir desde el banco
# o desde su Excel/LibreOffice — agregar soporte requeriría xlrd<2.0 que ya
# no se mantiene activamente.
EXTENSIONES_PERMITIDAS = {".csv", ".xlsx"}
TAMANO_MAXIMO_BYTES = 10 * 1024 * 1024  # 10 MB


# ── Schemas ───────────────────────────────────────────────────────────────────

class MovimientoImportar(BaseModel):
    fecha: str
    descripcion: str = Field(max_length=255)
    monto: float = Field(allow_inf_nan=False)
    tipo: str
    categoria: str

    # Mismas reglas que la carga manual de ingresos y gastos. /confirmar
    # recibe la lista que armó el preview, pero es un endpoint como cualquier
    # otro: sin estos controles, un monto negativo o NaN se guardaba tal cual,
    # y uno fuera de rango hacía fallar la importación con un error 500.
    @field_validator("descripcion")
    @classmethod
    def descripcion_no_vacia(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("La descripción no puede estar vacía")
        return v

    @field_validator("monto")
    @classmethod
    def monto_valido(cls, v):
        if v <= 0:
            raise ValueError("El monto debe ser mayor a cero")
        if v >= 10 ** 10:
            raise ValueError("El monto supera el máximo admitido (10.000.000.000)")
        return v

    @model_validator(mode="after")
    def categoria_valida_segun_el_tipo(self):
        """La categoría tiene que existir en el catálogo del tipo de movimiento.

        Ingresos y gastos usan catálogos distintos: el clasificador de ML
        trabaja con categorías de gasto, y el módulo de ingresos tiene las
        suyas. En la práctica el preview ya asigna una válida, pero /confirmar
        es un endpoint como cualquier otro y puede recibir una llamada directa;
        sin esta validación entraba texto libre y los totales por categoría del
        Dashboard y del PDF se fragmentaban.
        """
        catalogos = {"ingreso": CATEGORIAS_INGRESO, "gasto": CATEGORIAS_GASTO}
        validas = catalogos.get(self.tipo)
        if validas is None:
            raise ValueError("El tipo de movimiento debe ser 'ingreso' o 'gasto'")
        if self.categoria not in validas:
            raise ValueError(
                f"Categoría inválida para un {self.tipo}. "
                "Las válidas son: " + ", ".join(validas)
            )
        return self


class ConfirmarRequest(BaseModel):
    movimientos: list[MovimientoImportar]
    mapeo: dict


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/preview")
async def preview_csv(
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    nombre = archivo.filename or ""
    extension = os.path.splitext(nombre)[1].lower()
    if extension not in EXTENSIONES_PERMITIDAS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Formato no soportado. Extensiones permitidas: {', '.join(sorted(EXTENSIONES_PERMITIDAS))}",
        )

    contenido_bytes = await archivo.read()

    if len(contenido_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo está vacío.",
        )
    if len(contenido_bytes) > TAMANO_MAXIMO_BYTES:
        limite_mb = TAMANO_MAXIMO_BYTES // (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"El archivo supera el tamaño máximo permitido ({limite_mb} MB).",
        )

    # Toda la lógica posterior trabaja sobre un DataFrame, sin importar si
    # vino de .csv o .xlsx. leer_dataframe se encarga de elegir el motor.
    df = leer_dataframe(contenido_bytes, extension)
    if df is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo leer el archivo. Verificá que sea un CSV o Excel válido.",
        )

    mapeo = detectar_columnas_csv(df, db)
    if not mapeo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo detectar la estructura del archivo. Verificá que tenga encabezados claros (fecha, descripción, monto).",
        )

    # Filas que no se pudieron leer (sin fecha, importe ilegible, etc.): se
    # informan en la respuesta para que el usuario sepa qué quedó afuera.
    filas_omitidas: list[dict] = []
    todos = procesar_csv(df, mapeo, omitidas=filas_omitidas)
    if not todos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se encontraron movimientos válidos en el archivo.",
        )

    # La detección de duplicados y la clasificación se aplican sobre el lote
    # COMPLETO, no solo sobre las 20 filas que el frontend muestra: el paso
    # /confirmar persiste exactamente la lista que devolvemos acá, así que si
    # clasificáramos solo una parte, el resto del archivo se perdería en la
    # importación. El recorte a 20 filas es solo visual y lo hace el cliente.
    todos_marcados = detectar_posibles_duplicados(db, current_user.id, todos)
    # Pares ingreso/gasto del mismo archivo con pinta de transferencia entre
    # cuentas propias: se marcan para omitirlos (no son facturación real).
    todos_marcados = detectar_transferencias_propias_en_lote(todos_marcados)
    posibles_duplicados = sum(1 for m in todos_marcados if m.get("posible_duplicado"))
    transferencias_propias = sum(
        1 for m in todos_marcados
        if m.get("posible_transferencia_propia") and not m.get("posible_duplicado")
    )

    preview = clasificar_movimientos(todos_marcados, db, current_user.id)

    return {
        "total_filas": len(todos),
        "preview": preview,
        "mapeo_detectado": mapeo,
        "filas_omitidas": filas_omitidas,
        "resumen": {
            "total": len(todos),
            "omitidas": len(filas_omitidas),
            "nuevos": len(todos) - posibles_duplicados - transferencias_propias,
            "posibles_duplicados": posibles_duplicados,
            "transferencias_propias": transferencias_propias,
        },
    }


@router.post("/confirmar")
def confirmar_importacion(
    datos: ConfirmarRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    ingresos_nuevos = []
    gastos_nuevos = []

    # Red de seguridad: aunque el frontend ya filtre lo que el usuario marcó
    # como duplicado en el preview, volvemos a aplicar la detección server-side
    # antes de persistir. Si alguien llama directo al endpoint sin pasar por
    # el preview (por ejemplo desde un script), la idempotencia se mantiene.
    movimientos_dict = [m.model_dump() for m in datos.movimientos]
    a_importar, omitidos_por_duplicado, omitidos_por_transferencia = filtrar_no_duplicados(
        db, current_user.id, movimientos_dict,
    )

    # Validación previa de fechas, ANTES de abrir la transacción.
    # Antes, una fecha ilegible se reemplazaba en silencio por datetime.now():
    # un movimiento de mayo quedaba registrado como de hoy, lo que además
    # desplaza el período fiscal al que se imputa. Un registro que no se puede
    # interpretar tiene que frenar la importación completa, no inventarse.
    fechas = {}
    for i, mov in enumerate(a_importar):
        try:
            fechas[i] = datetime.fromisoformat(mov["fecha"])
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"El movimiento {i + 1} ('{mov.get('descripcion', '')[:60]}') tiene una "
                    f"fecha ilegible: '{mov.get('fecha')}'. No se importó ningún registro."
                ),
            )

    # Persistencia transaccional atómica (Objetivo Específico 1 — TFG):
    # si falla cualquier inserción, se revierte la operación completa
    # y ningún registro parcial queda en la base de datos.
    try:
        for i, mov in enumerate(a_importar):
            fecha = fechas[i]

            if mov["tipo"] == "ingreso":
                ingresos_nuevos.append(Ingreso(
                    usuario_id=current_user.id,
                    descripcion=mov["descripcion"],
                    monto=mov["monto"],
                    categoria=mov["categoria"],
                    fecha=fecha,
                ))
            elif mov["tipo"] == "gasto":
                gastos_nuevos.append(Gasto(
                    usuario_id=current_user.id,
                    descripcion=mov["descripcion"],
                    monto=mov["monto"],
                    categoria=mov["categoria"],
                    fecha=fecha,
                ))

        db.add_all(ingresos_nuevos)
        db.add_all(gastos_nuevos)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al persistir la importación. La operación fue revertida y no se cargaron registros parciales. ({type(e).__name__})",
        )

    # filtrar_no_duplicados ya descartó los movimientos que el archivo repetía
    # respecto de lo que había en la base. Queda el caso del archivo que trae
    # la misma línea dos veces adentro: ésas entran como nuevas, y acá se
    # marcan para que aparezcan en "Solo duplicados" igual que una carga
    # repetida hecha a mano. Se avisa, no se bloquea: dos cobros iguales el
    # mismo día son posibles y la decisión es del usuario.
    #
    # Los gastos no lo necesitan: el módulo de Auditoría tiene su propio
    # detector de gastos duplicados (detectar_gastos_duplicados), que los
    # ingresos no tienen.
    ingresos_marcados = 0
    if ingresos_nuevos:
        hubo_cambios = False
        for ingreso in ingresos_nuevos:
            if _actualizar_marca_duplicado(db, ingreso):
                hubo_cambios = True
        if hubo_cambios:
            db.commit()
        ingresos_marcados = sum(1 for i in ingresos_nuevos if i.es_duplicado)

    return {
        "importados": len(ingresos_nuevos) + len(gastos_nuevos),
        "ingresos_creados": len(ingresos_nuevos),
        "gastos_creados": len(gastos_nuevos),
        "omitidos_por_duplicado": omitidos_por_duplicado,
        "omitidos_por_transferencia": omitidos_por_transferencia,
        "ingresos_marcados_duplicados": ingresos_marcados,
    }
