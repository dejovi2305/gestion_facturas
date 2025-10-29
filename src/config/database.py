from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from models import Base
from models.usuario import Usuario
from models.cuenta import Cuenta
from models.cliente import Cliente

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


def guardar_cliente_si_no_existe(
    numero_cuenta: int,
    nombre: str | None = None,
    direccion: str | None = None,
    estrato: str | None = None,
    numero_medidor: str | None = None,
) -> tuple[bool, str]:
    """Crea un Cliente si no existe ya para la cuenta dada.

    Relaciona Cliente.cuenta con Cuenta.numero_cuenta (clave de negocio).
    Si la cuenta no existe, se crea. Si ya hay cliente para ese número, no inserta.

    Returns: (creado, mensaje)
    """
    db = SessionLocal()
    try:
        # Asegurar que exista la cuenta (o crearla)
        cuenta = db.query(Cuenta).filter(Cuenta.numero_cuenta == numero_cuenta).first()
        if not cuenta:
            cuenta = Cuenta(numero_cuenta=numero_cuenta, activo=True)
            db.add(cuenta)
            db.commit()
            db.refresh(cuenta)

        # Verificar si ya existe cliente para esta cuenta (por número de cuenta)
        existente = db.query(Cliente).filter(Cliente.cuenta == numero_cuenta).first()
        if existente:
            return (False, f"El cliente de la cuenta {numero_cuenta} ya existe.")

        # Crear cliente usando el número de cuenta como FK
        cliente = Cliente(
            cuenta=numero_cuenta,
            nombre=nombre,
            direccion=direccion,
            estrato=estrato,
            numero_medidor=numero_medidor,
            activo=True,
        )
        db.add(cliente)
        db.commit()
        db.refresh(cliente)
        return (True, f"Cliente creado para la cuenta {numero_cuenta}.")

    except Exception as e:
        db.rollback()
        return (False, f"Error al guardar el cliente: {str(e)}")
    finally:
        db.close()


