from sqlalchemy import Column, Integer, Boolean, Text
from sqlalchemy.orm import relationship
from . import Base


class Cuenta(Base):
    """Modelo para almacenar cuentas de servicios públicos."""
    
    __tablename__ = 'Cuenta'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    numero_cuenta = Column(Integer, unique=True, nullable=False, index=True)
    activo = Column(Boolean, default=True, nullable=False)
    motivo_cambio = Column(Text, nullable=True)

    # Relación 1:1 con Cliente a través de numero_cuenta
    cliente = relationship(
        "Cliente",
        uselist=False,
        primaryjoin="Cuenta.numero_cuenta == Cliente.cuenta",
        back_populates="cuenta_rel",
    )
    
    def __repr__(self):
        return (
            f"<Cuenta(id={self.id}, numero_cuenta={self.numero_cuenta}, "
            f"activo={self.activo}, motivo_cambio={self.motivo_cambio})>"
        )
