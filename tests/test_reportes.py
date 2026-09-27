"""
Tests del reporte financiero mensual en PDF (PB-13).

El PDF se genera de verdad con ReportLab: se verifica el código de estado,
el tipo de contenido, el encabezado de descarga y la firma binaria %PDF. Los
tests del final leen el TEXTO del PDF (con pypdf) para verificar cada dato
contra lo cargado: escala del período, cuota, facturado, caracteres
especiales, hora, variaciones y alertas.
"""

import io
import re
from datetime import date, datetime
from decimal import Decimal

import pytest
from pypdf import PdfReader

import app.services.reportes_service as rs
from app.services.reportes_service import ZONA_AR

INGRESO = {
    "descripcion": "Proyecto web para cliente",
    "monto": 80000,
    "categoria": "Desarrollo",
    "fecha": "2026-03-05T10:00:00",
}
GASTO = {
    "descripcion": "Hosting mensual",
    "monto": 4000,
    "categoria": "Infraestructura",
    "fecha": "2026-03-06T10:00:00",
}


def test_reporte_pdf_sin_auth(client):
    assert client.get("/reportes/pdf").status_code == 401


def test_descargar_pdf_mes_actual(client, auth_headers):
    # Sin parámetros el endpoint usa el último mes cerrado (HU-13) y genera el
    # PDF igual, aunque no haya movimientos cargados en el período.
    response = client.get("/reportes/pdf", headers=auth_headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:4] == b"%PDF"
    assert "attachment" in response.headers["content-disposition"]


def test_descargar_pdf_periodo_especifico(client, auth_headers):
    response = client.get("/reportes/pdf?mes=3&anio=2026", headers=auth_headers)
    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"
    assert "reporte_2026-03.pdf" in response.headers["content-disposition"]


def test_descargar_pdf_con_datos(client, auth_headers):
    # Con ingresos y gastos cargados el reporte debe armarse sin errores.
    client.post("/ingresos/", json=INGRESO, headers=auth_headers)
    client.post("/gastos/", json=GASTO, headers=auth_headers)

    response = client.get("/reportes/pdf?mes=3&anio=2026", headers=auth_headers)
    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"
    assert len(response.content) > 1000


def test_descargar_pdf_mes_invalido(client, auth_headers):
    # El mes está acotado a 1-12: un valor fuera de rango lo rechaza la
    # validación de query params antes de generar nada.
    response = client.get("/reportes/pdf?mes=13&anio=2026", headers=auth_headers)
    assert response.status_code == 422



# ── Contenido del PDF ──────────────────────────────────────────────────────────

# Escalas de la tesis: Tabla 18 (febrero a julio de 2026) y Tabla 19 (desde el
# 1/8/2026). Solo la categoría D, que es la que usan estos tests.
ESCALAS = [
    (date(2026, 2, 1), False, "26212853.42", "72414.10"),
    (date(2026, 8, 1), True, "30628651.43", "84612.93"),
]
AHORA = datetime(2026, 9, 27, 15, 20, tzinfo=ZONA_AR)


@pytest.fixture
def escalas(client):
    from app.database import get_db
    from app.main import app
    from app.models.categoria_monotributo import CategoriaMonotributo

    db = next(app.dependency_overrides[get_db]())
    for vigencia, activa, limite, cuota in ESCALAS:
        db.add(CategoriaMonotributo(letra="D", limite_anual=Decimal(limite), cuota_mensual=Decimal(cuota),
                                    actividad="servicios", fecha_vigencia=vigencia, activa=activa))
    db.commit()
    return db


@pytest.fixture
def reloj(monkeypatch):
    monkeypatch.setattr(rs, "ahora_ar", lambda: AHORA)
    monkeypatch.setattr("app.routers.reportes.ahora_ar", lambda: AHORA)


def _texto_pdf(respuesta) -> str:
    assert respuesta.status_code == 200, respuesta.text
    lector = PdfReader(io.BytesIO(respuesta.content))
    return re.sub(r"\s+", " ", " ".join(p.extract_text() for p in lector.pages))


def _pdf(client, headers, mes, anio=2026):
    return _texto_pdf(client.get(f"/reportes/pdf?mes={mes}&anio={anio}", headers=headers))


def _mov(client, headers, tipo, monto, fecha, categoria=None, descripcion="Movimiento"):
    cuerpo = {"descripcion": descripcion, "monto": monto, "fecha": f"{fecha}T12:00:00",
              "categoria": categoria or ("Servicios" if tipo == "ingresos" else "Software")}
    assert client.post(f"/{tipo}/", json=cuerpo, headers=headers).status_code == 201


def _categoria_d(client, headers):
    assert client.patch("/monotributo/categoria", json={"categoria_monotributo": "D"},
                        headers=headers).status_code == 200


def test_escala_vigente_en_cada_fecha(escalas):
    from app.services.monotributo_service import escala_vigente_en
    assert escala_vigente_en(escalas, date(2026, 7, 31))["D"].cuota_mensual == Decimal("72414.10")
    assert escala_vigente_en(escalas, date(2026, 8, 1))["D"].cuota_mensual == Decimal("84612.93")
    assert escala_vigente_en(escalas, date(2026, 1, 31)) == {}          # antes de la primera escala


def test_mes_anterior_al_cambio_usa_la_escala_de_ese_momento(client, auth_headers, escalas, reloj):
    # Regresión: mayo se evaluaba con la escala de agosto y una cuota bien
    # pagada figuraba "Sin registrar".
    _categoria_d(client, auth_headers)
    _mov(client, auth_headers, "ingresos", 2_160_000, "2026-05-10")
    _mov(client, auth_headers, "gastos", 72414.10, "2026-05-15", "Monotributo", "Pago monotributo")
    texto = _pdf(client, auth_headers, 5)
    assert "vigente desde el 01/02/2026" in texto
    assert "Tope anual de la categoría $ 26.212.853,42" in texto
    assert "Cuota del período Pagada ($ 72.414,10)" in texto


def test_pago_parcial_se_informa_con_lo_registrado(client, auth_headers, escalas, reloj):
    _categoria_d(client, auth_headers)
    _mov(client, auth_headers, "gastos", 72414.10, "2026-08-15", "Monotributo", "Pago monotributo")
    texto = _pdf(client, auth_headers, 8)
    assert "vigente desde el 01/08/2026" in texto
    assert "Parcial: $ 72.414,10 de $ 84.612,93" in texto


def test_cuota_sin_registrar(client, auth_headers, escalas, reloj):
    _categoria_d(client, auth_headers)
    assert "Cuota del período Sin registrar" in _pdf(client, auth_headers, 8)


def test_mes_sin_escala_cargada_no_inventa_valores(client, auth_headers, escalas, reloj):
    _categoria_d(client, auth_headers)
    texto = _pdf(client, auth_headers, 1)
    assert "No hay una escala de categorías cargada para este período" in texto
    assert "Tope anual" not in texto


def test_el_reporte_no_incluye_el_facturado_anual(client, auth_headers, escalas, reloj):
    # Decisión de diseño: el PDF es la foto del mes. El acumulado anual y el
    # % del tope (con proyección y semáforo) viven en la pantalla Monotributo.
    _categoria_d(client, auth_headers)
    _mov(client, auth_headers, "ingresos", 1_000_000, "2026-05-10")
    _mov(client, auth_headers, "ingresos", 5_000_000, "2026-08-10")
    texto = _pdf(client, auth_headers, 8)
    assert "Total ingresos $ 5.000.000,00" in texto
    assert "Facturado en el año" not in texto
    assert "del tope" not in texto
    assert "$ 6.000.000,00" not in texto


def test_mes_en_curso_se_marca_como_parcial(client, auth_headers, escalas, reloj):
    _categoria_d(client, auth_headers)
    texto = _pdf(client, auth_headers, 9)
    assert "Período en curso: datos parciales al 27/09/2026" in texto


def test_hora_de_argentina(client, auth_headers, reloj):
    assert "Generado: 27/09/2026 15:20 (hora de Argentina)" in _pdf(client, auth_headers, 8)


def test_sin_parametros_usa_el_ultimo_mes_cerrado(client, auth_headers, reloj):
    r = client.get("/reportes/pdf", headers=auth_headers)
    assert 'filename="reporte_2026-08.pdf"' in r.headers["content-disposition"]
    assert "Período: Agosto 2026" in _texto_pdf(r)


@pytest.mark.parametrize("query", ["mes=10&anio=2026", "mes=1&anio=2027", "mes=1&anio=2101"])
def test_periodos_futuros_se_rechazan(client, auth_headers, reloj, query):
    r = client.get(f"/reportes/pdf?{query}", headers=auth_headers)
    assert r.status_code == 422


def test_mensaje_del_periodo_futuro(client, auth_headers, reloj):
    r = client.get("/reportes/pdf?mes=12&anio=2026", headers=auth_headers)
    assert r.json()["detail"] == "El período todavía no comenzó: el reporte se puede generar hasta el mes en curso."


def test_caracteres_especiales_salen_tal_cual(client, reloj):
    # Regresión: "<SRL>" desaparecía y "A&B <Consultores>" salía "A&B; ".
    email = "especiales@test.com"
    client.post("/auth/register", json={"nombre": "Pérez & Hijos <SRL>", "email": email, "password": "Prueba1234"})
    token = client.post("/auth/login", data={"username": email, "password": "Prueba1234"}).json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    client.post("/facturas/", json={"cliente_nombre": "A&B <Consultores>", "descripcion": "Web", "monto": 50000,
                                    "fecha_emision": "2026-07-01T12:00:00", "fecha_vencimiento": "2026-08-01T12:00:00"},
                headers=h)
    client.post("/alertas/ejecutar-auditoria", headers=h)
    texto = _pdf(client, h, 8)
    assert "Pérez & Hijos <SRL>" in texto
    assert "'A&B <Consultores>'" in texto


def test_variacion_con_balance_anterior_negativo(client, auth_headers, reloj):
    # Regresión: pasar de −$ 100.000 a +$ 100.000 se mostraba como −200 %.
    _mov(client, auth_headers, "ingresos", 100_000, "2026-07-10")
    _mov(client, auth_headers, "gastos", 200_000, "2026-07-11")
    _mov(client, auth_headers, "ingresos", 250_000, "2026-08-10")
    _mov(client, auth_headers, "gastos", 150_000, "2026-08-11")
    texto = _pdf(client, auth_headers, 8)
    assert "Total ingresos $ 250.000,00 +150,0 %" in texto
    assert "Total gastos $ 150.000,00 −25,0 %" in texto
    assert "Balance $ 100.000,00 +200,0 %" in texto


def test_porcentajes_con_coma_decimal(client, auth_headers, reloj):
    _mov(client, auth_headers, "gastos", 60_000, "2026-08-10", "Software")
    _mov(client, auth_headers, "gastos", 40_000, "2026-08-11", "Hardware")
    texto = _pdf(client, auth_headers, 8)
    assert "Software $ 60.000,00 60,0 %" in texto
    assert "Hardware $ 40.000,00 40,0 %" in texto


def test_alertas_con_nombre_legible_y_aviso_de_las_que_no_entran(client, auth_headers, reloj):
    from app.database import get_db
    from app.main import app
    from app.models.alerta_auditoria import AlertaAuditoria, TipoAlerta
    from app.models.usuario import Usuario

    db = next(app.dependency_overrides[get_db]())
    usuario = db.query(Usuario).order_by(Usuario.id.desc()).first()
    for i in range(25):
        db.add(AlertaAuditoria(usuario_id=usuario.id, tipo=TipoAlerta.GASTO_DUPLICADO,
                               descripcion=f"Posible gasto duplicado número {i}", monto_involucrado=1000 + i))
    db.commit()
    texto = _pdf(client, auth_headers, 8)
    assert "Posible gasto duplicado 25" in texto          # resumen por tipo, con nombre legible
    assert "gasto_duplicado" not in texto
    assert "Y 5 alertas más" in texto


def test_incluye_el_descargo(client, auth_headers, reloj):
    texto = _pdf(client, auth_headers, 8)
    # Criterio textual de la HU-13.
    assert "no reemplaza el asesoramiento de un contador matriculado" in texto
