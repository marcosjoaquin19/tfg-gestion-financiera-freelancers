"""Capturas para las filminas: la demo del 14/10/2026 12:00 AR, contra la API simulada (8001)."""
import json, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta
from playwright.sync_api import sync_playwright

OUT = sys.argv[1]
API = "http://127.0.0.1:8001"
CSV = "/Users/marcosjoaquin/proyecto-tfg/defensa_final/demo/extracto_28sep_14oct.csv"
datos = urllib.parse.urlencode({"username": "demo@freelancecontrol.com", "password": "demo1234"}).encode()
token = json.load(urllib.request.urlopen(API + "/auth/login", datos))["access_token"]

def api(ruta):
    req = urllib.request.Request(API + ruta, headers={"Authorization": "Bearer " + token})
    return json.load(urllib.request.urlopen(req))

def esperar_estado(cond, tope=90):
    t0 = time.time()
    while time.time() - t0 < tope:
        e = api("/ml/estado")
        if cond(e): return e
        time.sleep(1.5)
    return api("/ml/estado")

def reenviar(route):
    route.continue_(url=route.request.url.replace("http://localhost:8000", API))

with sync_playwright() as p:
    nav = p.chromium.launch()
    ctx = nav.new_context(viewport={"width": 1336, "height": 758}, device_scale_factor=2,
                          locale="es-AR", timezone_id="America/Argentina/Buenos_Aires", accept_downloads=True)
    ctx.route("http://localhost:8000/**", reenviar)
    pg = ctx.new_page()
    pg.clock.install(time=datetime(2026, 10, 14, 12, 0, tzinfo=timezone(timedelta(hours=-3))))
    errores = []
    pg.on("console", lambda m: errores.append(m.text) if m.type == "error" else None)
    pg.goto("http://localhost:3000/login")
    pg.evaluate("([t]) => { localStorage.setItem('token', t); localStorage.setItem('userEmail', 'demo@freelancecontrol.com'); }", [token])

    def ir(ruta, espera=1500):
        pg.goto("http://localhost:3000" + ruta); pg.wait_for_load_state("networkidle"); pg.wait_for_timeout(espera)
    def foto(nombre, full=False):
        pg.screenshot(path=f"{OUT}/{nombre}.png", full_page=full); print("  ·", nombre)

    ir("/"); foto("01_dashboard_antes")
    print("estado ML antes:", api("/ml/estado"))

    ir("/importar")
    pg.locator('input[type="file"]').set_input_files(CSV)
    pg.get_by_role("button", name="Analizar archivo").click()
    pg.get_by_role("button", name="Confirmar importación").wait_for(timeout=30000)
    pg.wait_for_timeout(800)
    foto("02_import_preview"); foto("02_import_preview_full", full=True)
    pg.get_by_role("button", name="Confirmar importación").click()
    pg.wait_for_timeout(4000)
    foto("03_import_resultado"); foto("03_import_resultado_full", full=True)

    e = esperar_estado(lambda e: "propio" in json.dumps(e).lower() or (e.get("n_ejemplos") or 0) > 600)
    print("estado ML tras importar:", e)
    ir("/"); foto("04_dashboard_despues")

    ir("/clasificador"); foto("05_clasificador_estado")
    def clasificar(txt, nombre):
        ta = pg.locator("textarea"); ta.fill(txt)
        pg.get_by_role("button", name="Clasificar con IA").click()
        pg.wait_for_timeout(1800); foto(nombre)
    clasificar("licencia jetbrains anual", "06_jetbrains")
    # La corrección: un comercio que el modelo nunca vio.
    clasificar("mostaza palermo", "20_mostaza_palermo_antes")
    clasificar("mostaza", "21_mostaza_antes")
    pg.get_by_role("button", name="Corregir categoría").click()
    pg.locator("select").last.select_option("Alimentación")
    pg.get_by_role("button", name="Confirmar corrección").click()
    pg.wait_for_timeout(1500); foto("22_mostaza_correccion")
    n0 = e.get("n_ejemplos")
    e2 = esperar_estado(lambda x: x.get("n_ejemplos") != n0)
    print("estado ML tras corregir:", e2)
    pg.wait_for_timeout(1500)
    clasificar("mostaza", "23_mostaza_corregido")
    clasificar("mostaza palermo", "24_mostaza_palermo_despues")
    ir("/clasificador"); foto("12_clasificador_estado_final")

    ir("/gastos"); foto("13_gastos")
    ir("/facturas"); foto("14_facturas")
    ir("/auditoria")
    pg.get_by_role("button", name="Ejecutar auditoría").click()
    pg.wait_for_timeout(4000)
    foto("15_auditoria"); foto("15_auditoria_full", full=True)
    ir("/monotributo", 2500); foto("16_monotributo"); foto("16_monotributo_full", full=True)
    ir("/proyecciones", 3500); foto("17_proyecciones"); foto("17_proyecciones_full", full=True)
    ir("/recomendaciones", 2500); foto("18_recomendaciones"); foto("18_recomendaciones_full", full=True)
    ir("/", 2500)
    with pg.expect_download() as d:
        pg.get_by_role("button", name="Descargar reporte PDF").click()
    d.value.save_as(f"{OUT}/19_reporte.pdf"); print("  · 19_reporte.pdf", d.value.suggested_filename)
    print("errores de consola:", errores or "ninguno")
    nav.close()
