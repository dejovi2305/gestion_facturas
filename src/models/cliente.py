from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from . import Base


class Cliente(Base):
    """Modelo de cliente asociado a una cuenta.

    Relación 1:1 entre Cliente.cuenta (número de cuenta) y Cuenta.numero_cuenta.
    Las búsquedas/validaciones se hacen por el número de cuenta.
    """

    __tablename__ = "Cliente"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # Campo 'cuenta' almacena el número de cuenta y referencia a Cuenta.numero_cuenta
    cuenta = Column(Integer, ForeignKey("Cuenta.numero_cuenta"), nullable=False, unique=True, index=True)
    nombre = Column(String, nullable=True)
    direccion = Column(String, nullable=True)
    estrato = Column(String, nullable=True)
    numero_medidor = Column(String, nullable=True)
    activo = Column(Boolean, default=True, nullable=False)

    # Relación de navegación hacia Cuenta usando numero_cuenta
    cuenta_rel = relationship(
        "Cuenta",
        primaryjoin="Cliente.cuenta == Cuenta.numero_cuenta",
        back_populates="cliente",
    )

    def __repr__(self) -> str:
        return (
            f"<Cliente(id={self.id}, cuenta={self.cuenta}, nombre={self.nombre}, "
            f"direccion={self.direccion}, estrato={self.estrato}, numero_medidor={self.numero_medidor}, "
            f"activo={self.activo})>"
        )
