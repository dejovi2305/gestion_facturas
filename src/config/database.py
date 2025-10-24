
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from models.usuario import Usuario, Base

# Crear el engine de SQLAlchemy
DATABASE_URL = "sqlite:///app.db"
engine = create_engine(DATABASE_URL)

# Crear la clase SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def initialize_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        admin_user = db.query(Usuario).filter(Usuario.nombre_usuario == "admin").first()
        if not admin_user:
            admin_user = Usuario(nombre_usuario="admin", correo="admin@sistema.com", contrasenna="admin123", fecha_registro=datetime.now(), activo=True)
            db.add(admin_user)
            db.commit()
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()

