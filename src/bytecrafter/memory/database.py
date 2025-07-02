"""
Modelos de base de datos y configuración para el sistema de memoria
"""

import os
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, UniqueConstraint, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import JSON
from sqlalchemy.sql import func

# Base para todos los modelos
Base = declarative_base()

# Configuración de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bytecrafter_memory.db")
ENABLE_MEMORY = os.getenv("ENABLE_MEMORY", "true").lower() == "true"

# Engine y session
engine = None
SessionLocal = None

def get_json_type():
    """Retorna el tipo JSON apropiado según la base de datos"""
    if DATABASE_URL.startswith("postgresql"):
        return JSONB
    else:
        return JSON

class Conversation(Base):
    """Modelo para almacenar información de conversaciones"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), nullable=False, index=True)
    user_id = Column(String(50), default="default_user", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    title = Column(String(200))
    summary = Column(Text)
    status = Column(String(20), default="active")  # active, completed, archived
    
    # Relaciones
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    """Modelo para almacenar mensajes individuales"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(10), nullable=False)  # 'user' or 'model'
    content = Column(Text, nullable=False)
    tool_name = Column(String(50))
    tool_params = Column(JSON)
    tool_result = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    message_order = Column(Integer, nullable=False)
    
    # Relaciones
    conversation = relationship("Conversation", back_populates="messages")

class ProjectContext(Base):
    """Modelo para almacenar contexto de proyectos"""
    __tablename__ = "project_context"
    
    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String(100), nullable=False, index=True)
    file_path = Column(String(500))
    context_type = Column(String(50), index=True)  # 'file_structure', 'project_info', 'user_preference'
    context_data = Column(JSON, nullable=False)
    last_accessed = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (UniqueConstraint('project_name', 'file_path', 'context_type'),)

class LearningMemory(Base):
    """Modelo para almacenar aprendizajes y patrones"""
    __tablename__ = "learning_memory"
    
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), nullable=False, index=True)  # 'file_encoding', 'user_pattern', 'error_solution'
    key_pattern = Column(String(200), nullable=False, index=True)
    learned_data = Column(JSON, nullable=False)
    confidence_score = Column(Float, default=1.0)
    usage_count = Column(Integer, default=1)
    last_used = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

def init_database() -> bool:
    """Inicializa la base de datos y crea las tablas"""
    global engine, SessionLocal
    
    if not ENABLE_MEMORY:
        return False
    
    try:
        # Crear engine
        if DATABASE_URL.startswith("sqlite"):
            engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
        else:
            engine = create_engine(DATABASE_URL)
        
        # Crear session factory
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Crear tablas
        Base.metadata.create_all(bind=engine)
        
        print("✅ Base de datos de memoria inicializada correctamente")
        return True
        
    except Exception as e:
        print(f"❌ Error inicializando base de datos: {e}")
        return False

def get_session() -> Optional[Session]:
    """Obtiene una sesión de base de datos"""
    if not ENABLE_MEMORY or SessionLocal is None:
        return None
    
    try:
        return SessionLocal()
    except Exception as e:
        print(f"❌ Error obteniendo sesión de BD: {e}")
        return None

def test_connection() -> bool:
    """Prueba la conexión a la base de datos"""
    if not ENABLE_MEMORY:
        return False
    
    session = get_session()
    if session is None:
        return False
    
    try:
        # Prueba simple
        session.execute("SELECT 1")
        session.close()
        return True
    except Exception as e:
        print(f"❌ Error en conexión de BD: {e}")
        if session:
            session.close()
        return False

def cleanup_old_data(retention_days: int = 90) -> bool:
    """Limpia datos antiguos basado en política de retención"""
    if not ENABLE_MEMORY:
        return False
    
    session = get_session()
    if session is None:
        return False
    
    try:
        from datetime import timedelta
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
        
        # Marcar conversaciones viejas como archivadas
        old_conversations = session.query(Conversation).filter(
            Conversation.updated_at < cutoff_date,
            Conversation.status == "active"
        ).update({"status": "archived"})
        
        # Actualizar última acceso en contexto de proyectos
        session.query(ProjectContext).filter(
            ProjectContext.last_accessed < cutoff_date
        ).update({"last_accessed": func.now()})
        
        session.commit()
        session.close()
        
        print(f"✅ Limpieza completada: {old_conversations} conversaciones archivadas")
        return True
        
    except Exception as e:
        print(f"❌ Error en limpieza de datos: {e}")
        if session:
            session.rollback()
            session.close()
        return False 