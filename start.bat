@echo off
REM Inicio rapido de FreelanceControl con Docker (doble clic en Windows).
REM Requisito: Docker Desktop instalado y ABIERTO.
REM
REM El script crea el .env, levanta los contenedores, carga los datos de
REM demostracion y abre la aplicacion en el navegador.

cd /d "%~dp0"

echo ======================================================
echo    FreelanceControl - arranque con Docker
echo ======================================================

docker info >nul 2>&1
if errorlevel 1 (
  echo.
  echo   ERROR: Docker no esta corriendo.
  echo   Abri Docker Desktop, espera a que arranque y volve a ejecutar.
  echo.
  pause
  exit /b 1
)

if not exist .env (
  echo -^> Generando archivo .env ...
  (
    echo DATABASE_URL=postgresql://marcos:marcos123@db:5432/tfg_freelancers
    echo POSTGRES_USER=marcos
    echo POSTGRES_PASSWORD=marcos123
    echo POSTGRES_DB=tfg_freelancers
    echo SECRET_KEY=clave_demo_freelancecontrol_cambiar_si_se_usa_en_serio
    echo ALGORITHM=HS256
    echo ACCESS_TOKEN_EXPIRE_MINUTES=10080
    echo GROQ_API_KEY=
    echo GROQ_MODEL=llama-3.3-70b-versatile
  ) > .env
)

echo -^> Construyendo y levantando contenedores (la primera vez puede tardar varios minutos)...
docker compose up --build -d

echo -^> Esperando a que la API este lista...
timeout /t 30 /nobreak >nul

echo -^> Cargando datos de demostracion...
docker compose exec -T api python seed_modelo_base.py
docker compose exec -T api python seed_demo.py

echo -^> Abriendo http://localhost:3000 ...
start http://localhost:3000

echo.
echo ======================================================
echo    Listo. Usuario de prueba:
echo       demo@freelancecontrol.com   /   demo1234
echo    Para detener todo:  docker compose down
echo ======================================================
pause
