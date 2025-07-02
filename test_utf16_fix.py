#!/usr/bin/env python3
"""
Script de prueba específico para verificar la corrección del bug UTF-16
"""

import os
import sys
import tempfile

# Añadir el directorio src al path para poder importar bytecrafter
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from bytecrafter import tools

def test_utf16_detection():
    """Prueba que los archivos UTF-16 se detecten correctamente como texto"""
    print("🧪 Probando detección de archivos UTF-16...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Crear archivo UTF-16 LE (Little Endian)
        utf16le_file = os.path.join(temp_dir, "test_utf16le.md")
        content = """# README del Proyecto
        
Este es un archivo de prueba con acentos: áéíóú, ñ
Y algunos caracteres especiales: ¡¿€@#

## Descripción
Este proyecto hace algo muy interesante...

### Características
- Funcionalidad A
- Funcionalidad B  
- Funcionalidad C
"""
        
        # Escribir como UTF-16 LE
        with open(utf16le_file, "w", encoding="utf-16le") as f:
            f.write(content)
        
        print(f"📄 Archivo UTF-16LE creado: {utf16le_file}")
        
        # Probar detección de encoding
        detected_encoding = tools.detect_file_encoding(utf16le_file)
        print(f"  ✓ Encoding detectado: {detected_encoding}")
        
        # Probar si se marca como binario
        is_binary = tools.is_binary_file(utf16le_file)
        print(f"  ✓ ¿Es binario?: {is_binary}")
        
        # Probar get_file_info
        file_info = tools.get_file_info(utf16le_file)
        print(f"  ✓ Información completa:")
        print(f"    - Existe: {file_info.get('exists')}")
        print(f"    - Es binario: {file_info.get('is_binary')}")
        print(f"    - Encoding: {file_info.get('encoding')}")
        print(f"    - MIME type: {file_info.get('mime_type')}")
        
        # Probar lectura con read_file mejorado
        print(f"\n📖 Probando read_file con UTF-16:")
        result = tools.read_file(utf16le_file)
        
        # Mostrar resultado (truncado para legibilidad)
        if len(result) > 200:
            print(f"    {result[:200]}...")
        else:
            print(f"    {result}")
        
        # Verificar si contiene el contenido esperado
        if "README del Proyecto" in result and "áéíóú" in result:
            print("  ✅ ¡UTF-16 leído correctamente!")
            return True
        else:
            print("  ❌ Error: El contenido no se leyó correctamente")
            return False

def test_utf16_with_bom():
    """Prueba archivos UTF-16 con BOM (Byte Order Mark)"""
    print("\n🧪 Probando archivos UTF-16 con BOM...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Crear archivo UTF-16 con BOM
        utf16_bom_file = os.path.join(temp_dir, "test_utf16_bom.txt")
        content = "Archivo UTF-16 con BOM: ¡Hola mundo! 🌍"
        
        # Escribir como UTF-16 (incluye BOM automáticamente)
        with open(utf16_bom_file, "w", encoding="utf-16") as f:
            f.write(content)
        
        print(f"📄 Archivo UTF-16 con BOM creado")
        
        # Probar detección
        detected_encoding = tools.detect_file_encoding(utf16_bom_file)
        print(f"  ✓ Encoding detectado: {detected_encoding}")
        
        is_binary = tools.is_binary_file(utf16_bom_file)
        print(f"  ✓ ¿Es binario?: {is_binary}")
        
        # Probar lectura
        result = tools.read_file(utf16_bom_file)
        print(f"  ✓ Resultado de lectura: {result[:100]}...")
        
        if content in result:
            print("  ✅ ¡UTF-16 con BOM leído correctamente!")
            return True
        else:
            print("  ❌ Error: El contenido no se leyó correctamente")
            return False

def test_comparison_with_utf8():
    """Compara el comportamiento con archivos UTF-8 normales"""
    print("\n🧪 Comparando con archivos UTF-8 normales...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Crear archivo UTF-8
        utf8_file = os.path.join(temp_dir, "test_utf8.txt")
        content = "Archivo UTF-8 normal: áéíóú ñ ¡¿€@#"
        
        with open(utf8_file, "w", encoding="utf-8") as f:
            f.write(content)
        
        # Crear archivo UTF-16LE equivalente
        utf16_file = os.path.join(temp_dir, "test_utf16.txt")
        with open(utf16_file, "w", encoding="utf-16le") as f:
            f.write(content)
        
        print("📄 Archivos creados para comparación")
        
        # Comparar detección
        utf8_encoding = tools.detect_file_encoding(utf8_file)
        utf16_encoding = tools.detect_file_encoding(utf16_file)
        
        utf8_binary = tools.is_binary_file(utf8_file)
        utf16_binary = tools.is_binary_file(utf16_file)
        
        print(f"  UTF-8  -> Encoding: {utf8_encoding}, ¿Binario?: {utf8_binary}")
        print(f"  UTF-16 -> Encoding: {utf16_encoding}, ¿Binario?: {utf16_binary}")
        
        # Ambos deberían ser detectados como texto
        if not utf8_binary and not utf16_binary:
            print("  ✅ ¡Ambos archivos detectados correctamente como texto!")
            return True
        else:
            print("  ❌ Error: Algún archivo fue marcado incorrectamente como binario")
            return False

def main():
    """Ejecuta todas las pruebas"""
    print("🚀 Probando corrección del bug UTF-16\n")
    
    results = []
    
    try:
        results.append(test_utf16_detection())
        results.append(test_utf16_with_bom())
        results.append(test_comparison_with_utf8())
        
        if all(results):
            print("\n✅ ¡TODAS LAS PRUEBAS PASARON!")
            print("🎉 El bug de UTF-16 ha sido corregido exitosamente.")
            print("\n💡 Ahora Bytecrafter debería leer archivos UTF-16 directamente")
            print("   sin necesidad de conversión manual con iconv.")
        else:
            print("\n❌ ALGUNAS PRUEBAS FALLARON")
            print("🔧 Se necesita más trabajo para corregir el bug.")
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 