"""
Paquete de modelos (tablas de la base de datos).

Reexporta todos los modelos de SQLAlchemy en un solo lugar para que el resto de
la app los importe desde `app.models` y para que `Base.metadata.create_all` los
registre. Cada modelo está definido en su propio archivo dentro de este paquete.
"""

from app.database import Base
from app.models.usuario import Usuario
from app.models.ingreso import Ingreso
from app.models.gasto import Gasto
from app.models.factura import Factura
from app.models.proyeccion import Proyeccion
from app.models.alerta_auditoria import AlertaAuditoria
from app.models.cache_clasificacion import CacheClasificacion
from app.models.categoria_monotributo import CategoriaMonotributo
from app.models.modelo_clasificador import ModeloClasificador