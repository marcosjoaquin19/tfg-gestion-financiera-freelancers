"""
Endpoint de descarga del reporte mensual en PDF.

Cumple con el Objetivo Específico 4 del TFG: "consolidar indicadores
financieros mensuales y permitir la exportación del reporte en formato
PDF descargable".
"""

from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.usuario import Usuario
from app.services.reportes_service import ahora_ar, generar_pdf_mensual


router = APIRouter(prefix="/reportes", tags=["Reportes"])


@router.get("/pdf")
def descargar_pdf_mensual(
    mes: int = Query(default=None, ge=1, le=12),
    anio: int = Query(default=None, ge=2000, le=2100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Descarga el reporte mensual en PDF (botón del Dashboard).

    Parámetros opcionales: ?mes=9&anio=2026. Sin ellos, el último mes cerrado.
    Un mes futuro devuelve 422 (dato inválido) con un mensaje claro.
    """
    # HU-13: el reporte es "del mes cerrado". Sin período explícito se usa el
    # último mes cerrado. El mes en curso se puede pedir (el PDF lo marca como
    # datos parciales); un mes que todavía no empezó, no.
    hoy = ahora_ar().date()
    if mes is None and anio is None:
        mes_final, anio_final = (hoy.month - 1, hoy.year) if hoy.month > 1 else (12, hoy.year - 1)
    else:
        mes_final = mes or hoy.month
        anio_final = anio or hoy.year

    if (anio_final, mes_final) > (hoy.year, hoy.month):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El período todavía no comenzó: el reporte se puede generar hasta el mes en curso.",
        )

    pdf_bytes = generar_pdf_mensual(
        db=db,
        usuario_id=current_user.id,
        mes=mes_final,
        anio=anio_final,
    )

    # StreamingResponse manda los bytes del PDF al navegador como archivo. El
    # encabezado Content-Disposition: attachment fuerza la descarga (criterio
    # de la HU-13) en lugar de abrirlo dentro de la pestaña, y le pone nombre.
    nombre_archivo = f"reporte_{anio_final}-{mes_final:02d}.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{nombre_archivo}"',
        },
    )
