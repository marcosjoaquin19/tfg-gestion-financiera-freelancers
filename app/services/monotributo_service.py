from datetime import datetime
from sqlalchemy import extract
from sqlalchemy.orm import Session
from app.models.usuario import Usuario
from app.models.ingreso import Ingreso
from app.models.gasto import Gasto
from app.models.proyeccion import Proyeccion
from app.models.categoria_monotributo import CategoriaMonotributo

MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}

CATEGORIAS_ORDEN = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K"]


def get_categoria(db: Session, letra: str) -> CategoriaMonotributo | None:
    return (
        db.query(CategoriaMonotributo)
        .filter(CategoriaMonotributo.letra == letra.upper(), CategoriaMonotributo.activa == True)
        .first()
    )


def calcular_estado_monotributo(db: Session, usuario_id: int) -> dict | None:
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario or not usuario.categoria_monotributo:
        return None

    cat = usuario.categoria_monotributo.upper()
    datos_cat = get_categoria(db, cat)
    if datos_cat is None:
        return None

    limite_anual = float(datos_cat.limite_anual)
    cuota_mensual = float(datos_cat.cuota_mensual)

    now = datetime.now()
    anio_actual = now.year

    # Facturado real del año
    resultado = db.query(Ingreso).filter(
        Ingreso.usuario_id == usuario_id,
        extract("year", Ingreso.fecha) == anio_actual,
    ).all()
    facturado_anual = float(sum(i.monto for i in resultado))

    porcentaje_usado = round((facturado_anual / limite_anual * 100), 1) if limite_anual > 0 else 0.0

    # Proyección desde hoy hasta fin de año usando Prophet
    fin_de_anio = datetime(anio_actual, 12, 31)
    proyecciones = db.query(Proyeccion).filter(
        Proyeccion.usuario_id == usuario_id,
        Proyeccion.fecha_proyeccion >= now,
        Proyeccion.fecha_proyeccion <= fin_de_anio,
    ).all()

    total_proyectado_restante = float(sum(p.monto_proyectado for p in proyecciones)) if proyecciones else 0.0
    proyeccion_anual = round(facturado_anual + total_proyectado_restante, 2)

    pct_proyectado = (proyeccion_anual / limite_anual * 100) if limite_anual > 0 else 0.0
    if pct_proyectado < 70:
        estado = "verde"
    elif pct_proyectado < 90:
        estado = "amarillo"
    else:
        estado = "rojo"

    # Meses hasta superar el límite anual.
    # Las proyecciones se generan con frecuencia mensual (una fila por mes,
    # ver prophet_service), así que el ingreso mensual promedio es el total
    # proyectado dividido la cantidad de meses proyectados.
    meses_para_limite = None
    if proyecciones and total_proyectado_restante > 0:
        ingreso_mensual = total_proyectado_restante / len(proyecciones)
        restante = limite_anual - facturado_anual
        if ingreso_mensual > 0 and restante > 0:
            meses_para_limite = max(0, round(restante / ingreso_mensual, 1))

    # Categoría siguiente
    idx = CATEGORIAS_ORDEN.index(cat)
    categoria_siguiente = CATEGORIAS_ORDEN[idx + 1] if idx + 1 < len(CATEGORIAS_ORDEN) else None

    return {
        "categoria_actual": cat,
        "limite_anual": limite_anual,
        "cuota_mensual": cuota_mensual,
        "facturado_anual": facturado_anual,
        "porcentaje_usado": porcentaje_usado,
        "proyeccion_anual": proyeccion_anual,
        "estado": estado,
        "meses_para_limite": meses_para_limite,
        "categoria_siguiente": categoria_siguiente,
    }


def verificar_pago_monotributo(db: Session, usuario_id: int) -> dict:
    now = datetime.now()
    mes = now.month
    anio = now.year

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    cat = usuario.categoria_monotributo if usuario else None
    datos_cat = get_categoria(db, cat) if cat else None
    monto_esperado = float(datos_cat.cuota_mensual) if datos_cat else None

    gasto = db.query(Gasto).filter(
        Gasto.usuario_id == usuario_id,
        Gasto.categoria == "Monotributo",
        extract("month", Gasto.fecha) == mes,
        extract("year", Gasto.fecha) == anio,
    ).first()

    gasto_encontrado = None
    if gasto:
        gasto_encontrado = {
            "id": gasto.id,
            "descripcion": gasto.descripcion,
            "monto": float(gasto.monto),
            "fecha": str(gasto.fecha),
        }

    return {
        "pagado": gasto is not None,
        "mes": MESES_ES[mes],
        "anio": anio,
        "monto_esperado": monto_esperado,
        "gasto_encontrado": gasto_encontrado,
    }
