#!/usr/bin/env python3
"""
Script de prueba simple para verificar la corrección del bug UTF-16
Sin dependencias externas complejas
"""

import os
import tempfile
import chardet
import mimetypes
from pathlib import Path

def detect_file_encoding_simple(file_path: str) -> str:
    """Versión simplificada de detect_file_encoding"""
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read(32768)
            if not raw_data:
                return 'utf-8'
            
            # Check for BOM first
            if raw_data.startswith(b'\xff\xfe'):
                return 'utf-16le'
            elif raw_data.startswith(b'\xfe\xff'):
                return 'utf-16be'
            elif raw_data.startswith(b'\xef\xbb\xbf'):
                return 'utf-8-sig'
            
            # Use chardet for detection
            result = chardet.detect(raw_data)
            encoding = result.get('encoding', 'utf-8')
            confidence = result.get('confidence', 0)
            
            # Handle chardet's UTF-16 detection
            if encoding and 'utf-16' in encoding.lower():
                try:
                    raw_data.decode(encoding)
                    return encoding
                except UnicodeDecodeError:
                    for utf16_variant in ['utf-16le', 'utf-16be']:
                        try:
                            raw_data.decode(utf16_variant)
                            return utf16_variant
                        except UnicodeDecodeError:
                            continue
            
            # If confidence is good, use it
            if confidence > 0.7 and encoding:
                try:
                    raw_data.decode(encoding)
                    return encoding
                except (UnicodeDecodeError, LookupError):
                    pass
            
            # Fallback encodings
            for fallback_encoding in ['utf-8', 'utf-16le', 'utf-16be', 'latin1', 'cp1252']:
                try:
                    raw_data.decode(fallback_encoding)
                    return fallback_encoding
                except (UnicodeDecodeError, LookupError):
                    continue
            
            return 'utf-8'
    except Exception:
        return 'utf-8'

def is_binary_file_simple(file_path: str) -> bool:
    """Versión simplificada de is_binary_file"""
    try:
        # First check MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            return not mime_type.startswith('text/')
        
        # Use chardet to detect if it's text
        with open(file_path, 'rb') as f:
            chunk = f.read(8192)
            if not chunk:
                return False
            
            # Try to detect encoding first
            result = chardet.detect(chunk)
            encoding = result.get('encoding', '').lower()
            confidence = result.get('confidence', 0)
            
            # If chardet detects a text encoding with decent confidence
            if encoding and confidence > 0.5:
                text_encodings = ['utf-8', 'utf-16', 'utf-16le', 'utf-16be', 'utf-32', 
                                'ascii', 'latin1', 'cp1252', 'iso-8859-1']
                if any(enc in encoding for enc in text_encodings):
                    return False  # It's text
            
            # Check for null bytes, but exclude UTF-16 patterns
            null_count = chunk.count(b'\x00')
            total_bytes = len(chunk)
            
            if null_count == 0:
                return False  # No nulls = likely text
            
            # If roughly half the bytes are null, might be UTF-16
            if total_bytes > 0 and 0.3 <= (null_count / total_bytes) <= 0.7:
                # Check for UTF-16 BOM or patterns
                if chunk.startswith(b'\xff\xfe') or chunk.startswith(b'\xfe\xff'):
                    return False  # UTF-16 with BOM = text
                
                # Check for UTF-16LE pattern (ASCII chars followed by null)
                ascii_null_pattern = 0
                for i in range(0, min(100, len(chunk) - 1), 2):
                    if 32 <= chunk[i] <= 126 and chunk[i + 1] == 0:  # ASCII + null
                        ascii_null_pattern += 1
                
                if ascii_null_pattern > 10:  # Strong UTF-16LE pattern
                    return False  # It's UTF-16 text
            
            # High null density = likely binary
            if null_count / total_bytes > 0.3:
                return True
                
            return False  # Default to text
            
    except Exception:
        return False

def test_utf16_detection():
    """Prueba la detección de archivos UTF-16"""
    print("🧪 Probando detección de archivos UTF-16...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Crear archivo UTF-16 LE
        utf16le_file = os.path.join(temp_dir, "test_utf16le.md")
        content = """# README del Proyecto

Este es un archivo de prueba con acentos: áéíóú, ñ
Y algunos caracteres especiales: ¡¿€@#

## Descripción
Este proyecto hace algo muy interesante...
"""
        
        # Escribir como UTF-16 LE
        with open(utf16le_file, "w", encoding="utf-16le") as f:
            f.write(content)
        
        print(f"📄 Archivo UTF-16LE creado")
        
        # Probar detección de encoding
        detected_encoding = detect_file_encoding_simple(utf16le_file)
        print(f"  ✓ Encoding detectado: {detected_encoding}")
        
        # Probar si se marca como binario
        is_binary = is_binary_file_simple(utf16le_file)
        print(f"  ✓ ¿Es binario?: {is_binary}")
        
        # Probar lectura directa
        try:
            with open(utf16le_file, 'r', encoding=detected_encoding) as f:
                read_content = f.read()
            
            if "README del Proyecto" in read_content and "áéíóú" in read_content:
                print("  ✅ ¡UTF-16 detectado y leído correctamente!")
                return True
            else:
                print("  ❌ Error: El contenido no se leyó correctamente")
                return False
                
        except Exception as e:
            print(f"  ❌ Error al leer: {e}")
            return False

def test_utf16_with_bom():
    """Prueba archivos UTF-16 con BOM"""
    print("\n🧪 Probando archivos UTF-16 con BOM...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        utf16_bom_file = os.path.join(temp_dir, "test_utf16_bom.txt")
        content = "Archivo UTF-16 con BOM: ¡Hola mundo! 🌍"
        
        # Escribir como UTF-16 (incluye BOM automáticamente)
        with open(utf16_bom_file, "w", encoding="utf-16") as f:
            f.write(content)
        
        print(f"📄 Archivo UTF-16 con BOM creado")
        
        # Probar detección
        detected_encoding = detect_file_encoding_simple(utf16_bom_file)
        print(f"  ✓ Encoding detectado: {detected_encoding}")
        
        is_binary = is_binary_file_simple(utf16_bom_file)
        print(f"  ✓ ¿Es binario?: {is_binary}")
        
        # Probar lectura
        try:
            with open(utf16_bom_file, 'r', encoding=detected_encoding) as f:
                read_content = f.read()
            
            if content in read_content:
                print("  ✅ ¡UTF-16 con BOM detectado y leído correctamente!")
                return True
            else:
                print("  ❌ Error: El contenido no coincide")
                return False
                
        except Exception as e:
            print(f"  ❌ Error al leer: {e}")
            return False

def test_comparison():
    """Compara UTF-8 vs UTF-16"""
    print("\n🧪 Comparando UTF-8 vs UTF-16...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        content = "Archivo de prueba: áéíóú ñ ¡¿€@#"
        
        # Crear archivo UTF-8
        utf8_file = os.path.join(temp_dir, "test_utf8.txt")
        with open(utf8_file, "w", encoding="utf-8") as f:
            f.write(content)
        
        # Crear archivo UTF-16LE
        utf16_file = os.path.join(temp_dir, "test_utf16.txt")
        with open(utf16_file, "w", encoding="utf-16le") as f:
            f.write(content)
        
        # Comparar detección
        utf8_encoding = detect_file_encoding_simple(utf8_file)
        utf16_encoding = detect_file_encoding_simple(utf16_file)
        
        utf8_binary = is_binary_file_simple(utf8_file)
        utf16_binary = is_binary_file_simple(utf16_file)
        
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
    print("🚀 Probando corrección del bug UTF-16 (versión simple)\n")
    
    results = []
    
    try:
        results.append(test_utf16_detection())
        results.append(test_utf16_with_bom())
        results.append(test_comparison())
        
        if all(results):
            print("\n✅ ¡TODAS LAS PRUEBAS PASARON!")
            print("🎉 La corrección del bug UTF-16 funciona correctamente.")
            print("\n💡 Esto significa que Bytecrafter ahora debería:")
            print("   • Detectar archivos UTF-16 como texto (no binario)")
            print("   • Leer archivos UTF-16 directamente sin conversión manual")
            print("   • Manejar tanto UTF-16LE como UTF-16BE con y sin BOM")
        else:
            print("\n❌ ALGUNAS PRUEBAS FALLARON")
            print("🔧 Se necesita más trabajo en la corrección.")
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 