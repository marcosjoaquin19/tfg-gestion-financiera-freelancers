"""
Router de Importación — carga masiva desde extractos bancarios.

Expone bajo /importar la subida de extractos en CSV/XLSX. El flujo: el usuario
sube el archivo, el sistema detecta automáticamente las columnas (fecha, monto,
descripción), clasifica cada movimiento como ingreso o gasto, marca posibles
duplicados y, tras la confirmación del usuario, guarda los movimientos en la BD.
La lógica de parseo y clasificación vive en csv_service.
"""

import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.models.ingreso import Ingreso
from app.models.gasto import Gasto
from app.dependencies import get_current_user
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
    descripcion: str
    monto: float
    tipo: str
    categoria: str


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

    todos = procesar_csv(df, mapeo)
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
        "resumen": {
            "total": len(todos),
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

    # Persistencia transaccional atómica (Objetivo Específico 1 — TFG):
    # si falla cualquier inserción, se revierte la operación completa
    # y ningún registro parcial queda en la base de datos.
    try:
        for mov in a_importar:
            try:
                fecha = datetime.fromisoformat(mov["fecha"])
            except (ValueError, TypeError):
                fecha = datetime.now()

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

    return {
        "importados": len(ingresos_nuevos) + len(gastos_nuevos),
        "ingresos_creados": len(ingresos_nuevos),
        "gastos_creados": len(gastos_nuevos),
        "omitidos_por_duplicado": omitidos_por_duplicado,
        "omitidos_por_transferencia": omitidos_por_transferencia,
    }
