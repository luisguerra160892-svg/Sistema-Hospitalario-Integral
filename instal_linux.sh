#!/bin/bash

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}===============================================${NC}"
echo -e "${GREEN}🏥 INSTALADOR SISTEMA HOSPITALARIO - Linux/Mac${NC}"
echo -e "${GREEN}===============================================${NC}"
echo

# Verificar Python
echo "[1/6] Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 no encontrado${NC}"
    echo "Instale Python3:"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  Mac: brew install python"
    exit 1
fi

echo -e "${GREEN}✅ Python encontrado: $(python3 --version)${NC}"

# Crear entorno virtual
echo
echo "[2/6] Creando entorno virtual..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error creando entorno virtual${NC}"
    exit 1
fi

# Activar entorno virtual
echo
echo "[3/6] Activando entorno virtual..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error activando entorno virtual${NC}"
    exit 1
fi

# Instalar dependencias
echo
echo "[4/6] Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Error instalando dependencias${NC}"
    exit 1
fi

# Configurar base de datos
echo
echo "[5/6] Configurando base de datos..."
python3 -c "
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

# Crear script de inicio
echo
echo "[6/6] Creando script de inicio..."
cat > start_hospital.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
python main.py
EOF

chmod +x start_hospital.sh

# Crear acceso directo en escritorio (Linux)
if [ -d "$HOME/Desktop" ]; then
    cat > "$HOME/Desktop/Hospital System.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Hospital System
Comment=Sistema Hospitalario Integral
Exec=$PWD/start_hospital.sh
Icon=$PWD/resources/hospital.png
Terminal=true
Categories=Medical;
EOF
    chmod +x "$HOME/Desktop/Hospital System.desktop"
fi

echo
echo -e "${GREEN}===============================================${NC}"
echo -e "${GREEN}✅ INSTALACIÓN COMPLETADA${NC}"
echo -e "${GREEN}===============================================${NC}"
echo
echo "🚀 Para iniciar la aplicación:"
echo "   ./start_hospital.sh"
echo "   o ejecute: python main.py"
echo
echo "🌐 Acceda en: http://localhost:5000"
echo "👤 Usuario: admin | Contraseña: admin123"
echo