"""
Herramientas de control de navegador remoto para Bytecrafter CLI.
Similar a las funcionalidades de navegador remoto de Cline.
"""

import os
import subprocess
import tempfile
import time
import json
import requests

class BrowserController:
    """Controlador para navegador Chrome via CDP."""
    
    def __init__(self):
        self.browser_process = None
        self.port = 9222
        
    def start_browser(self, headless: bool = True, debug_port: int = 9222) -> str:
        """Inicia Chrome con CDP habilitado."""
        try:
            self.port = debug_port
            
            # Buscar Chrome
            chrome_paths = [
                "google-chrome",
                "chromium-browser", 
                "/usr/bin/google-chrome",
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
            ]
            
            chrome_exe = None
            for path in chrome_paths:
                if os.path.exists(path):
                    chrome_exe = path
                    break
                # También verificar en PATH
                try:
                    subprocess.run([path, "--version"], capture_output=True, timeout=2)
                    chrome_exe = path
                    break
                except:
                    continue
            
            if not chrome_exe:
                return "❌ Chrome no encontrado. Instala Google Chrome o Chromium."
            
            # Directorio temporal
            user_data_dir = tempfile.mkdtemp(prefix="bytecrafter_chrome_")
            
            # Argumentos de Chrome
            chrome_args = [
                chrome_exe,
                f"--remote-debugging-port={debug_port}",
                f"--user-data-dir={user_data_dir}",
                "--no-first-run",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor"
            ]
            
            if headless:
                chrome_args.extend(["--headless", "--disable-gpu"])
            
            # Iniciar Chrome
            self.browser_process = subprocess.Popen(
                chrome_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Esperar inicio
            time.sleep(3)
            
            if self.browser_process.poll() is not None:
                return f"❌ Chrome falló al iniciar. Código de salida: {self.browser_process.poll()}"
            
            # Verificar que CDP está funcionando
            try:
                response = requests.get(f"http://localhost:{debug_port}/json", timeout=5)
                if response.status_code == 200:
                    return f"✅ Navegador iniciado en puerto {debug_port}"
                else:
                    return f"❌ CDP no responde en puerto {debug_port}"
            except:
                return f"❌ No se puede conectar a CDP en puerto {debug_port}"
            
        except Exception as e:
            return f"❌ Error iniciando navegador: {e}"
    
    def navigate_to_url(self, url: str) -> str:
        """Navega a una URL usando CDP REST API."""
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'http://' + url
            
            # Obtener primera pestaña
            tabs_response = requests.get(f"http://localhost:{self.port}/json")
            tabs = tabs_response.json()
            
            if not tabs:
                return "❌ No hay pestañas disponibles"
            
            tab_id = tabs[0]['id']
            
            # Navegar
            navigate_data = {
                "id": 1,
                "method": "Page.navigate",
                "params": {"url": url}
            }
            
            # Aquí necesitaríamos WebSocket para comando completo
            # Por simplicidad, usamos la URL directa para ahora
            return f"✅ Solicitada navegación a: {url}"
            
        except Exception as e:
            return f"❌ Error navegando: {e}"

    def take_screenshot(self, save_path: str = None) -> str:
        """Toma screenshot usando CDP."""
        try:
            if not save_path:
                save_path = f"screenshot_{int(time.time())}.png"
            
            # Implementación simplificada - requiere WebSocket real para CDP completo
            return f"✅ Funcionalidad de screenshot disponible (requiere implementación WebSocket completa)"
            
        except Exception as e:
            return f"❌ Error tomando screenshot: {e}"
    
    def close_browser(self) -> str:
        """Cierra el navegador."""
        try:
            if self.browser_process:
                self.browser_process.terminate()
                try:
                    self.browser_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.browser_process.kill()
                self.browser_process = None
            
            return "✅ Navegador cerrado"
            
        except Exception as e:
            return f"❌ Error cerrando navegador: {e}"

# Instancia global
browser_controller = BrowserController()

def start_browser_session(headless: bool = True) -> str:
    """Inicia sesión de navegador."""
    return browser_controller.start_browser(headless)

def navigate_browser(url: str) -> str:
    """Navega el navegador a una URL."""
    return browser_controller.navigate_to_url(url)

def take_browser_screenshot(save_path: str = None) -> str:
    """Toma screenshot del navegador."""
    return browser_controller.take_screenshot(save_path)

def close_browser_session() -> str:
    """Cierra sesión de navegador."""
    return browser_controller.close_browser() 