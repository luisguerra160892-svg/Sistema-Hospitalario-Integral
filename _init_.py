from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_jwt_extended import JWTManager
from flask_wtf.csrf import CSRFProtect
from flask_cors import CORS
import os
import logging
from logging.handlers import RotatingFileHandler

# Inicializar extensiones
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
jwt = JWTManager()
csrf = CSRFProtect()
cors = CORS()

def create_app(config_name='default'):
    """Factory function para crear la aplicación Flask"""
    
    app = Flask(__name__)
    
    # Cargar configuración
    from config import config
    app.config.from_object(config[config_name])
    
    # Configurar logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler(
            'logs/hospital.log', 
            maxBytes=10240, 
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Hospital System startup')
    
    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    jwt.init_app(app)
    csrf.init_app(app)
    cors.init_app(app)
    
    # Configurar login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicie sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'
    
    # Registrar blueprints
    from app.routes.auth import auth_bp
    from app.routes.pacientes import pacientes_bp
    from app.routes.consultas import consultas_bp
    from app.routes.citas import citas_bp
    from app.routes.laboratorio import lab_bp
    from app.routes.reportes import reportes_bp
    from app.routes.mobile import mobile_bp
    from app.routes.backup import backup_bp
    from app.routes.admin import admin_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(pacientes_bp, url_prefix='/pacientes')
    app.register_blueprint(consultas_bp, url_prefix='/consultas')
    app.register_blueprint(citas_bp, url_prefix='/citas')
    app.register_blueprint(lab_bp, url_prefix='/laboratorio')
    app.register_blueprint(reportes_bp, url_prefix='/reportes')
    app.register_blueprint(mobile_bp, url_prefix='/api/mobile')
    app.register_blueprint(backup_bp, url_prefix='/backup')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Crear contexto para templates
    @app.context_processor
    def utility_processor():
        from datetime import datetime
        return dict(
            current_year=datetime.now().year,
            app_name="Sistema Hospitalario",
            version="1.0.0"
        )
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('403.html'), 403
    
    # Crear tablas y datos iniciales
    with app.app_context():
        db.create_all()
        
        # Crear datos iniciales si no existen
        from app.utils.seed import seed_database
        seed_database()
        
        # Iniciar tareas programadas
        from app.utils.backup_manager import start_backup_scheduler
        start_backup_scheduler()
    
    return app