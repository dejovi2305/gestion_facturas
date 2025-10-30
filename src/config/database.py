from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from models import Base
from models.usuario import Usuario
from models.cuenta import Cuenta
from models.cliente import Cliente
from models.consumo import Consumo

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


def existe_cuenta(numero_cuenta: int) -> bool:
    """Devuelve True si existe una Cuenta con ese número de cuenta."""
    db = SessionLocal()
    try:
        return db.query(Cuenta).filter(Cuenta.numero_cuenta == numero_cuenta).first() is not None
    finally:
        db.close()


def existe_cliente_para_cuenta(numero_cuenta: int) -> bool:
    """Devuelve True si existe un Cliente asociado al número de cuenta dado."""
    db = SessionLocal()
    try:
        return db.query(Cliente).filter(Cliente.cuenta == numero_cuenta).first() is not None
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


def guardar_consumo(
    numero_cuenta: int,
    cufe: str | None,
    consumo_kwh: float | int | None = None,
    valor_kwh: float | None = None,
    valor_kwh_subsidiado: float | None = None,
    fecha_maxima_pago: str | None = None,  # formato YYYY-MM-DD
    valor_total: float | None = None,
    valor_total_pagar: float | None = None,
    intereses_mora: float | None = None,
    numero_orden: int | None = None,
) -> tuple[bool, str, int | None]:
    """Guarda un registro de Consumo.

    - Para campos requeridos no extraídos asigna por defecto:
      consumo_kwh=0, valor_kwh=0.0, valor_kwh_subsidiado=0.0,
      fecha_maxima_pago=hoy, valor_total=0.0, valor_total_pagar=0.0,
      intereses_mora=0.0, numero_orden=0

    Returns: (creado, mensaje, id_consumo)
    """
    from datetime import date, datetime

    db = SessionLocal()
    try:
        # Asegurar cuenta
        cuenta = db.query(Cuenta).filter(Cuenta.numero_cuenta == numero_cuenta).first()
        if not cuenta:
            cuenta = Cuenta(numero_cuenta=numero_cuenta, activo=True)
            db.add(cuenta)
            db.commit()
            db.refresh(cuenta)

        # Validar CUFE obligatorio
        if not cufe or not str(cufe).strip():
            return False, "El CUFE/UUID es requerido para registrar el consumo.", None

        cufe = str(cufe).strip()

        # Verificar existencia previa por CUFE
        existente = db.query(Consumo).filter(Consumo.cufe == cufe).first()
        if existente:
            return False, f"Ya existe un consumo con CUFE {cufe} (id={existente.id}).", existente.id

        # Normalizar valores
        def to_int(v, default=0):
            try:
                return int(round(float(v)))
            except Exception:
                return default

        def to_float(v, default=0.0):
            try:
                return float(v)
            except Exception:
                return default

        if fecha_maxima_pago:
            try:
                fmp = datetime.strptime(fecha_maxima_pago.strip(), "%Y-%m-%d").date()
            except Exception:
                fmp = date.today()
        else:
            fmp = date.today()

        consumo = Consumo(
            cuenta=numero_cuenta,
            cufe=cufe,
            consumo_kwh=to_int(consumo_kwh, 0),
            valor_kwh=to_float(valor_kwh, 0.0),
            valor_kwh_subsidiado=to_float(valor_kwh_subsidiado, 0.0),
            fecha_maxima_pago=fmp,
            valor_total=to_float(valor_total, 0.0),
            Valor_total_pagar=to_float(valor_total_pagar, 0.0),
            intereses_mora=to_float(intereses_mora, 0.0),
            numero_orden=to_int(numero_orden, 0),
        )

        db.add(consumo)
        db.commit()
        db.refresh(consumo)
        return True, f"Consumo registrado para cuenta {numero_cuenta} (id={consumo.id}).", consumo.id
    except Exception as e:
        db.rollback()
        return False, f"Error al guardar el consumo: {e}", None
    finally:
        db.close()


