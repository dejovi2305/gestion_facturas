from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from models import Base
from models.usuario import Usuario
from models.cuenta import Cuenta

# Crear el engine de SQLAlchemy
DATABASE_URL = "sqlite:///app.db"
engine = create_engine(DATABASE_URL)

# Crear la clase SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def initialize_database():
    """Inicializa la base de datos y crea usuario admin por defecto."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin_user = db.query(Usuario).filter(Usuario.nombre_usuario == "admin").first()
        if not admin_user:
            admin_user = Usuario(
                nombre_usuario="admin",
                correo="admin@sistema.com",
                contrasenna="admin123",
                fecha_registro=datetime.now(),
                activo=True
            )
            db.add(admin_user)
            db.commit()
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()


def guardar_cuenta_si_no_existe(numero_cuenta: int) -> tuple[bool, str]:
    """Guarda una cuenta en la base de datos si no existe.
    
    Args:
        numero_cuenta: Número de cuenta como entero (requerido).
    
    Returns:
        tuple[bool, str]: (True si se creó nueva cuenta, mensaje descriptivo)
    """
    db = SessionLocal()
    try:
        # Verificar si la cuenta ya existe
        cuenta_existente = db.query(Cuenta).filter(
            Cuenta.numero_cuenta == numero_cuenta
        ).first()
        
        if cuenta_existente:
            return (False, f"La cuenta {numero_cuenta} ya existe en la base de datos.")
        
        # Crear nueva cuenta
        nueva_cuenta = Cuenta(
            numero_cuenta=numero_cuenta,
            activo=True
        )
        
        db.add(nueva_cuenta)
        db.commit()
        db.refresh(nueva_cuenta)
        
        return (True, f"Cuenta {numero_cuenta} guardada exitosamente.")
        
    except Exception as e:
        db.rollback()
        return (False, f"Error al guardar la cuenta: {str(e)}")
    finally:
        db.close()


