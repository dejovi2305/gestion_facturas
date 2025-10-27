from sqlalchemy import Column, Integer, Boolean
from . import Base


class Cuenta(Base):
    """Modelo para almacenar cuentas de servicios públicos."""
    
    __tablename__ = 'cuentas'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_cuenta = Column(Integer, unique=True, nullable=False, index=True)
    activo = Column(Boolean, default=True, nullable=False)
    
    def __repr__(self):
        return f"<Cuenta(id={self.id}, numero_cuenta={self.numero_cuenta}, activo={self.activo})>"
