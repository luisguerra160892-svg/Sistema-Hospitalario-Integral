from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
from sqlalchemy import desc, func

from app import db
from app.models.core import Consulta, Paciente, Prescripcion, ExamenFisico
from app.models.laboratorio import SolicitudLaboratorio
from app.forms.consulta_forms import ConsultaForm, PrescripcionForm, ExamenFisicoForm
from app.utils.report_generator import ReportGenerator

consultas_bp = Blueprint('consultas', __name__)

@consultas_bp.route('/')
@login_required
def list_consultas():
    """Lista de consultas"""
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    medico_id = request.args.get('medico_id', type=int)
    paciente_id = request.args.get('paciente_id', type=int)
    fecha = request.args.get('fecha')
    
    # Construir consulta base
    query = Consulta.query
    
    # Filtrar por médico
    if medico_id:
        query = query.filter_by(medico_id=medico_id)
    
    # Filtrar por paciente
    if paciente_id:
        query = query.filter_by(paciente_id=paciente_id)
    
    # Filtrar por fecha
    if fecha:
        try:
            fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
            query = query.filter(func.date(Consulta.fecha_consulta) == fecha_obj)
        except:
            pass
    
    # Ordenar por fecha más reciente
    query = query.order_by(desc(Consulta.fecha_consulta))
    
    # Paginar
    consultas = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Estadísticas
    total_hoy = Consulta.query.filter(
        func.date(Consulta.fecha_consulta) == date.today()
    ).count()
    
    total_mes = Consulta.query.filter(
        func.extract('month', Consulta.fecha_consulta) == date.today().month,
        func.extract('year', Consulta.fecha_consulta) == date.today().year
    ).count()
    
    return render_template('consultas/list.html',
                         consultas=consultas,
                         medico_id=medico_id,
                         paciente_id=paciente_id,
                         fecha=fecha,
                         total_hoy=total_hoy,
                         total_mes=total_mes,
                         title='Lista de Consultas')

@consultas_bp.route('/nueva', methods=['GET', 'POST'])
@login_required
def nueva_consulta():
    """Crear nueva consulta"""
    
    form = ConsultaForm()
    
    # Si viene de una cita, precargar datos
    cita_id = request.args.get('cita_id', type=int)
    if cita_id:
        from app.models.citas import Cita
        cita = Cita.query.get(cita_id)
        if cita:
            form.paciente_id.data = cita.paciente_id
            form.motivo_consulta.data = cita.motivo
    
    # Lista de pacientes para autocomplete
    pacientes = Paciente.query.filter_by(activo=True)\
        .order_by(Paciente.apellidos.asc(), Paciente.nombre.asc()).all()
    
    if form.validate_on_submit():
        # Crear consulta
        consulta = Consulta(
            paciente_id=form.paciente_id.data,
            medico_id=current_user.id,
            motivo_consulta=form.motivo_consulta.data,
            sintomas=form.sintomas.data,
            historia_enfermedad_actual=form.historia_enfermedad_actual.data,
            diagnostico_principal=form.diagnostico_principal.data,
            diagnosticos_secundarios=form.diagnosticos_secundarios.data,
            cie10_codigo=form.cie10_codigo.data,
            tratamiento=form.tratamiento.data,
            recomendaciones=form.recomendaciones.data,
            notas_medicas=form.notas_medicas.data,
            proxima_cita=form.proxima_cita.data,
            peso=form.peso.data,
            altura=form.altura.data,
            creado_por=current_user.id
        )
        
        # Calcular IMC si hay peso y altura
        if form.peso.data and form.altura.data:
            altura_m = form.altura.data / 100  # Convertir a metros
            consulta.imc = form.peso.data / (altura_m ** 2)
        
        db.session.add(consulta)
        
        # Actualizar cita si existe
        if cita_id:
            cita = Cita.query.get(cita_id)
            if cita:
                cita.consulta_id = consulta.id
                cita.estado = EstadoCita.COMPLETADA
        
        db.session.commit()
        
        flash('Consulta creada exitosamente.', 'success')
        return redirect(url_for('consultas.detalle_consulta', id=consulta.id))
    
    return render_template('consultas/form.html',
                         form=form,
                         pacientes=pacientes,
                         cita_id=cita_id,
                         title='Nueva Consulta')

@consultas_bp.route('/<int:id>')
@login_required
def detalle_consulta(id):
    """Detalle de consulta"""
    
    consulta = Consulta.query.get_or_404(id)
    
    # Verificar permisos
    if current_user.rol not in ['administrador', 'medico'] and consulta.medico_id != current_user.id:
        flash('No tienes permisos para ver esta consulta.', 'danger')
        return redirect(url_for('consultas.list_consultas'))
    
    # Obtener prescripciones
    prescripciones = Prescripcion.query.filter_by(consulta_id=id).all()
    
    # Obtener examen físico
    examen_fisico = ExamenFisico.query.filter_by(id=consulta.examen_fisico_id).first()
    
    # Obtener solicitudes de laboratorio
    solicitudes_lab = SolicitudLaboratorio.query.filter_by(consulta_id=id).all()
    
    return render_template('consultas/detail.html',
                         consulta=consulta,
                         prescripciones=prescripciones,
                         examen_fisico=examen_fisico,
                         solicitudes_lab=solicitudes_lab,
                         title=f'Consulta {consulta.codigo_consulta}')

@consultas_bp.route('/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_consulta(id):
    """Editar consulta"""
    
    consulta = Consulta.query.get_or_404(id)
    
    # Verificar permisos
    if consulta.medico_id != current_user.id and current_user.rol != 'administrador':
        flash('No tienes permisos para editar esta consulta.', 'danger')
        return redirect(url_for('consultas.detalle_consulta', id=id))
    
    form = ConsultaForm(obj=consulta)
    
    if form.validate_on_submit():
        # Actualizar consulta
        consulta.motivo_consulta = form.motivo_consulta.data
        consulta.sintomas = form.sintomas.data
        consulta.historia_enfermedad_actual = form.historia_enfermedad_actual.data
        consulta.diagnostico_principal = form.diagnostico_principal.data
        consulta.diagnosticos_secundarios = form.diagnosticos_secundarios.data
        consulta.cie10_codigo = form.cie10_codigo.data
        consulta.tratamiento = form.tratamiento.data
        consulta.recomendaciones = form.recomendaciones.data
        consulta.notas_medicas = form.notas_medicas.data
        consulta.proxima_cita = form.proxima_cita.data
        consulta.peso = form.peso.data
        consulta.altura = form.altura.data
        
        # Calcular IMC
        if form.peso.data and form.altura.data:
            altura_m = form.altura.data / 100
            consulta.imc = form.peso.data / (altura_m ** 2)
        
        db.session.commit()
        flash('Consulta actualizada exitosamente.', 'success')
        return redirect(url_for('consultas.detalle_consulta', id=consulta.id))
    
    return render_template('consultas/form.html',
                         form=form,
                         consulta=consulta,
                         title=f'Editar Consulta {consulta.codigo_consulta}')

@consultas_bp.route('/<int:id>/examen-fisico', methods=['GET', 'POST'])
@login_required
def examen_fisico(id):
    """Examen físico de la consulta"""
    
    consulta = Consulta.query.get_or_404(id)
    
    # Verificar permisos
    if consulta.medico_id != current_user.id and current_user.rol != 'administrador':
        flash('No tienes permisos para editar esta consulta.', 'danger')
        return redirect(url_for('consultas.detalle_consulta', id=id))
    
    examen = ExamenFisico.query.filter_by(id=consulta.examen_fisico_id).first()
    
    if examen:
        form = ExamenFisicoForm(obj=examen)
    else:
        form = ExamenFisicoForm()
    
    if form.validate_on_submit():
        if not examen:
            examen = ExamenFisico()
            db.session.add(examen)
        
        # Actualizar examen físico
        examen.signos_vitales = form.signos_vitales.data
        examen.cabeza = form.cabeza.data
        examen.cuello = form.cuello.data
        examen.torax = form.torax.data
        examen.abdomen = form.abdomen.data
        examen.extremidades = form.extremidades.data
        examen.sistema_nervioso = form.sistema_nervioso.data
        examen.piel = form.piel.data
        examen.otros = form.otros.data
        examen.notas = form.notas.data
        
        # Asociar con consulta
        consulta.examen_fisico_id = examen.id
        
        db.session.commit()
        flash('Examen físico actualizado exitosamente.', 'success')
        return redirect(url_for('consultas.detalle_consulta', id=consulta.id))
    
    return render_template('consultas/examen_fisico.html',
                         form=form,
                         consulta=consulta,
                         title=f'Examen Físico - {consulta.codigo_consulta}')

@consultas_bp.route('/<int:id>/prescripciones')
@login_required
def list_prescripciones(id):
    """Lista de prescripciones de la consulta"""
    
    consulta = Consulta.query.get_or_404(id)
    prescripciones = Prescripcion.query.filter_by(consulta_id=id).all()
    
    return render_template('consultas/prescripciones.html',
                         consulta=consulta,
                         prescripciones=prescripciones,
                         title=f'Prescripciones - {consulta.codigo_consulta}')

@consultas_bp.route('/<int:id>/nueva-prescripcion', methods=['GET', 'POST'])
@login_required
def nueva_prescripcion(id):
    """Agregar prescripción a consulta"""
    
    consulta = Consulta.query.get_or_404(id)
    
    # Verificar permisos
    if consulta.medico_id != current_user.id and current_user.rol != 'administrador':
        flash('No tienes permisos para agregar prescripciones a esta consulta.', 'danger')
        return redirect(url_for('consultas.detalle_consulta', id=id))
    
    form = PrescripcionForm()
    
    if form.validate_on_submit():
        prescripcion = Prescripcion(
            consulta_id=id,
            medico_id=current_user.id,
            medicamento=form.medicamento.data,
            dosis=form.dosis.data,
            frecuencia=form.frecuencia.data,
            duracion=form.duracion.data,
            via_administracion=form.via_administracion.data,
            indicaciones=form.indicaciones.data,
            fecha_inicio=form.fecha_inicio.data,
            fecha_fin=form.fecha_fin.data,
            creado_por=current_user.id
        )
        
        db.session.add(prescripcion)
        db.session.commit()
        
        flash('Prescripción agregada exitosamente.', 'success')
        return redirect(url_for('consultas.list_prescripciones', id=id))
    
    return render_template('consultas/prescripcion_form.html',
                         form=form,
                         consulta=consulta,
                         title='Nueva Prescripción')

@consultas_bp.route('/prescripcion/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_prescripcion(id):
    """Editar prescripción"""
    
    prescripcion = Prescripcion.query.get_or_404(id)
    consulta = Consulta.query.get_or_404(prescripcion.consulta_id)
    
    # Verificar permisos
    if consulta.medico_id != current_user.id and current_user.rol != 'administrador':
        flash('No tienes permisos para editar esta prescripción.', 'danger')
        return redirect(url_for('consultas.detalle_consulta', id=consulta.id))
    
    form = PrescripcionForm(obj=prescripcion)
    
    if form.validate_on_submit():
        prescripcion.medicamento = form.medicamento.data
        prescripcion.dosis = form.dosis.data
        prescripcion.frecuencia = form.frecuencia.data
        prescripcion.duracion = form.duracion.data
        prescripcion.via_administracion = form.via_administracion.data
        prescripcion.indicaciones = form.indicaciones.data
        prescripcion.fecha_inicio = form.fecha_inicio.data
        prescripcion.fecha_fin = form.fecha_fin.data
        
        db.session.commit()
        flash('Prescripción actualizada exitosamente.', 'success')
        return redirect(url_for('consultas.list_prescripciones', id=consulta.id))
    
    return render_template('consultas/prescripcion_form.html',
                         form=form,
                         consulta=consulta,
                         prescripcion=prescripcion,
                         title='Editar Prescripción')

@consultas_bp.route('/prescripcion/<int:id>/eliminar')
@login_required
def eliminar_prescripcion(id):
    """Eliminar prescripción"""
    
    prescripcion = Prescripcion.query.get_or_404(id)
    consulta_id = prescripcion.consulta_id
    consulta = Consulta.query.get(consulta_id)
    
    # Verificar permisos
    if consulta.medico_id != current_user.id and current_user.rol != 'administrador':
        flash('No tienes permisos para eliminar esta prescripción.', 'danger')
        return redirect(url_for('consultas.detalle_consulta', id=consulta_id))
    
    db.session.delete(prescripcion)
    db.session.commit()
    
    flash('Prescripción eliminada exitosamente.', 'success')
    return redirect(url_for('consultas.list_prescripciones', id=consulta_id))

@consultas_bp.route('/<int:id>/imprimir')
@login_required
def imprimir_consulta(id):
    """Imprimir consulta"""
    
    consulta = Consulta.query.get_or_404(id)
    prescripciones = Prescripcion.query.filter_by(consulta_id=id).all()
    examen_fisico = ExamenFisico.query.filter_by(id=consulta.examen_fisico_id).first()
    
    return render_template('consultas/imprimir.html',
                         consulta=consulta,
                         prescripciones=prescripciones,
                         examen_fisico=examen_fisico,
                         title=f'Consulta {consulta.codigo_consulta}')

@consultas_bp.route('/api/estadisticas')
@login_required
def api_estadisticas():
    """API para estadísticas de consultas"""
    
    from datetime import datetime, timedelta
    
    # Obtener parámetros
    periodo = request.args.get('periodo', 'mes')  # dia, semana, mes, año
    medico_id = request.args.get('medico_id', type=int)
    
    # Calcular fechas según periodo
    hoy = date.today()
    
    if periodo == 'dia':
        start_date = hoy
        end_date = hoy
    elif periodo == 'semana':
        start_date = hoy - timedelta(days=hoy.weekday())
        end_date = start_date + timedelta(days=6)
    elif periodo == 'mes':
        start_date = date(hoy.year, hoy.month, 1)
        if hoy.month == 12:
            end_date = date(hoy.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(hoy.year, hoy.month + 1, 1) - timedelta(days=1)
    else:  # año
        start_date = date(hoy.year, 1, 1)
        end_date = date(hoy.year, 12, 31)
    
    # Generar reporte
    report_generator = ReportGenerator()
    estadisticas = report_generator.generate_consultas_report(
        start_date=datetime.combine(start_date, datetime.min.time()),
        end_date=datetime.combine(end_date, datetime.max.time()),
        medico_id=medico_id
    )
    
    return jsonify(estadisticas)