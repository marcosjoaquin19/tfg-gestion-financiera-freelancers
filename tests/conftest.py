import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db


# Usamos SQLite en memoria para los tests
# StaticPool → todas las conexiones comparten la misma BD en memoria
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    # Crea todas las tablas antes de cada test y las borra al terminar
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db, monkeypatch):
    # Reemplaza get_db por la sesión de test
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    # El reentrenamiento automático del clasificador corre en una BackgroundTask
    # de FastAPI que abre su propia sesión vía SessionLocal (apunta a PostgreSQL).
    # En tests no queremos esa conexión, así que neutralizamos el hook.
    from app.routers import gastos as gastos_router
    monkeypatch.setattr(gastos_router, "_reentrenar_en_background", lambda *a, **k: None)

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def usuario_registrado(client):
    # Crea un usuario y devuelve sus datos
    client.post("/auth/register", json={
        "nombre": "Test User",
        "email": "test@test.com",
        "password": "password123"
    })
    return {"email": "test@test.com", "password": "password123"}


@pytest.fixture
def auth_headers(client, usuario_registrado):
    # Devuelve el header Authorization listo para usar en los requests
    response = client.post("/auth/login", data={
        "username": usuario_registrado["email"],
        "password": usuario_registrado["password"]
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
