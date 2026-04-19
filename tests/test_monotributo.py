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
