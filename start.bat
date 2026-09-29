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

REM La SECRET_KEY y la clave de la base se arman con numeros al azar en cada
REM equipo: ninguna queda escrita en el repositorio (y la API no arranca con
REM una clave fija o publica, ni con menos de 32 caracteres). La clave de la
REM base se usa una sola vez, cuando Docker crea la base: si ya existe una
REM base de una instalacion anterior, no borres el .env (o borra tambien la
REM base con "docker compose down -v").
if not exist .env (
  echo -^> Generando archivo .env ...
  set DB_PASSWORD=fc%RANDOM%%RANDOM%%RANDOM%%RANDOM%%RANDOM%%RANDOM%
)
REM Bloque aparte: Windows reemplaza %DB_PASSWORD% al leer cada bloque, asi
REM que en el mismo bloque del "set" todavia estaria vacia.
if not exist .env (
  (
    echo DATABASE_URL=postgresql://freelancecontrol:%DB_PASSWORD%@db:5432/tfg_freelancers
    echo POSTGRES_USER=freelancecontrol
    echo POSTGRES_PASSWORD=%DB_PASSWORD%
    echo POSTGRES_DB=tfg_freelancers
    echo SECRET_KEY=freelancecontrol_local_%RANDOM%%RANDOM%%RANDOM%%RANDOM%_%RANDOM%%RANDOM%%RANDOM%%RANDOM%_%RANDOM%%RANDOM%%RANDOM%%RANDOM%
    echo ALGORITHM=HS256
    echo ACCESS_TOKEN_EXPIRE_MINUTES=10080
    echo GROQ_API_KEY=
    echo GROQ_MODEL=openai/gpt-oss-120b
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
