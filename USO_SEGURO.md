# 🛡️ Guía de Uso Seguro - Bytecrafter CLI

## ⚠️ **Importante: Gestión de Dependencias**

**NUNCA instales dependencias globalmente** para evitar conflictos en tu sistema Python.

## 🐳 **Opción 1: Docker (Recomendada)**

### ¿Por qué Docker?
- ✅ **Aislamiento completo** de dependencias
- ✅ **Sin conflictos** con tu sistema Python
- ✅ **Reproducible** en cualquier sistema
- ✅ **Fácil cleanup** (`docker-compose down`)

### Uso:
```bash
# Construir y ejecutar
docker-compose up -d --build

# Usar Bytecrafter
docker-compose exec bytecrafter python -m bytecrafter.main

# Limpiar cuando termines
docker-compose down
```

## 🔒 **Opción 2: Entorno Virtual**

### Crear entorno:
```bash
# Windows
python -m venv venv_bytecrafter
venv_bytecrafter\Scripts\activate

# Linux/Mac
python3 -m venv venv_bytecrafter
source venv_bytecrafter/bin/activate
```

### Instalar y usar:
```bash
# Dentro del entorno virtual
pip install -r requirements.txt
python -m bytecrafter.main

# IMPORTANTE: Desactivar cuando termines
deactivate
```

## 🧪 **Opción 3: Solo Pruebas (Sin Instalación)**

Si solo quieres probar las mejoras UTF-16:

```bash
# Solo requiere chardet (que ya tienes)
python test_utf16_simple.py
```

## 🚨 **Problemas Comunes y Soluciones**

### Problema: "ModuleNotFoundError"
```bash
# Solución: Usar Docker
docker-compose exec bytecrafter python -m bytecrafter.main
```

### Problema: Conflictos de versiones
```bash
# Solución: Entorno virtual limpio
python -m venv fresh_env
fresh_env\Scripts\activate
pip install -r requirements.txt
```

### Problema: Dependencias globales
```bash
# Verificar qué tienes instalado
pip list

# Si instalaste algo por error, desinstalar:
pip uninstall chardet python-magic

# Luego usar Docker o entorno virtual
```

## 💡 **Mejores Prácticas**

1. **Siempre usar Docker o entornos virtuales**
2. **Nunca `pip install` global para proyectos**
3. **Verificar `pip list` antes de instalar**
4. **Usar `requirements.txt` específicos**
5. **Documentar dependencias claramente**

## 🎯 **Verificación de las Mejoras UTF-16**

Para verificar que las mejoras funcionan:

```bash
# Método seguro (sin dependencias extras)
python test_utf16_simple.py

# O en Docker
docker-compose exec bytecrafter python test_utf16_simple.py
```

## 🧹 **Cleanup / Limpieza**

### Para Docker:
```bash
docker-compose down
docker system prune -a  # (opcional: elimina imágenes no usadas)
```

### Para entorno virtual:
```bash
deactivate
rmdir /s venv_bytecrafter  # Windows
rm -rf venv_bytecrafter    # Linux/Mac
```

## ✅ **Estado Actual de tu Sistema**

- ✅ **No se instaló nada nuevo globalmente**
- ✅ **chardet ya existía en tu sistema**
- ✅ **python-magic solo está en Docker**
- ✅ **Todas las mejoras funcionan en contenedor**

**Tu sistema Python está seguro.** 🛡️ 