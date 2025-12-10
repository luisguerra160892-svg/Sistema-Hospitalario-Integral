from flask import Blueprint, render_template, jsonify, request, send_file
from flask_login import login_required, current_user
from datetime import datetime
import os
from pathlib import Path
import zipfile
import json

from app import db
from app.utils.backup_manager import BackupManager
from app.models.core import Usuario

backup_bp = Blueprint('backup', __name__)

@backup_bp.route('/')
@login_required
def backup_dashboard():
    """Dashboard de backups"""
    
    # Solo administradores
    if current_user.rol != 'administrador':
        return jsonify({'error': 'No autorizado'}), 403
    
    backup_manager = BackupManager(current_app._get_current_object())
    
    # Listar backups existentes
    backups = []
    backup_dir = Path(backup_manager.backup_dir)
    
    if backup_dir.exists():
        for file in backup_dir.glob('backup_*.zip'):
            stats = file.stat()
            backups.append({
                'nombre': file.name,
                'fecha': datetime.fromtimestamp(stats.st_mtime).strftime('%d/%m/%Y %H:%M:%S'),
                'tamaño': stats.st_size,
                'tamaño_mb': round(stats.st_size / (1024 * 1024), 2),
                'ruta': str(file)
            })
    
    # Ordenar por fecha (más reciente primero)
    backups.sort(key=lambda x: x['nombre'], reverse=True)
    
    # Estadísticas del sistema
    db_size = backup_manager.get_database_size()
    total_size_mb = backup_manager.get_total_size_mb()
    
    return render_template('backup/dashboard.html',
                         backups=backups,
                         db_size_mb=round(db_size / (1024 * 1024), 2),
                         total_size_mb=round(total_size_mb, 2),
                         title='Gestión de Backups')

@backup_bp.route('/crear', methods=['POST'])
@login_required
def crear_backup():
    """Crear backup manual"""
    
    if current_user.rol != 'administrador':
        return jsonify({'error': 'No autorizado'}), 403
    
    backup_manager = BackupManager(current_app._get_current_object())
    
    try:
        backup_file = backup_manager.create_backup()
        
        return jsonify({
            'success': True,
            'message': 'Backup creado exitosamente',
            'backup': backup_file.name,
            'tamaño_mb': round(backup_file.stat().st_size / (1024 * 1024), 2)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/restaurar', methods=['POST'])
@login_required
def restaurar_backup():
    """Restaurar desde backup"""
    
    if current_user.rol != 'administrador':
        return jsonify({'error': 'No autorizado'}), 403
    
    backup_file = request.form.get('backup_file')
    
    if not backup_file:
        return jsonify({'error': 'Archivo de backup no especificado'}), 400
    
    backup_path = Path('backups') / backup_file
    
    if not backup_path.exists():
        return jsonify({'error': 'Archivo de backup no encontrado'}), 404
    
    backup_manager = BackupManager(current_app._get_current_object())
    
    try:
        # Hacer backup actual antes de restaurar
        backup_manager.create_backup()
        
        # Restaurar
        backup_manager.restore_backup(backup_path)
        
        return jsonify({
            'success': True,
            'message': 'Sistema restaurado exitosamente. Reinicie la aplicación.'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/descargar/<nombre>')
@login_required
def descargar_backup(nombre):
    """Descargar archivo de backup"""
    
    if current_user.rol != 'administrador':
        return jsonify({'error': 'No autorizado'}), 403
    
    backup_path = Path('backups') / nombre
    
    if not backup_path.exists():
        return jsonify({'error': 'Archivo no encontrado'}), 404
    
    return send_file(
        backup_path,
        as_attachment=True,
        download_name=nombre,
        mimetype='application/zip'
    )

@backup_bp.route('/eliminar/<nombre>', methods=['DELETE'])
@login_required
def eliminar_backup(nombre):
    """Eliminar archivo de backup"""
    
    if current_user.rol != 'administrador':
        return jsonify({'error': 'No autorizado'}), 403
    
    backup_path = Path('backups') / nombre
    
    if not backup_path.exists():
        return jsonify({'error': 'Archivo no encontrado'}), 404
    
    try:
        backup_path.unlink()
        return jsonify({'success': True, 'message': 'Backup eliminado'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@backup_bp.route('/configuracion', methods=['GET', 'POST'])
@login_required
def configurar_backup():
    """Configurar backups automáticos"""
    
    if current_user.rol != 'administrador':
        return jsonify({'error': 'No autorizado'}), 403
    
    if request.method == 'POST':
        hora = request.form.get('hora', '2')
        minuto = request.form.get('minuto', '0')
        retention_days = request.form.get('retention_days', '30')
        
        # Guardar configuración
        config_file = Path('config/backup_config.json')
        config_file.parent.mkdir(exist_ok=True)
        
        config = {
            'auto_backup': {
                'hora': int(hora),
                'minuto': int(minuto),
                'activo': request.form.get('auto_backup') == 'on'
            },
            'retention_days': int(retention_days),
            'notificaciones': {
                'email': request.form.get('notificar_email') == 'on',
                'email_destino': request.form.get('email_destino', '')
            }
        }
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Reiniciar scheduler
        from app.utils.backup_manager import start_backup_scheduler
        start_backup_scheduler()
        
        flash('Configuración de backup guardada.', 'success')
        return redirect(url_for('backup.configurar_backup'))
    
    # Cargar configuración actual
    config_file = Path('config/backup_config.json')
    config = {}
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
    
    return render_template('backup/configuracion.html',
                         config=config,
                         title='Configuración de Backups')

@backup_bp.route('/estado-sistema')
@login_required
def estado_sistema():
    """Estado del sistema"""
    
    if current_user.rol != 'administrador':
        return jsonify({'error': 'No autorizado'}), 403
    
    import psutil
    import platform
    
    # Información del sistema
    sistema_info = {
        'sistema': platform.system(),
        'version': platform.version(),
        'procesador': platform.processor(),
        'arquitectura': platform.architecture()[0]
    }
    
    # Uso de CPU
    cpu_percent = psutil.cpu_percent(interval=1)
    
    # Uso de memoria
    memoria = psutil.virtual_memory()
    
    # Uso de disco
    disco = psutil.disk_usage('/')
    
    # Base de datos
    backup_manager = BackupManager(current_app._get_current_object())
    db_size = backup_manager.get_database_size()
    
    return jsonify({
        'sistema': sistema_info,
        'cpu': cpu_percent,
        'memoria': {
            'total': round(memoria.total / (1024**3), 2),  # GB
            'disponible': round(memoria.available / (1024**3), 2),
            'porcentaje': memoria.percent
        },
        'disco': {
            'total': round(disco.total / (1024**3), 2),
            'usado': round(disco.used / (1024**3), 2),
            'libre': round(disco.free / (1024**3), 2),
            'porcentaje': disco.percent
        },
        'base_datos': {
            'tamaño_mb': round(db_size / (1024 * 1024), 2),
            'pacientes': Paciente.query.count(),
            'consultas': Consulta.query.count(),
            'usuarios': Usuario.query.count()
        }
    })

@backup_bp.route('/exportar-datos')
@login_required
def exportar_datos():
    """Exportar datos del sistema"""
    
    if current_user.rol != 'administrador':
        return jsonify({'error': 'No autorizado'}), 403
    
    formato = request.args.get('formato', 'json')
    
    if formato == 'json':
        # Exportar a JSON
        data = {}
        
        # Exportar cada tabla
        from app.models import *
        
        tablas = {
            'usuarios': Usuario,
            'pacientes': Paciente,
            'consultas': Consulta,
            'citas': Cita,
            'laboratorios': Laboratorio,
            'solicitudes_lab': SolicitudLaboratorio
        }
        
        for nombre, modelo in tablas.items():
            items = modelo.query.all()
            data[nombre] = [item.to_dict() for item in items]
        
        # Crear archivo
        from flask import send_file
        from io import BytesIO
        
        output = BytesIO()
        output.write(json.dumps(data, indent=2, default=str).encode('utf-8'))
        output.seek(0)
        
        return send_file(
            output,
            as_attachment=True,
            download_name=f'exportacion_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
            mimetype='application/json'
        )
    
    else:
        # Otros formatos (CSV, Excel)
        return jsonify({'error': 'Formato no soportado'}), 400