from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.dependencies import get_current_user
from app.services.ia_service import generar_resumen_financiero

MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}

router = APIRouter(prefix="/resumen", tags=["Resumen"])


@router.get("/financiero")
def resumen_financiero(
    mes: int = Query(default=None, ge=1, le=12),
    anio: int = Query(default=None, ge=2000),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    hoy = datetime.now()
    mes_final = mes or hoy.month
    anio_final = anio or hoy.year

    resumen, generado_con_ia, sin_datos = generar_resumen_financiero(
        usuario_id=current_user.id,
        db=db,
        mes=mes_final,
        anio=anio_final,
    )

    return {
        "resumen": resumen,
        "generado_con_ia": generado_con_ia,
        "sin_datos": sin_datos,
        "periodo": f"{MESES_ES[mes_final]} {anio_final}",
    }
