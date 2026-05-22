# ESTADO DEL PROYECTO — TFG Freelancers API

> Actualizado el 2026-05-22. Descripción exhaustiva del estado actual del sistema.

---

## 1. Stack Tecnológico con Versiones Exactas

### Backend
| Componente | Tecnología | Versión |
|---|---|---|
| Lenguaje | Python | 3.11 |
| Framework web | FastAPI | 0.110.0 |
| Servidor ASGI | Uvicorn | 0.29.0 |
| ORM | SQLAlchemy | 2.0.29 |
| Validación | Pydantic | 2.6.4 |
| Driver PostgreSQL | psycopg2-binary | 2.9.9 |
| Autenticación JWT | python-jose | 3.3.0 |
| Hash contraseñas | passlib + bcrypt | 1.7.4 + 4.1.2 |
| Variables de entorno | python-dotenv | 1.0.1 |
| Validación emails | email-validator | 2.1.1 |
| Formularios | python-multipart | 0.0.9 |
| Predicciones ML | Prophet | 1.1.5 |
| Backend Prophet | cmdstanpy | 1.2.4 |
| Manipulación datos | pandas | 2.2.1 |
| Cliente IA | groq | 0.13.0 |
| Migraciones BD | alembic | 1.13.1 |
| Clasificador NLP | scikit-learn | 1.4.2 |
| Serialización de modelos | joblib | 1.4.0 |
| Generación de PDF | reportlab | 4.1.0 |
| Lectura de Excel | openpyxl | 3.1.2 |

### Base de datos
| Componente | Tecnología | Versión |
|---|---|---|
| Motor BD | PostgreSQL | 15 |

### Testing
| Componente | Tecnología | Versión |
|---|---|---|
| Framework tests | pytest | 8.1.1 |
| Cliente HTTP tests | httpx | 0.27.0 |
| Cobertura | pytest-cov | 5.0.0 |
| BD tests | SQLite | in-memory |

### Frontend
| Componente | Tecnología | Versión |
|---|---|---|
| Runtime | Node.js | 18 (Alpine) |
| Framework | React | (ver frontend/package.json) |

### Infraestructura
| Componente | Tecnología |
|---|---|
| Contenedores | Docker + Docker Compose 3.8 |
| Modelo IA externo | Groq llama-3.3-70b-versatile — solo resúmenes y recomendaciones |

---

## 2. Estructura Completa de Carpetas

```
proyecto-tfg/
├── .env                                      # Variables de entorno (credenciales — NO commitear)
├── .gitignore
├── alembic.ini                               # Configuración Alembic
├── Dockerfile                                # Backend: Python 3.11-slim
├── docker-compose.yml                        # Servicios: db + api + frontend
├── requirements.txt                          # Dependencias Python con versiones exactas
├── seed_categorias_monotributo.py            # Script seed: categorías A-K del Monotributo
├── seed_ingresos.py                          # Script seed: ingresos de ejemplo
├── seed_demo.py                              # Script seed: usuario y datos de demostración
├── seed_modelo_base.py                       # Script seed: entrena y persiste el clasificador base
├── evaluar_modelo.py                         # Script: evalúa el clasificador con validación cruzada
│
├── app/
│   ├── __init__.py
│   ├── main.py                               # App FastAPI, CORS, registro de routers
│   ├── database.py                           # Engine, SessionLocal, Base, get_db()
│   ├── dependencies.py                       # OAuth2PasswordBearer, get_current_user()
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── usuario.py
│   │   ├── ingreso.py
│   │   ├── gasto.py
│   │   ├── factura.py
│   │   ├── proyeccion.py
│   │   ├── alerta_auditoria.py
│   │   ├── categoria_monotributo.py
│   │   ├── cache_clasificacion.py
│   │   └── modelo_clasificador.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── usuario.py
│   │   ├── ingreso.py
│   │   ├── gasto.py
│   │   ├── factura.py
│   │   ├── proyeccion.py
│   │   └── alerta.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth.py                           # Hash/verificación contraseñas, JWT, CRUD usuario
│   │   ├── auditoria.py                      # Módulo M3: detección duplicados, anomalías, discrepancias
│   │   ├── ml_service.py                     # Clasificador NLP local (Naive Bayes/SVM + TF-IDF), reentrenamiento
│   │   ├── prophet_service.py                # Proyecciones con Prophet o media móvil (fallback)
│   │   ├── ia_service.py                     # Clasificación (delega en ml_service) + Groq para resumen/recomendaciones
│   │   ├── csv_service.py                    # Importación CSV/Excel: detección columnas, parsing, duplicados
│   │   ├── reportes_service.py               # Generación del reporte mensual en PDF (ReportLab)
│   │   └── monotributo_service.py            # Estado Monotributo, verificación pago mensual
│   │
│   └── routers/
│       ├── __init__.py
│       ├── auth.py                           # /auth/register, /auth/login
│       ├── ingresos.py                       # CRUD /ingresos/
│       ├── gastos.py                         # CRUD /gastos/ + clasificación IA
│       ├── facturas.py                       # CRUD /facturas/ + PATCH estado
│       ├── alertas.py                        # GET/PATCH /alertas/, POST ejecutar-auditoria
│       ├── proyecciones.py                   # POST generar + GET /proyecciones/
│       ├── resumen.py                        # GET /resumen/financiero
│       ├── recomendaciones.py                # GET /recomendaciones/
│       ├── importar.py                       # POST /importar/preview + /importar/confirmar (CSV y Excel)
│       ├── monotributo.py                    # GET /monotributo/estado + /pago, PATCH /categoria
│       ├── ml.py                             # GET /ml/estado, POST /ml/reentrenar, POST /ml/corregir
│       └── reportes.py                       # GET /reportes/pdf — reporte mensual descargable
│
├── alembic/
│   ├── env.py                                # Setup Alembic: lee .env, importa modelos
│   ├── script.py.mako                        # Template para scripts de migración
│   └── versions/
│       ├── 0001_initial_schema.py            # Migración inicial: todas las tablas base
│       ├── 0002_tabla_categoria_monotributo.py  # Tabla categorias_monotributo
│       └── 0003_tabla_modelo_clasificador.py    # Tabla modelos_clasificador
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                           # Fixtures: SQLite in-memory, TestClient, usuario/auth
│   ├── test_auth.py
│   ├── test_ingresos.py
│   ├── test_gastos.py
│   ├── test_facturas.py
│   ├── test_proyecciones.py
│   ├── test_auditoria.py
│   ├── test_ia.py
│   ├── test_importar.py
│   ├── test_monotributo.py
│   ├── test_ml.py
│   └── test_reportes.py
│
└── frontend/
    ├── Dockerfile                            # Node 18-alpine, npm start
    ├── package.json
    ├── src/
    │   ├── components/
    │   └── pages/
    └── node_modules/
```

---

## 3. Modelos de Datos

### Enums

```python
# factura.py
class EstadoFactura(str, Enum):
    PENDIENTE = "pendiente"
    PAGADA    = "pagada"
    VENCIDA   = "vencida"

# alerta_auditoria.py
class TipoAlerta(str, Enum):
    GASTO_DUPLICADO          = "gasto_duplicado"
    ANOMALIA_ESTADISTICA     = "anomalia_estadistica"
    DISCREPANCIA_FACTURACION = "discrepancia_facturacion"
    RIESGO_RECATEGORIZACION  = "riesgo_recategorizacion"
    FACTURA_IMPAGA           = "factura_impaga"
    COMISION_EXCESIVA        = "comision_excesiva"
```

### Tabla: `usuarios`

| Columna | Tipo | Restricciones |
|---|---|---|
| id | Integer | PK, index |
| nombre | String(100) | NOT NULL |
| email | String(150) | UNIQUE, NOT NULL, index |
| password_hash | String(255) | NOT NULL |
| es_activo | Boolean | default=True |
| categoria_monotributo | String(2) | nullable |
| actividad_monotributo | String(20) | default="servicios" |
| fecha_creacion | DateTime(tz) | server_default=now() |

**Relaciones:** → ingresos, gastos, facturas, proyecciones, alertas_auditoria

---

### Tabla: `ingresos`

| Columna | Tipo | Restricciones |
|---|---|---|
| id | Integer | PK, index |
| usuario_id | Integer | FK usuarios.id, NOT NULL |
| descripcion | String(255) | NOT NULL |
| monto | Numeric(12,2) | NOT NULL |
| categoria | String(100) | NOT NULL |
| fecha | DateTime(tz) | NOT NULL |
| fecha_creacion | DateTime(tz) | server_default=now() |

**Relaciones:** → usuario

---

### Tabla: `gastos`

| Columna | Tipo | Restricciones |
|---|---|---|
| id | Integer | PK, index |
| usuario_id | Integer | FK usuarios.id, NOT NULL |
| descripcion | String(255) | NOT NULL |
| monto | Numeric(12,2) | NOT NULL |
| categoria | String(100) | NOT NULL |
| fecha | DateTime(tz) | NOT NULL |
| es_duplicado | Boolean | default=False — marcado por módulo auditoría |
| fecha_creacion | DateTime(tz) | server_default=now() |

**Relaciones:** → usuario

---

### Tabla: `facturas`

| Columna | Tipo | Restricciones |
|---|---|---|
| id | Integer | PK, index |
| usuario_id | Integer | FK usuarios.id, NOT NULL |
| cliente_nombre | String(200) | NOT NULL |
| descripcion | String(500) | NOT NULL |
| monto | Numeric(12,2) | NOT NULL |
| estado | Enum(EstadoFactura) | default=PENDIENTE |
| fecha_emision | DateTime(tz) | NOT NULL |
| fecha_vencimiento | DateTime(tz) | NOT NULL |
| fecha_pago | DateTime(tz) | nullable |
| fecha_creacion | DateTime(tz) | server_default=now() |

**Relaciones:** → usuario

---

### Tabla: `proyecciones`

| Columna | Tipo | Restricciones |
|---|---|---|
| id | Integer | PK, index |
| usuario_id | Integer | FK usuarios.id, NOT NULL, index |
| fecha_proyeccion | DateTime(tz) | NOT NULL, index |
| monto_proyectado | Numeric(12,2) | NOT NULL |
| monto_lower | Numeric(12,2) | NOT NULL — límite inferior del intervalo de confianza |
| monto_upper | Numeric(12,2) | NOT NULL — límite superior del intervalo de confianza |
| fecha_generacion | DateTime(tz) | server_default=now() |

**Relaciones:** → usuario

---

### Tabla: `alertas_auditoria`

| Columna | Tipo | Restricciones |
|---|---|---|
| id | Integer | PK, index |
| usuario_id | Integer | FK usuarios.id, NOT NULL, index |
| tipo | Enum(TipoAlerta) | NOT NULL |
| descripcion | String(500) | NOT NULL |
| monto_involucrado | Numeric(12,2) | nullable |
| resuelta | Boolean | default=False |
| fecha_deteccion | DateTime(tz) | server_default=now() |

**Relaciones:** → usuario

---

### Tabla: `categorias_monotributo`

| Columna | Tipo | Restricciones |
|---|---|---|
| id | Integer | PK |
| letra | String(2) | UNIQUE, index, NOT NULL |
| limite_anual | Numeric(15,2) | NOT NULL |
| cuota_mensual | Numeric(12,2) | NOT NULL |
| actividad | String(20) | NOT NULL, default="servicios" |
| fecha_vigencia | Date | NOT NULL |
| activa | Boolean | NOT NULL, default=True |

**Datos seed:** Categorías A–K (servicios), vigencia 2026-02-01, límites desde $10M hasta $108M anuales.

---

### Tabla: `cache_clasificacion`

| Columna | Tipo | Restricciones |
|---|---|---|
| id | Integer | PK, index |
| descripcion_normalizada | String | UNIQUE, index, NOT NULL |
| categoria | String | NOT NULL |
| fecha_creacion | DateTime | server_default=now(), NOT NULL |

**Propósito:** Registra descripciones ya clasificadas. Histórico: nació como caché de respuestas de Groq; con el clasificador local la tabla quedó en desuso (ver sección 7).

---

### Tabla: `modelos_clasificador`

| Columna | Tipo | Restricciones |
|---|---|---|
| id | Integer | PK, index |
| usuario_id | Integer | FK usuarios.id, nullable, index — NULL = modelo base compartido |
| modelo_serializado | Text | NOT NULL — pipeline scikit-learn serializado con joblib + base64 |
| algoritmo | String(20) | NOT NULL — "naive_bayes" o "svm" |
| precision | Float | nullable — accuracy media por validación cruzada |
| n_ejemplos | Integer | default=0 — tamaño del dataset de entrenamiento |
| fecha_entrenamiento | DateTime(tz) | server_default=now() |
| activo | Boolean | default=True |

**Propósito:** Persiste el clasificador entrenado. Existe un modelo base (`usuario_id` NULL) entrenado sobre el dataset de 600 ejemplos, y modelos personalizados por usuario cuando éste acumula 20 o más gastos propios.

---

## 4. Endpoints Implementados

### Autenticación — `/auth`

| Método | Ruta | Body (entrada) | Respuesta | Notas |
|---|---|---|---|---|
| POST | `/auth/register` | `UsuarioCreate` | `UsuarioResponse` (201) | Valida email único, hashea password |
| POST | `/auth/login` | `OAuth2PasswordRequestForm` | `Token` (200) | Anti-enumeración: mismo error si email no existe o password incorrecto |

---

### Ingresos — `/ingresos`

| Método | Ruta | Body / Params | Respuesta | Notas |
|---|---|---|---|---|
| POST | `/ingresos/` | `IngresoCreate` | `IngresoResponse` (201) | usuario_id del JWT |
| GET | `/ingresos/` | `?categoria, limite, offset` | `list[IngresoResponse]` | Ordenado por fecha DESC |
| GET | `/ingresos/{id}` | — | `IngresoResponse` | Verifica ownership |
| PUT | `/ingresos/{id}` | `IngresoCreate` | `IngresoResponse` | Verifica ownership |
| DELETE | `/ingresos/{id}` | — | 204 | Verifica ownership |

---

### Gastos — `/gastos`

| Método | Ruta | Body / Params | Respuesta | Notas |
|---|---|---|---|---|
| POST | `/gastos/clasificar` | `{descripcion}` | `{categoria_sugerida, fuente, confianza, requiere_revision}` | Clasificador NLP local; marca para revisión si la confianza < 0.30 |
| POST | `/gastos/` | `GastoCreate` | `GastoResponse` (201) | usuario_id del JWT |
| GET | `/gastos/` | `?categoria, solo_duplicados, limite, offset` | `list[GastoResponse]` | Filtro por duplicados marcados |
| GET | `/gastos/{id}` | — | `GastoResponse` | Verifica ownership |
| PUT | `/gastos/{id}` | `GastoCreate` | `GastoResponse` | Verifica ownership |
| DELETE | `/gastos/{id}` | — | 204 | Verifica ownership |

---

### Facturas — `/facturas`

| Método | Ruta | Body / Params | Respuesta | Notas |
|---|---|---|---|---|
| POST | `/facturas/` | `FacturaCreate` | `FacturaResponse` (201) | Estado inicial: PENDIENTE |
| GET | `/facturas/` | `?estado, cliente_nombre, limite, offset` | `list[FacturaResponse]` | cliente_nombre: búsqueda parcial case-insensitive |
| GET | `/facturas/{id}` | — | `FacturaResponse` | Verifica ownership |
| PUT | `/facturas/{id}` | `FacturaUpdate` | `FacturaResponse` | 409 si estado=PAGADA |
| PATCH | `/facturas/{id}/estado` | `FacturaEstadoUpdate` | `FacturaResponse` | Si estado=PAGADA, requiere fecha_pago |
| DELETE | `/facturas/{id}` | — | 204 | 409 si estado=PAGADA |

---

### Alertas de Auditoría — `/alertas`

| Método | Ruta | Body / Params | Respuesta | Notas |
|---|---|---|---|---|
| POST | `/alertas/ejecutar-auditoria` | — | `{mensaje, detalle}` | Borra alertas no resueltas y regenera |
| GET | `/alertas/` | `?tipo, solo_pendientes, limite, offset` | `list[AlertaResponse]` | Ordenado por fecha DESC |
| GET | `/alertas/{id}` | — | `AlertaResponse` | Verifica ownership |
| PATCH | `/alertas/{id}/resolver` | `AlertaResolverUpdate` | `AlertaResponse` | Solo marcar como resuelta/pendiente |

---

### Proyecciones — `/proyecciones`

| Método | Ruta | Body / Params | Respuesta | Notas |
|---|---|---|---|---|
| POST | `/proyecciones/generar` | `ProyeccionGenerarRequest` | `list[ProyeccionResponse]` (201) | Borra proyecciones anteriores; usa Prophet si ≥10 ingresos, media móvil si no |
| GET | `/proyecciones/` | `?limite, offset` | `list[ProyeccionResponse]` | Ordenado por fecha_proyeccion ASC |
| GET | `/proyecciones/{id}` | — | `ProyeccionResponse` | Verifica ownership |

---

### Resumen Financiero — `/resumen`

| Método | Ruta | Params | Respuesta | Notas |
|---|---|---|---|---|
| GET | `/resumen/financiero` | `?mes, anio` | `{resumen: str, generado_con_ia: bool, periodo: str}` | Default: mes/año actual; fallback sin IA si falta GROQ_API_KEY |

---

### Recomendaciones — `/recomendaciones`

| Método | Ruta | Respuesta | Notas |
|---|---|---|---|
| GET | `/recomendaciones/` | `{recomendaciones: list[str], generado_con_ia: bool}` | Analiza alertas, facturas, tendencias, proyecciones; genera 3-5 acciones |

---

### Importación CSV — `/importar`

| Método | Ruta | Body | Respuesta | Notas |
|---|---|---|---|---|
| POST | `/importar/preview` | `UploadFile` (CSV o XLSX) | `{total_filas, preview, mapeo_detectado, resumen}` | Detección heurística local de columnas; marca posibles duplicados; preview de 20 filas |
| POST | `/importar/confirmar` | `{movimientos, mapeo}` | `{importados, ingresos_creados, gastos_creados, omitidos_por_duplicado}` | Importación bulk transaccional e idempotente |

---

### Monotributo — `/monotributo`

| Método | Ruta | Body | Respuesta | Notas |
|---|---|---|---|---|
| GET | `/monotributo/estado` | — | Objeto de estado o `{sin_categoria: true}` | Incluye porcentaje, proyección, alerta verde/amarillo/rojo |
| GET | `/monotributo/pago` | — | `{pagado, mes, anio, monto_esperado, gasto_encontrado}` | Busca Gasto con categoria="Monotributo" del mes actual |
| PATCH | `/monotributo/categoria` | `UsuarioUpdateMonotributo` | `UsuarioResponse` | Valida que la categoría exista y esté activa |

---

### Clasificador ML — `/ml`

| Método | Ruta | Body | Respuesta | Notas |
|---|---|---|---|---|
| GET | `/ml/estado` | — | Estado del modelo (algoritmo, precisión, n_ejemplos, propio/base) | — |
| POST | `/ml/reentrenar` | — | Resultado del reentrenamiento | Modelo personalizado si hay ≥20 gastos propios; si no, usa el base |
| POST | `/ml/corregir` | `{descripcion, categoria_correcta}` | `{mensaje, nuevo_estado, ...}` | Registra la corrección y reentrena; 422 si la categoría es inválida |

---

### Reportes — `/reportes`

| Método | Ruta | Params | Respuesta | Notas |
|---|---|---|---|---|
| GET | `/reportes/pdf` | `?mes, anio` | `application/pdf` (descarga) | Reporte mensual consolidado; default: mes/año actual |

---

### Raíz

| Método | Ruta | Respuesta |
|---|---|---|
| GET | `/` | `{"mensaje": "API funcionando correctamente ✅"}` |
| GET | `/health` | `{"status": "ok", "servicio": "TFG Freelancers API"}` |

---

## 5. Configuración de Base de Datos

### Conexión (`app/database.py`)

```python
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

- **Pool:** 5 conexiones activas + 10 overflow
- **Inyección de sesión:** Patrón `Depends(get_db)` con `yield` + cierre garantizado en `finally`

### Variables de entorno (`.env`)

```
POSTGRES_USER=marcos
POSTGRES_PASSWORD=marcos123
POSTGRES_DB=tfg_freelancers
DATABASE_URL=postgresql://marcos:marcos123@db:5432/tfg_freelancers

SECRET_KEY=supersecretkey123cambiarenproducccion
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080   # 7 días

GROQ_API_KEY=<clave expuesta — ver notas de seguridad>
GROQ_MODEL=llama-3.3-70b-versatile
```

### Alembic (`alembic.ini` + `alembic/env.py`)

- Lee `DATABASE_URL` del `.env` mediante `load_dotenv()` en `env.py`
- Usa `NullPool` para el modo online (evita conflictos con pool en migraciones)
- Importa `Base` y todos los modelos para `target_metadata`
- Soporta modo online y offline

### Migraciones aplicadas

| Revisión | Archivo | Contenido |
|---|---|---|
| `0001` | `0001_initial_schema.py` | Crea enums PostgreSQL (EstadoFactura, TipoAlerta) + tablas: usuarios, ingresos, gastos, facturas, proyecciones, alertas_auditoria, cache_clasificacion |
| `0002` | `0002_tabla_categoria_monotributo.py` | Crea tabla categorias_monotributo + índice único en columna `letra` |
| `0003` | `0003_tabla_modelo_clasificador.py` | Crea tabla modelos_clasificador (clasificador NLP serializado) |

Las tres migraciones son **idempotentes** (verifican existencia antes de crear).

---

## 6. Decisiones de Arquitectura

### Seguridad y autenticación
- **usuario_id siempre del JWT**: En ningún endpoint se acepta `usuario_id` del request body — se extrae exclusivamente del token. Previene acceso cruzado entre usuarios.
- **Anti-enumeración en login**: El endpoint retorna el mismo mensaje de error tanto si el email no existe como si la contraseña es incorrecta.
- **CORS restringido**: Solo orígenes `localhost:3000`, `localhost:3001`, `127.0.0.1:3000`, `127.0.0.1:3001`.

### Auditoría (Módulo M3)
- Las alertas no resueltas se **borran antes de regenerar** para evitar duplicados.
- El módulo se ejecuta on-demand vía `POST /alertas/ejecutar-auditoria`.
- Los gastos identificados como duplicados se marcan con `es_duplicado=True` en la tabla `gastos`.
- **Parámetros ajustables**: ventana de duplicados (3 días), umbral de anomalía (2σ z-score), mínimo de datos (5 gastos por categoría).

### Proyecciones Prophet
- **Patrón replace**: cada generación borra las proyecciones anteriores del usuario.
- **Fallback automático**: si el usuario tiene <10 ingresos históricos, usa media móvil en lugar de Prophet.
- Proyecciones con **intervalos de confianza** (lower/upper) almacenados en BD.

### Inmutabilidad de facturas
- No se permite editar ni eliminar facturas con `estado=PAGADA` (HTTP 409).
- Solo se permite cambiar el estado vía `PATCH /facturas/{id}/estado` (datos históricos inmutables).

### Clasificación con ML local (soberanía de datos)
- La clasificación de gastos corre **100% local**: la descripción nunca se transmite a servicios externos.
- Modelo base entrenado sobre un dataset de 600 ejemplos etiquetados; selección automática Naive Bayes / SVM según volumen, sobre vectorización TF-IDF.
- Reentrenamiento automático: al acumular 20+ gastos propios se entrena un modelo personalizado que combina el dataset base con los ejemplos del usuario; las correcciones manuales también disparan reentrenamiento.
- Si la confianza de la predicción es inferior a 0.30, se sugiere "Otros" y se marca el gasto para revisión manual.
- Groq se reserva exclusivamente para el resumen financiero y las recomendaciones, sobre datos numéricos agregados, con fallback local determinístico.
- Categorías: Software, Hardware, Infraestructura, Marketing, Servicios, Capacitación, Suscripciones, Transporte, Alimentación, Impuestos, Monotributo, Otros.

### Monotributo
- El estado se calcula dinámicamente combinando ingresos reales + proyecciones Prophet.
- El pago mensual se verifica buscando un `Gasto` con `categoria="Monotributo"` en el mes actual.
- Semáforo: **verde** (<70% del límite), **amarillo** (70–90%), **rojo** (>90%).

### Contenedores
- La migración Alembic se ejecuta automáticamente al arrancar el contenedor (`CMD alembic upgrade head && uvicorn ...`).
- El frontend usa volumen montado (`./frontend/src:/app/src`) para hot-reload en desarrollo.

---

## 7. Funcionalidades Implementadas vs Pendientes

### Implementado ✅

#### Core
- [x] Registro y login de usuarios con JWT
- [x] CRUD completo de Ingresos
- [x] CRUD completo de Gastos (con flag `es_duplicado`)
- [x] CRUD completo de Facturas con máquina de estados (PENDIENTE → PAGADA/VENCIDA)
- [x] Filtros en todos los listados (categoría, estado, fechas, paginación)

#### Módulo M3 — Auditoría Inteligente
- [x] Detección de gastos duplicados (misma descripción+monto+categoría en ventana de 3 días)
- [x] Detección de anomalías estadísticas (z-score > 2σ por categoría)
- [x] Detección de facturas vencidas sin cobrar
- [x] Detección de pago Monotributo faltante en el mes
- [x] Alertas persistidas en BD con resolución manual por el usuario

#### Clasificador NLP local (Naive Bayes / SVM)
- [x] Clasificación automática de gastos 100% local, sin servicios externos
- [x] Modelo base entrenado sobre 600 ejemplos etiquetados
- [x] Reentrenamiento automático con las correcciones del usuario
- [x] Marca para revisión manual cuando la confianza es baja

#### Módulo IA externa — Groq / LLaMA 3.3
- [x] Resumen financiero mensual en lenguaje natural (con fallback local)
- [x] Recomendaciones personalizadas sobre datos agregados (con fallback local)

#### Proyecciones Prophet
- [x] Generación de proyecciones mensuales con intervalos de confianza
- [x] Fallback a media móvil cuando hay pocos datos históricos

#### Importación de movimientos (CSV / Excel)
- [x] Detección heurística local de columnas (sin servicios externos)
- [x] Soporte multiformato: CSV y XLSX
- [x] Preview con clasificación previa y detección de duplicados
- [x] Confirmación e importación bulk transaccional e idempotente

#### Monotributo
- [x] Tabla de categorías en BD con seed (A–K, servicios)
- [x] Cálculo dinámico de estado y riesgo de recategorización
- [x] Verificación de pago mensual
- [x] Actualización de categoría del usuario

#### Reportes
- [x] Reporte mensual consolidado en PDF descargable (ReportLab)

#### Infraestructura
- [x] Docker Compose con 3 servicios (db, api, frontend)
- [x] Migraciones Alembic con 3 revisiones aplicadas
- [x] Suite de tests con 11 módulos (SQLite in-memory)

### Pendiente / Mejoras identificadas ⚠️

#### Seguridad
- [x] **SECRET_KEY** — regenerada a clave aleatoria de 64 caracteres
- [x] **`.env`** — fuera del control de versiones (`.gitignore`) + `.env.example` documentado
- [ ] **SECRET_KEY antigua en el historial** — mitigada por la rotación (la clave vieja ya no es válida); reescribir el historial es opcional
- [ ] **CORS de producción** — configurar orígenes reales en deploy

#### Funcionalidad
- [ ] Filtros por rango de fechas en ingresos/gastos (solo hay por categoría)
- [ ] Endpoint de estadísticas/totales (ingresos vs gastos por período)
- [ ] Webhook o notificaciones de alertas (email/push)
- [ ] Soporte multi-actividad Monotributo (solo "servicios" implementado)
- [ ] Gestión de clientes (entidad propia en lugar de solo `cliente_nombre` en facturas)
- [ ] Paginación total_count en headers para el frontend

#### Calidad de código
- [ ] Tabla `cache_clasificacion` en desuso desde la migración al clasificador local — pendiente de eliminar
- [ ] Alerta de Monotributo impago reutiliza el tipo `FACTURA_IMPAGA` — falta un tipo de enum propio
- [ ] Cobertura de tests del frontend (no existe)
- [ ] Tests de integración con PostgreSQL real (conftest usa SQLite)
- [ ] Documentación OpenAPI enriquecida (descriptions, examples en schemas)

#### Infraestructura
- [ ] Health check de BD en docker-compose (`healthcheck` para `db` antes de `api`)
- [ ] Variables de entorno separadas para desarrollo vs producción
- [ ] Logging estructurado (actualmente solo uvicorn default)
- [ ] Rate limiting en endpoints de IA

---

## 8. Dependencias del Proyecto

### `requirements.txt` (completo con versiones exactas)

```
fastapi==0.110.0
uvicorn==0.29.0
sqlalchemy==2.0.29
psycopg2-binary==2.9.9
python-jose==3.3.0
passlib==1.7.4
bcrypt==4.1.2
python-dotenv==1.0.1
pydantic==2.6.4
email-validator==2.1.1
prophet==1.1.5
cmdstanpy==1.2.4
pandas==2.2.1
pytest==8.1.1
httpx==0.27.0
pytest-cov==5.0.0
python-multipart==0.0.9
groq==0.13.0
alembic==1.13.1
scikit-learn==1.4.2
joblib==1.4.0
reportlab==4.1.0
openpyxl==3.1.2
```

### Dependencias por grupo funcional

| Grupo | Paquetes |
|---|---|
| Web framework | fastapi, uvicorn, python-multipart |
| Base de datos | sqlalchemy, psycopg2-binary, alembic |
| Validación | pydantic, email-validator |
| Autenticación | python-jose, passlib, bcrypt |
| IA / ML | scikit-learn, joblib, prophet, cmdstanpy, pandas, groq |
| Reportes e importación | reportlab, openpyxl |
| Utilidades | python-dotenv |
| Testing | pytest, pytest-cov, httpx |

---

*Documento actualizado el 2026-05-22. Refleja el clasificador NLP local, los módulos de ML y reportes, la rotación de credenciales y la suite de tests ampliada.*
