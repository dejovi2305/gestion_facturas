from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from . import Base


class Alerta(Base):
    """Modelo de alerta asociada a una cuenta.

    Nota: Se relaciona por número de cuenta (Cuenta.numero_cuenta).
    """

    __tablename__ = "Alerta"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    dias_habiles = Column(Integer, nullable=False, default=0)
    # Relación por número de cuenta (clave de negocio)
    cuenta = Column(Integer, ForeignKey("Cuenta.numero_cuenta"), nullable=False, index=True)

    # Relación de navegación (opcional)
    cuenta_rel = relationship(
        "Cuenta",
        primaryjoin="Alerta.cuenta == Cuenta.numero_cuenta",
        viewonly=True,
    )

    def __repr__(self) -> str:
        return (
            f"<Alerta(id={self.id}, cuenta={self.cuenta}, dias_habiles={self.dias_habiles})>"
        )
