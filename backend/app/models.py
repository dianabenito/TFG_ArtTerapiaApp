from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    """Modelo base de usuario con herencia de tabla única (STI).
    
    Representa un usuario genérico en el sistema. Utiliza herencia de tabla única
    (Single Table Inheritance) para soportar diferentes tipos de usuarios (pacientes
    y terapeutas) en la misma tabla de base de datos.
    
    Attributes:
        id (int): Identificador único del usuario.
        email (str): Correo electrónico único del usuario. Indexado para búsquedas rápidas.
        full_name (str): Nombre completo del usuario.
        hashed_password (str): Contraseña hasheada del usuario. Nunca se almacena en texto plano.
        is_active (bool): Indica si la cuenta del usuario está activa. Por defecto True.
        created_at (datetime): Fecha y hora de creación del usuario. Se asigna automáticamente.
        type (str): Discriminador para herencia. Valores: 'user', 'patient', 'therapist'.
    
    Note:
        Esta clase utiliza el patrón Single Table Inheritance (STI) de SQLAlchemy.
        Las subclases Patient y Therapist heredan de esta clase base.
    """
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # discriminator column for single-table inheritance
    type = Column(String(50), nullable=False, server_default='user')

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'user'
    }

class Patient(User):
    """Subtipo de usuario que representa a un paciente.
    
    Extiende el modelo User para representar pacientes que reciben terapia.
    Los pacientes pueden generar imágenes durante las sesiones de terapia.
    
    Attributes:
        images (List[Image]): Lista de imágenes generadas por el paciente.
            Relación uno-a-muchos con el modelo Image.
    
    Note:
        Hereda todos los atributos de User. El discriminador 'type' se establece
        automáticamente como 'patient'.
    """

    images = relationship("Image", back_populates="owner")  # One user can have many images

    __mapper_args__ = {
        'polymorphic_identity': 'patient'
    }


class Therapist(User):
    """Subtipo de usuario que representa a un terapeuta.
    
    Extiende el modelo User para representar terapeutas que conducen sesiones
    con pacientes. Los terapeutas pueden crear, gestionar y finalizar sesiones.
    
    Note:
        Hereda todos los atributos de User. El discriminador 'type' se establece
        automáticamente como 'therapist'.
    """

    __mapper_args__ = {
        'polymorphic_identity': 'therapist'
    }


class Image(Base):
    """Modelo para imágenes generadas durante las sesiones de terapia.
    
    Almacena información sobre las imágenes creadas por pacientes usando
    Stable Diffusion XL a través de ComfyUI. Cada imagen está asociada
    a un paciente (owner) y opcionalmente a una sesión específica.
    
    Attributes:
        id (int): Identificador único de la imagen.
        fileName (str): Nombre del archivo de imagen almacenado en el sistema.
        seed (int, optional): Semilla utilizada para la generación de la imagen.
            Permite reproducir la misma imagen con los mismos parámetros.
        owner_id (int): ID del paciente propietario de la imagen.
            Clave foránea que referencia users.id.
        session_id (int, optional): ID de la sesión en la que se generó la imagen.
            Clave foránea que referencia sessions.id. Puede ser None.
        owner (Patient): Relación con el paciente propietario de la imagen.
        session (Session): Relación con la sesión en la que se generó la imagen.
    
    Note:
        Las imágenes pueden existir sin estar asociadas a una sesión específica
        (session_id puede ser NULL).
    """
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    fileName = Column(String, nullable=False)
    seed = Column(Integer, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=True)

    owner = relationship("Patient", back_populates="images") # One item belongs to one user
    session = relationship("Session", back_populates="images") # One item belongs to one user


class Session(Base):
    """Modelo para sesiones de terapia entre terapeuta y paciente.
    
    Representa una sesión de arte-terapia con fechas de inicio y fin programadas.
    Las sesiones son creadas por terapeutas para trabajar con pacientes específicos.
    Pueden contener múltiples imágenes generadas durante la sesión.
    
    Attributes:
        id (int): Identificador único de la sesión.
        patient_id (int): ID del paciente que participa en la sesión.
            Clave foránea que referencia users.id.
        therapist_id (int): ID del terapeuta que conduce la sesión.
            Clave foránea que referencia users.id.
        created_at (datetime): Fecha y hora de creación del registro de sesión.
            Se asigna automáticamente al crear la sesión.
        start_date (datetime): Fecha y hora de inicio programada de la sesión.
        end_date (datetime): Fecha y hora de fin programada de la sesión.
        ended_at (datetime, optional): Timestamp real cuando el terapeuta finaliza la sesión.
            Es None mientras la sesión está activa.
        patient (Patient): Relación con el paciente de la sesión.
        therapist (Therapist): Relación con el terapeuta de la sesión.
        images (List[Image]): Lista de imágenes generadas durante esta sesión.
    
    Note:
        Una sesión se considera activa si ended_at es None. El terapeuta puede
        finalizarla antes de end_date estableciendo ended_at.
    """
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    therapist_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Period during which the session is active
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    # Real end timestamp set when the therapist finalizes the session
    ended_at = Column(DateTime(timezone=True), nullable=True)

    patient = relationship("Patient", foreign_keys=[patient_id])
    therapist = relationship("Therapist", foreign_keys=[therapist_id])
    images = relationship("Image", back_populates="session")