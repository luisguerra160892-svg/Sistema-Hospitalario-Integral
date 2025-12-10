from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app import db
from app.models.core import Usuario, RolUsuario
from app.forms.auth_forms import LoginForm, RegisterForm, ChangePasswordForm
from app.utils.security import generate_password_reset_token, verify_password_reset_token

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de inicio de sesión"""
    
    # Si el usuario ya está autenticado, redirigir al dashboard
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        # Buscar usuario por nombre de usuario o email
        user = Usuario.query.filter(
            (Usuario.username == form.username.data) | 
            (Usuario.email == form.username.data)
        ).first()
        
        if user and user.check_password(form.password.data):
            if user.activo:
                login_user(user, remember=form.remember.data)
                
                # Actualizar último acceso
                from datetime import datetime
                user.ultimo_acceso = datetime.utcnow()
                db.session.commit()
                
                flash('¡Inicio de sesión exitoso!', 'success')
                
                # Redirigir según el rol
                next_page = request.args.get('next')
                if not next_page or not next_page.startswith('/'):
                    next_page = url_for('main.dashboard')
                return redirect(next_page)
            else:
                flash('Tu cuenta está desactivada. Contacta al administrador.', 'danger')
        else:
            flash('Nombre de usuario o contraseña incorrectos.', 'danger')
    
    return render_template('auth/login.html', form=form, title='Iniciar Sesión')

@auth_bp.route('/logout')
@login_required
def logout():
    """Cerrar sesión"""
    logout_user()
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """Registro de nuevos usuarios (solo administradores)"""
    
    # Solo administradores pueden registrar usuarios
    if current_user.rol != RolUsuario.ADMINISTRADOR:
        flash('No tienes permisos para acceder a esta página.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    form = RegisterForm()
    
    if form.validate_on_submit():
        # Verificar que el username no exista
        if Usuario.query.filter_by(username=form.username.data).first():
            flash('El nombre de usuario ya existe.', 'danger')
            return render_template('auth/register.html', form=form)
        
        # Verificar que el email no exista
        if Usuario.query.filter_by(email=form.email.data).first():
            flash('El correo electrónico ya está registrado.', 'danger')
            return render_template('auth/register.html', form=form)
        
        # Crear nuevo usuario
        user = Usuario(
            username=form.username.data,
            email=form.email.data,
            nombre=form.nombre.data,
            apellidos=form.apellidos.data,
            rol=form.rol.data,
            especialidad=form.especialidad.data,
            cedula=form.cedula.data,
            telefono=form.telefono.data,
            direccion=form.direccion.data,
            fecha_nacimiento=form.fecha_nacimiento.data,
            sexo=form.sexo.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'Usuario {user.username} registrado exitosamente.', 'success')
        return redirect(url_for('admin.list_users'))
    
    return render_template('auth/register.html', form=form, title='Registrar Usuario')

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Perfil del usuario"""
    form = RegisterForm(obj=current_user)
    form.password.data = None  # No mostrar contraseña
    
    if form.validate_on_submit():
        # Actualizar datos del usuario
        current_user.nombre = form.nombre.data
        current_user.apellidos = form.apellidos.data
        current_user.email = form.email.data
        current_user.telefono = form.telefono.data
        current_user.direccion = form.direccion.data
        current_user.fecha_nacimiento = form.fecha_nacimiento.data
        current_user.sexo = form.sexo.data
        
        db.session.commit()
        flash('Perfil actualizado exitosamente.', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/profile.html', form=form, title='Mi Perfil')

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Cambiar contraseña"""
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Contraseña cambiada exitosamente.', 'success')
            return redirect(url_for('auth.profile'))
        else:
            flash('La contraseña actual es incorrecta.', 'danger')
    
    return render_template('auth/change_password.html', form=form, title='Cambiar Contraseña')

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Olvidé mi contraseña"""
    from flask import jsonify
    from app.utils.notifications import send_password_reset_email
    
    if request.method == 'POST':
        email = request.form.get('email')
        user = Usuario.query.filter_by(email=email).first()
        
        if user:
            token = generate_password_reset_token(user.id)
            send_password_reset_email(user, token)
            flash('Se ha enviado un correo con instrucciones para restablecer tu contraseña.', 'info')
        else:
            flash('No existe una cuenta con ese correo electrónico.', 'danger')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html', title='Recuperar Contraseña')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Restablecer contraseña con token"""
    user_id = verify_password_reset_token(token)
    
    if not user_id:
        flash('El enlace de restablecimiento es inválido o ha expirado.', 'danger')
        return redirect(url_for('auth.login'))
    
    user = Usuario.query.get(user_id)
    if not user:
        flash('Usuario no encontrado.', 'danger')
        return redirect(url_for('auth.login'))
    
    form = ChangePasswordForm()
    form.current_password.label.text = 'Nueva Contraseña'
    
    if form.validate_on_submit():
        user.set_password(form.new_password.data)
        db.session.commit()
        flash('Tu contraseña ha sido restablecida. Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', form=form, token=token, title='Restablecer Contraseña')

@auth_bp.route('/switch-role/<role>')
@login_required
def switch_role(role):
    """Cambiar rol temporalmente (solo para desarrollo/admin)"""
    if current_user.rol == RolUsuario.ADMINISTRADOR:
        session['temp_role'] = role
        flash(f'Rol cambiado temporalmente a {role}.', 'info')
    return redirect(request.referrer or url_for('main.dashboard'))