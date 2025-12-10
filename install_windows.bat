@echo off
chcp 65001 > nul
title 🏥 Instalador Sistema Hospitalario - Windows

echo ===============================================
echo  🏥 INSTALADOR SISTEMA HOSPITALARIO
echo ===============================================
echo.

echo [1/6] Verificando requisitos...
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ Python no encontrado. Instalando...
    powershell -Command "Start-Process 'https://www.python.org/ftp/python/3.11.4/python-3.11.4-amd64.exe'"
    echo Por favor, instale Python y vuelva a ejecutar este script.
    pause
    exit /b 1
)

echo ✅ Python instalado: 
python --version

echo.
echo [2/6] Creando entorno virtual...
python -m venv venv
if errorlevel 1 (
    echo ❌ Error creando entorno virtual.
    pause
    exit /b 1
)

echo.
echo [3/6] Activando entorno virtual...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Error activando entorno virtual.
    pause
    exit /b 1
)

echo.
echo [4/6] Instalando dependencias...
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Error instalando dependencias.
    pause
    exit /b 1
)

echo.
echo [5/6] Configurando base de datos...
python -c "
from app import create_app, db
from app.models.core import Usuario

app = create_app()
with app.app_context():
    db.create_all()
    if not Usuario.query.filter_by(username='admin').first():
        admin = Usuario(
            username='admin',
            nombre='Administrador',
            rol='administrador'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
    print('✅ Base de datos configurada')
"

echo.
echo [6/6] Creando acceso directo...
powershell -Command "
\$WshShell = New-Object -comObject WScript.Shell
\$Shortcut = \$WshShell.CreateShortcut(\"$env:USERPROFILE\\Desktop\\Hospital System.lnk\")
\$Shortcut.TargetPath = \"$env:USERPROFILE\\Desktop\\sistema-hospitalario\\venv\\Scripts\\python.exe\"
\$Shortcut.Arguments = 'main.py'
\$Shortcut.WorkingDirectory = \"$env:USERPROFILE\\Desktop\\sistema-hospitalario\"
\$Shortcut.IconLocation = \"$env:USERPROFILE\\Desktop\\sistema-hospitalario\\resources\\hospital.ico\"
\$Shortcut.Save()
"

echo.
echo ===============================================
echo  ✅ INSTALACIÓN COMPLETADA
echo ===============================================
echo.
echo 📍 Acceso directo creado en el escritorio
echo 🚀 Para iniciar: Doble clic en "Hospital System.lnk"
echo 🌐 O ejecute: python main.py
echo 👤 Usuario: admin | Contraseña: admin123
echo.
pause