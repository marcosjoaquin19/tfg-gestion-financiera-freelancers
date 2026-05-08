"""
Endpoint de descarga del reporte mensual en PDF.

Cumple con el Objetivo Específico 4 del TFG: "consolidar indicadores
financieros mensuales y permitir la exportación del reporte en formato
PDF descargable".
"""

from datetime import datetime
from io import BytesIO

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.usuario import Usuario
from app.services.reportes_service import generar_pdf_mensual


router = APIRouter(prefix="/reportes", tags=["Reportes"])


@router.get("/pdf")
def descargar_pdf_mensual(
    mes: int = Query(default=None, ge=1, le=12),
    anio: int = Query(default=None, ge=2000),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    # Si el front no especifica período, asumimos el mes corriente. Es lo que
    # el usuario suele querer cuando hace "descargar reporte" sin más contexto.
    hoy = datetime.now()
    mes_final = mes or hoy.month
    anio_final = anio or hoy.year

    pdf_bytes = generar_pdf_mensual(
        db=db,
        usuario_id=current_user.id,
        mes=mes_final,
        anio=anio_final,
    )

    # StreamingResponse + BytesIO porque el PDF puede ser mediano y no
    # queremos cargarlo entero en una variable de respuesta. El header
    # Content-Disposition fuerza la descarga en lugar de mostrarlo inline.
    nombre_archivo = f"reporte_{anio_final}-{mes_final:02d}.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{nombre_archivo}"',
        },
    )
