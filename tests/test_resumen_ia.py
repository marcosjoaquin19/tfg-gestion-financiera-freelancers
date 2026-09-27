"""
Tests del resumen financiero con IA (GET /resumen/financiero, HU-11).

Groq se reemplaza por un doble (`GroqFalso`) que devuelve respuestas
programadas —buenas, cortadas, con formato, con cifras inventadas— o lanza
errores. Así se prueba cada control del servicio sin salir a internet y se
puede inspeccionar exactamente qué se le habría enviado al servicio externo.
"""

from types import SimpleNamespace

import pytest

import app.services.ia_service as ia


# --- Doble de Groq -------------------------------------------------------------

class GroqFalso:
    respuestas: list = []       # (contenido, finish_reason) o una excepción
    llamadas: list = []         # kwargs de cada chat.completions.create
    config: dict = {}           # kwargs con los que se creó el cliente

    def __init__(self, **kwargs):
        GroqFalso.config = kwargs
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        GroqFalso.llamadas.append(kwargs)
        r = GroqFalso.respuestas.pop(0)
        if isinstance(r, Exception):
            raise r
        contenido, fin = r
        return SimpleNamespace(
            model=kwargs["model"],
            choices=[SimpleNamespace(message=SimpleNamespace(content=contenido), finish_reason=fin)],
        )


@pytest.fixture
def groq(monkeypatch):
    GroqFalso.respuestas = []
    GroqFalso.llamadas = []
    GroqFalso.config = {}
    monkeypatch.setattr(ia, "Groq", GroqFalso)
    monkeypatch.setenv("GROQ_API_KEY", "gsk_de_prueba")
    monkeypatch.setenv("GROQ_MODEL", "openai/gpt-oss-120b")
    return GroqFalso


@pytest.fixture
def mes_con_datos(client, auth_headers):
    """Agosto 2026: 3 cobros por $ 2.800.000, gastos por $ 431.000 en tres
    rubros y una factura pendiente de $ 3.150.000. Descripciones y cliente
    llevan un nombre propio para verificar que nunca viajan a la IA."""
    for monto in (1_000_000, 900_000, 900_000):
        client.post("/ingresos/", json={
            "descripcion": "Honorarios Juan Pérez", "monto": monto,
            "categoria": "Servicios", "fecha": "2026-08-10T12:00:00",
        }, headers=auth_headers)
    for desc, monto, cat in [("Hosting de Juan Pérez", 176_000, "Infraestructura"),
                             ("Contador Juan Pérez", 95_000, "Servicios"),
                             ("Curso online", 160_000, "Capacitación")]:
        client.post("/gastos/", json={
            "descripcion": desc, "monto": monto, "categoria": cat, "fecha": "2026-08-12T12:00:00",
        }, headers=auth_headers)
    client.post("/facturas/", json={
        "cliente_nombre": "Estudio Pérez", "descripcion": "Sitio web de Juan Pérez",
        "monto": 3_150_000, "fecha_emision": "2026-09-01T12:00:00",
        "fecha_vencimiento": "2099-12-31T12:00:00",
    }, headers=auth_headers)
    return {"mes": 8, "anio": 2026}


def _pedir(client, headers, mes=8, anio=2026):
    r = client.get(f"/resumen/financiero?mes={mes}&anio={anio}", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


BUENO = (
    "En Agosto 2026 cobraste $ 2.800.000,00 en tres ingresos y tus gastos sumaron $ 431.000,00, "
    "así que cerraste el mes con un superávit de $ 2.369.000,00. El rubro con más gasto fue "
    "Infraestructura, con $ 176.000,00, seguido por Capacitación con $ 160.000,00 y Servicios con "
    "$ 95.000,00. Hoy tenés una factura pendiente de cobro por $ 3.150.000,00, que puede ser de otro "
    "mes. Es un buen momento para revisar tus gastos fijos y seguir registrando cada movimiento."
)


# --- Privacidad del payload (HU-11, CP-M10-03) ---------------------------------

def test_a_la_ia_solo_viajan_totales_agregados(client, auth_headers, groq, mes_con_datos):
    groq.respuestas = [(BUENO, "stop")]
    _pedir(client, auth_headers)

    enviado = " ".join(m["content"] for m in groq.llamadas[0]["messages"])
    assert "Pérez" not in enviado and "Juan" not in enviado          # ni descripciones ni clientes
    assert "Hosting" not in enviado and "Curso" not in enviado
    assert "Ingresos del mes: $ 2.800.000,00 (3 cobros)" in enviado   # formato argentino
    assert "Infraestructura $ 176.000,00" in enviado                  # categoría de la lista cerrada
    assert "superávit de $ 2.369.000,00" in enviado
    assert "Facturas pendientes de cobro a hoy: 1 por $ 3.150.000,00" in enviado


def test_parametros_de_la_llamada(client, auth_headers, groq, mes_con_datos):
    groq.respuestas = [(BUENO, "stop")]
    _pedir(client, auth_headers)

    llamada = groq.llamadas[0]
    assert llamada["model"] == "openai/gpt-oss-120b"
    assert llamada["max_tokens"] == ia.GROQ_MAX_TOKENS
    assert llamada["temperature"] == ia.GROQ_TEMPERATURA
    assert llamada["extra_body"] == {"reasoning_effort": "low"}
    assert groq.config["max_retries"] == 0                            # sin reintentos de red
    assert groq.config["timeout"].connect == 3.0 and groq.config["timeout"].read == 10.0


def test_otro_modelo_no_recibe_reasoning_effort(client, auth_headers, groq, mes_con_datos, monkeypatch):
    monkeypatch.setenv("GROQ_MODEL", "llama-3.1-8b-instant")
    groq.respuestas = [(BUENO, "stop")]
    _pedir(client, auth_headers)
    assert groq.llamadas[0]["extra_body"] is None


# --- Respuesta válida ---------------------------------------------------------

def test_resumen_valido_se_devuelve_como_ia(client, auth_headers, groq, mes_con_datos):
    groq.respuestas = [(BUENO, "stop")]
    data = _pedir(client, auth_headers)
    assert data["generado_con_ia"] is True
    assert data["motivo_reserva"] is None
    assert data["resumen"] == BUENO
    assert data["periodo"] == "Agosto 2026"


def test_markdown_titulos_y_vinetas_quedan_en_un_parrafo(client, auth_headers, groq, mes_con_datos):
    con_formato = (
        "**Resumen financiero – Agosto 2026**\n\n"
        "En **Agosto 2026** cobraste $ 2.800.000,00 en tres ingresos y tus gastos sumaron $ 431.000,00. "
        "Cerraste el mes con un superávit de $ 2.369.000,00.\n\n"
        "- Infraestructura: $ 176.000,00\n- Capacitación: $ 160.000,00\n- Servicios: $ 95.000,00\n\n"
        "Hoy tenés una factura pendiente de cobro por $ 3.150.000,00. Seguí registrando cada movimiento "
        "para mantener tus números al día y tomar mejores decisiones."
    )
    groq.respuestas = [(con_formato, "stop")]
    texto = _pedir(client, auth_headers)["resumen"]
    assert "**" not in texto and "\n" not in texto and "- " not in texto
    assert not texto.startswith("Resumen financiero")                 # el título suelto se quita
    assert "Infraestructura: $ 176.000,00. Capacitación" in texto     # viñetas cerradas con punto


# --- Respuestas cortadas o cortas (el problema de septiembre) --------------------

def test_respuesta_cortada_descarta_la_oracion_incompleta(client, auth_headers, groq, mes_con_datos):
    cortada = BUENO + " Además tenés una importante cartera por"
    groq.respuestas = [(cortada, "length")]
    data = _pedir(client, auth_headers)
    assert data["generado_con_ia"] is True
    assert data["resumen"].endswith("movimiento.")
    assert "cartera por" not in data["resumen"]


def test_cortada_en_el_punto_de_un_monto_tambien_se_descarta(client, auth_headers, groq, mes_con_datos):
    # "$ 3." termina en punto pero es un monto a medias: con finish_reason
    # "length" la última oración se descarta siempre.
    groq.respuestas = [(BUENO + " Si cobrás esa factura vas a sumar $ 3.", "length")]
    texto = _pedir(client, auth_headers)["resumen"]
    assert "$ 3." not in texto.replace("$ 3.150", "")


def test_respuesta_demasiado_corta_se_reintenta(client, auth_headers, groq, mes_con_datos):
    groq.respuestas = [("En Agosto 2026 cobraste $ 2.800.000,00 y tus gastos", "length"), (BUENO, "stop")]
    data = _pedir(client, auth_headers)
    assert len(groq.llamadas) == 2
    assert data["generado_con_ia"] is True and data["resumen"] == BUENO


def test_dos_respuestas_invalidas_usan_la_plantilla(client, auth_headers, groq, mes_con_datos):
    groq.respuestas = [("Todo bien.", "stop"), ("Resumen: cobraste plata.", "length")]
    data = _pedir(client, auth_headers)
    assert len(groq.llamadas) == 2
    assert data["generado_con_ia"] is False
    assert data["motivo_reserva"] == "respuesta_descartada"
    assert data["resumen"].startswith("En Agosto 2026 cobraste $ 2.800.000,00")


def test_nunca_supera_150_palabras(client, auth_headers, groq, mes_con_datos):
    largo = BUENO + " " + " ".join(["Seguí así y mantené tus registros ordenados cada semana."] * 20)
    groq.respuestas = [(largo, "stop")]
    texto = _pedir(client, auth_headers)["resumen"]
    assert len(texto.split()) <= ia.MAX_PALABRAS_RESUMEN
    assert texto.endswith(".")                                         # recorta en oración completa


# --- Cifras que no estaban en los datos --------------------------------------------

@pytest.mark.parametrize("agregado", [
    "Cuando cobres esa factura, tu flujo va a superar los $ 5.950.000,00.",   # cuenta propia
    "Tus gastos representan el 15 % de tus ingresos.",                      # porcentaje calculado
    "El mes que viene podrías cobrar unos 4 millones.",                     # predicción con cifra
])
def test_cifra_no_enviada_se_rechaza_y_reintenta(client, auth_headers, groq, mes_con_datos, agregado):
    groq.respuestas = [(BUENO + " " + agregado, "stop"), (BUENO, "stop")]
    data = _pedir(client, auth_headers)
    assert len(groq.llamadas) == 2
    assert data["resumen"] == BUENO


def test_redondeos_de_cifras_enviadas_se_aceptan(client, auth_headers, groq, mes_con_datos):
    redondeado = BUENO.replace("$ 2.800.000,00", "$ 2,8 millones").replace("$ 431.000,00", "431 mil")
    groq.respuestas = [(redondeado, "stop")]
    data = _pedir(client, auth_headers)
    assert len(groq.llamadas) == 1 and data["generado_con_ia"] is True


# --- Fallas del servicio externo (HU-11, CP-M10-04) --------------------------------

def test_error_de_red_usa_la_plantilla_sin_reintentar(client, auth_headers, groq, mes_con_datos):
    groq.respuestas = [TimeoutError("Request timed out.")]
    data = _pedir(client, auth_headers)
    assert len(groq.llamadas) == 1
    assert data["generado_con_ia"] is False
    assert data["motivo_reserva"] == "servicio_no_disponible"


def test_limite_de_uso_se_informa_aparte(client, auth_headers, groq, mes_con_datos):
    import httpx
    from groq import RateLimitError
    pedido = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    respuesta = httpx.Response(429, request=pedido)
    groq.respuestas = [RateLimitError("Rate limit reached", response=respuesta, body=None)]
    data = _pedir(client, auth_headers)
    assert len(groq.llamadas) == 1
    assert data["generado_con_ia"] is False and data["motivo_reserva"] == "limite_de_uso"


def test_sin_clave_no_llama_a_groq(client, auth_headers, groq, mes_con_datos, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY")
    data = _pedir(client, auth_headers)
    assert groq.llamadas == []
    assert data["motivo_reserva"] == "sin_clave" and data["generado_con_ia"] is False


def test_plantilla_local_completa(client, auth_headers, groq, mes_con_datos, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY")
    texto = _pedir(client, auth_headers)["resumen"]
    assert texto == (
        "En Agosto 2026 cobraste $ 2.800.000,00 en 3 ingresos y tus gastos sumaron $ 431.000,00: "
        "el mes cerró con superávit de $ 2.369.000,00. El rubro con más gasto fue Infraestructura, "
        "con $ 176.000,00. Hoy tenés 1 factura pendiente de cobro por $ 3.150.000,00."
    )


def test_plantilla_con_deficit_y_sin_facturas(client, auth_headers, groq, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY")
    client.post("/ingresos/", json={"descripcion": "Cobro", "monto": 100_000, "categoria": "Servicios",
                                    "fecha": "2026-07-10T12:00:00"}, headers=auth_headers)
    client.post("/gastos/", json={"descripcion": "Notebook", "monto": 400_000, "categoria": "Hardware",
                                  "fecha": "2026-07-11T12:00:00"}, headers=auth_headers)
    texto = _pedir(client, auth_headers, mes=7)["resumen"]
    assert "cobraste $ 100.000,00 en 1 ingreso " in texto
    assert "déficit de $ 300.000,00" in texto
    assert "Hoy no tenés facturas pendientes de cobro." in texto


def test_plantilla_solo_gastos(client, auth_headers, groq, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY")
    client.post("/gastos/", json={"descripcion": "Hosting", "monto": 50_000, "categoria": "Infraestructura",
                                  "fecha": "2026-06-11T12:00:00"}, headers=auth_headers)
    texto = _pedir(client, auth_headers, mes=6)["resumen"]
    assert texto.startswith("En Junio 2026 no registraste ingresos y tus gastos sumaron $ 50.000,00")


# --- Mes sin datos y parámetros ------------------------------------------------------

def test_mes_sin_movimientos_no_llama_a_la_ia(client, auth_headers, groq):
    data = _pedir(client, auth_headers, mes=1, anio=2026)
    assert data["sin_datos"] is True and data["generado_con_ia"] is False
    assert groq.llamadas == []


@pytest.mark.parametrize("query", ["mes=0", "mes=13", "anio=1999", "anio=2101", "anio=99999", "mes=abc"])
def test_parametros_fuera_de_rango(client, auth_headers, query):
    assert client.get(f"/resumen/financiero?{query}", headers=auth_headers).status_code == 422
