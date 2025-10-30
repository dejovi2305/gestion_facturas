from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, joinedload
from datetime import datetime
from models import Base
from models.usuario import Usuario
from models.cuenta import Cuenta
from models.cliente import Cliente
from models.consumo import Consumo
from models.orden_pago import OrdenPago
from models.alerta import Alerta
from config.security import encriptar_contrasena, codificar_para_almacenamiento

# Crear el engine de SQLAlchemy
DATABASE_URL = "sqlite:///app.db"
engine = create_engine(DATABASE_URL)

# Crear la clase SessionLocal
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def initialize_database():
    """Inicializa la base de datos, crea usuario admin y orden de pago semilla."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Crear usuario admin si no existe
        admin_user = db.query(Usuario).filter(Usuario.nombre_usuario == "admin").first()
        if not admin_user:
            # Encriptar contraseña del admin
            hash_pwd, salt = encriptar_contrasena("admin123")
            contrasena_encriptada = codificar_para_almacenamiento(hash_pwd, salt)
            
            admin_user = Usuario(
                nombre_usuario="admin",
                correo="admin@sistema.com",
                contrasenna=contrasena_encriptada,
                fecha_registro=datetime.now(),
                activo=True
            )
            db.add(admin_user)
        
        # Crear orden de pago semilla (orden 0) si no existe
        orden_semilla = db.query(OrdenPago).filter(OrdenPago.id == 1).first()
        if not orden_semilla:
            orden_semilla = OrdenPago(
                id=1,
                numero_orden=0,
                fecha=datetime.now().date(),
                valor=0
            )
            db.add(orden_semilla)
        
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


# ===== Cuentas: CRUD helpers =====
def listar_cuentas(activo: bool | None = True) -> list[Cuenta]:
    """Lista cuentas por estado.

    activo=True -> solo activas; False -> solo inactivas; None -> todas.
    """
    db = SessionLocal()
    try:
        q = db.query(Cuenta)
        if activo is True:
            q = q.filter(Cuenta.activo.is_(True))
        elif activo is False:
            q = q.filter(Cuenta.activo.is_(False))
        return q.order_by(Cuenta.numero_cuenta.asc()).all()
    finally:
        db.close()


def crear_cuenta(numero_cuenta: int, activo: bool = True) -> tuple[bool, str, int | None]:
    """Crea una cuenta nueva, validando unicidad de numero_cuenta."""
    db = SessionLocal()
    try:
        existente = db.query(Cuenta).filter(Cuenta.numero_cuenta == numero_cuenta).first()
        if existente:
            return False, f"Ya existe la cuenta {numero_cuenta}.", existente.id
        c = Cuenta(numero_cuenta=numero_cuenta, activo=bool(activo))
        db.add(c)
        db.commit()
        db.refresh(c)
        return True, f"Cuenta {numero_cuenta} creada.", c.id
    except Exception as e:
        db.rollback()
        return False, f"Error al crear cuenta: {e}", None
    finally:
        db.close()


def actualizar_cuenta(cuenta_id: int, numero_cuenta: int | None = None, activo: bool | None = None) -> tuple[bool, str]:
    """Actualiza numero_cuenta y/o activo de una cuenta existente."""
    db = SessionLocal()
    try:
        c = db.query(Cuenta).filter(Cuenta.id == cuenta_id).first()
        if not c:
            return False, "Cuenta no encontrada."
        if numero_cuenta is not None and numero_cuenta != c.numero_cuenta:
            # Validar unicidad
            dup = db.query(Cuenta).filter(Cuenta.numero_cuenta == numero_cuenta).first()
            if dup:
                return False, f"Ya existe la cuenta {numero_cuenta}."
            # Si hay Cliente o Consumo, actualizar FKs si aplica (usan numero_cuenta)
            # Cliente.cuenta y Consumo.cuenta referencian el número, por tanto cambiar numero_cuenta
            # puede requerir lógica adicional; por simplicidad lo permitimos si no hay referencias.
            tiene_cliente = db.query(Cliente).filter(Cliente.cuenta == c.numero_cuenta).first() is not None
            tiene_consumo = db.query(Consumo).filter(Consumo.cuenta == c.numero_cuenta).first() is not None
            if tiene_cliente or tiene_consumo:
                return False, "No se puede cambiar el número de cuenta porque tiene referencias (Cliente/Consumo)."
            c.numero_cuenta = numero_cuenta
        if activo is not None:
            c.activo = bool(activo)
        db.commit()
        return True, "Cuenta actualizada."
    except Exception as e:
        db.rollback()
        return False, f"Error al actualizar cuenta: {e}"
    finally:
        db.close()


def eliminar_cuenta(cuenta_id: int) -> tuple[bool, str]:
    """Elimina una cuenta si no tiene referencias (Cliente/Consumo)."""
    db = SessionLocal()
    try:
        c = db.query(Cuenta).filter(Cuenta.id == cuenta_id).first()
        if not c:
            return False, "Cuenta no encontrada."
        # Bloquear eliminación si hay referencias
        tiene_cliente = db.query(Cliente).filter(Cliente.cuenta == c.numero_cuenta).first() is not None
        tiene_consumo = db.query(Consumo).filter(Consumo.cuenta == c.numero_cuenta).first() is not None
        if tiene_cliente or tiene_consumo:
            return False, "No se puede eliminar la cuenta: existen registros relacionados (Cliente/Consumo)."
        db.delete(c)
        db.commit()
        return True, "Cuenta eliminada."
    except Exception as e:
        db.rollback()
        return False, f"Error al eliminar cuenta: {e}"
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


# ===== Clientes: CRUD helpers =====
def listar_clientes(activo: bool | None = True) -> list[Cliente]:
    """Lista clientes por estado.

    activo=True -> solo activos; False -> solo inactivos; None -> todos.
    """
    db = SessionLocal()
    try:
        q = db.query(Cliente)
        if activo is True:
            q = q.filter(Cliente.activo.is_(True))
        elif activo is False:
            q = q.filter(Cliente.activo.is_(False))
        return q.order_by(Cliente.cuenta.asc()).all()
    finally:
        db.close()


def crear_cliente(
    numero_cuenta: int,
    nombre: str | None = None,
    direccion: str | None = None,
    estrato: str | None = None,
    numero_medidor: str | None = None,
    activo: bool = True
) -> tuple[bool, str, int | None]:
    """Crea un cliente nuevo, validando que exista la cuenta y unicidad."""
    db = SessionLocal()
    try:
        # Verificar que la cuenta exista
        cuenta = db.query(Cuenta).filter(Cuenta.numero_cuenta == numero_cuenta).first()
        if not cuenta:
            return False, f"No existe la cuenta {numero_cuenta}. Créela primero.", None
        
        # Validar unicidad (un cliente por cuenta)
        existente = db.query(Cliente).filter(Cliente.cuenta == numero_cuenta).first()
        if existente:
            return False, f"Ya existe un cliente para la cuenta {numero_cuenta}.", existente.id
        
        c = Cliente(
            cuenta=numero_cuenta,
            nombre=nombre,
            direccion=direccion,
            estrato=estrato,
            numero_medidor=numero_medidor,
            activo=bool(activo)
        )
        db.add(c)
        db.commit()
        db.refresh(c)
        return True, f"Cliente creado para cuenta {numero_cuenta}.", c.id
    except Exception as e:
        db.rollback()
        return False, f"Error al crear cliente: {e}", None
    finally:
        db.close()


def actualizar_cliente(
    cliente_id: int,
    numero_cuenta: int | None = None,
    nombre: str | None = None,
    direccion: str | None = None,
    estrato: str | None = None,
    numero_medidor: str | None = None,
    activo: bool | None = None
) -> tuple[bool, str]:
    """Actualiza un cliente existente."""
    db = SessionLocal()
    try:
        c = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if not c:
            return False, "Cliente no encontrado."
        
        if numero_cuenta is not None and numero_cuenta != c.cuenta:
            # Validar que la nueva cuenta exista
            cuenta = db.query(Cuenta).filter(Cuenta.numero_cuenta == numero_cuenta).first()
            if not cuenta:
                return False, f"No existe la cuenta {numero_cuenta}."
            # Validar unicidad
            dup = db.query(Cliente).filter(Cliente.cuenta == numero_cuenta).first()
            if dup:
                return False, f"Ya existe un cliente para la cuenta {numero_cuenta}."
            c.cuenta = numero_cuenta
        
        if nombre is not None:
            c.nombre = nombre
        if direccion is not None:
            c.direccion = direccion
        if estrato is not None:
            c.estrato = estrato
        if numero_medidor is not None:
            c.numero_medidor = numero_medidor
        if activo is not None:
            c.activo = bool(activo)
        
        db.commit()
        return True, "Cliente actualizado."
    except Exception as e:
        db.rollback()
        return False, f"Error al actualizar cliente: {e}"
    finally:
        db.close()


def eliminar_cliente(cliente_id: int) -> tuple[bool, str]:
    """Elimina un cliente si no tiene consumos referenciados."""
    db = SessionLocal()
    try:
        c = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if not c:
            return False, "Cliente no encontrado."
        
        # Bloquear si hay consumos
        tiene_consumo = db.query(Consumo).filter(Consumo.cuenta == c.cuenta).first() is not None
        if tiene_consumo:
            return False, "No se puede eliminar el cliente: existen consumos relacionados."
        
        db.delete(c)
        db.commit()
        return True, "Cliente eliminado."
    except Exception as e:
        db.rollback()
        return False, f"Error al eliminar cliente: {e}"
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
    orden_pago_id: int | None = None,
) -> tuple[bool, str, int | None]:
    """Guarda un registro de Consumo.

    - Para campos requeridos no extraídos asigna por defecto:
      consumo_kwh=0, valor_kwh=0.0, valor_kwh_subsidiado=0.0,
      fecha_maxima_pago=hoy, valor_total=0.0, valor_total_pagar=0.0,
      intereses_mora=0.0, orden_pago_id=1 (orden semilla)

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

        # Si no se proporciona orden_pago_id, usar la orden semilla (id=1)
        if orden_pago_id is None:
            orden_pago_id = 1

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
            orden_pago_id=orden_pago_id,
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


# ===== Usuarios: CRUD helpers con seguridad =====
def listar_usuarios(activo: bool | None = True) -> list[Usuario]:
    """Lista usuarios por estado.

    activo=True -> solo activos; False -> solo inactivos; None -> todos.
    """
    db = SessionLocal()
    try:
        q = db.query(Usuario)
        if activo is True:
            q = q.filter(Usuario.activo.is_(True))
        elif activo is False:
            q = q.filter(Usuario.activo.is_(False))
        return q.order_by(Usuario.nombre_usuario.asc()).all()
    finally:
        db.close()


def crear_usuario(
    nombre_usuario: str,
    correo: str,
    contrasena_plana: str,
    activo: bool = True
) -> tuple[bool, str, int | None]:
    """Crea un usuario nuevo con contraseña encriptada."""
    db = SessionLocal()
    try:
        # Validar unicidad del nombre de usuario
        existente = db.query(Usuario).filter(Usuario.nombre_usuario == nombre_usuario).first()
        if existente:
            return False, f"Ya existe el usuario '{nombre_usuario}'.", existente.id
        
        # Validaciones básicas
        if not nombre_usuario or not nombre_usuario.strip():
            return False, "El nombre de usuario no puede estar vacío.", None
        if not contrasena_plana or len(contrasena_plana) < 4:
            return False, "La contraseña debe tener al menos 4 caracteres.", None
        if not correo or '@' not in correo:
            return False, "Ingrese un correo electrónico válido.", None
        
        # Encriptar contraseña
        hash_pwd, salt = encriptar_contrasena(contrasena_plana)
        contrasena_encriptada = codificar_para_almacenamiento(hash_pwd, salt)
        
        u = Usuario(
            nombre_usuario=nombre_usuario.strip(),
            correo=correo.strip(),
            contrasenna=contrasena_encriptada,
            fecha_registro=datetime.now(),
            activo=bool(activo)
        )
        db.add(u)
        db.commit()
        db.refresh(u)
        return True, f"Usuario '{nombre_usuario}' creado exitosamente.", u.id
    except Exception as e:
        db.rollback()
        return False, f"Error al crear usuario: {e}", None
    finally:
        db.close()


def actualizar_usuario(
    usuario_id: int,
    nombre_usuario: str | None = None,
    correo: str | None = None,
    contrasena_plana: str | None = None,
    activo: bool | None = None
) -> tuple[bool, str]:
    """Actualiza un usuario existente. Si se proporciona contraseña, se encripta."""
    db = SessionLocal()
    try:
        u = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not u:
            return False, "Usuario no encontrado."
        
        # Actualizar nombre de usuario si se proporciona
        if nombre_usuario is not None and nombre_usuario.strip():
            nombre_usuario = nombre_usuario.strip()
            if nombre_usuario != u.nombre_usuario:
                # Validar unicidad
                dup = db.query(Usuario).filter(Usuario.nombre_usuario == nombre_usuario).first()
                if dup:
                    return False, f"Ya existe el usuario '{nombre_usuario}'."
                u.nombre_usuario = nombre_usuario
        
        # Actualizar correo
        if correo is not None and correo.strip():
            if '@' not in correo:
                return False, "Ingrese un correo electrónico válido."
            u.correo = correo.strip()
        
        # Actualizar contraseña si se proporciona
        if contrasena_plana is not None and contrasena_plana.strip():
            if len(contrasena_plana) < 4:
                return False, "La contraseña debe tener al menos 4 caracteres."
            hash_pwd, salt = encriptar_contrasena(contrasena_plana)
            contrasena_encriptada = codificar_para_almacenamiento(hash_pwd, salt)
            u.contrasenna = contrasena_encriptada
        
        # Actualizar estado
        if activo is not None:
            u.activo = bool(activo)
        
        db.commit()
        return True, "Usuario actualizado exitosamente."
    except Exception as e:
        db.rollback()
        return False, f"Error al actualizar usuario: {e}"
    finally:
        db.close()


def eliminar_usuario(usuario_id: int) -> tuple[bool, str]:
    """Elimina un usuario (solo si no es el admin principal)."""
    db = SessionLocal()
    try:
        u = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if not u:
            return False, "Usuario no encontrado."
        
        # Proteger usuario admin
        if u.nombre_usuario.lower() == "admin":
            return False, "No se puede eliminar el usuario administrador principal."
        
        db.delete(u)
        db.commit()
        return True, f"Usuario '{u.nombre_usuario}' eliminado exitosamente."
    except Exception as e:
        db.rollback()
        return False, f"Error al eliminar usuario: {e}"
    finally:
        db.close()


def autenticar_usuario(nombre_usuario: str, contrasena_plana: str) -> tuple[bool, str, Usuario | None]:
    """
    Autentica un usuario verificando su contraseña encriptada.
    
    Returns:
        Tupla (autenticado, mensaje, usuario_obj)
    """
    from config.security import verificar_contrasena, decodificar_de_almacenamiento, es_contrasena_encriptada
    
    db = SessionLocal()
    try:
        u = db.query(Usuario).filter(Usuario.nombre_usuario == nombre_usuario).first()
        
        if not u:
            return False, "Usuario no encontrado.", None
        
        if not u.activo:
            return False, "Usuario inactivo. Contacte al administrador.", None
        
        # Verificar si la contraseña almacenada está encriptada
        if es_contrasena_encriptada(u.contrasenna):
            # Contraseña encriptada: verificar con hash
            try:
                salt, hash_almacenado = decodificar_de_almacenamiento(u.contrasenna)
                if verificar_contrasena(contrasena_plana, hash_almacenado, salt):
                    return True, "Autenticación exitosa.", u
                else:
                    return False, "Contraseña incorrecta.", None
            except Exception:
                return False, "Error al verificar contraseña.", None
        else:
            # Contraseña en texto plano (BD antigua): comparar directamente
            # y actualizar a formato encriptado
            if u.contrasenna == contrasena_plana:
                # Migrar contraseña a formato encriptado
                hash_pwd, salt = encriptar_contrasena(contrasena_plana)
                u.contrasenna = codificar_para_almacenamiento(hash_pwd, salt)
                db.commit()
                return True, "Autenticación exitosa (contraseña migrada).", u
            else:
                return False, "Contraseña incorrecta.", None
    finally:
        db.close()


# ===== Consumos: CRUD helpers =====
def listar_consumos(cuenta: int | None = None, limite: int | None = None) -> list[Consumo]:
    """Lista consumos, opcionalmente filtrados por cuenta.

    Args:
        cuenta: Número de cuenta para filtrar (None = todos)
        limite: Límite de registros a retornar (None = todos)
    """
    db = SessionLocal()
    try:
        q = db.query(Consumo).options(joinedload(Consumo.orden_pago_rel))
        if cuenta is not None:
            q = q.filter(Consumo.cuenta == cuenta)
        q = q.order_by(Consumo.fecha_maxima_pago.desc())
        if limite:
            q = q.limit(limite)
        return q.all()
    finally:
        db.close()


def obtener_consumo_por_id(consumo_id: int) -> Consumo | None:
    """Obtiene un consumo por su ID."""
    db = SessionLocal()
    try:
        return db.query(Consumo).filter(Consumo.id == consumo_id).first()
    finally:
        db.close()


def actualizar_consumo(
    consumo_id: int,
    consumo_kwh: int | None = None,
    valor_kwh: float | None = None,
    valor_kwh_subsidiado: float | None = None,
    fecha_maxima_pago: str | None = None,
    valor_total: float | None = None,
    valor_total_pagar: float | None = None,
    intereses_mora: float | None = None,
    orden_pago_id: int | None = None
) -> tuple[bool, str]:
    """Actualiza campos de un consumo existente."""
    from datetime import datetime
    
    db = SessionLocal()
    try:
        c = db.query(Consumo).filter(Consumo.id == consumo_id).first()
        if not c:
            return False, "Consumo no encontrado."
        
        if consumo_kwh is not None:
            c.consumo_kwh = int(consumo_kwh)
        if valor_kwh is not None:
            c.valor_kwh = float(valor_kwh)
        if valor_kwh_subsidiado is not None:
            c.valor_kwh_subsidiado = float(valor_kwh_subsidiado)
        if fecha_maxima_pago is not None:
            try:
                c.fecha_maxima_pago = datetime.strptime(fecha_maxima_pago, "%Y-%m-%d").date()
            except Exception:
                return False, "Formato de fecha inválido. Use YYYY-MM-DD."
        if valor_total is not None:
            c.valor_total = float(valor_total)
        if valor_total_pagar is not None:
            c.Valor_total_pagar = float(valor_total_pagar)
        if intereses_mora is not None:
            c.intereses_mora = float(intereses_mora)
        if orden_pago_id is not None:
            c.orden_pago_id = int(orden_pago_id)
        
        db.commit()
        return True, "Consumo actualizado exitosamente."
    except Exception as e:
        db.rollback()
        return False, f"Error al actualizar consumo: {e}"
    finally:
        db.close()


def eliminar_consumo(consumo_id: int) -> tuple[bool, str]:
    """Elimina un consumo por su ID."""
    db = SessionLocal()
    try:
        c = db.query(Consumo).filter(Consumo.id == consumo_id).first()
        if not c:
            return False, "Consumo no encontrado."
        
        db.delete(c)
        db.commit()
        return True, "Consumo eliminado exitosamente."
    except Exception as e:
        db.rollback()
        return False, f"Error al eliminar consumo: {e}"
    finally:
        db.close()


# ===== Órdenes de Pago: CRUD helpers =====

def listar_ordenes_pago(limite: int = None):
    """
    Lista todas las órdenes de pago.
    
    Args:
        limite: Número máximo de registros a retornar (opcional)
    
    Returns:
        Lista de objetos OrdenPago ordenados por fecha descendente
    """
    db = SessionLocal()
    try:
        query = db.query(OrdenPago).order_by(OrdenPago.fecha.desc())
        
        if limite:
            query = query.limit(limite)
        
        return query.all()
    finally:
        db.close()


def obtener_orden_pago_por_id(orden_id: int):
    """Obtiene una orden de pago por su ID."""
    db = SessionLocal()
    try:
        return db.query(OrdenPago).filter(OrdenPago.id == orden_id).first()
    finally:
        db.close()


def crear_orden_pago(
    numero_orden: int,
    fecha,
    valor: float
) -> tuple[bool, str]:
    """
    Crea una nueva orden de pago.
    
    Args:
        numero_orden: Número único de la orden
        fecha: Fecha de la orden (string YYYY-MM-DD o objeto date)
        valor: Valor total de la orden
    
    Returns:
        tuple[bool, str]: (éxito, mensaje)
    """
    db = SessionLocal()
    try:
        # Verificar que el número de orden no exista
        orden_existente = db.query(OrdenPago).filter(OrdenPago.numero_orden == numero_orden).first()
        if orden_existente:
            return False, f"El número de orden {numero_orden} ya existe."
        
        # Convertir fecha string a objeto date si es necesario
        if isinstance(fecha, str):
            from datetime import datetime
            fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
        else:
            fecha_obj = fecha
        
        # Crear nueva orden
        nueva_orden = OrdenPago(
            numero_orden=numero_orden,
            fecha=fecha_obj,
            valor=valor
        )
        
        db.add(nueva_orden)
        db.commit()
        return True, "Orden de pago creada exitosamente."
    except Exception as e:
        db.rollback()
        return False, f"Error al crear orden de pago: {e}"
    finally:
        db.close()


def actualizar_orden_pago(
    orden_id: int,
    numero_orden: int = None,
    fecha = None,
    valor: float = None
) -> tuple[bool, str]:
    """
    Actualiza una orden de pago existente.
    Solo actualiza los campos proporcionados (no None).
    
    Args:
        fecha: Fecha (string YYYY-MM-DD o objeto date)
    
    Returns:
        tuple[bool, str]: (éxito, mensaje)
    """
    db = SessionLocal()
    try:
        orden = db.query(OrdenPago).filter(OrdenPago.id == orden_id).first()
        if not orden:
            return False, "Orden de pago no encontrada."
        
        # Actualizar solo campos proporcionados
        if numero_orden is not None:
            # Verificar que el nuevo número no exista en otra orden
            orden_existente = db.query(OrdenPago).filter(
                OrdenPago.numero_orden == numero_orden,
                OrdenPago.id != orden_id
            ).first()
            if orden_existente:
                return False, f"El número de orden {numero_orden} ya existe en otra orden."
            orden.numero_orden = int(numero_orden)
        
        if fecha is not None:
            # Convertir fecha string a objeto date si es necesario
            if isinstance(fecha, str):
                from datetime import datetime
                fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
            else:
                fecha_obj = fecha
            orden.fecha = fecha_obj
        
        if valor is not None:
            orden.valor = float(valor)
        
        db.commit()
        return True, "Orden de pago actualizada exitosamente."
    except Exception as e:
        db.rollback()
        return False, f"Error al actualizar orden de pago: {e}"
    finally:
        db.close()


def eliminar_orden_pago(orden_id: int) -> tuple[bool, str]:
    """Elimina una orden de pago por su ID."""
    db = SessionLocal()
    try:
        orden = db.query(OrdenPago).filter(OrdenPago.id == orden_id).first()
        if not orden:
            return False, "Orden de pago no encontrada."
        
        db.delete(orden)
        db.commit()
        return True, "Orden de pago eliminada exitosamente."
    except Exception as e:
        db.rollback()
        return False, f"Error al eliminar orden de pago: {e}"
    finally:
        db.close()


# =====================================================================
# CRUD Alertas
# =====================================================================

def listar_alertas(cuenta: int = None):
    """Lista todas las alertas o filtra por cuenta.
    
    Args:
        cuenta: Número de cuenta para filtrar (None = todas)
    """
    db = SessionLocal()
    try:
        q = db.query(Alerta)
        if cuenta is not None:
            q = q.filter(Alerta.cuenta == cuenta)
        q = q.order_by(Alerta.id)
        return q.all()
    finally:
        db.close()


def obtener_alerta_por_id(alerta_id: int) -> Alerta | None:
    """Obtiene una alerta por su ID."""
    db = SessionLocal()
    try:
        return db.query(Alerta).filter(Alerta.id == alerta_id).first()
    finally:
        db.close()


def crear_alerta(cuenta: int, dias_habiles: int) -> tuple[bool, str]:
    """Crea una nueva alerta asociada a una cuenta.
    
    Args:
        cuenta: Número de cuenta
        dias_habiles: Días hábiles para la alerta
    """
    db = SessionLocal()
    try:
        # Verificar que la cuenta existe
        cuenta_obj = db.query(Cuenta).filter(Cuenta.numero_cuenta == cuenta).first()
        if not cuenta_obj:
            return False, f"La cuenta {cuenta} no existe."
        
        # Verificar si ya existe una alerta para esta cuenta
        alerta_existente = db.query(Alerta).filter(Alerta.cuenta == cuenta).first()
        if alerta_existente:
            return False, f"Ya existe una alerta para la cuenta {cuenta}."
        
        nueva_alerta = Alerta(
            cuenta=cuenta,
            dias_habiles=dias_habiles
        )
        db.add(nueva_alerta)
        db.commit()
        return True, "Alerta creada exitosamente."
    except Exception as e:
        db.rollback()
        return False, f"Error al crear alerta: {e}"
    finally:
        db.close()


def actualizar_alerta(
    alerta_id: int,
    cuenta: int = None,
    dias_habiles: int = None
) -> tuple[bool, str]:
    """Actualiza campos de una alerta existente."""
    db = SessionLocal()
    try:
        alerta = db.query(Alerta).filter(Alerta.id == alerta_id).first()
        if not alerta:
            return False, "Alerta no encontrada."
        
        if cuenta is not None:
            # Verificar que la cuenta existe
            cuenta_obj = db.query(Cuenta).filter(Cuenta.numero_cuenta == cuenta).first()
            if not cuenta_obj:
                return False, f"La cuenta {cuenta} no existe."
            
            # Verificar que no exista otra alerta con esa cuenta
            alerta_existente = db.query(Alerta).filter(
                Alerta.cuenta == cuenta,
                Alerta.id != alerta_id
            ).first()
            if alerta_existente:
                return False, f"Ya existe una alerta para la cuenta {cuenta}."
            
            alerta.cuenta = cuenta
        
        if dias_habiles is not None:
            alerta.dias_habiles = dias_habiles
        
        db.commit()
        return True, "Alerta actualizada exitosamente."
    except Exception as e:
        db.rollback()
        return False, f"Error al actualizar alerta: {e}"
    finally:
        db.close()


def eliminar_alerta(alerta_id: int) -> tuple[bool, str]:
    """Elimina una alerta por su ID."""
    db = SessionLocal()
    try:
        alerta = db.query(Alerta).filter(Alerta.id == alerta_id).first()
        if not alerta:
            return False, "Alerta no encontrada."
        
        db.delete(alerta)
        db.commit()
        return True, "Alerta eliminada exitosamente."
    except Exception as e:
        db.rollback()
        return False, f"Error al eliminar alerta: {e}"
    finally:
        db.close()





