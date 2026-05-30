"""
Pobla un usuario de demostración con datos representativos de un freelancer
monotributista, para que la aplicación se vea realista en capturas y defensa.

Ejecutar:
    docker compose exec api python seed_demo.py
"""
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

# Gastos: variados por categoría, distribuidos en cada mes.
GASTOS_POR_MES = [
    [("Suscripción Adobe Creative Cloud", 38000, "Suscripciones"),
     ("Notebook Lenovo ThinkPad", 1450000, "Hardware"),
     ("AWS EC2 hosting mensual", 92000, "Infraestructura"),
     ("Honorarios contadora enero", 85000, "Servicios"),
     ("Pago monotributo enero", 48000, "Monotributo"),
     ("Almuerzo reunión cliente", 32000, "Alimentación"),
     ("Uber a reunión Brand Studio", 14500, "Transporte")],
    [("Suscripción Adobe Creative Cloud", 38000, "Suscripciones"),
     ("Licencia JetBrains anual", 165000, "Software"),
     ("AWS EC2 hosting mensual", 95000, "Infraestructura"),
     ("Honorarios contadora febrero", 85000, "Servicios"),
     ("Pago monotributo febrero", 48000, "Monotributo"),
     ("Curso Platzi escuela de datos", 54000, "Capacitación"),
     ("Nafta YPF estación de servicio", 41000, "Transporte")],
    [("Suscripción Adobe Creative Cloud", 39000, "Suscripciones"),
     ("Monitor LG UltraGear 27", 480000, "Hardware"),
     ("AWS EC2 hosting mensual", 98000, "Infraestructura"),
     ("Honorarios contadora marzo", 90000, "Servicios"),
     ("Pago monotributo marzo", 51000, "Monotributo"),
     ("Publicidad Google Ads campaña", 120000, "Marketing"),
     ("Cena cliente restaurante", 46000, "Alimentación")],
    [("Suscripción Adobe Creative Cloud", 39000, "Suscripciones"),
     ("Ingresos brutos CABA declaración", 138000, "Impuestos"),
     ("AWS EC2 hosting mensual", 101000, "Infraestructura"),
     ("Honorarios contadora abril", 90000, "Servicios"),
     ("Pago monotributo abril", 51000, "Monotributo"),
     ("Teclado y mouse Logitech", 96000, "Hardware"),
     ("Uber viajes a reuniones", 28000, "Transporte")],
    [("Suscripción Adobe Creative Cloud", 40000, "Suscripciones"),
     ("Dominio y certificado SSL anual", 72000, "Infraestructura"),
     ("AWS EC2 hosting mensual", 104000, "Infraestructura"),
     ("Honorarios contadora mayo", 95000, "Servicios"),
     ("Pago monotributo mayo", 54000, "Monotributo"),
     ("Workshop React avanzado online", 68000, "Capacitación"),
     ("Almuerzo coworking mensual", 52000, "Alimentación")],
]


def crear_movimientos(db, usuario):
    anio = 2026
    for i in range(5):
        mes = i + 1
        for dia, (desc, monto) in zip((5, 15, 25), INGRESOS_POR_MES[i]):
            db.add(Ingreso(
                usuario_id=usuario.id, descripcion=desc, monto=monto,
                categoria="Servicios", fecha=datetime(anio, mes, dia, 10, 0),
            ))
        for j, (desc, monto, cat) in enumerate(GASTOS_POR_MES[i]):
            dia = 3 + j * 3
            db.add(Gasto(
                usuario_id=usuario.id, descripcion=desc, monto=monto,
                categoria=cat, fecha=datetime(anio, mes, dia, 12, 0),
            ))
    db.commit()
    print("Ingresos y gastos creados (enero a mayo 2026).")


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
    for cliente, desc, monto, emision, venc, estado, pago in facturas:
        db.add(Factura(
            usuario_id=usuario.id, cliente_nombre=cliente, descripcion=desc,
            monto=monto, estado=estado, fecha_emision=emision,
            fecha_vencimiento=venc, fecha_pago=pago,
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
