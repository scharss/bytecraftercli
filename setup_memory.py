#!/usr/bin/env python3
"""
Script para configurar el sistema de memoria persistente de Bytecrafter CLI
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Crea archivo .env con configuración de memoria"""
    env_content = """# Configuración de Bytecrafter CLI

# API Key de Google Gemini (REQUERIDO)
GEMINI_API_KEY=your_gemini_api_key_here

# Configuración de Memoria Persistente
ENABLE_MEMORY=true

# Base de datos (descomenta UNA de las opciones):

# Opción 1: SQLite (más simple, recomendado para desarrollo)
DATABASE_URL=sqlite:///./bytecrafter_memory.db

# Opción 2: PostgreSQL (recomendado para producción)
# DATABASE_URL=postgresql://username:password@localhost:5432/bytecrafter_memory

# Configuración de retención de datos
MEMORY_RETENTION_DAYS=90

# Modelo por defecto
DEFAULT_MODEL=gemini-1.5-flash
"""
    
    env_path = Path(".env")
    
    if env_path.exists():
        print("⚠️  Archivo .env ya existe")
        overwrite = input("¿Deseas sobrescribirlo? (y/N): ").lower().strip()
        if overwrite != 'y':
            print("✅ Manteniendo archivo .env existente")
            return
    
    try:
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("✅ Archivo .env creado exitosamente")
        print("📝 Por favor edita el archivo .env y configura tu GEMINI_API_KEY")
    except Exception as e:
        print(f"❌ Error creando archivo .env: {e}")

def check_dependencies():
    """Verifica que las dependencias estén instaladas"""
    try:
        import sqlalchemy
        print("✅ SQLAlchemy instalado")
    except ImportError:
        print("❌ SQLAlchemy no instalado")
        return False
    
    try:
        import alembic
        print("✅ Alembic instalado")
    except ImportError:
        print("❌ Alembic no instalado")
        return False
    
    # Opcional: PostgreSQL
    try:
        import psycopg2
        print("✅ psycopg2 instalado (PostgreSQL disponible)")
    except ImportError:
        print("⚠️  psycopg2 no instalado (solo SQLite disponible)")
    
    return True

def test_database_connection():
    """Prueba la conexión a la base de datos"""
    try:
        # Cargar variables de entorno
        if Path(".env").exists():
            from dotenv import load_dotenv
            load_dotenv()
        
        from src.bytecrafter.memory.database import init_database, test_connection
        
        print("🔧 Inicializando base de datos...")
        if init_database():
            print("✅ Base de datos inicializada correctamente")
            
            if test_connection():
                print("✅ Conexión a base de datos exitosa")
                return True
            else:
                print("❌ Error en conexión a base de datos")
                return False
        else:
            print("❌ Error inicializando base de datos")
            return False
            
    except Exception as e:
        print(f"❌ Error probando base de datos: {e}")
        return False

def main():
    """Función principal"""
    print("🧠 Configuración del Sistema de Memoria Persistente")
    print("=" * 50)
    
    # 1. Verificar dependencias
    print("\n1. Verificando dependencias...")
    if not check_dependencies():
        print("❌ Instala las dependencias faltantes: pip install -r requirements.txt")
        return False
    
    # 2. Crear archivo .env
    print("\n2. Configurando archivo de entorno...")
    create_env_file()
    
    # 3. Probar base de datos
    print("\n3. Probando conexión a base de datos...")
    if test_database_connection():
        print("\n✅ ¡Sistema de memoria configurado exitosamente!")
        print("\n📚 Ahora Bytecrafter recordará:")
        print("   • Conversaciones anteriores")
        print("   • Contexto de proyectos")
        print("   • Patrones de uso y aprendizajes")
        print("   • Soluciones a problemas recurrentes")
        print("\n🚀 Ejecuta: python -m src.bytecrafter.main")
        return True
    else:
        print("\n❌ Error en configuración de memoria")
        print("💡 Verifica:")
        print("   • Que el archivo .env tenga configuración correcta")
        print("   • Que PostgreSQL esté ejecutándose (si usas PostgreSQL)")
        print("   • Que los permisos de escritura estén disponibles (si usas SQLite)")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 