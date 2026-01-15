"""Configuración de la base de datos SQLAlchemy.

Este módulo configura la conexión a la base de datos SQLite y proporciona
las utilidades necesarias para el ORM.

Attributes:
    SQLALCHEMY_DATABASE_URL (str): URL de conexión a la base de datos SQLite.
    engine (Engine): Motor de base de datos SQLAlchemy.
    SessionLocal (sessionmaker): Factory para crear sesiones de base de datos.
    Base (DeclarativeMeta): Clase base declarativa para modelos ORM.

Note:
    El parámetro check_same_thread=False es necesario para SQLite en entornos
    multi-threading como FastAPI.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///../artTerapia_app.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False} 
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()