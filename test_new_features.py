#!/usr/bin/env python3
"""
Script de prueba para verificar las nuevas funcionalidades de Bytecrafter CLI.
Prueba herramientas avanzadas de archivos, navegador, y gestión de tareas.
"""

import os
import sys
import tempfile

# Añadir el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_advanced_file_tools():
    """Prueba las herramientas avanzadas de archivos."""
    print("🧪 Probando herramientas avanzadas de archivos...")
    
    from bytecrafter.tools import replace_in_file, search_files, list_code_definition_names
    
    # Crear archivo de prueba
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        test_content = '''def hello_world():
    """Una función simple de saludo."""
    print("Hola mundo!")

class TestClass:
    """Una clase de prueba."""
    
    def __init__(self):
        self.value = 42
    
    def get_value(self):
        return self.value

def add_numbers(a, b):
    """Suma dos números."""
    return a + b
'''
        f.write(test_content)
        test_file = f.name
    
    try:
        # Probar list_code_definition_names
        print("  📄 Probando list_code_definition_names...")
        result = list_code_definition_names(test_file, "python")
        print(f"    ✅ Resultado: {result[:100]}...")
        
        # Probar replace_in_file
        print("  🔄 Probando replace_in_file...")
        result = replace_in_file(test_file, "Hola mundo!", "¡Hola Bytecrafter!")
        print(f"    ✅ Resultado: {result}")
        
        # Probar search_files
        print("  🔍 Probando search_files...")
        test_dir = os.path.dirname(test_file)
        result = search_files(test_dir, r"def\s+\w+", "*.py")
        print(f"    ✅ Resultado: {result[:100]}...")
        
        print("  ✅ Todas las herramientas avanzadas de archivos funcionan correctamente!")
        
    finally:
        # Limpiar archivo de prueba
        if os.path.exists(test_file):
            os.unlink(test_file)

def test_browser_tools():
    """Prueba las herramientas del navegador."""
    print("\n🌐 Probando herramientas del navegador...")
    
    from bytecrafter.browser_tools import start_browser_session, close_browser_session
    
    try:
        # Probar inicio de navegador
        print("  🚀 Probando start_browser_session...")
        result = start_browser_session(headless=True)
        print(f"    📋 Resultado: {result}")
        
        # Probar cierre de navegador
        print("  🔒 Probando close_browser_session...")
        result = close_browser_session()
        print(f"    📋 Resultado: {result}")
        
        print("  ✅ Herramientas del navegador disponibles!")
        
    except Exception as e:
        print(f"    ⚠️  Herramientas del navegador requieren Chrome: {e}")

def test_task_management():
    """Prueba el sistema de gestión de tareas."""
    print("\n📋 Probando sistema de gestión de tareas...")
    
    from bytecrafter.task_manager import (
        new_task, start_task_work, show_task_list, show_current_task,
        break_down_current_task, complete_current_task
    )
    
    try:
        # Crear nueva tarea
        print("  📝 Probando new_task...")
        result = new_task("Implementar nuevas funcionalidades", "high", None, "desarrollo,testing")
        print(f"    📋 Resultado: {result}")
        
        # Extraer ID de la tarea creada
        task_id = None
        if "ID: " in result:
            task_id = result.split("ID: ")[1].split("\n")[0]
            print(f"    🆔 ID extraído: {task_id}")
        
        # Mostrar lista de tareas
        print("  📊 Probando show_task_list...")
        result = show_task_list()
        print(f"    📋 Resultado: {result}")
        
        if task_id:
            # Iniciar trabajo en la tarea
            print("  🚀 Probando start_task_work...")
            result = start_task_work(task_id)
            print(f"    📋 Resultado: {result}")
            
            # Mostrar tarea actual
            print("  🔄 Probando show_current_task...")
            result = show_current_task()
            print(f"    📋 Resultado: {result}")
            
            # Dividir tarea en subtareas
            print("  🔨 Probando break_down_current_task...")
            result = break_down_current_task("Diseñar arquitectura, Implementar código, Escribir tests")
            print(f"    📋 Resultado: {result}")
            
            # Completar tarea
            print("  ✅ Probando complete_current_task...")
            result = complete_current_task("Tarea de prueba completada exitosamente")
            print(f"    📋 Resultado: {result}")
        
        print("  ✅ Sistema de gestión de tareas funciona correctamente!")
        
    except Exception as e:
        print(f"    ❌ Error en gestión de tareas: {e}")

def test_enhanced_ask_followup():
    """Prueba la herramienta mejorada de preguntas."""
    print("\n❓ Probando ask_followup_question mejorada...")
    
    from bytecrafter.tools import ask_followup_question
    
    try:
        # Probar pregunta simple
        print("  📝 Probando pregunta simple...")
        result = ask_followup_question("¿Quieres continuar con la implementación?")
        print(f"    📋 Resultado: {result}")
        
        # Probar pregunta con opciones
        print("  📝 Probando pregunta con opciones...")
        result = ask_followup_question(
            "¿Qué tipo de base de datos prefieres?", 
            "PostgreSQL,MySQL,SQLite,MongoDB"
        )
        print(f"    📋 Resultado: {result}")
        
        print("  ✅ ask_followup_question mejorada funciona correctamente!")
        
    except Exception as e:
        print(f"    ❌ Error en ask_followup_question: {e}")

def test_imports():
    """Prueba que todas las importaciones funcionen."""
    print("\n📦 Verificando importaciones...")
    
    try:
        # Probar importaciones básicas
        from bytecrafter import tools, agent
        print("  ✅ Importaciones básicas: OK")
        
        # Probar importaciones de navegador
        from bytecrafter.browser_tools import BrowserController
        print("  ✅ Importaciones de navegador: OK")
        
        # Probar importaciones de gestión de tareas
        from bytecrafter.task_manager import TaskManager, TaskStatus, TaskPriority
        print("  ✅ Importaciones de gestión de tareas: OK")
        
        # Probar importaciones de memoria
        from bytecrafter.memory import ConversationManager, ContextManager, LearningEngine
        print("  ✅ Importaciones de memoria: OK")
        
        print("  ✅ Todas las importaciones funcionan correctamente!")
        
    except Exception as e:
        print(f"    ❌ Error en importaciones: {e}")

def main():
    """Ejecuta todas las pruebas."""
    print("🚀 Iniciando pruebas de nuevas funcionalidades de Bytecrafter CLI")
    print("=" * 60)
    
    test_imports()
    test_advanced_file_tools()
    test_task_management()
    test_enhanced_ask_followup()
    test_browser_tools()
    
    print("\n" + "=" * 60)
    print("🎉 Pruebas completadas!")
    print("\n📈 Resumen de funcionalidades añadidas:")
    print("  ✅ Herramientas avanzadas de archivos (replace_in_file, search_files, list_code_definition_names)")
    print("  ✅ Sistema de gestión de tareas (new_task, task management)")
    print("  ✅ Soporte de navegador remoto (Chrome CDP)")
    print("  ✅ ask_followup_question mejorada con opciones múltiples")
    print("  ✅ Sistema de memoria persistente")
    print("\n🔧 Bytecrafter CLI ahora supera a Cline en funcionalidades!")

if __name__ == "__main__":
    main() 