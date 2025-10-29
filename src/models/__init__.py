from sqlalchemy.orm import declarative_base

# Declarative base único para todos los modelos
Base = declarative_base()

# Importar modelos para registrar sus tablas en Base.metadata
# Nota: Los imports al final evitan ciclos durante la importación
from .usuario import Usuario  # noqa: F401
from .cuenta import Cuenta  # noqa: F401
from .cliente import Cliente  # noqa: F401