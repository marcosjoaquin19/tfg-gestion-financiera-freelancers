import pytest


@pytest.fixture(autouse=True)
def seed_categorias(client):
    from decimal import Decimal
    from datetime import date
    from app.models.categoria_monotributo import CategoriaMonotributo
    from app.database import get_db
    from app.main import app

    db = next(app.dependency_overrides[get_db]())
    for letra, limite, cuota in [
        ("A", Decimal("1000000"), Decimal("5000")),
        ("B", Decimal("1500000"), Decimal("6000")),
    ]:
        db.add(CategoriaMonotributo(
            letra=letra,
            limite_anual=limite,
            cuota_mensual=cuota,
            actividad="servicios",
            fecha_vigencia=date(2024, 1, 1),
            activa=True,
        ))
    db.commit()


def test_estado_sin_categoria(client, auth_headers):
    response = client.get("/monotributo/estado", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data.get("sin_categoria") is True


def test_actualizar_categoria(client, auth_headers):
    response = client.patch(
        "/monotributo/categoria",
        json={"categoria_monotributo": "A"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["categoria_monotributo"] == "A"


def test_estado_con_categoria(client, auth_headers):
    client.patch(
        "/monotributo/categoria",
        json={"categoria_monotributo": "B"},
        headers=auth_headers,
    )
    response = client.get("/monotributo/estado", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "categoria_actual" in data
    assert "limite_anual" in data
    assert "cuota_mensual" in data


def test_pago_monotributo(client, auth_headers):
    response = client.get("/monotributo/pago", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "pagado" in data


# ── Facturación móvil 12 meses (sugerencia del docente) ──────────────────────

def test_facturacion_12_meses_sin_auth(client):
    assert client.get("/monotributo/facturacion-12-meses").status_code == 401


def test_facturacion_12_meses_vacio(client, auth_headers):
    response = client.get("/monotributo/facturacion-12-meses", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["facturacion_12_meses"] == 0
    assert data["categoria"] is None


def test_facturacion_12_meses_excluye_ingresos_de_hace_mas_de_un_anio(client, auth_headers):
    # Cargamos un ingreso reciente y otro de hace más de un año. El cálculo
    # AFIP es ventana móvil de 12 meses, así que el viejo no debe contar.
    from datetime import datetime, timedelta
    reciente = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S")
    antiguo = (datetime.now() - timedelta(days=400)).strftime("%Y-%m-%dT%H:%M:%S")

    client.post("/ingresos/", json={
        "descripcion": "Reciente", "monto": 5000,
        "categoria": "Desarrollo", "fecha": reciente,
    }, headers=auth_headers)
    client.post("/ingresos/", json={
        "descripcion": "Antiguo", "monto": 9999,
        "categoria": "Desarrollo", "fecha": antiguo,
    }, headers=auth_headers)

    response = client.get("/monotributo/facturacion-12-meses", headers=auth_headers)
    assert response.json()["facturacion_12_meses"] == 5000


def test_facturacion_12_meses_incluye_categoria_y_porcentaje(client, auth_headers):
    # Si el usuario tiene categoría seteada, la respuesta agrega el
    # porcentaje del límite anual ya consumido por la facturación móvil.
    client.patch(
        "/monotributo/categoria",
        json={"categoria_monotributo": "A"},
        headers=auth_headers,
    )

    from datetime import datetime
    hoy = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    client.post("/ingresos/", json={
        "descripcion": "Cobro", "monto": 100000,
        "categoria": "Servicios", "fecha": hoy,
    }, headers=auth_headers)

    data = client.get("/monotributo/facturacion-12-meses", headers=auth_headers).json()
    assert data["facturacion_12_meses"] == 100000
    assert data["categoria"]["categoria"] == "A"
    assert data["categoria"]["limite_anual"] == 1_000_000.0
    assert data["categoria"]["porcentaje_usado"] == 10.0
