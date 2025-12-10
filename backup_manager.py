import os
import zipfile
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import schedule
import time
import threading
from app import db
from app.models import *

class BackupManager:
    def __init__(self, app, backup_dir='backups', retention_days=30):
        self.app = app
        self.backup_dir = Path(backup_dir)
        self.retention_days = retention_days
        self.ensure_backup_dir()
    
    def ensure_backup_dir(self):
        """Crea el directorio de backups si no existe"""
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self, full_backup=True):
        """Crea un backup completo"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.backup_dir / f'backup_{timestamp}.zip'
        
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
            # Backup de la base de datos
            self.backup_database(backup_zip)
            
            # Backup de archivos importantes
            self.backup_important_files(backup_zip)
            
            # Backup de configuraciones
            self.backup_configurations(backup_zip)
        
        # Limpiar backups antiguos
        self.clean_old_backups()
        
        # Registrar en log
        self.log_backup(backup_file)
        
        return backup_file
    
    def backup_database(self, zip_file):
        """Backup de datos de la base de datos"""
        with self.app.app_context():
            # Exportar cada modelo a JSON
            models = [
                (Usuario, 'usuarios.json'),
                (Paciente, 'pacientes.json'),
                (Consulta, 'consultas.json'),
                (Cita, 'citas.json'),
                (SolicitudLaboratorio, 'solicitudes_lab.json'),
                (Laboratorio, 'laboratorios.json'),
                (TipoAnalisisLab, 'tipos_analisis.json')
            ]
            
            for model, filename in models:
                try:
                    data = [item.to_dict() for item in model.query.all()]
                    zip_file.writestr(f'database/{filename}', json.dumps(data, indent=2, default=str))
                except Exception as e:
                    print(f"Error backup {model.__name__}: {e}")
    
    def backup_important_files(self, zip_file):
        """Backup de archivos importantes"""
        important_files = [
            'config.py',
            'requirements.txt',
            'README.md',
            'LICENSE'
        ]
        
        for file in important_files:
            if Path(file).exists():
                zip_file.write(file, f'files/{file}')
        
        # Backup de directorios importantes
        important_dirs = ['logs', 'uploads']
        for dir_name in important_dirs:
            dir_path = Path(dir_name)
            if dir_path.exists():
                for file_path in dir_path.rglob('*'):
                    if file_path.is_file():
                        arcname = f'{dir_name}/{file_path.relative_to(dir_path)}'
                        zip_file.write(file_path, arcname)
    
    def backup_configurations(self, zip_file):
        """Backup de configuraciones"""
        config_data = {
            'timestamp': datetime.now().isoformat(),
            'app_version': '1.0.0',
            'backup_type': 'full',
            'database_size': self.get_database_size(),
            'file_count': self.count_files(),
            'total_size_mb': self.get_total_size_mb()
        }
        
        zip_file.writestr('metadata.json', json.dumps(config_data, indent=2))
    
    def get_database_size(self):
        """Obtiene tamaño de la base de datos"""
        db_path = 'hospital.db'
        if Path(db_path).exists():
            return Path(db_path).stat().st_size
        return 0
    
    def count_files(self):
        """Cuenta archivos en directorios importantes"""
        count = 0
        for dir_name in ['uploads', 'logs', 'backups']:
            dir_path = Path(dir_name)
            if dir_path.exists():
                count += sum(1 for _ in dir_path.rglob('*') if _.is_file())
        return count
    
    def get_total_size_mb(self):
        """Obtiene tamaño total en MB"""
        total = 0
        for dir_name in ['uploads', 'logs', 'backups']:
            dir_path = Path(dir_name)
            if dir_path.exists():
                total += sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
        return total / (1024 * 1024)  # MB
    
    def clean_old_backups(self):
        """Elimina backups antiguos"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        for backup_file in self.backup_dir.glob('backup_*.zip'):
            # Extraer fecha del nombre del archivo
            try:
                file_date_str = backup_file.stem.replace('backup_', '')
                file_date = datetime.strptime(file_date_str, '%Y%m%d_%H%M%S')
                
                if file_date < cutoff_date:
                    backup_file.unlink()
                    print(f"Eliminado backup antiguo: {backup_file.name}")
            except:
                pass
    
    def log_backup(self, backup_file):
        """Registra el backup en el log"""
        log_file = Path('logs/backup.log')
        log_file.parent.mkdir(exist_ok=True)
        
        with open(log_file, 'a') as f:
            f.write(f"{datetime.now().isoformat()} - Backup creado: {backup_file.name} "
                   f"({backup_file.stat().st_size / (1024*1024):.2f} MB)\n")
    
    def restore_backup(self, backup_file):
        """Restaura desde un backup"""
        backup_path = Path(backup_file)
        
        if not backup_path.exists():
            raise FileNotFoundError(f"Backup no encontrado: {backup_file}")
        
        # Extraer backup
        extract_dir = Path('temp_restore')
        with zipfile.ZipFile(backup_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        try:
            # Restaurar database (esto es simplificado - en producción necesitarías más lógica)
            database_dir = extract_dir / 'database'
            if database_dir.exists():
                print("⚠️  Restauración de base de datos requiere implementación específica")
            
            # Restaurar archivos
            files_dir = extract_dir / 'files'
            if files_dir.exists():
                for file_path in files_dir.rglob('*'):
                    if file_path.is_file():
                        dest_path = Path(file_path.relative_to(files_dir))
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(file_path, dest_path)
            
            print(f"✅ Restauración completada desde: {backup_path.name}")
            
        finally:
            # Limpiar directorio temporal
            shutil.rmtree(extract_dir, ignore_errors=True)
    
    def schedule_backups(self, hour=2, minute=0):
        """Programa backups automáticos"""
        schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(self.create_backup)
        
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)  # Revisar cada minuto
        
        # Iniciar scheduler en segundo plano
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        print(f"✅ Backups programados diariamente a las {hour:02d}:{minute:02d}")

def start_backup_scheduler():
    """Inicia el scheduler de backups"""
    from app import create_app
    app = create_app()
    
    backup_manager = BackupManager(app)
    backup_manager.schedule_backups(hour=2, minute=0)  # 2:00 AM