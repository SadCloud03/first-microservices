from sqlalchemy import (
    Column, Integer, BigInteger, String, Text,
    Boolean, ForeignKey, DateTime, func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from logging_service.DataBase.db import Base


class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    tokens = relationship("Token", back_populates="service", cascade="all, delete-orphan")
    logs = relationship("Log", back_populates="service", cascade="all, delete-orphan")


class Token(Base):
    __tablename__ = "tokens"

    id = Column(Integer, primary_key=True)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"))
    token = Column(Text, nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    service = relationship("Service", back_populates="tokens")


class Log(Base):
    __tablename__ = "logs"

    id = Column(BigInteger, primary_key=True)
    service_id = Column(Integer, ForeignKey("services.id", ondelete="CASCADE"))
    level = Column(String(20))
    message = Column(Text, nullable=False)
    extra = Column(JSONB, nullable=True)   # si querés JSON real después lo migramos a JSONB
    created_at = Column(DateTime, server_default=func.now())

    service = relationship("Service", back_populates="logs")
