#!/usr/bin/env python3
"""
Script para crear releases automáticos en GitHub
"""

import os
import sys
import json
import subprocess
from datetime import datetime

def get_version():
    """Obtener versión del proyecto"""
    try:
        with open('pyproject.toml', 'r') as f:
            for line in f:
                if 'version' in line:
                    return line.split('=')[1].strip().strip('"')
    except:
        return "1.0.0"

def create_zip():
    """Crear archivo ZIP para release"""
    import zipfile
    
    version = get_version()
    zip_name = f"sistema-hospitalario-v{version}.zip"
    
    files_to_include = [
        'main.py',
        'config.py',
        'requirements.txt',
        'README.md',
        'LICENSE',
        '.env.example'
    ]
    
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Agregar archivos principales
        for file in files_to_include:
            if os.path.exists(file):
                zipf.write(file)
        
        # Agregar carpetas
        folders = ['app', 'docs', 'scripts']
        for folder in folders:
            if os.path.exists(folder):
                for root, dirs, files in os.walk(folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, os.path.join(folder, '..'))
                        zipf.write(file_path, arcname)
    
    return zip_name

def create_exe():
    """Crear ejecutable para Windows"""
    try:
        subprocess.run(['pyinstaller', '--clean', '--onefile', 'main.py'], 
                      check=True, capture_output=True)
        return 'dist/main.exe'
    except:
        return None

def main():
    print("🏥 Creando release para GitHub...")
    
    version = get_version()
    print(f"📦 Versión: {version}")
    
    # Crear archivos para release
    zip_file = create_zip()
    print(f"✅ ZIP creado: {zip_file}")
    
    # Crear tag en Git
    subprocess.run(['git', 'tag', f'v{version}'])
    subprocess.run(['git', 'push', 'origin', f'v{version}'])
    
    print("\n🎉 Release creado exitosamente!")
    print(f"\n📋 Para crear release en GitHub:")
    print(f"1. Ve a: https://github.com/tu-usuario/sistema-hospitalario/releases/new")
    print(f"2. Selecciona tag: v{version}")
    print(f"3. Título: Versión {version}")
    print(f"4. Descripción: Ver CHANGELOG.md")
    print(f"5. Subir archivo: {zip_file}")
    print(f"6. Publicar release")

if __name__ == '__main__':
    main()