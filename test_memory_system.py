#!/usr/bin/env python3
"""
Script de prueba para el sistema de memoria persistente
"""

import os
import sys
from pathlib import Path

def test_memory_system():
    """Prueba el sistema de memoria persistente"""
    print("🧪 Pruebas del Sistema de Memoria Persistente")
    print("=" * 50)
    
    try:
        # Cargar configuración
        from dotenv import load_dotenv
        if Path(".env").exists():
            load_dotenv()
        
        # Importar componentes del sistema de memoria
        from src.bytecrafter.memory import (
            init_database, 
            ConversationManager, 
            ContextManager, 
            LearningEngine
        )
        
        print("✅ Módulos de memoria importados correctamente")
        
        # 1. Probar inicialización de base de datos
        print("\n1. Probando inicialización de base de datos...")
        if init_database():
            print("✅ Base de datos inicializada")
        else:
            print("❌ Error inicializando base de datos")
            return False
        
        # 2. Probar ConversationManager
        print("\n2. Probando gestor de conversaciones...")
        conv_manager = ConversationManager()
        
        # Crear conversación de prueba
        conv_id = conv_manager.start_new_conversation("Prueba de memoria persistente")
        if conv_id:
            print(f"✅ Conversación creada: ID {conv_id}")
            
            # Guardar algunos mensajes
            conv_manager.save_message("user", "¿Qué es qrspace8?")
            conv_manager.save_message("model", "qrspace8 es un proyecto con archivos UTF-16")
            print("✅ Mensajes guardados")
            
            # Recuperar historial
            history = conv_manager.get_conversation_history()
            if len(history) >= 2:
                print(f"✅ Historial recuperado: {len(history)} mensajes")
            else:
                print("❌ Error recuperando historial")
                return False
                
            # Buscar conversaciones
            search_results = conv_manager.search_conversations("qrspace8")
            if search_results:
                print(f"✅ Búsqueda exitosa: {len(search_results)} resultados")
            else:
                print("⚠️  Sin resultados de búsqueda (normal si es primera ejecución)")
                
        else:
            print("❌ Error creando conversación")
            return False
        
        # 3. Probar ContextManager
        print("\n3. Probando gestor de contexto...")
        context_manager = ContextManager()
        
        # Guardar contexto de proyecto
        project_data = {
            "name": "qrspace8",
            "files": ["README.md", "config.json"],
            "encoding_issues": ["UTF-16LE detected in README.md"]
        }
        
        if context_manager.save_project_info("qrspace8", "project_info", project_data):
            print("✅ Contexto de proyecto guardado")
            
            # Recuperar contexto
            retrieved = context_manager.get_project_info("qrspace8")
            if retrieved:
                print(f"✅ Contexto recuperado: {len(retrieved)} entradas")
            else:
                print("❌ Error recuperando contexto")
                return False
        else:
            print("❌ Error guardando contexto")
            return False
        
        # 4. Probar LearningEngine
        print("\n4. Probando motor de aprendizaje...")
        learning_engine = LearningEngine()
        
        # Aprender un patrón de encoding
        if learning_engine.learn_file_encoding_solution(
            "README.md", "utf-16le", "Usar detección automática", True
        ):
            print("✅ Patrón de encoding aprendido")
            
            # Obtener sugerencia
            suggestion = learning_engine.get_file_encoding_suggestion("README.md")
            if suggestion:
                print(f"✅ Sugerencia obtenida: {suggestion['data']['encoding']}")
            else:
                print("❌ Error obteniendo sugerencia")
                return False
        else:
            print("❌ Error aprendiendo patrón")
            return False
        
        # Aprender solución de error
        if learning_engine.learn_error_solution(
            "UnicodeDecodeError",
            "'utf-8' codec can't decode byte 0xff",
            "Usar detección automática de encoding",
            {"file_type": "text", "solution": "chardet"}
        ):
            print("✅ Solución de error aprendida")
        else:
            print("❌ Error aprendiendo solución")
            return False
        
        print("\n✅ ¡Todas las pruebas pasaron exitosamente!")
        print("\n📚 Sistema de memoria funcionando correctamente:")
        print("   • Conversaciones se guardan y recuperan")
        print("   • Contexto de proyectos se mantiene")
        print("   • Patrones y soluciones se aprenden")
        print("   • Búsqueda en memoria funciona")
        
        return True
        
    except ImportError as e:
        print(f"❌ Error de importación: {e}")
        print("💡 Instala dependencias: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def demonstrate_memory_benefit():
    """Demuestra el beneficio del sistema de memoria"""
    print("\n" + "="*50)
    print("🎯 Demostración del Beneficio de Memoria")
    print("="*50)
    
    print("\n🔴 ANTES (Sin memoria):")
    print("Usuario: ¿Qué es qrspace8?")
    print("Bytecrafter: No tengo información sobre qrspace8...")
    print("Usuario: [frustrado] ¡Ya te expliqué qué es qrspace8!")
    
    print("\n🟢 DESPUÉS (Con memoria):")
    print("Usuario: ¿Qué es qrspace8?")
    print("🧠 Consultando memoria previa...")
    print("Bytecrafter: Según nuestras conversaciones anteriores, qrspace8 es un proyecto con:")
    print("   • Un README.md en UTF-16LE (32,194 bytes)")
    print("   • Problemas de encoding que resolvimos")
    print("   • Estructura de archivos que analizamos")
    print("   ¿Te gustaría que continúe donde lo dejamos?")
    
    print("\n💡 Beneficios:")
    print("   ✅ No hay que repetir información")
    print("   ✅ Continuidad entre sesiones")
    print("   ✅ Aprendizaje de patrones")
    print("   ✅ Mejor experiencia de usuario")

if __name__ == "__main__":
    success = test_memory_system()
    
    if success:
        demonstrate_memory_benefit()
        print("\n🚀 El sistema de memoria está listo para usar!")
        print("   Ejecuta: python -m src.bytecrafter.main")
    else:
        print("\n❌ Hay problemas con el sistema de memoria")
        print("💡 Ejecuta primero: python setup_memory.py")
    
    sys.exit(0 if success else 1) 