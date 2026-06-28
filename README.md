# FreelanceControl — Gestión financiera para freelancers (Monotributo)

Aplicación web para que un trabajador independiente (monotributista en Argentina)
lleve el control de sus **ingresos, gastos y facturas**, reciba **alertas de
auditoría**, **proyecte sus finanzas**, controle su **categoría de Monotributo**
y obtenga un **resumen y recomendaciones** asistidos por IA. Incluye un
**clasificador de gastos** basado en aprendizaje automático (NLP) que corre 100 %
de forma local.

Trabajo Final de Grado.

---

## Stack tecnológico

| Capa        | Tecnología                                              |
|-------------|---------------------------------------------------------|
| Backend     | Python 3.11 · FastAPI · SQLAlchemy · Alembic            |
| Base de datos | PostgreSQL 15                                         |
| Machine Learning | scikit-learn (clasificador de gastos) · Prophet (proyecciones) |
| IA generativa | Groq (resumen y recomendaciones) — **opcional**, con fallback local |
| Frontend    | React 19 · React Router · Axios                         |
| Auth        | JWT (python-jose) · bcrypt                               |
| Infra       | Docker · Docker Compose                                  |

---

## Cómo ejecutar la aplicación

> **⚡ Inicio rápido (doble clic):** con Docker Desktop abierto, hacé doble clic en
> **`start.command`** (macOS) o **`start.bat`** (Windows). El script crea el `.env`,
> levanta todo, carga los datos de demostración y abre la app en el navegador.
> *(En macOS, la primera vez puede que tengas que hacer clic derecho → **Abrir**.)*
> Más abajo están los pasos manuales por si preferís hacerlo a mano.

Hay **dos formas**. La **Opción A (Docker)** es la recomendada: levanta la base de
datos, el backend y el frontend con un solo comando y no requiere instalar Python,
Node ni PostgreSQL en la computadora.

### Requisitos previos

- **Opción A:** [Docker Desktop](https://www.docker.com/products/docker-desktop/)
  instalado y abierto.
- **Opción B (manual):** Python 3.11+, Node.js 18+ y PostgreSQL 15 instalados.

---

### Opción A — Con Docker Compose (recomendada)

**1. Crear el archivo `.env`**

En la raíz del proyecto, copiar la plantilla y luego editarla:

```bash
cp .env.example .env
```

Abrir el `.env` y dejarlo con **exactamente** estos valores (coinciden con la base
de datos que crea Docker Compose):

```env
DATABASE_URL=postgresql://marcos:marcos123@db:5432/tfg_freelancers

SECRET_KEY=pegar_aca_una_clave_aleatoria
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Opcional: sólo para el resumen y las recomendaciones con IA.
# Si se deja vacío, esos módulos usan un fallback local determinístico
# y la aplicación funciona igual.
GROQ_API_KEY=
GROQ_MODEL=llama-3.3-70b-versatile
```

Para generar la `SECRET_KEY` se puede usar:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

**2. Levantar todo**

```bash
docker compose up --build -d
```

Esto construye e inicia tres contenedores: la base de datos, la API (que aplica
las migraciones automáticamente al arrancar) y el frontend.

**3. Cargar los datos de demostración**

Una vez que los contenedores están arriba, ejecutar estos dos comandos:

```bash
docker compose exec api python seed_modelo_base.py   # entrena el clasificador base
docker compose exec api python seed_demo.py          # crea el usuario demo con datos
```

**4. Abrir la aplicación**

- Frontend: **http://localhost:3000**
- API (documentación interactiva): **http://localhost:8000/docs**

**5. Iniciar sesión con el usuario de demostración**

| Email                        | Contraseña |
|------------------------------|------------|
| `demo@freelancecontrol.com`  | `demo1234` |

**Para detener la aplicación:**

```bash
docker compose down          # detiene los contenedores (conserva los datos)
docker compose down -v        # detiene y borra también la base de datos
```

---

### Opción B — Ejecución manual (sin Docker)

Requiere tener PostgreSQL corriendo localmente con una base llamada
`tfg_freelancers`.

**Backend**

```bash
# 1. Entorno virtual
python -m venv venv
source venv/bin/activate          # en Windows: venv\Scripts\activate

# 2. Dependencias
pip install -r requirements.txt

# 3. Variables de entorno
cp .env.example .env
# Editar .env y apuntar DATABASE_URL a tu PostgreSQL local, por ejemplo:
# DATABASE_URL=postgresql://USUARIO:CLAVE@localhost:5432/tfg_freelancers

# 4. Migraciones (crea las tablas)
alembic upgrade head

# 5. Datos de demostración
python seed_modelo_base.py
python seed_demo.py

# 6. Levantar la API
uvicorn app.main:app --reload
```

La API queda en **http://localhost:8000**.

**Frontend** (en otra terminal)

```bash
cd frontend
npm install
npm start
```

El frontend queda en **http://localhost:3000** y apunta por defecto a
`http://localhost:8000`. Para cambiar la URL del backend, definir
`REACT_APP_API_URL`.

---

## Ejecutar los tests

El proyecto incluye una suite de tests automatizados del backend (pytest).

```bash
# Con Docker:
docker compose exec api pytest

# De forma manual (con el venv activado):
pytest
```

---

## Estructura del proyecto

```
.
├── app/                  # Backend (FastAPI)
│   ├── models/           # Modelos de datos (SQLAlchemy)
│   ├── schemas/          # Esquemas de validación (Pydantic)
│   ├── routers/          # Endpoints de la API por módulo
│   ├── services/         # Lógica de negocio (auth, ML, IA, auditoría, etc.)
│   ├── database.py       # Conexión a la base de datos
│   └── main.py           # Punto de entrada de la API
├── alembic/              # Migraciones de la base de datos
├── frontend/             # Aplicación React
│   └── src/
│       ├── pages/        # Páginas de la aplicación
│       └── components/   # Componentes reutilizables
├── tests/                # Tests automatizados (pytest)
├── docs/                 # Manual completo, informe y material de defensa
├── seed_demo.py          # Carga el usuario y los datos de demostración
├── seed_modelo_base.py   # Entrena el modelo base del clasificador
├── docker-compose.yml    # Orquestación de DB + API + frontend
├── Dockerfile            # Imagen del backend
└── requirements.txt      # Dependencias de Python
```

---

## Documentación adicional

En la carpeta [`docs/`](docs/) se incluye material complementario:

- **`FreelanceControl_Manual_Completo.pdf`** — manual de usuario detallado.
- **`FreelanceControl_Informe_Capitulos.pdf`** — informe del trabajo.
- **`DEMO.md`** y **`GUION_DEMO_5MIN.md`** — guías de la demostración.
- **`extractos_ejemplo/`** — archivos CSV de ejemplo para probar la importación.

---

## Notas

- El archivo `.env` **no** se incluye en el repositorio por contener credenciales;
  hay que crearlo a partir de `.env.example` como se indica arriba.
- La **clasificación de gastos** funciona de forma totalmente local con el modelo
  de Machine Learning; no depende de ningún servicio externo.
- La **IA generativa** (resumen y recomendaciones) es opcional: si no se configura
  `GROQ_API_KEY`, la aplicación usa un fallback local y sigue funcionando.
