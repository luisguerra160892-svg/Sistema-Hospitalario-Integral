#!/usr/bin/env python3
"""
Punto de entrada principal del Sistema Hospitalario
"""

import os
import sys
import webbrowser
import threading
import time
from datetime import datetime
from pathlib import Path

# Añadir directorio actual al path
sys.path.insert(0, str(Path(__file__).parent))

def setup_environment():
    """Configura el entorno de la aplicación"""
    
    # Crear directorios necesarios
    directories = ['backups', 'logs', 'uploads', 'temp', 'data']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    # Configurar logging
    import logging
    from logging.handlers import RotatingFileHandler
    
    log_file = 'logs/hospital.log'
    handler = RotatingFileHandler(log_file, maxBytes=10000000, backupCount=10)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    
    print(f"📝 Logs en: {log_file}")

def check_dependencies():
    """Verifica e instala dependencias faltantes"""
    try:
        import flask
        import sqlalchemy
        import pandas
        return True
    except ImportError as e:
        print(f"⚠️  Dependencia faltante: {e}")
        print("📦 Instalando dependencias...")
        
        # Instalar requirements.txt si existe
        if os.path.exists('requirements.txt'):
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            return True
        return False

def create_windows_shortcut():
    """Crea acceso directo en Windows"""
    if sys.platform == 'win32':
        try:
            import winshell
            from win32com.client import Dispatch
            
            desktop = winshell.desktop()
            shortcut_path = os.path.join(desktop, "Hospital System.lnk")
            
            target = sys.executable
            working_dir = os.path.dirname(os.path.abspath(__file__))
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = target
            shortcut.WorkingDirectory = working_dir
            shortcut.Arguments = 'main.py'
            
            # Buscar icono
            icon_path = os.path.join(working_dir, 'resources', 'hospital.ico')
            if os.path.exists(icon_path):
                shortcut.IconLocation = icon_path
            
            shortcut.save()
            print("✅ Acceso directo creado en el escritorio")
            
        except ImportError:
            print("ℹ️  Instala pywin32 para crear accesos directos automáticos")
        except Exception as e:
            print(f"⚠️  No se pudo crear acceso directo: {e}")

def open_browser():
    """Abre el navegador automáticamente"""
    time.sleep(3)
    try:
        webbrowser.open('http://localhost:5000')
    except:
        pass

def get_local_ip():
    """Obtiene la IP local"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

def main():
    """Función principal"""
    
    print("=" * 70)
    print("🏥  SISTEMA HOSPITALARIO INTEGRAL")
    print("=" * 70)
    
    # Configuración inicial
    setup_environment()
    
    # Verificar dependencias
    if not check_dependencies():
        print("❌ Error: No se pudieron instalar las dependencias")
        sys.exit(1)
    
    # Crear aplicación Flask
    from app import create_app
    
    app = create_app(os.getenv('FLASK_ENV') or 'default')
    
    # Crear acceso directo (solo primera vez)
    if not os.path.exists('.installed'):
        create_windows_shortcut()
        with open('.installed', 'w') as f:
            f.write(datetime.now().isoformat())
        print("✅ Configuración inicial completada")
    
    # Abrir navegador en segundo plano
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Obtener IP local
    local_ip = get_local_ip()
    
    # Mostrar información
    print("\n" + "=" * 70)
    print("✅ SISTEMA LISTO")
    print("=" * 70)
    print("\n🌐 ACCESOS DISPONIBLES:")
    print(f"   • Local:     http://localhost:5000")
    print(f"   • Red:       http://{local_ip}:5000")
    print(f"   • Externa:   http://[TU_IP_PUBLICA]:5000")
    
    print("\n👤 CREDENCIALES POR DEFECTO:")
    print("   • Usuario:    admin")
    print("   • Contraseña: admin123")
    
    print("\n📊 ESTADÍSTICAS:")
    print("   • Base de datos: data/hospital.db")
    print("   • Logs:         logs/hospital.log")
    print("   • Backups:      backups/")
    print("   • Uploads:      uploads/")
    
    print("\n🛑 PARA DETENER: Presiona CTRL + C")
    print("=" * 70 + "\n")
    
    # Iniciar aplicación
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n👋 Aplicación detenida por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPresiona Enter para salir...")

if __name__ == '__main__':
    main()