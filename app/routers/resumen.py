"""
Router de Resumen Financiero — resumen mensual redactado con IA.

Expone GET /resumen/financiero. Toma los datos del mes pedido (o el actual),
delega en ia_service la redacción de un resumen en lenguaje natural (modelo
Groq) e informa si pudo generarse con IA o si no hay datos suficientes.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.dependencies import get_current_user
from app.services.ia_service import generar_resumen_financiero

# Nombres de los meses en español para mostrar el período en la respuesta.
MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}

router = APIRouter(prefix="/resumen", tags=["Resumen"])


# GET /resumen/financiero?mes=&anio=
# Genera el resumen del período indicado; si no se pasan mes/año, usa el actual.
@router.get("/financiero")
def resumen_financiero(
    mes: int = Query(default=None, ge=1, le=12),
    anio: int = Query(default=None, ge=2000),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    # Si el frontend no especifica período, se usa el mes y año actuales.
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
