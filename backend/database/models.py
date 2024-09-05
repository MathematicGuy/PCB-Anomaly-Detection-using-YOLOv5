from sqlalchemy import Column, Integer, String, Float, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

# Users Table Model
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), nullable=False, unique=True, index=True)
    password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)

# PCBs Table Model
class PCB(Base):
    __tablename__ = "pcbs"

    pcb_id = Column(Integer, primary_key=True, index=True)
    image_path = Column(String(255), nullable=False, unique=True, index=True)
    upload_date = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)

    # Relationship to Errors table
    errors = relationship("Error", back_populates="pcb")

# Errors Table Model
class Error(Base):
    __tablename__ = "errors"

    error_id = Column(Integer, primary_key=True, index=True)
    pcb_id = Column(Integer, ForeignKey('pcbs.pcb_id'), nullable=False)
    error_type = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    confidence = Column(Float, nullable=False)

    # Relationship to PCBs table
    pcb = relationship("PCB", back_populates="errors")
