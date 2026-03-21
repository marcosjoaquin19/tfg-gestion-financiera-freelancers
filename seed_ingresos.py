"""
Script para cargar 18 ingresos de prueba via API REST.
Distribuidos entre octubre 2025 y marzo 2026 con montos
fluctuantes para que Prophet detecte tendencia y estacionalidad.
"""
import requests

API = "http://localhost:8000"

# ── Login ──────────────────────────────────────────────────────────────────────
res = requests.post(
    f"{API}/auth/login",
    data={"username": "marcos@test.com", "password": "mipassword123"},
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)
if res.status_code != 200:
    print(f"Error en login: {res.status_code} — {res.text}")
    exit(1)

token = res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
print(f"Login OK — token obtenido")

# ── Ingresos de prueba ─────────────────────────────────────────────────────────
INGRESOS = [
    # Octubre 2025 — base baja
    {"fecha": "2025-10-05", "descripcion": "Desarrollo landing page empresa textil",      "monto": 38000, "categoria": "Desarrollo Web"},
    {"fecha": "2025-10-14", "descripcion": "Consultoría técnica startup fintech",          "monto": 22000, "categoria": "Consultoría"},
    {"fecha": "2025-10-28", "descripcion": "Mantenimiento mensual e-commerce",             "monto": 15000, "categoria": "Mantenimiento"},

    # Noviembre 2025 — leve suba
    {"fecha": "2025-11-03", "descripcion": "App móvil para delivery local (fase 1)",       "monto": 55000, "categoria": "Desarrollo Mobile"},
    {"fecha": "2025-11-17", "descripcion": "Integración pasarela de pagos MercadoPago",    "monto": 28000, "categoria": "Desarrollo Web"},
    {"fecha": "2025-11-25", "descripcion": "Auditoría de seguridad aplicación web",        "monto": 18500, "categoria": "Consultoría"},

    # Diciembre 2025 — pico fin de año
    {"fecha": "2025-12-02", "descripcion": "Rediseño plataforma de turnos médicos",        "monto": 72000, "categoria": "Desarrollo Web"},
    {"fecha": "2025-12-10", "descripcion": "App móvil para delivery local (fase 2)",       "monto": 55000, "categoria": "Desarrollo Mobile"},
    {"fecha": "2025-12-22", "descripcion": "Soporte técnico urgente cliente premium",      "monto": 12000, "categoria": "Soporte"},

    # Enero 2026 — baja estacional post-fiestas
    {"fecha": "2026-01-08", "descripcion": "Migración de base de datos a PostgreSQL",      "monto": 33000, "categoria": "Infraestructura"},
    {"fecha": "2026-01-20", "descripcion": "Consultoría arquitectura microservicios",      "monto": 26000, "categoria": "Consultoría"},
    {"fecha": "2026-01-29", "descripcion": "Dashboard analytics para empresa logística",   "monto": 48000, "categoria": "Desarrollo Web"},

    # Febrero 2026 — recuperación
    {"fecha": "2026-02-06", "descripcion": "Sistema de facturación electrónica AFIP",      "monto": 65000, "categoria": "Desarrollo Web"},
    {"fecha": "2026-02-14", "descripcion": "Integración API terceros plataforma SaaS",     "monto": 41000, "categoria": "Desarrollo Web"},
    {"fecha": "2026-02-27", "descripcion": "Capacitación equipo React + Node.js",          "monto": 19000, "categoria": "Capacitación"},

    # Marzo 2026 — pico más alto, tendencia al alza
    {"fecha": "2026-03-04", "descripcion": "Plataforma e-learning para instituto educativo","monto": 95000, "categoria": "Desarrollo Web"},
    {"fecha": "2026-03-18", "descripcion": "App móvil reservas para cadena de gimnasios",  "monto": 78000, "categoria": "Desarrollo Mobile"},
    {"fecha": "2026-03-27", "descripcion": "Consultoría optimización performance BD",       "monto": 31000, "categoria": "Consultoría"},
]

# ── POST de cada ingreso ───────────────────────────────────────────────────────
ok = 0
for ing in INGRESOS:
    payload = {
        "descripcion":  ing["descripcion"],
        "monto":        ing["monto"],
        "categoria":    ing["categoria"],
        "fecha":        ing["fecha"] + "T12:00:00",
    }
    r = requests.post(f"{API}/ingresos/", json=payload, headers=headers)
    if r.status_code == 201:
        ok += 1
        print(f"  ✓ {ing['fecha']}  ${ing['monto']:>7,}  {ing['descripcion'][:45]}")
    else:
        print(f"  ✗ ERROR {r.status_code}: {r.text[:80]}")

print(f"\n{ok}/{len(INGRESOS)} ingresos cargados correctamente.")
