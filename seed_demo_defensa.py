"""
Datos de la defensa oral (14/10/2026): enero a septiembre de 2026.

A diferencia de seed_demo.py (que corre el calendario para que el demo
siempre termine en el mes actual), este dataset tiene fechas FIJAS: el día de
la defensa octubre arranca vacío y se completa en vivo importando el extracto
defensa_final/demo/extracto_28sep_14oct.csv.

Qué deja armado:
  • Meses de facturación alta (5 a 10 millones) y baja (1 a 2 millones), para
    que el gráfico de proyección y el semáforo del Monotributo tengan historia.
  • Los cuatro detectores de la auditoría con algo que encontrar el 14/10:
      - DUPLICADO: dos "Suscripción Adobe Creative Cloud" de $38.000 en junio
        (días 3 y 5: misma categoría, dentro de la ventana de 3 días).
      - ANOMALÍA: "Servidor dedicado AWS Reserved" de $900.000 en julio,
        contra 8 gastos de Infraestructura en la ventana de 6 meses.
      - FACTURA VENCIDA: Consultora Aurora (venció el 20/08) y Brand Studio
        (venció el 08/10; el extracto trae su cobro del 09/10).
      - MONOTRIBUTO IMPAGO: octubre no tiene pago hasta importar el extracto.
  • Cuotas del Monotributo con las dos escalas: la de febrero hasta julio y la
    vigente desde el 1/8 (el reporte de cada mes usa la que regía entonces).
  • Tres movimientos del 28 al 30/09 cargados con la descripción del banco,
    como si vinieran de un extracto anterior: al importar el nuevo, el sistema
    los reconoce como repetidos y los omite.
  • Facturas en los tres estados.

El usuario queda con el modelo base del clasificador (sin modelo propio), para
mostrar en vivo el reentrenamiento con sus datos.

Ejecutar (borra y recrea el usuario demo):
    docker compose exec api python seed_demo_defensa.py
"""
import logging
from datetime import datetime

# Prophet avisa que no encontró plotly (solo sirve para gráficos interactivos
# que el sistema no usa); se silencia para que la salida del seed quede limpia.
logging.getLogger("prophet.plot").setLevel(logging.CRITICAL)

from app.database import SessionLocal
from app.models.factura import Factura, EstadoFactura
from app.models.gasto import Gasto
from app.models.ingreso import Ingreso
from app.models.usuario import Usuario
from app.services.auth import hashear_password
from app.services.duplicados_gasto import marcar_duplicado_si_corresponde
from seed_demo import EMAIL, PASSWORD, asegurar_categorias_monotributo, limpiar_usuario_previo

CATEGORIA = "G"
ANIO = 2026

# Cuota de la categoría G: escala de febrero a julio y escala desde el 1/8.
CUOTA_HASTA_JULIO = 197108.23
CUOTA_DESDE_AGOSTO = 230312.94

# Ingresos: (mes, día, descripción, monto, categoría)
INGRESOS = [
    # Enero — baja ($1.400.000)
    (1, 10, "Mantenimiento mensual Acme Corp", 480000, "Soporte y Mantenimiento"),
    (1, 22, "Landing page Nube Digital", 920000, "Desarrollo Web"),
    # Febrero — baja ($1.900.000)
    (2, 10, "Mantenimiento mensual Acme Corp", 480000, "Soporte y Mantenimiento"),
    (2, 14, "Ajustes sitio Estudio Lumen", 650000, "Desarrollo Web"),
    (2, 25, "Consultoría técnica Brand Studio", 770000, "Consultoría"),
    # Marzo — alta ($6.300.000)
    (3, 10, "Mantenimiento mensual Acme Corp", 510000, "Soporte y Mantenimiento"),
    (3, 13, "E-commerce Tienda Sur, primera etapa", 3200000, "Desarrollo Web"),
    (3, 20, "Desarrollo de API Estudio Lumen", 1450000, "Desarrollo"),
    (3, 27, "Consultoría de arquitectura Brand Studio", 1140000, "Consultoría"),
    # Abril — baja ($1.600.000)
    (4, 10, "Mantenimiento mensual Acme Corp", 510000, "Soporte y Mantenimiento"),
    (4, 24, "Rediseño de sitio institucional Nube Digital", 1090000, "Diseño"),
    # Mayo — alta ($8.100.000)
    (5, 8, "E-commerce Tienda Sur, segunda etapa", 3800000, "Desarrollo Web"),
    (5, 10, "Mantenimiento mensual Acme Corp", 540000, "Soporte y Mantenimiento"),
    (5, 19, "App mobile Grupo Delta, primera etapa", 2600000, "Desarrollo Mobile"),
    (5, 28, "Módulo de reportes Estudio Lumen", 1160000, "Desarrollo"),
    # Junio — baja ($1.200.000)
    (6, 10, "Mantenimiento mensual Acme Corp", 540000, "Soporte y Mantenimiento"),
    (6, 23, "Soporte técnico Consultora Aurora", 660000, "Soporte y Mantenimiento"),
    # Julio — alta ($5.700.000)
    (7, 9, "App mobile Grupo Delta, segunda etapa", 2900000, "Desarrollo Mobile"),
    (7, 10, "Mantenimiento mensual Acme Corp", 570000, "Soporte y Mantenimiento"),
    (7, 17, "Integración de pagos Fintech Río, primera etapa", 1480000, "Desarrollo"),
    (7, 29, "Posicionamiento SEO Nube Digital", 750000, "Marketing Digital"),
    # Agosto — baja ($1.800.000)
    (8, 10, "Mantenimiento mensual Acme Corp", 570000, "Soporte y Mantenimiento"),
    (8, 21, "Consultoría de performance Brand Studio", 1230000, "Consultoría"),
    # Septiembre — alta ($9.300.000)
    (9, 4, "App mobile Grupo Delta, cierre del proyecto", 3900000, "Desarrollo Mobile"),
    (9, 10, "Mantenimiento mensual Acme Corp", 600000, "Soporte y Mantenimiento"),
    (9, 16, "Integración de pagos Fintech Río, segunda etapa", 2750000, "Desarrollo"),
    (9, 24, "Mantenimiento anual Tienda Sur", 2050000, "Soporte y Mantenimiento"),
]

# Gastos: (mes, día, descripción, monto, categoría)
GASTOS = [
    # Enero
    (1, 3, "Suscripción Adobe Creative Cloud", 36000, "Suscripciones"),
    (1, 6, "Licencia JetBrains anual", 165000, "Software"),
    (1, 10, "AWS EC2 hosting mensual", 88000, "Infraestructura"),
    (1, 12, "Honorarios contadora enero", 85000, "Servicios"),
    (1, 15, "Pago monotributo enero", CUOTA_HASTA_JULIO, "Monotributo"),
    (1, 22, "Uber a reunión con cliente", 12500, "Transporte"),
    (1, 25, "Almuerzo de trabajo con cliente", 28000, "Alimentación"),
    # Febrero
    (2, 3, "Suscripción Adobe Creative Cloud", 36000, "Suscripciones"),
    (2, 10, "AWS EC2 hosting mensual", 90000, "Infraestructura"),
    (2, 12, "Honorarios contadora febrero", 85000, "Servicios"),
    (2, 15, "Pago monotributo febrero", CUOTA_HASTA_JULIO, "Monotributo"),
    (2, 18, "Curso Platzi escuela de datos", 54000, "Capacitación"),
    (2, 22, "Nafta YPF estación de servicio", 38000, "Transporte"),
    # Marzo
    (3, 3, "Suscripción Adobe Creative Cloud", 38000, "Suscripciones"),
    (3, 6, "Notebook Lenovo ThinkPad", 1450000, "Hardware"),
    (3, 10, "AWS EC2 hosting mensual", 94000, "Infraestructura"),
    (3, 12, "Honorarios contadora marzo", 90000, "Servicios"),
    (3, 15, "Pago monotributo marzo", CUOTA_HASTA_JULIO, "Monotributo"),
    (3, 18, "Publicidad Google Ads campaña", 120000, "Marketing"),
    (3, 24, "Cena con cliente en restaurante", 46000, "Alimentación"),
    # Abril
    (4, 3, "Suscripción Adobe Creative Cloud", 38000, "Suscripciones"),
    (4, 6, "Ingresos brutos CABA declaración", 138000, "Impuestos"),
    (4, 10, "AWS EC2 hosting mensual", 97000, "Infraestructura"),
    (4, 12, "Honorarios contadora abril", 90000, "Servicios"),
    (4, 15, "Pago monotributo abril", CUOTA_HASTA_JULIO, "Monotributo"),
    (4, 18, "Teclado y mouse Logitech", 96000, "Hardware"),
    (4, 22, "Uber viajes a reuniones", 26000, "Transporte"),
    # Mayo
    (5, 3, "Suscripción Adobe Creative Cloud", 38000, "Suscripciones"),
    (5, 10, "AWS EC2 hosting mensual", 101000, "Infraestructura"),
    (5, 12, "Honorarios contadora mayo", 95000, "Servicios"),
    (5, 15, "Pago monotributo mayo", CUOTA_HASTA_JULIO, "Monotributo"),
    (5, 18, "Workshop React avanzado online", 68000, "Capacitación"),
    (5, 22, "Almuerzo coworking mensual", 52000, "Alimentación"),
    (5, 26, "Dominio y certificado SSL anual", 72000, "Infraestructura"),
    # Junio — el par duplicado de Adobe (días 3 y 5)
    (6, 3, "Suscripción Adobe Creative Cloud", 38000, "Suscripciones"),
    (6, 5, "Suscripción Adobe Creative Cloud", 38000, "Suscripciones"),
    (6, 10, "AWS EC2 hosting mensual", 104000, "Infraestructura"),
    (6, 12, "Honorarios contadora junio", 95000, "Servicios"),
    (6, 15, "Pago monotributo junio", CUOTA_HASTA_JULIO, "Monotributo"),
    (6, 20, "Uber a oficina de cliente", 18000, "Transporte"),
    (6, 24, "Ingresos brutos CABA declaración", 142000, "Impuestos"),
    # Julio — el gasto atípico de Infraestructura
    (7, 3, "Suscripción Adobe Creative Cloud", 40000, "Suscripciones"),
    (7, 10, "AWS EC2 hosting mensual", 108000, "Infraestructura"),
    (7, 11, "Servidor dedicado AWS Reserved", 900000, "Infraestructura"),
    (7, 12, "Honorarios contadora julio", 100000, "Servicios"),
    (7, 15, "Pago monotributo julio", CUOTA_HASTA_JULIO, "Monotributo"),
    (7, 18, "Publicidad Meta Ads Instagram", 150000, "Marketing"),
    (7, 23, "Monitor LG UltraGear 27", 480000, "Hardware"),
    (7, 27, "Almuerzo de trabajo con cliente", 34000, "Alimentación"),
    # Agosto — primera cuota con la escala nueva
    (8, 3, "Suscripción Adobe Creative Cloud", 40000, "Suscripciones"),
    (8, 10, "AWS EC2 hosting mensual", 112000, "Infraestructura"),
    (8, 12, "Honorarios contadora agosto", 100000, "Servicios"),
    (8, 15, "Pago monotributo agosto", CUOTA_DESDE_AGOSTO, "Monotributo"),
    (8, 19, "Curso Udemy Docker y Kubernetes", 45000, "Capacitación"),
    (8, 26, "Nafta YPF estación de servicio", 42000, "Transporte"),
    # Septiembre
    (9, 3, "Suscripción Adobe Creative Cloud", 42000, "Suscripciones"),
    (9, 10, "AWS EC2 hosting mensual", 115000, "Infraestructura"),
    (9, 12, "Honorarios contadora septiembre", 105000, "Servicios"),
    (9, 15, "Pago monotributo septiembre", CUOTA_DESDE_AGOSTO, "Monotributo"),
    (9, 17, "DigitalOcean droplet de pruebas", 35000, "Infraestructura"),
    (9, 21, "Cena con cliente en restaurante", 58000, "Alimentación"),
    (9, 25, "Uber viajes a reuniones", 22000, "Transporte"),
    # 28 al 30/09: importados de un extracto anterior (descripción del banco).
    # El extracto de la defensa arranca el 28/09 y los repite.
    (9, 28, "RAPPI PEDIDO ALMUERZO", 18500, "Alimentación"),
    (9, 29, "UBER VIAJE", 9800, "Transporte"),
    (9, 30, "CARGA SUBE", 5000, "Transporte"),
]

# Facturas: (cliente, descripción, monto, emisión, vencimiento, estado, pago)
FACTURAS = [
    ("Nube Digital", "Rediseño de sitio institucional", 1090000,
     (3, 25), (4, 24), EstadoFactura.PAGADA, (4, 24)),
    ("Estudio Lumen", "Módulo de reportes", 1160000,
     (4, 28), (5, 28), EstadoFactura.PAGADA, (5, 28)),
    ("Grupo Delta", "App mobile, segunda etapa", 2900000,
     (6, 10), (7, 10), EstadoFactura.PAGADA, (7, 9)),
    ("Fintech Río", "Integración de pagos, segunda etapa", 2750000,
     (8, 16), (9, 16), EstadoFactura.PAGADA, (9, 16)),
    ("Consultora Aurora", "Auditoría técnica de plataforma", 430000,
     (7, 20), (8, 20), EstadoFactura.PENDIENTE, None),
    ("Brand Studio", "Consultoría de arquitectura de software", 980000,
     (9, 8), (10, 8), EstadoFactura.PENDIENTE, None),
    ("Tienda Sur", "Soporte trimestral", 1100000,
     (9, 30), (10, 30), EstadoFactura.PENDIENTE, None),
    ("Acme Corp", "Mantenimiento de sistemas, octubre", 630000,
     (10, 1), (10, 31), EstadoFactura.PENDIENTE, None),
]


def _fecha(mes, dia, hora=12):
    return datetime(ANIO, mes, dia, hora, 0)


def crear_usuario(db):
    usuario = Usuario(
        nombre="María Fernández",
        email=EMAIL,
        password_hash=hashear_password(PASSWORD),
        es_activo=True,
        categoria_monotributo=CATEGORIA,
        actividad_monotributo="servicios",
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    print(f"Usuario demo creado (id={usuario.id}, categoría {CATEGORIA}).")
    return usuario


def crear_movimientos(db, usuario):
    for mes, dia, desc, monto, cat in INGRESOS:
        db.add(Ingreso(usuario_id=usuario.id, descripcion=desc, monto=monto,
                       categoria=cat, fecha=_fecha(mes, dia, 10)))
    for mes, dia, desc, monto, cat in GASTOS:
        db.add(Gasto(usuario_id=usuario.id, descripcion=desc, monto=monto,
                     categoria=cat, fecha=_fecha(mes, dia)))
    db.commit()
    # Misma marca que pone la API al crear o importar un gasto: así el par de
    # Adobe de junio aparece en el filtro "Solo duplicados" de Gastos, igual
    # que en la Auditoría.
    for gasto in db.query(Gasto).filter(Gasto.usuario_id == usuario.id).all():
        marcar_duplicado_si_corresponde(db, gasto)
    db.commit()
    print(f"Ingresos: {len(INGRESOS)} (${sum(i[3] for i in INGRESOS):,.0f}). "
          f"Gastos: {len(GASTOS)}. Enero a septiembre de {ANIO}.".replace(",", "."))


def crear_facturas(db, usuario):
    for cliente, desc, monto, emision, venc, estado, pago in FACTURAS:
        db.add(Factura(
            usuario_id=usuario.id, cliente_nombre=cliente, descripcion=desc,
            monto=monto, estado=estado,
            fecha_emision=_fecha(*emision, 0),
            fecha_vencimiento=_fecha(*venc, 0),
            fecha_pago=_fecha(*pago, 0) if pago else None,
        ))
    db.commit()
    print(f"Facturas: {len(FACTURAS)}.")


def main():
    db = SessionLocal()
    try:
        asegurar_categorias_monotributo(db)
        limpiar_usuario_previo(db)
        usuario = crear_usuario(db)
        crear_movimientos(db, usuario)
        crear_facturas(db, usuario)
        print("\nDatos de la defensa cargados.")
        print(f"  Login: {EMAIL} / {PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
