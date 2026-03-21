from datetime import datetime
from sqlalchemy import extract
from sqlalchemy.orm import Session
from app.models.usuario import Usuario
from app.models.ingreso import Ingreso
from app.models.gasto import Gasto
from app.models.proyeccion import Proyeccion

CATEGORIAS_SERVICIOS = {
    "A": {"limite_anual": 10277988,  "cuota_mensual": 42387},
    "B": {"limite_anual": 15068988,  "cuota_mensual": 48251},
    "C": {"limite_anual": 21010988,  "cuota_mensual": 56502},
    "D": {"limite_anual": 27540988,  "cuota_mensual": 72414},
    "E": {"limite_anual": 34650988,  "cuota_mensual": 102548},
    "F": {"limite_anual": 45280988,  "cuota_mensual": 129045},
    "G": {"limite_anual": 56510988,  "cuota_mensual": 174378},
    "H": {"limite_anual": 79130988,  "cuota_mensual": 447347},
    "I": {"limite_anual": 94500988,  "cuota_mensual": 606019},
    "J": {"limite_anual": 101430988, "cuota_mensual": 805938},
    "K": {"limite_anual": 108357084, "cuota_mensual": 1080000},
}

MESES_ES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}

CATEGORIAS_ORDEN = list(CATEGORIAS_SERVICIOS.keys())


def calcular_estado_monotributo(db: Session, usuario_id: int) -> dict | None:
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario or not usuario.categoria_monotributo:
        return None

    cat = usuario.categoria_monotributo.upper()
    if cat not in CATEGORIAS_SERVICIOS:
        return None

    datos_cat = CATEGORIAS_SERVICIOS[cat]
    limite_anual = datos_cat["limite_anual"]
    cuota_mensual = datos_cat["cuota_mensual"]

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

    # Meses hasta superar el límite
    meses_para_limite = None
    if proyecciones:
        dias_proyectados = len(proyecciones)
        if dias_proyectados > 0 and total_proyectado_restante > 0:
            ingreso_diario = total_proyectado_restante / dias_proyectados
            ingreso_mensual = ingreso_diario * 30
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
    monto_esperado = CATEGORIAS_SERVICIOS.get(cat, {}).get("cuota_mensual") if cat else None

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
