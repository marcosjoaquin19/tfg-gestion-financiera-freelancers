"""
Pobla un usuario de demostración con datos representativos de un freelancer
monotributista, para que la aplicación se vea realista en capturas y defensa.

Ejecutar:
    docker compose exec api python seed_demo.py
"""
import calendar
from datetime import datetime, timedelta

from app.database import SessionLocal
from app.services.auth import hashear_password
from app.models.usuario import Usuario
from app.models.ingreso import Ingreso
from app.models.gasto import Gasto
from app.models.factura import Factura, EstadoFactura
from app.models.proyeccion import Proyeccion
from app.models.alerta_auditoria import AlertaAuditoria
from app.models.cache_clasificacion import CacheClasificacion
from app.models.modelo_clasificador import ModeloClasificador
from app.models.categoria_monotributo import CategoriaMonotributo

EMAIL = "demo@freelancecontrol.com"
PASSWORD = "demo1234"

# Las fechas de movimientos y facturas se diseñaron con mayo 2026 como "mes en
# curso" (de eso dependen los 4 detectores de auditoría y la factura vencida).
# Para que el demo siempre se vea vivo —el Dashboard muestra "del mes" y un mes
# vacío sale en $0— desplazamos TODO el dataset en bloque para que el último mes
# coincida con el mes actual, conservando intactas las relaciones relativas.
ANCLA_ORIGINAL = (2026, 5)  # (año, mes) con el que se escribieron las fechas


def offset_meses_hasta_hoy():
    """Cantidad de meses a desplazar para que el ancla caiga en el mes actual."""
    hoy = datetime.now()
    return (hoy.year * 12 + hoy.month) - (ANCLA_ORIGINAL[0] * 12 + ANCLA_ORIGINAL[1])


def desplazar(fecha, offset):
    """Mueve `fecha` `offset` meses hacia adelante, ajustando el día al mes."""
    if fecha is None:
        return None
    total = fecha.year * 12 + (fecha.month - 1) + offset
    anio, mes = total // 12, total % 12 + 1
    dia = min(fecha.day, calendar.monthrange(anio, mes)[1])
    return fecha.replace(year=anio, month=mes, day=dia)


def limpiar_usuario_previo(db):
    usuario = db.query(Usuario).filter(Usuario.email == EMAIL).first()
    if usuario:
        # Borramos TODAS las filas hijas antes del usuario. Si olvidamos una
        # tabla con FK usuario_id NOT NULL (p. ej. alertas_auditoria), al borrar
        # el usuario SQLAlchemy intenta poner la FK en NULL y viola la constraint.
        # cache_clasificacion y modelos_clasificador filtran por usuario.id, así
        # que nunca tocan el modelo base compartido (usuario_id NULL).
        for modelo in (Ingreso, Gasto, Factura, Proyeccion,
                       AlertaAuditoria, CacheClasificacion, ModeloClasificador):
            db.query(modelo).filter(modelo.usuario_id == usuario.id).delete()
        db.delete(usuario)
        db.commit()
        print("Usuario demo previo eliminado.")


def crear_usuario(db):
    usuario = Usuario(
        nombre="María Fernández",
        email=EMAIL,
        password_hash=hashear_password(PASSWORD),
        es_activo=True,
        categoria_monotributo="D",
        actividad_monotributo="servicios",
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    print(f"Usuario demo creado (id={usuario.id}).")
    return usuario


# Ingresos: 3 por mes, enero a mayo 2026. Cobros de proyectos freelance.
INGRESOS_POR_MES = [
    [("Honorarios desarrollo web Estudio Lumen", 920000),
     ("Cobro mantenimiento mensual Acme Corp", 480000),
     ("Proyecto landing page Nube Digital", 760000)],
    [("Honorarios desarrollo API Estudio Lumen", 1150000),
     ("Cobro mantenimiento mensual Acme Corp", 480000),
     ("Consultoría técnica Brand Studio", 640000)],
    [("Proyecto e-commerce Tienda Sur", 1850000),
     ("Cobro mantenimiento mensual Acme Corp", 510000),
     ("Honorarios rediseño Nube Digital", 880000)],
    [("Honorarios desarrollo módulo Estudio Lumen", 1320000),
     ("Cobro mantenimiento mensual Acme Corp", 510000),
     ("Consultoría arquitectura Brand Studio", 970000)],
    [("Proyecto integración Tienda Sur", 1640000),
     ("Cobro mantenimiento mensual Acme Corp", 540000),
     ("Honorarios soporte Nube Digital", 720000)],
]

# Gastos: variados por categoría, con día explícito. Los datos están diseñados
# para que la auditoría (HU-08) dispare sus cuatro detectores en la defensa:
#
#  • DUPLICADO  → dos "Adobe Creative Cloud" de $38.000 en enero (días 3 y 5,
#                 dentro de la ventana de 3 días, misma categoría).
#  • ANOMALÍA   → "Servidor dedicado AWS Reserved" de $900.000 en marzo, muy por
#                 encima de la media de Infraestructura (que tiene 7 gastos, así
#                 el z-score supera 2σ; con menos de 5 el detector no actúa).
#  • DISCREPANCIA → factura de Consultora Aurora vencida sin cobrar (ver facturas).
#  • MONOTRIBUTO IMPAGO → mayo (mes en curso) NO tiene pago de Monotributo.
#
# Cada gasto es (descripcion, monto, categoria, dia).
GASTOS_POR_MES = [
    # Enero — incluye el par duplicado de Adobe (días 3 y 5).
    [("Suscripción Adobe Creative Cloud", 38000, "Suscripciones", 3),
     ("Suscripción Adobe Creative Cloud", 38000, "Suscripciones", 5),
     ("Notebook Lenovo ThinkPad", 1450000, "Hardware", 8),
     ("AWS EC2 hosting mensual", 92000, "Infraestructura", 10),
     ("Honorarios contadora enero", 85000, "Servicios", 12),
     ("Pago monotributo enero", 72414.10, "Monotributo", 15),
     ("Almuerzo reunión cliente", 32000, "Alimentación", 18),
     ("Uber a reunión Brand Studio", 14500, "Transporte", 22)],
    # Febrero
    [("Suscripción Adobe Creative Cloud", 38000, "Suscripciones", 3),
     ("Licencia JetBrains anual", 165000, "Software", 6),
     ("AWS EC2 hosting mensual", 95000, "Infraestructura", 10),
     ("Honorarios contadora febrero", 85000, "Servicios", 12),
     ("Pago monotributo febrero", 72414.10, "Monotributo", 15),
     ("Curso Platzi escuela de datos", 54000, "Capacitación", 18),
     ("Nafta YPF estación de servicio", 41000, "Transporte", 22)],
    # Marzo — incluye el outlier de Infraestructura (anomalía estadística).
    [("Suscripción Adobe Creative Cloud", 39000, "Suscripciones", 3),
     ("Monitor LG UltraGear 27", 480000, "Hardware", 6),
     ("AWS EC2 hosting mensual", 98000, "Infraestructura", 10),
     ("Servidor dedicado AWS Reserved", 900000, "Infraestructura", 11),
     ("Honorarios contadora marzo", 90000, "Servicios", 12),
     ("Pago monotributo marzo", 72414.10, "Monotributo", 15),
     ("Publicidad Google Ads campaña", 120000, "Marketing", 18),
     ("Cena cliente restaurante", 46000, "Alimentación", 22)],
    # Abril
    [("Suscripción Adobe Creative Cloud", 39000, "Suscripciones", 3),
     ("Ingresos brutos CABA declaración", 138000, "Impuestos", 6),
     ("AWS EC2 hosting mensual", 101000, "Infraestructura", 10),
     ("Honorarios contadora abril", 90000, "Servicios", 12),
     ("Pago monotributo abril", 72414.10, "Monotributo", 15),
     ("Teclado y mouse Logitech", 96000, "Hardware", 18),
     ("Uber viajes a reuniones", 28000, "Transporte", 22)],
    # Mayo (mes en curso) — SIN pago de Monotributo, a propósito, para que la
    # auditoría dispare la alerta de cuota impaga.
    [("Suscripción Adobe Creative Cloud", 40000, "Suscripciones", 3),
     ("Dominio y certificado SSL anual", 72000, "Infraestructura", 6),
     ("AWS EC2 hosting mensual", 104000, "Infraestructura", 10),
     ("Honorarios contadora mayo", 95000, "Servicios", 12),
     ("Workshop React avanzado online", 68000, "Capacitación", 18),
     ("Almuerzo coworking mensual", 52000, "Alimentación", 22)],
]


def crear_movimientos(db, usuario):
    offset = offset_meses_hasta_hoy()
    anio = 2026
    for i in range(5):
        mes = i + 1
        for dia, (desc, monto) in zip((5, 15, 25), INGRESOS_POR_MES[i]):
            db.add(Ingreso(
                usuario_id=usuario.id, descripcion=desc, monto=monto,
                categoria="Servicios",
                fecha=desplazar(datetime(anio, mes, dia, 10, 0), offset),
            ))
        for desc, monto, cat, dia in GASTOS_POR_MES[i]:
            db.add(Gasto(
                usuario_id=usuario.id, descripcion=desc, monto=monto,
                categoria=cat,
                fecha=desplazar(datetime(anio, mes, dia, 12, 0), offset),
            ))
    db.commit()
    primer_mes = desplazar(datetime(2026, 1, 1), offset)
    ultimo_mes = desplazar(datetime(2026, 5, 1), offset)
    print(f"Ingresos y gastos creados ({primer_mes:%b %Y} a {ultimo_mes:%b %Y}).")


def crear_facturas(db, usuario):
    facturas = [
        # (cliente, descripcion, monto, emision, vencimiento, estado, pago)
        ("Estudio Lumen", "Desarrollo de módulo de reportes", 1320000,
         datetime(2026, 4, 2), datetime(2026, 5, 2), EstadoFactura.PAGADA, datetime(2026, 4, 28)),
        ("Acme Corp", "Mantenimiento mensual de sistemas", 540000,
         datetime(2026, 5, 1), datetime(2026, 5, 31), EstadoFactura.PENDIENTE, None),
        ("Brand Studio", "Consultoría de arquitectura de software", 970000,
         datetime(2026, 5, 6), datetime(2026, 6, 6), EstadoFactura.PENDIENTE, None),
        ("Tienda Sur", "Integración de pasarela de pagos", 1640000,
         datetime(2026, 5, 8), datetime(2026, 6, 8), EstadoFactura.PENDIENTE, None),
        ("Nube Digital", "Rediseño de sitio institucional", 880000,
         datetime(2026, 3, 10), datetime(2026, 4, 10), EstadoFactura.PAGADA, datetime(2026, 4, 5)),
        ("Consultora Aurora", "Auditoría técnica de plataforma", 430000,
         datetime(2026, 3, 20), datetime(2026, 4, 20), EstadoFactura.PENDIENTE, None),
    ]
    offset = offset_meses_hasta_hoy()
    for cliente, desc, monto, emision, venc, estado, pago in facturas:
        db.add(Factura(
            usuario_id=usuario.id, cliente_nombre=cliente, descripcion=desc,
            monto=monto, estado=estado,
            fecha_emision=desplazar(emision, offset),
            fecha_vencimiento=desplazar(venc, offset),
            fecha_pago=desplazar(pago, offset),
        ))
    db.commit()
    print(f"Facturas creadas ({len(facturas)}).")


def asegurar_categorias_monotributo(db):
    # El estado de Monotributo del demo depende de que la tabla de categorías
    # esté poblada. Si está vacía (BD recién creada, downgrade, etc.) el
    # endpoint devuelve sin_categoria y el semáforo no se ve en la defensa.
    # Reutilizamos el seed de categorías para dejar el demo reproducible de
    # un solo comando.
    from seed_categorias_monotributo import seed_categorias
    if db.query(CategoriaMonotributo).count() == 0:
        seed_categorias(db=db)
    else:
        print("Categorías Monotributo ya presentes.")


def main():
    db = SessionLocal()
    try:
        asegurar_categorias_monotributo(db)
        limpiar_usuario_previo(db)
        usuario = crear_usuario(db)
        crear_movimientos(db, usuario)
        crear_facturas(db, usuario)
        print("\nSeed demo completado.")
        print(f"  Login: {EMAIL} / {PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
