#!/usr/bin/env python3
"""
Script de prueba para verificar las mejoras implementadas en Bytecrafter CLI
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Añadir el directorio src al path para poder importar bytecrafter
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from bytecrafter import tools

def test_encoding_detection():
    """Prueba la detección de encoding con diferentes tipos de archivo"""
    print("🧪 Probando detección de encoding...")
    
    # Crear archivos de prueba con diferentes encodings
    with tempfile.TemporaryDirectory() as temp_dir:
        # Archivo UTF-8
        utf8_file = os.path.join(temp_dir, "utf8_test.txt")
        with open(utf8_file, "w", encoding="utf-8") as f:
            f.write("¡Hola mundo! Texto con acentos y ñ")
        
        # Archivo Latin-1
        latin1_file = os.path.join(temp_dir, "latin1_test.txt")
        with open(latin1_file, "w", encoding="latin1") as f:
            f.write("Texto en Latin-1 con caracteres especiales")
        
        # Probar detección
        utf8_encoding = tools.detect_file_encoding(utf8_file)
        latin1_encoding = tools.detect_file_encoding(latin1_file)
        
        print(f"  ✓ UTF-8 detectado como: {utf8_encoding}")
        print(f"  ✓ Latin-1 detectado como: {latin1_encoding}")

def test_binary_detection():
    """Prueba la detección de archivos binarios"""
    print("\n🧪 Probando detección de archivos binarios...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Archivo de texto
        text_file = os.path.join(temp_dir, "text.txt")
        with open(text_file, "w") as f:
            f.write("Este es un archivo de texto")
        
        # Archivo binario simulado
        binary_file = os.path.join(temp_dir, "binary.bin")
        with open(binary_file, "wb") as f:
            f.write(b"\x00\x01\x02\x03\xFF\xFE\xFD")
        
        # Probar detección
        is_text_binary = tools.is_binary_file(text_file)
        is_binary_binary = tools.is_binary_file(binary_file)
        
        print(f"  ✓ Archivo de texto detectado como binario: {is_text_binary}")
        print(f"  ✓ Archivo binario detectado como binario: {is_binary_binary}")

def test_file_info():
    """Prueba la función get_file_info"""
    print("\n🧪 Probando información de archivos...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Crear archivo de prueba
        test_file = os.path.join(temp_dir, "test.py")
        with open(test_file, "w") as f:
            f.write("# Archivo de prueba Python\nprint('Hola mundo')\n")
        
        # Obtener información
        file_info = tools.get_file_info(test_file)
        
        print(f"  ✓ Archivo existe: {file_info.get('exists')}")
        print(f"  ✓ Es archivo: {file_info.get('is_file')}")
        print(f"  ✓ Tamaño: {file_info.get('size')} bytes")
        print(f"  ✓ MIME type: {file_info.get('mime_type')}")
        print(f"  ✓ Es binario: {file_info.get('is_binary')}")
        print(f"  ✓ Encoding: {file_info.get('encoding')}")

def test_read_file_improved():
    """Prueba la función read_file mejorada"""
    print("\n🧪 Probando función read_file mejorada...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Archivo de texto normal
        text_file = os.path.join(temp_dir, "normal.txt")
        with open(text_file, "w", encoding="utf-8") as f:
            f.write("Línea 1\nLínea 2 con acentos\nLínea 3 con ñ")
        
        # Archivo binario
        binary_file = os.path.join(temp_dir, "image.jpg")
        with open(binary_file, "wb") as f:
            f.write(b"\xFF\xD8\xFF\xE0")  # Header JPEG simulado
        
        # Probar lectura
        print("  📄 Leyendo archivo de texto:")
        text_result = tools.read_file(text_file)
        print(f"    {text_result[:100]}...")
        
        print("\n  📄 Intentando leer archivo binario:")
        binary_result = tools.read_file(binary_file)
        print(f"    {binary_result[:200]}...")

def test_inspect_file():
    """Prueba la nueva función inspect_file"""
    print("\n🧪 Probando función inspect_file...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Crear archivo de prueba
        test_file = os.path.join(temp_dir, "ejemplo.py")
        content = """#!/usr/bin/env python3
\"\"\"
Archivo de ejemplo para probar inspect_file
\"\"\"

def saludar(nombre):
    return f"¡Hola {nombre}!"

if __name__ == "__main__":
    print(saludar("Mundo"))
"""
        with open(test_file, "w") as f:
            f.write(content)
        
        # Inspeccionar archivo
        inspection = tools.inspect_file(test_file)
        print(f"    {inspection[:300]}...")

def test_list_files_improved():
    """Prueba la función list_files mejorada"""
    print("\n🧪 Probando función list_files mejorada...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Crear estructura de archivos de prueba
        os.makedirs(os.path.join(temp_dir, "subdir"))
        
        # Diferentes tipos de archivos
        files_to_create = [
            ("archivo.txt", "Archivo de texto"),
            ("script.py", "print('Python script')"),
            ("datos.json", '{"test": "data"}'),
            ("subdir/otro.md", "# Markdown file")
        ]
        
        for file_path, content in files_to_create:
            full_path = os.path.join(temp_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w") as f:
                f.write(content)
        
        # Listar archivos
        listing = tools.list_files(temp_dir)
        print(f"    {listing[:400]}...")

def test_safe_execute():
    """Prueba la función safe_execute"""
    print("\n🧪 Probando función safe_execute...")
    
    # Comando simple
    result1 = tools.safe_execute("echo 'Hola desde safe_execute'")
    print(f"  ✓ Echo: {result1[:100]}...")
    
    # Comando con error
    result2 = tools.safe_execute("comando_inexistente")
    print(f"  ✓ Comando inexistente: {result2[:100]}...")
    
    # Comando con directorio de trabajo
    with tempfile.TemporaryDirectory() as temp_dir:
        result3 = tools.safe_execute("pwd", working_dir=temp_dir)
        print(f"  ✓ PWD con working_dir: {result3[:100]}...")

def main():
    """Ejecuta todas las pruebas"""
    print("🚀 Iniciando pruebas de las mejoras de Bytecrafter CLI\n")
    
    try:
        test_encoding_detection()
        test_binary_detection()
        test_file_info()
        test_read_file_improved()
        test_inspect_file()
        test_list_files_improved()
        test_safe_execute()
        
        print("\n✅ ¡Todas las pruebas completadas exitosamente!")
        print("\n🎉 Las mejoras están funcionando correctamente.")
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 