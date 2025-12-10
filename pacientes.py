from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import or_, and_
from datetime import datetime, date
import json

from app import db
from app.models.core import Paciente, Sexo, EstadoCivil, Consulta
from app.models.citas import Cita, EstadoCita
from app.forms.paciente_forms import PacienteForm, SearchPacienteForm
from app.utils.validators import validate_cedula

pacientes_bp = Blueprint('pacientes', __name__)

@pacientes_bp.route('/')
@login_required
def list_pacientes():
    """Lista de pacientes"""
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    search = request.args.get('search', '')
    estado = request.args.get('estado', 'activos')
    
    # Construir consulta base
    query = Paciente.query
    
    # Filtrar por estado
    if estado == 'activos':
        query = query.filter_by(activo=True)
    elif estado == 'inactivos':
        query = query.filter_by(activo=False)
    
    # Buscar
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Paciente.cedula.ilike(search_term),
                Paciente.nombre.ilike(search_term),
                Paciente.apellidos.ilike(search_term),
                Paciente.telefono.ilike(search_term),
                Paciente.email.ilike(search_term)
            )
        )
    
    # Ordenar
    query = query.order_by(Paciente.apellidos.asc(), Paciente.nombre.asc())
    
    # Paginar
    pacientes = query.paginate(page=page, per_page=per_page, error_out=False)
    
    form = SearchPacienteForm()
    if search:
        form.search.data = search
    
    return render_template('pacientes/list.html', 
                         pacientes=pacientes, 
                         form=form, 
                         estado=estado,
                         title='Lista de Pacientes')

@pacientes_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_paciente():
    """Crear nuevo paciente"""
    
    form = PacienteForm()
    
    if form.validate_on_submit():
        # Verificar si la cédula ya existe
        if Paciente.query.filter_by(cedula=form.cedula.data).first():
            flash('Ya existe un paciente con esta cédula.', 'danger')
            return render_template('pacientes/form.html', form=form, title='Nuevo Paciente')
        
        # Crear paciente
        paciente = Paciente(
            cedula=form.cedula.data,
            nombre=form.nombre.data,
            apellidos=form.apellidos.data,
            fecha_nacimiento=form.fecha_nacimiento.data,
            sexo=form.sexo.data,
            estado_civil=form.estado_civil.data,
            direccion=form.direccion.data,
            telefono=form.telefono.data,
            telefono_emergencia=form.telefono_emergencia.data,
            email=form.email.data,
            ocupacion=form.ocupacion.data,
            lugar_trabajo=form.lugar_trabajo.data,
            grupo_sanguineo=form.grupo_sanguineo.data,
            rh_factor=form.rh_factor.data,
            alergias=form.alergias.data,
            enfermedades_cronicas=form.enfermedades_cronicas.data,
            medicamentos_actuales=form.medicamentos_actuales.data,
            antecedentes_familiares=form.antecedentes_familiares.data,
            antecedentes_personales=form.antecedentes_personales.data,
            habitos=form.habitos.data,
            contacto_emergencia_nombre=form.contacto_emergencia_nombre.data,
            contacto_emergencia_parentesco=form.contacto_emergencia_parentesco.data,
            contacto_emergencia_telefono=form.contacto_emergencia_telefono.data,
            notas=form.notas.data
        )
        
        db.session.add(paciente)
        db.session.commit()
        
        flash(f'Paciente {paciente.nombre_completo} creado exitosamente.', 'success')
        return redirect(url_for('pacientes.detalle_paciente', id=paciente.id))
    
    return render_template('pacientes/form.html', form=form, title='Nuevo Paciente')

@pacientes_bp.route('/<int:id>')
@login_required
def detalle_paciente(id):
    """Detalle del paciente"""
    
    paciente = Paciente.query.get_or_404(id)
    
    # Obtener consultas recientes
    consultas = Consulta.query.filter_by(paciente_id=id)\
        .order_by(Consulta.fecha_consulta.desc())\
        .limit(10).all()
    
    # Obtener citas próximas
    citas = Cita.query.filter(
        Cita.paciente_id == id,
        Cita.estado.in_([EstadoCita.PROGRAMADA, EstadoCita.CONFIRMADA])
    ).order_by(Cita.fecha_cita.asc())\
     .limit(5).all()
    
    # Obtener solicitudes de laboratorio pendientes
    from app.models.laboratorio import SolicitudLaboratorio, EstadoSolicitud
    solicitudes_lab = SolicitudLaboratorio.query.filter(
        SolicitudLaboratorio.paciente_id == id,
        SolicitudLaboratorio.estado != EstadoSolicitud.COMPLETADA
    ).order_by(SolicitudLaboratorio.fecha_solicitud.desc())\
     .limit(5).all()
    
    return render_template('pacientes/detail.html',
                         paciente=paciente,
                         consultas=consultas,
                         citas=citas,
                         solicitudes_lab=solicitudes_lab,
                         title=f'Paciente: {paciente.nombre_completo}')

@pacientes_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_paciente(id):
    """Editar paciente"""
    
    paciente = Paciente.query.get_or_404(id)
    form = PacienteForm(obj=paciente)
    
    if form.validate_on_submit():
        # Verificar si la cédula ha cambiado y si ya existe
        if form.cedula.data != paciente.cedula:
            if Paciente.query.filter_by(cedula=form.cedula.data).first():
                flash('Ya existe un paciente con esta cédula.', 'danger')
                return render_template('pacientes/form.html', form=form, paciente=paciente, title='Editar Paciente')
        
        # Actualizar datos
        paciente.cedula = form.cedula.data
        paciente.nombre = form.nombre.data
        paciente.apellidos = form.apellidos.data
        paciente.fecha_nacimiento = form.fecha_nacimiento.data
        paciente.sexo = form.sexo.data
        paciente.estado_civil = form.estado_civil.data
        paciente.direccion = form.direccion.data
        paciente.telefono = form.telefono.data
        paciente.telefono_emergencia = form.telefono_emergencia.data
        paciente.email = form.email.data
        paciente.ocupacion = form.ocupacion.data
        paciente.lugar_trabajo = form.lugar_trabajo.data
        paciente.grupo_sanguineo = form.grupo_sanguineo.data
        paciente.rh_factor = form.rh_factor.data
        paciente.alergias = form.alergias.data
        paciente.enfermedades_cronicas = form.enfermedades_cronicas.data
        paciente.medicamentos_actuales = form.medicamentos_actuales.data
        paciente.antecedentes_familiares = form.antecedentes_familiares.data
        paciente.antecedentes_personales = form.antecedentes_personales.data
        paciente.habitos = form.habitos.data
        paciente.contacto_emergencia_nombre = form.contacto_emergencia_nombre.data
        paciente.contacto_emergencia_parentesco = form.contacto_emergencia_parentesco.data
        paciente.contacto_emergencia_telefono = form.contacto_emergencia_telefono.data
        paciente.notas = form.notas.data
        
        db.session.commit()
        flash('Paciente actualizado exitosamente.', 'success')
        return redirect(url_for('pacientes.detalle_paciente', id=paciente.id))
    
    return render_template('pacientes/form.html', form=form, paciente=paciente, title='Editar Paciente')

@pacientes_bp.route('/<int:id>/toggle-estado')
@login_required
def toggle_estado_paciente(id):
    """Activar/desactivar paciente"""
    
    paciente = Paciente.query.get_or_404(id)
    paciente.activo = not paciente.activo
    
    estado = "activado" if paciente.activo else "desactivado"
    db.session.commit()
    
    flash(f'Paciente {estado} exitosamente.', 'success')
    return redirect(url_for('pacientes.detalle_paciente', id=paciente.id))

@pacientes_bp.route('/<int:id>/historial')
@login_required
def historial_paciente(id):
    """Historial completo del paciente"""
    
    paciente = Paciente.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Obtener todas las consultas
    consultas = Consulta.query.filter_by(paciente_id=id)\
        .order_by(Consulta.fecha_consulta.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('pacientes/historial.html',
                         paciente=paciente,
                         consultas=consultas,
                         title=f'Historial: {paciente.nombre_completo}')

@pacientes_bp.route('/<int:id>/citas')
@login_required
def citas_paciente(id):
    """Citas del paciente"""
    
    paciente = Paciente.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = 20
    estado = request.args.get('estado', 'todas')
    
    # Construir consulta
    query = Cita.query.filter_by(paciente_id=id)
    
    if estado != 'todas':
        query = query.filter_by(estado=EstadoCita[estado.upper()])
    
    citas = query.order_by(Cita.fecha_cita.desc())\
                .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('pacientes/citas.html',
                         paciente=paciente,
                         citas=citas,
                         estado=estado,
                         title=f'Citas: {paciente.nombre_completo}')

@pacientes_bp.route('/<int:id>/laboratorio')
@login_required
def laboratorio_paciente(id):
    """Resultados de laboratorio del paciente"""
    
    paciente = Paciente.query.get_or_404(id)
    from app.models.laboratorio import SolicitudLaboratorio
    
    solicitudes = SolicitudLaboratorio.query.filter_by(paciente_id=id)\
        .order_by(SolicitudLaboratorio.fecha_solicitud.desc())\
        .all()
    
    return render_template('pacientes/laboratorio.html',
                         paciente=paciente,
                         solicitudes=solicitudes,
                         title=f'Laboratorio: {paciente.nombre_completo}')

@pacientes_bp.route('/api/buscar')
@login_required
def api_buscar_pacientes():
    """API para buscar pacientes (autocomplete)"""
    
    term = request.args.get('q', '')
    limit = request.args.get('limit', 10, type=int)
    
    if not term or len(term) < 2:
        return jsonify([])
    
    pacientes = Paciente.query.filter(
        and_(
            Paciente.activo == True,
            or_(
                Paciente.cedula.ilike(f'%{term}%'),
                Paciente.nombre.ilike(f'%{term}%'),
                Paciente.apellidos.ilike(f'%{term}%'),
                Paciente.telefono.ilike(f'%{term}%')
            )
        )
    ).limit(limit).all()
    
    results = [{
        'id': p.id,
        'text': f"{p.cedula} - {p.nombre} {p.apellidos}",
        'cedula': p.cedula,
        'nombre': p.nombre,
        'apellidos': p.apellidos,
        'edad': p.edad,
        'sexo': p.sexo.value if p.sexo else None
    } for p in pacientes]
    
    return jsonify(results)

@pacientes_bp.route('/api/<int:id>/info')
@login_required
def api_info_paciente(id):
    """API para obtener información del paciente"""
    
    paciente = Paciente.query.get_or_404(id)
    
    return jsonify({
        'id': paciente.id,
        'cedula': paciente.cedula,
        'nombre_completo': paciente.nombre_completo,
        'edad': paciente.edad,
        'sexo': paciente.sexo.value if paciente.sexo else None,
        'grupo_sanguineo': f"{paciente.grupo_sanguineo}{paciente.rh_factor}" if paciente.grupo_sanguineo else None,
        'alergias': paciente.alergias,
        'enfermedades_cronicas': paciente.enfermedades_cronicas,
        'telefono': paciente.telefono,
        'email': paciente.email
    })

@pacientes_bp.route('/api/cedula/<cedula>')
@login_required
def api_paciente_por_cedula(cedula):
    """API para buscar paciente por cédula"""
    
    paciente = Paciente.query.filter_by(cedula=cedula).first()
    
    if paciente:
        return jsonify({
            'existe': True,
            'paciente': {
                'id': paciente.id,
                'cedula': paciente.cedula,
                'nombre_completo': paciente.nombre_completo,
                'edad': paciente.edad,
                'sexo': paciente.sexo.value if paciente.sexo else None
            }
        })
    
    return jsonify({'existe': False})

@pacientes_bp.route('/exportar')
@login_required
def exportar_pacientes():
    """Exportar pacientes a Excel"""
    
    import pandas as pd
    from io import BytesIO
    from flask import send_file
    
    # Obtener todos los pacientes activos
    pacientes = Paciente.query.filter_by(activo=True).all()
    
    # Crear DataFrame
    data = []
    for p in pacientes:
        data.append({
            'Cédula': p.cedula,
            'Nombre': p.nombre,
            'Apellidos': p.apellidos,
            'Edad': p.edad,
            'Sexo': p.sexo.value if p.sexo else '',
            'Teléfono': p.telefono,
            'Email': p.email,
            'Dirección': p.direccion,
            'Fecha Registro': p.fecha_registro.strftime('%d/%m/%Y') if p.fecha_registro else '',
            'Grupo Sanguíneo': f"{p.grupo_sanguineo}{p.rh_factor}" if p.grupo_sanguineo else ''
        })
    
    df = pd.DataFrame(data)
    
    # Crear archivo Excel en memoria
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Pacientes', index=False)
    
    output.seek(0)
    
    # Enviar archivo
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'pacientes_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )