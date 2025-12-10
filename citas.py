from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date, time, timedelta
from sqlalchemy import and_, or_
import json

from app import db
from app.models.citas import Cita, EstadoCita, TipoConsulta, HorarioMedico, BloqueoHorario
from app.models.core import Paciente, Usuario, RolUsuario
from app.forms.cita_forms import CitaForm, HorarioForm, BloqueoForm
from app.utils.notifications import send_appointment_reminder, send_appointment_confirmation

citas_bp = Blueprint('citas', __name__)

@citas_bp.route('/')
@login_required
def list_citas():
    """Lista de citas"""
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    fecha_str = request.args.get('fecha')
    estado = request.args.get('estado', 'todas')
    medico_id = request.args.get('medico_id', type=int)
    
    # Parsear fecha
    if fecha_str:
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except:
            fecha = date.today()
    else:
        fecha = date.today()
    
    # Construir consulta base
    query = Cita.query.filter(db.func.date(Cita.fecha_cita) == fecha)
    
    # Filtrar por médico
    if medico_id:
        query = query.filter_by(medico_id=medico_id)
    elif current_user.rol == RolUsuario.MEDICO:
        # Médicos solo ven sus citas
        query = query.filter_by(medico_id=current_user.id)
    
    # Filtrar por estado
    if estado != 'todas':
        query = query.filter_by(estado=EstadoCita[estado.upper()])
    
    # Ordenar por hora
    query = query.order_by(Cita.fecha_cita.asc())
    
    # Paginar
    citas = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Estadísticas del día
    total_citas = Cita.query.filter(
        db.func.date(Cita.fecha_cita) == fecha
    ).count()
    
    citas_completadas = Cita.query.filter(
        db.func.date(Cita.fecha_cita) == fecha,
        Cita.estado == EstadoCita.COMPLETADA
    ).count()
    
    citas_pendientes = Cita.query.filter(
        db.func.date(Cita.fecha_cita) == fecha,
        Cita.estado.in_([EstadoCita.PROGRAMADA, EstadoCita.CONFIRMADA])
    ).count()
    
    # Lista de médicos para filtro
    medicos = Usuario.query.filter_by(rol=RolUsuario.MEDICO, activo=True).all()
    
    return render_template('citas/list.html',
                         citas=citas,
                         fecha=fecha,
                         fecha_str=fecha_str or fecha.isoformat(),
                         estado=estado,
                         medico_id=medico_id,
                         medicos=medicos,
                         total_citas=total_citas,
                         citas_completadas=citas_completadas,
                         citas_pendientes=citas_pendientes,
                         title='Citas del Día')

@citas_bp.route('/calendario')
@login_required
def calendario():
    """Calendario de citas"""
    
    medico_id = request.args.get('medico_id', current_user.id if current_user.rol == RolUsuario.MEDICO else None)
    
    # Lista de médicos
    medicos = Usuario.query.filter_by(rol=RolUsuario.MEDICO, activo=True).all()
    
    return render_template('citas/calendario.html',
                         medico_id=medico_id,
                         medicos=medicos,
                         title='Calendario de Citas')

@citas_bp.route('/api/calendario')
@login_required
def api_calendario():
    """API para calendario (FullCalendar)"""
    
    start_str = request.args.get('start')
    end_str = request.args.get('end')
    medico_id = request.args.get('medico_id', type=int)
    
    # Parsear fechas
    start_date = datetime.strptime(start_str, '%Y-%m-%d') if start_str else date.today()
    end_date = datetime.strptime(end_str, '%Y-%m-%d') if end_str else date.today() + timedelta(days=30)
    
    # Construir consulta
    query = Cita.query.filter(
        Cita.fecha_cita.between(start_date, end_date)
    )
    
    if medico_id:
        query = query.filter_by(medico_id=medico_id)
    elif current_user.rol == RolUsuario.MEDICO:
        query = query.filter_by(medico_id=current_user.id)
    
    citas = query.all()
    
    # Formatear para FullCalendar
    eventos = []
    for cita in citas:
        color = {
            EstadoCita.PROGRAMADA: '#17a2b8',  # azul
            EstadoCita.CONFIRMADA: '#28a745',   # verde
            EstadoCita.EN_PROCESO: '#ffc107',   # amarillo
            EstadoCita.COMPLETADA: '#6c757d',   # gris
            EstadoCita.CANCELADA: '#dc3545',    # rojo
            EstadoCita.NO_PRESENTADO: '#343a40' # negro
        }.get(cita.estado, '#6c757d')
        
        eventos.append({
            'id': cita.id,
            'title': f"{cita.paciente.nombre_completo} - {cita.tipo_consulta.value}",
            'start': cita.fecha_cita.isoformat(),
            'end': (cita.fecha_cita + timedelta(minutes=cita.duracion)).isoformat(),
            'color': color,
            'textColor': 'white',
            'extendedProps': {
                'paciente': cita.paciente.nombre_completo,
                'medico': cita.medico.nombre_completo,
                'tipo': cita.tipo_consulta.value,
                'estado': cita.estado.value,
                'sala': cita.sala or '',
                'motivo': cita.motivo or ''
            }
        })
    
    return jsonify(eventos)

@citas_bp.route('/nueva', methods=['GET', 'POST'])
@login_required
def nueva_cita():
    """Crear nueva cita"""
    
    form = CitaForm()
    
    # Precargar paciente si viene de ficha
    paciente_id = request.args.get('paciente_id', type=int)
    if paciente_id:
        paciente = Paciente.query.get(paciente_id)
        if paciente:
            form.paciente_id.data = paciente_id
    
    if form.validate_on_submit():
        # Verificar disponibilidad
        fecha_cita = datetime.combine(form.fecha.data, form.hora.data)
        
        # Verificar si el médico ya tiene cita en ese horario
        conflicto = Cita.query.filter(
            Cita.medico_id == form.medico_id.data,
            Cita.fecha_cita == fecha_cita,
            Cita.estado.in_([EstadoCita.PROGRAMADA, EstadoCita.CONFIRMADA])
        ).first()
        
        if conflicto:
            flash('El médico ya tiene una cita programada en ese horario.', 'danger')
            return render_template('citas/form.html', form=form)
        
        # Crear cita
        cita = Cita(
            paciente_id=form.paciente_id.data,
            medico_id=form.medico_id.data,
            fecha_cita=fecha_cita,
            duracion=form.duracion.data,
            tipo_consulta=form.tipo_consulta.data,
            motivo=form.motivo.data,
            sala=form.sala.data,
            creado_por=current_user.id
        )
        
        db.session.add(cita)
        db.session.commit()
        
        # Enviar notificación si está configurado
        if form.enviar_notificacion.data:
            send_appointment_confirmation(cita)
        
        flash(f'Cita {cita.codigo_cita} creada exitosamente.', 'success')
        return redirect(url_for('citas.detalle_cita', id=cita.id))
    
    # Lista de pacientes para autocomplete
    pacientes = Paciente.query.filter_by(activo=True)\
        .order_by(Paciente.apellidos.asc(), Paciente.nombre.asc()).all()
    
    # Lista de médicos
    medicos = Usuario.query.filter_by(rol=RolUsuario.MEDICO, activo=True).all()
    
    return render_template('citas/form.html',
                         form=form,
                         pacientes=pacientes,
                         medicos=medicos,
                         paciente_id=paciente_id,
                         title='Nueva Cita')

@citas_bp.route('/<int:id>')
@login_required
def detalle_cita(id):
    """Detalle de cita"""
    
    cita = Cita.query.get_or_404(id)
    
    # Verificar permisos
    if current_user.rol == RolUsuario.MEDICO and cita.medico_id != current_user.id:
        flash('No tienes permisos para ver esta cita.', 'danger')
        return redirect(url_for('citas.list_citas'))
    
    return render_template('citas/detail.html',
                         cita=cita,
                         title=f'Cita {cita.codigo_cita}')

@citas_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_cita(id):
    """Editar cita"""
    
    cita = Cita.query.get_or_404(id)
    
    # Verificar permisos
    if cita.medico_id != current_user.id and current_user.rol != RolUsuario.ADMINISTRADOR:
        flash('No tienes permisos para editar esta cita.', 'danger')
        return redirect(url_for('citas.detalle_cita', id=id))
    
    form = CitaForm(obj=cita)
    
    # Establecer fecha y hora por separado
    if cita.fecha_cita:
        form.fecha.data = cita.fecha_cita.date()
        form.hora.data = cita.fecha_cita.time()
    
    if form.validate_on_submit():
        # Verificar disponibilidad (excluyendo esta cita)
        fecha_cita = datetime.combine(form.fecha.data, form.hora.data)
        
        conflicto = Cita.query.filter(
            Cita.medico_id == form.medico_id.data,
            Cita.fecha_cita == fecha_cita,
            Cita.id != id,
            Cita.estado.in_([EstadoCita.PROGRAMADA, EstadoCita.CONFIRMADA])
        ).first()
        
        if conflicto:
            flash('El médico ya tiene una cita programada en ese horario.', 'danger')
            return render_template('citas/form.html', form=form, cita=cita)
        
        # Actualizar cita
        cita.paciente_id = form.paciente_id.data
        cita.medico_id = form.medico_id.data
        cita.fecha_cita = fecha_cita
        cita.duracion = form.duracion.data
        cita.tipo_consulta = form.tipo_consulta.data
        cita.motivo = form.motivo.data
        cita.sala = form.sala.data
        
        db.session.commit()
        
        flash('Cita actualizada exitosamente.', 'success')
        return redirect(url_for('citas.detalle_cita', id=cita.id))
    
    # Lista de pacientes y médicos
    pacientes = Paciente.query.filter_by(activo=True).all()
    medicos = Usuario.query.filter_by(rol=RolUsuario.MEDICO, activo=True).all()
    
    return render_template('citas/form.html',
                         form=form,
                         cita=cita,
                         pacientes=pacientes,
                         medicos=medicos,
                         title='Editar Cita')

@citas_bp.route('/<int:id>/confirmar')
@login_required
def confirmar_cita(id):
    """Confirmar cita"""
    
    cita = Cita.query.get_or_404(id)
    
    if cita.estado != EstadoCita.PROGRAMADA:
        flash('Solo se pueden confirmar citas programadas.', 'danger')
        return redirect(url_for('citas.detalle_cita', id=id))
    
    cita.estado = EstadoCita.CONFIRMADA
    db.session.commit()
    
    # Enviar notificación de confirmación
    send_appointment_confirmation(cita)
    
    flash('Cita confirmada exitosamente.', 'success')
    return redirect(url_for('citas.detalle_cita', id=id))

@citas_bp.route('/<int:id>/cancelar', methods=['GET', 'POST'])
@login_required
def cancelar_cita(id):
    """Cancelar cita"""
    
    cita = Cita.query.get_or_404(id)
    
    if request.method == 'POST':
        motivo = request.form.get('motivo', '')
        
        cita.estado = EstadoCita.CANCELADA
        cita.motivo_cancelacion = motivo
        cita.fecha_cancelacion = datetime.utcnow()
        cita.cancelada_por = current_user.id
        
        db.session.commit()
        
        flash('Cita cancelada exitosamente.', 'success')
        return redirect(url_for('citas.detalle_cita', id=id))
    
    return render_template('citas/cancelar.html',
                         cita=cita,
                         title='Cancelar Cita')

@citas_bp.route('/<int:id>/completar')
@login_required
def completar_cita(id):
    """Marcar cita como completada"""
    
    cita = Cita.query.get_or_404(id)
    
    if cita.estado not in [EstadoCita.PROGRAMADA, EstadoCita.CONFIRMADA, EstadoCita.EN_PROCESO]:
        flash('No se puede completar esta cita.', 'danger')
        return redirect(url_for('citas.detalle_cita', id=id))
    
    cita.estado = EstadoCita.COMPLETADA
    db.session.commit()
    
    flash('Cita marcada como completada.', 'success')
    return redirect(url_for('consultas.nueva_consulta', cita_id=id))

@citas_bp.route('/<int:id>/no-presentado')
@login_required
def no_presentado_cita(id):
    """Marcar cita como no presentado"""
    
    cita = Cita.query.get_or_404(id)
    
    if cita.estado != EstadoCita.PROGRAMADA:
        flash('Solo se pueden marcar como no presentado citas programadas.', 'danger')
        return redirect(url_for('citas.detalle_cita', id=id))
    
    cita.estado = EstadoCita.NO_PRESENTADO
    db.session.commit()
    
    flash('Cita marcada como no presentado.', 'warning')
    return redirect(url_for('citas.detalle_cita', id=id))

@citas_bp.route('/api/disponibilidad')
@login_required
def api_disponibilidad():
    """API para verificar disponibilidad"""
    
    medico_id = request.args.get('medico_id', type=int)
    fecha_str = request.args.get('fecha')
    
    if not medico_id or not fecha_str:
        return jsonify({'error': 'Parámetros incompletos'}), 400
    
    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
    except:
        return jsonify({'error': 'Fecha inválida'}), 400
    
    # Obtener horario del médico para ese día
    dia_semana = fecha.isoweekday()  # 1=Lunes, 7=Domingo
    horario = HorarioMedico.query.filter_by(
        medico_id=medico_id,
        dia_semana=dia_semana,
        activo=True
    ).first()
    
    if not horario:
        return jsonify({'horas_disponibles': []})
    
    # Obtener citas del médico para ese día
    citas = Cita.query.filter(
        db.func.date(Cita.fecha_cita) == fecha,
        Cita.medico_id == medico_id,
        Cita.estado.in_([EstadoCita.PROGRAMADA, EstadoCita.CONFIRMADA])
    ).all()
    
    # Generar slots disponibles
    horas_disponibles = []
    hora_actual = horario.hora_inicio
    
    while hora_actual < horario.hora_fin:
        # Verificar si hay cita en este slot
        cita_existente = False
        slot_inicio = datetime.combine(fecha, hora_actual)
        slot_fin = slot_inicio + timedelta(minutes=horario.duracion_cita)
        
        for cita in citas:
            cita_fin = cita.fecha_cita + timedelta(minutes=cita.duracion)
            if not (slot_fin <= cita.fecha_cita or slot_inicio >= cita_fin):
                cita_existente = True
                break
        
        if not cita_existente:
            horas_disponibles.append(hora_actual.strftime('%H:%M'))
        
        # Siguiente slot
        hora_actual = (datetime.combine(date.today(), hora_actual) + 
                      timedelta(minutes=horario.duracion_cita)).time()
    
    return jsonify({
        'horario': {
            'inicio': horario.hora_inicio.strftime('%H:%M'),
            'fin': horario.hora_fin.strftime('%H:%M'),
            'duracion_cita': horario.duracion_cita
        },
        'horas_disponibles': horas_disponibles
    })

@citas_bp.route('/horarios')
@login_required
def list_horarios():
    """Lista de horarios de médicos"""
    
    medico_id = request.args.get('medico_id', type=int)
    
    if medico_id:
        horarios = HorarioMedico.query.filter_by(medico_id=medico_id).all()
    else:
        horarios = HorarioMedico.query.all()
    
    medicos = Usuario.query.filter_by(rol=RolUsuario.MEDICO, activo=True).all()
    
    return render_template('citas/horarios.html',
                         horarios=horarios,
                         medicos=medicos,
                         medico_id=medico_id,
                         title='Horarios de Médicos')

@citas_bp.route('/horarios/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_horario():
    """Crear nuevo horario"""
    
    form = HorarioForm()
    
    if form.validate_on_submit():
        # Verificar si ya existe horario para ese médico y día
        existente = HorarioMedico.query.filter_by(
            medico_id=form.medico_id.data,
            dia_semana=form.dia_semana.data
        ).first()
        
        if existente:
            flash('Ya existe un horario para este médico en ese día.', 'danger')
            return render_template('citas/horario_form.html', form=form)
        
        horario = HorarioMedico(
            medico_id=form.medico_id.data,
            dia_semana=form.dia_semana.data,
            hora_inicio=form.hora_inicio.data,
            hora_fin=form.hora_fin.data,
            duracion_cita=form.duracion_cita.data,
            max_citas_dia=form.max_citas_dia.data
        )
        
        db.session.add(horario)
        db.session.commit()
        
        flash('Horario creado exitosamente.', 'success')
        return redirect(url_for('citas.list_horarios'))
    
    medicos = Usuario.query.filter_by(rol=RolUsuario.MEDICO, activo=True).all()
    
    return render_template('citas/horario_form.html',
                         form=form,
                         medicos=medicos,
                         title='Nuevo Horario')

@citas_bp.route('/recordatorios')
@login_required
def enviar_recordatorios():
    """Enviar recordatorios de citas"""
    
    # Citas para mañana que no tengan recordatorio enviado
    mañana = date.today() + timedelta(days=1)
    citas = Cita.query.filter(
        db.func.date(Cita.fecha_cita) == mañana,
        Cita.estado.in_([EstadoCita.PROGRAMADA, EstadoCita.CONFIRMADA]),
        Cita.recordatorio_enviado == False
    ).all()
    
    enviadas = 0
    for cita in citas:
        try:
            send_appointment_reminder(cita)
            cita.recordatorio_enviado = True
            enviadas += 1
        except Exception as e:
            print(f"Error enviando recordatorio para cita {cita.id}: {e}")
    
    db.session.commit()
    
    flash(f'Se enviaron {enviadas} recordatorios para mañana.', 'success')
    return redirect(url_for('citas.list_citas'))