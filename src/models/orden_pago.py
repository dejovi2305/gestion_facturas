from sqlalchemy import Column, Integer, Date, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from . import Base


class OrdenPago(Base):
    """Modelo de orden de pago.

    Nota: Se relaciona con Consumo por numero_orden (campo numero_orden en Consumo).
    """

    __tablename__ = "OrdenPago"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    numero_orden = Column(Integer, nullable=False, unique=True, index=True)
    fecha = Column(Date, nullable=False)
    valor = Column(Numeric(18, 2), nullable=False, default=0)

    def __repr__(self) -> str:
        return (
            f"<OrdenPago(id={self.id}, numero_orden={self.numero_orden}, "
            f"fecha={self.fecha}, valor={self.valor})>"
        )
