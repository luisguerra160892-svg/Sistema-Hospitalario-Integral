@echo off
chcp 65001 > nul
echo ========================================
echo  🏥 CONSTRUYENDO SISTEMA HOSPITALARIO
echo ========================================

REM Verificar Python
python --version > nul 2>&1
if errorlevel 1 (
    echo ❌ Python no encontrado. Instale Python 3.8+ primero.
    pause
    exit /b 1
)

REM Verificar PyInstaller
pip list | findstr PyInstaller > nul
if errorlevel 1 (
    echo 📦 Instalando PyInstaller...
    pip install pyinstaller
)

REM Instalar dependencias
echo 📦 Instalando dependencias...
pip install -r requirements_installer.txt

REM Crear directorios necesarios
if not exist "resources" mkdir resources
if not exist "data" mkdir data
if not exist "backups" mkdir backups
if not exist "logs" mkdir logs
if not exist "uploads" mkdir uploads

REM Crear base de datos inicial
echo 🗄️  Creando base de datos inicial...
python -c "
from app import create_app, db
from app.models.core import Usuario
import os

app = create_app('development')
with app.app_context():
    db.create_all()
    if not Usuario.query.filter_by(username='admin').first():
        admin = Usuario(
            username='admin',
            nombre='Administrador del Sistema',
            rol='administrador',
            email='admin@hospital.cu'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('✅ Base de datos creada con usuario admin')
"

REM Compilar con PyInstaller
echo 🔨 Compilando ejecutable...
pyinstaller --clean --noconfirm HospitalSystem.spec

if exist "dist\HospitalSystem.exe" (
    echo ✅ COMPILACIÓN EXITOSA!
    echo.
    echo 📂 El ejecutable está en: dist\HospitalSystem.exe
    echo 📦 Tamaño: %~z0
    echo.
    echo 🚀 Para probar: dist\HospitalSystem.exe
) else (
    echo ❌ Error en la compilación
)

echo.
pause