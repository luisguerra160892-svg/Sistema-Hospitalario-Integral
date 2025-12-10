from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func
import json
import pandas as pd
from io import BytesIO

from app import db
from app.models.laboratorio import (
    Laboratorio, CategoriaAnalisis, TipoAnalisisLab,
    SolicitudLaboratorio, DetalleSolicitudLab, ResultadoLaboratorio,
    EstadoSolicitud, PrioridadAnalisis
)
from app.models.core import Paciente, Consulta
from app.forms.laboratorio_forms import (
    SolicitudLaboratorioForm, ResultadoLabForm, 
    TipoAnalisisForm, LaboratorioForm
)
from app.utils.report_generator import ReportGenerator

lab_bp = Blueprint('laboratorio', __name__)

@lab_bp.route('/')
@login_required
def list_solicitudes():
    """Lista de solicitudes de laboratorio"""
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    estado = request.args.get('estado', 'todas')
    prioridad = request.args.get('prioridad')
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    
    # Construir consulta base
    query = SolicitudLaboratorio.query
    
    # Filtrar por estado
    if estado != 'todas':
        query = query.filter_by(estado=EstadoSolicitud[estado.upper()])
    
    # Filtrar por prioridad
    if prioridad:
        query = query.filter_by(prioridad=PrioridadAnalisis[prioridad.upper()])
    
    # Filtrar por fechas
    if fecha_inicio:
        try:
            fecha_ini = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            query = query.filter(SolicitudLaboratorio.fecha_solicitud >= fecha_ini)
        except:
            pass
    
    if fecha_fin:
        try:
            fecha_f = datetime.strptime(fecha_fin, '%Y-%m-%d')
            query = query.filter(SolicitudLaboratorio.fecha_solicitud <= fecha_f)
        except:
            pass
    
    # Ordenar
    query = query.order_by(SolicitudLaboratorio.fecha_solicitud.desc())
    
    # Paginar
    solicitudes = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Estadísticas
    total_hoy = SolicitudLaboratorio.query.filter(
        func.date(SolicitudLaboratorio.fecha_solicitud) == datetime.today().date()
    ).count()
    
    pendientes = SolicitudLaboratorio.query.filter_by(
        estado=EstadoSolicitud.PENDIENTE
    ).count()
    
    return render_template('laboratorio/solicitudes.html',
                         solicitudes=solicitudes,
                         estado=estado,
                         prioridad=prioridad,
                         fecha_inicio=fecha_inicio,
                         fecha_fin=fecha_fin,
                         total_hoy=total_hoy,
                         pendientes=pendientes,
                         title='Solicitudes de Laboratorio')

@lab_bp.route('/solicitud/nueva', methods=['GET', 'POST'])
@login_required
def nueva_solicitud():
    """Crear nueva solicitud de laboratorio"""
    
    form = SolicitudLaboratorioForm()
    
    # Precargar paciente si viene de consulta
    paciente_id = request.args.get('paciente_id', type=int)
    consulta_id = request.args.get('consulta_id', type=int)
    
    if paciente_id:
        paciente = Paciente.query.get(paciente_id)
        if paciente:
            form.paciente_id.data = paciente_id
    
    if consulta_id:
        consulta = Consulta.query.get(consulta_id)
        if consulta:
            form.consulta_id.data = consulta_id
            form.paciente_id.data = consulta.paciente_id
            form.diagnostico_presuntivo.data = consulta.diagnostico_principal
    
    if form.validate_on_submit():
        # Crear solicitud
        solicitud = SolicitudLaboratorio(
            paciente_id=form.paciente_id.data,
            medico_solicitante_id=current_user.id,
            consulta_id=form.consulta_id.data,
            laboratorio_id=form.laboratorio_id.data,
            prioridad=form.prioridad.data,
            diagnostico_presuntivo=form.diagnostico_presuntivo.data,
            instrucciones_especiales=form.instrucciones_especiales.data,
            notas=form.notas.data,
            creado_por=current_user.id
        )
        
        # Agregar análisis seleccionados
        for tipo_analisis_id in form.tipos_analisis.data:
            tipo = TipoAnalisisLab.query.get(tipo_analisis_id)
            if tipo:
                detalle = DetalleSolicitudLab(
                    tipo_analisis_id=tipo_analisis_id
                )
                solicitud.detalles.append(detalle)
        
        db.session.add(solicitud)
        db.session.commit()
        
        flash(f'Solicitud {solicitud.codigo_solicitud} creada exitosamente.', 'success')
        return redirect(url_for('laboratorio.detalle_solicitud', id=solicitud.id))
    
    # Lista de tipos de análisis
    tipos_analisis = TipoAnalisisLab.query.filter_by(activo=True).all()
    categorias = CategoriaAnalisis.query.filter_by(activo=True).all()
    
    return render_template('laboratorio/solicitud_form.html',
                         form=form,
                         tipos_analisis=tipos_analisis,
                         categorias=categorias,
                         paciente_id=paciente_id,
                         consulta_id=consulta_id,
                         title='Nueva Solicitud de Laboratorio')

@lab_bp.route('/solicitud/<int:id>')
@login_required
def detalle_solicitud(id):
    """Detalle de solicitud de laboratorio"""
    
    solicitud = SolicitudLaboratorio.query.get_or_404(id)
    
    return render_template('laboratorio/solicitud_detalle.html',
                         solicitud=solicitud,
                         title=f'Solicitud {solicitud.codigo_solicitud}')

@lab_bp.route('/solicitud/<int:id>/procesar', methods=['GET', 'POST'])
@login_required
def procesar_solicitud(id):
    """Procesar solicitud (cambiar estado)"""
    
    solicitud = SolicitudLaboratorio.query.get_or_404(id)
    
    if request.method == 'POST':
        nuevo_estado = request.form.get('estado')
        notas = request.form.get('notas', '')
        
        if nuevo_estado in [e.name for e in EstadoSolicitud]:
            solicitud.estado = EstadoSolicitud[nuevo_estado]
            solicitud.notas = notas
            
            if nuevo_estado == 'EN_PROCESO':
                solicitud.recibido_por = current_user.id
            elif nuevo_estado == 'COMPLETADA':
                solicitud.fecha_entrega_real = datetime.utcnow()
                solicitud.tecnico_responsable = current_user.id
            
            db.session.commit()
            flash(f'Estado actualizado a {nuevo_estado}.', 'success')
    
    return redirect(url_for('laboratorio.detalle_solicitud', id=id))

@lab_bp.route('/solicitud/<int:id>/resultados', methods=['GET', 'POST'])
@login_required
def registrar_resultados(id):
    """Registrar resultados de análisis"""
    
    solicitud = SolicitudLaboratorio.query.get_or_404(id)
    
    if request.method == 'POST':
        # Procesar cada análisis
        for detalle in solicitud.detalles:
            resultado_key = f'resultado_{detalle.id}'
            referencia_key = f'referencia_{detalle.id}'
            observaciones_key = f'observaciones_{detalle.id}'
            
            if resultado_key in request.form:
                detalle.resultados = request.form[resultado_key]
                detalle.valores_referencia = request.form.get(referencia_key, '')
                detalle.observaciones_tecnicas = request.form.get(observaciones_key, '')
                detalle.fecha_procesamiento = datetime.utcnow()
                detalle.tecnico_responsable = current_user.id
                detalle.estado = 'completado'
        
        # Actualizar estado de la solicitud
        todos_completados = all(d.estado == 'completado' for d in solicitud.detalles)
        if todos_completados:
            solicitud.estado = EstadoSolicitud.COMPLETADA
            solicitud.fecha_entrega_real = datetime.utcnow()
        
        db.session.commit()
        flash('Resultados registrados exitosamente.', 'success')
        
        return redirect(url_for('laboratorio.detalle_solicitud', id=id))
    
    return render_template('laboratorio/registrar_resultados.html',
                         solicitud=solicitud,
                         title=f'Resultados - {solicitud.codigo_solicitud}')

@lab_bp.route('/solicitud/<int:id>/imprimir')
@login_required
def imprimir_solicitud(id):
    """Imprimir solicitud de laboratorio"""
    
    solicitud = SolicitudLaboratorio.query.get_or_404(id)
    
    return render_template('laboratorio/imprimir_solicitud.html',
                         solicitud=solicitud,
                         title=f'Solicitud {solicitud.codigo_solicitud}')

@lab_bp.route('/solicitud/<int:id>/resultado-pdf')
@login_required
def resultado_pdf(id):
    """Generar PDF de resultados"""
    
    solicitud = SolicitudLaboratorio.query.get_or_404(id)
    
    if solicitud.estado != EstadoSolicitud.COMPLETADA:
        flash('La solicitud no está completada.', 'danger')
        return redirect(url_for('laboratorio.detalle_solicitud', id=id))
    
    # Usar ReportGenerator para crear PDF
    from app.utils.report_generator import ReportGenerator
    pdf_data = ReportGenerator.generate_lab_result_pdf(solicitud)
    
    return send_file(
        BytesIO(pdf_data),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'resultados_{solicitud.codigo_solicitud}.pdf'
    )

@lab_bp.route('/tipos-analisis')
@login_required
def list_tipos_analisis():
    """Lista de tipos de análisis"""
    
    categorias = CategoriaAnalisis.query.filter_by(activo=True).all()
    tipos = TipoAnalisisLab.query.filter_by(activo=True).all()
    
    return render_template('laboratorio/tipos_analisis.html',
                         categorias=categorias,
                         tipos=tipos,
                         title='Tipos de Análisis')

@lab_bp.route('/tipo-analisis/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo_tipo_analisis():
    """Crear nuevo tipo de análisis"""
    
    form = TipoAnalisisForm()
    
    if form.validate_on_submit():
        tipo = TipoAnalisisLab(
            nombre=form.nombre.data,
            codigo=form.codigo.data,
            descripcion=form.descripcion.data,
            categoria_id=form.categoria_id.data,
            precio=form.precio.data,
            tiempo_entrega=form.tiempo_entrega.data,
            instrucciones_preparacion=form.instrucciones_preparacion.data,
            valores_referencia=form.valores_referencia.data,
            unidad_medida=form.unidad_medida.data,
            requiere_ayuno=form.requiere_ayuno.data,
            requiere_cita_previo=form.requiere_cita_previo.data,
            muestra_tipo=form.muestra_tipo.data,
            muestra_cantidad=form.muestra_cantidad.data,
            metodo=form.metodo.data
        )
        
        db.session.add(tipo)
        db.session.commit()
        
        flash(f'Tipo de análisis {tipo.nombre} creado exitosamente.', 'success')
        return redirect(url_for('laboratorio.list_tipos_analisis'))
    
    categorias = CategoriaAnalisis.query.filter_by(activo=True).all()
    
    return render_template('laboratorio/tipo_analisis_form.html',
                         form=form,
                         categorias=categorias,
                         title='Nuevo Tipo de Análisis')

@lab_bp.route('/api/analisis/paciente/<int:paciente_id>')
@login_required
def api_analisis_paciente(paciente_id):
    """API para obtener análisis previos de un paciente"""
    
    solicitudes = SolicitudLaboratorio.query.filter_by(
        paciente_id=paciente_id,
        estado=EstadoSolicitud.COMPLETADA
    ).order_by(SolicitudLaboratorio.fecha_solicitud.desc()).limit(10).all()
    
    resultados = []
    for solicitud in solicitudes:
        for detalle in solicitud.detalles:
            if detalle.resultados:
                resultados.append({
                    'fecha': solicitud.fecha_solicitud.strftime('%d/%m/%Y'),
                    'analisis': detalle.tipo_analisis.nombre,
                    'resultado': detalle.resultados,
                    'unidad': detalle.tipo_analisis.unidad_medida.value if detalle.tipo_analisis.unidad_medida else '',
                    'referencia': detalle.valores_referencia
                })
    
    return jsonify(resultados)

@lab_bp.route('/exportar-solicitudes')
@login_required
def exportar_solicitudes():
    """Exportar solicitudes a Excel"""
    
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    
    query = SolicitudLaboratorio.query
    
    if fecha_inicio:
        fecha_ini = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        query = query.filter(SolicitudLaboratorio.fecha_solicitud >= fecha_ini)
    
    if fecha_fin:
        fecha_f = datetime.strptime(fecha_fin, '%Y-%m-%d')
        query = query.filter(SolicitudLaboratorio.fecha_solicitud <= fecha_f)
    
    solicitudes = query.all()
    
    # Crear DataFrame
    data = []
    for s in solicitudes:
        data.append({
            'Código': s.codigo_solicitud,
            'Paciente': s.paciente.nombre_completo if s.paciente else '',
            'Médico': s.medico_solicitante.nombre_completo if s.medico_solicitante else '',
            'Fecha Solicitud': s.fecha_solicitud.strftime('%d/%m/%Y %H:%M') if s.fecha_solicitud else '',
            'Fecha Entrega': s.fecha_entrega_real.strftime('%d/%m/%Y %H:%M') if s.fecha_entrega_real else '',
            'Estado': s.estado.value,
            'Prioridad': s.prioridad.value,
            'Total Análisis': len(s.detalles),
            'Total': s.total
        })
    
    df = pd.DataFrame(data)
    
    # Crear archivo Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Solicitudes', index=False)
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'solicitudes_lab_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )