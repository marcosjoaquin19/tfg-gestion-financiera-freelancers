import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.models.ingreso import Ingreso
from app.models.gasto import Gasto
from app.dependencies import get_current_user
from app.services.csv_service import detectar_columnas_csv, procesar_csv, clasificar_movimientos
from datetime import datetime

router = APIRouter(prefix="/importar", tags=["Importar"])

# Validación previa del archivo importado (Objetivo Específico 1 — TFG)
EXTENSIONES_PERMITIDAS = {".csv"}
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

    try:
        contenido = contenido_bytes.decode("utf-8")
    except UnicodeDecodeError:
        contenido = contenido_bytes.decode("latin-1")

    mapeo = detectar_columnas_csv(contenido, db)
    if not mapeo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se pudo detectar la estructura del CSV. Verificá que el archivo tenga encabezados claros.",
        )

    todos = procesar_csv(contenido, mapeo)
    if not todos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se encontraron movimientos válidos en el CSV.",
        )

    preview_raw = todos[:20]
    preview = clasificar_movimientos(preview_raw, db, current_user.id)

    return {
        "total_filas": len(todos),
        "preview": preview,
        "mapeo_detectado": mapeo,
    }


@router.post("/confirmar")
def confirmar_importacion(
    datos: ConfirmarRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    ingresos_nuevos = []
    gastos_nuevos = []

    # Persistencia transaccional atómica (Objetivo Específico 1 — TFG):
    # si falla cualquier inserción, se revierte la operación completa
    # y ningún registro parcial queda en la base de datos.
    try:
        for mov in datos.movimientos:
            try:
                fecha = datetime.fromisoformat(mov.fecha)
            except Exception:
                fecha = datetime.now()

            if mov.tipo == "ingreso":
                ingresos_nuevos.append(Ingreso(
                    usuario_id=current_user.id,
                    descripcion=mov.descripcion,
                    monto=mov.monto,
                    categoria=mov.categoria,
                    fecha=fecha,
                ))
            elif mov.tipo == "gasto":
                gastos_nuevos.append(Gasto(
                    usuario_id=current_user.id,
                    descripcion=mov.descripcion,
                    monto=mov.monto,
                    categoria=mov.categoria,
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
    }
