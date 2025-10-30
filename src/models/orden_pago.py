from sqlalchemy import Column, Integer, Date, Numeric
from sqlalchemy.orm import relationship
from . import Base


class OrdenPago(Base):
    """Modelo de orden de pago.

    Una orden de pago puede asociarse a múltiples consumos (relación 1:N).
    """

    __tablename__ = "OrdenPago"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    numero_orden = Column(Integer, nullable=False, unique=True, index=True)
    fecha = Column(Date, nullable=False)
    valor = Column(Numeric(18, 2), nullable=False, default=0)

    # Relación con Consumo (una orden -> muchos consumos)
    consumos = relationship(
        "Consumo",
        back_populates="orden_pago_rel",
    )

    def __repr__(self) -> str:
        return (
            f"<OrdenPago(id={self.id}, numero_orden={self.numero_orden}, "
            f"fecha={self.fecha}, valor={self.valor})>"
        )
