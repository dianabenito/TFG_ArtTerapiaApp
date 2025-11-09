from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # discriminator column for single-table inheritance
    type = Column(String(50), nullable=False, server_default='user')

    items = relationship("Item", back_populates="owner")  # One user can have many items

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'user'
    }

class Patient(User):
    """Patient subtype of User. Add patient-specific fields here later."""

    images = relationship("Image", back_populates="owner")  # One user can have many images

    __mapper_args__ = {
        'polymorphic_identity': 'patient'
    }


class Therapist(User):
    """Therapist subtype of User. Add therapist-specific fields here later."""

    __mapper_args__ = {
        'polymorphic_identity': 'therapist'
    }


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="items") # One item belongs to one user

class Image(Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True)
    fileName = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("Patient", back_populates="images") # One item belongs to one user

