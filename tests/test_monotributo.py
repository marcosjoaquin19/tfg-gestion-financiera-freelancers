def test_estado_sin_categoria(client, auth_headers):
    # El usuario recién creado no tiene categoria_monotributo asignada
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
    # Asignamos categoría primero
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
