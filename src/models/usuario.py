from sqlalchemy import Column, Integer, String, Boolean, DateTime
from . import Base

class Usuario(Base):
    __tablename__ = "Usuario"
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    nombre_usuario = Column(String, unique=True, nullable=False)
    correo = Column(String, nullable=False)
    contrasenna = Column(String, nullable=False)
    fecha_registro = Column(DateTime, nullable=False)
    activo = Column(Boolean, nullable=False, default=True)
