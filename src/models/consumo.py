from sqlalchemy import Column, Integer, Numeric, Date, ForeignKey, String
from sqlalchemy.orm import relationship
from . import Base


class Consumo(Base):
    """Registro de consumo por factura.

    Nota: Se relaciona por número de cuenta (Cuenta.numero_cuenta) como en Cliente.
    Cada consumo está asociado a una orden de pago (OrdenPago.id).
    Los campos obligatorios reciben valores por defecto (0 o fecha actual) si no fueron extraídos.
    """

    __tablename__ = "Consumo"

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    # Relación por número de cuenta (clave de negocio)
    cuenta = Column(Integer, ForeignKey("Cuenta.numero_cuenta"), nullable=False, index=True)
    
    # Relación con OrdenPago (muchos consumos -> una orden)
    orden_pago_id = Column(Integer, ForeignKey("OrdenPago.id"), nullable=False, default=1, index=True)

    # Campos de consumo
    cufe = Column(String, nullable=False, unique=True, index=True)
    consumo_kwh = Column(Integer, nullable=False, default=0)
    valor_kwh = Column(Numeric(18, 6), nullable=False, default=0)
    valor_kwh_subsidiado = Column(Numeric(18, 6), nullable=False, default=0)
    fecha_maxima_pago = Column(Date, nullable=False)
    valor_total = Column(Numeric(18, 2), nullable=False, default=0)
    Valor_total_pagar = Column(Numeric(18, 2), nullable=False, default=0)
    intereses_mora = Column(Numeric(18, 2), nullable=False, default=0)

    # Relaciones de navegación
    cuenta_rel = relationship(
        "Cuenta",
        primaryjoin="Consumo.cuenta == Cuenta.numero_cuenta",
        viewonly=True,
    )
    
    orden_pago_rel = relationship(
        "OrdenPago",
        back_populates="consumos",
    )

    def __repr__(self) -> str:
        return (
            f"<Consumo(id={self.id}, cuenta={self.cuenta}, orden_pago_id={self.orden_pago_id}, "
            f"cufe={self.cufe}, consumo_kwh={self.consumo_kwh}, "
            f"valor_kwh={self.valor_kwh}, valor_total={self.valor_total}, total_pagar={self.Valor_total_pagar})>"
        )
