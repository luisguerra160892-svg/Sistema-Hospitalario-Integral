from flask import Blueprint, render_template, jsonify, request, send_file
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date
from io import BytesIO
import json

from app import db
from app.models.core import Consulta, Paciente, Usuario
from app.models.citas import Cita, EstadoCita
from app.models.laboratorio import SolicitudLaboratorio, EstadoSolicitud
from app.utils.report_generator import ReportGenerator

reportes_bp = Blueprint('reportes', __name__)

@reportes_bp.route('/')
@login_required
def dashboard():
    """Dashboard de reportes"""
    
    hoy = date.today()
    inicio_mes = date(hoy.year, hoy.month, 1)
    
    # Estadísticas generales
    total_pacientes = Paciente.query.filter_by(activo=True).count()
    total_medicos = Usuario.query.filter_by(rol='medico', activo=True).count()
    
    # Consultas del mes
    consultas_mes = Consulta.query.filter(
        db.func.extract('month', Consulta.fecha_consulta) == hoy.month,
        db.func.extract('year', Consulta.fecha_consulta) == hoy.year
    ).count()
    
    # Citas del mes
    citas_mes = Cita.query.filter(
        db.func.extract('month', Cita.fecha_cita) == hoy.month,
        db.func.extract('year', Cita.fecha_cita) == hoy.year
    ).count()
    
    # Solicitudes de lab del mes
    solicitudes_mes = SolicitudLaboratorio.query.filter(
        db.func.extract('month', SolicitudLaboratorio.fecha_solicitud) == hoy.month,
        db.func.extract('year', SolicitudLaboratorio.fecha_solicitud) == hoy.year
    ).count()
    
    # Ingresos estimados del mes (ejemplo)
    ingresos_mes = 0  # Aquí iría lógica de facturación
    
    return render_template('reportes/dashboard.html',
                         total_pacientes=total_pacientes,
                         total_medicos=total_medicos,
                         consultas_mes=consultas_mes,
                         citas_mes=citas_mes,
                         solicitudes_mes=solicitudes_mes,
                         ingresos_mes=ingresos_mes,
                         title='Dashboard de Reportes')

@reportes_bp.route('/consultas')
@login_required
def reporte_consultas():
    """Reporte de consultas"""
    
    # Fechas por defecto: último mes
    fecha_fin = date.today()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    return render_template('reportes/consultas.html',
                         fecha_inicio=fecha_inicio,
                         fecha_fin=fecha_fin,
                         title='Reporte de Consultas')

@reportes_bp.route('/api/consultas')
@login_required
def api_reporte_consultas():
    """API para datos de reporte de consultas"""
    
    fecha_inicio_str = request.args.get('fecha_inicio')
    fecha_fin_str = request.args.get('fecha_fin')
    medico_id = request.args.get('medico_id', type=int)
    
    # Parsear fechas
    try:
        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d')
        fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d')
    except:
        # Por defecto: último mes
        fecha_fin = datetime.today()
        fecha_inicio = fecha_fin - timedelta(days=30)
    
    # Ajustar fecha_fin para incluir todo el día
    fecha_fin = fecha_fin.replace(hour=23, minute=59, second=59)
    
    # Generar reporte
    report_generator = ReportGenerator()
    reporte = report_generator.generate_consultas_report(
        start_date=fecha_inicio,
        end_date=fecha_fin,
        medico_id=medico_id
    )
    
    return jsonify(reporte)

@reportes_bp.route('/pacientes')
@login_required
def reporte_pacientes():
    """Reporte de pacientes"""
    
    return render_template('reportes/pacientes.html',
                         title='Reporte de Pacientes')

@reportes_bp.route('/api/pacientes')
@login_required
def api_reporte_pacientes():
    """API para datos de reporte de pacientes"""
    
    report_generator = ReportGenerator()
    reporte = report_generator.generate_pacientes_report()
    
    return jsonify(reporte)

@reportes_bp.route('/citas')
@login_required
def reporte_citas():
    """Reporte de citas"""
    
    # Fechas por defecto: último mes
    fecha_fin = date.today()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    return render_template('reportes/citas.html',
                         fecha_inicio=fecha_inicio,
                         fecha_fin=fecha_fin,
                         title='Reporte de Citas')

@reportes_bp.route('/api/citas')
@login_required
def api_reporte_citas():
    """API para datos de reporte de citas"""
    
    fecha_inicio_str = request.args.get('fecha_inicio')
    fecha_fin_str = request.args.get('fecha_fin')
    
    try:
        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d')
        fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d')
    except:
        fecha_fin = datetime.today()
        fecha_inicio = fecha_fin - timedelta(days=30)
    
    # Ajustar fecha_fin
    fecha_fin = fecha_fin.replace(hour=23, minute=59, second=59)
    
    report_generator = ReportGenerator()
    reporte = report_generator.generate_citas_report(
        start_date=fecha_inicio,
        end_date=fecha_fin
    )
    
    return jsonify(reporte)

@reportes_bp.route('/laboratorio')
@login_required
def reporte_laboratorio():
    """Reporte de laboratorio"""
    
    # Fechas por defecto: último mes
    fecha_fin = date.today()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    return render_template('reportes/laboratorio.html',
                         fecha_inicio=fecha_inicio,
                         fecha_fin=fecha_fin,
                         title='Reporte de Laboratorio')

@reportes_bp.route('/api/laboratorio')
@login_required
def api_reporte_laboratorio():
    """API para datos de reporte de laboratorio"""
    
    fecha_inicio_str = request.args.get('fecha_inicio')
    fecha_fin_str = request.args.get('fecha_fin')
    
    try:
        fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d')
        fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d')
    except:
        fecha_fin = datetime.today()
        fecha_inicio = fecha_fin - timedelta(days=30)
    
    fecha_fin = fecha_fin.replace(hour=23, minute=59, second=59)
    
    report_generator = ReportGenerator()
    reporte = report_generator.generate_laboratorio_report(
        start_date=fecha_inicio,
        end_date=fecha_fin
    )
    
    return jsonify(reporte)

@reportes_bp.route('/generar-pdf')
@login_required
def generar_pdf():
    """Generar reporte en PDF"""
    
    tipo = request.args.get('tipo')
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    
    try:
        fecha_ini = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fecha_f = datetime.strptime(fecha_fin, '%Y-%m-%d')
    except:
        fecha_f = datetime.today()
        fecha_ini = fecha_f - timedelta(days=30)
    
    report_generator = ReportGenerator()
    
    if tipo == 'consultas':
        datos = report_generator.generate_consultas_report(fecha_ini, fecha_f)
        titulo = f'Reporte de Consultas {fecha_ini.strftime("%d/%m/%Y")} - {fecha_f.strftime("%d/%m/%Y")}'
    elif tipo == 'citas':
        datos = report_generator.generate_citas_report(fecha_ini, fecha_f)
        titulo = f'Reporte de Citas {fecha_ini.strftime("%d/%m/%Y")} - {fecha_f.strftime("%d/%m/%Y")}'
    elif tipo == 'laboratorio':
        datos = report_generator.generate_laboratorio_report(fecha_ini, fecha_f)
        titulo = f'Reporte de Laboratorio {fecha_ini.strftime("%d/%m/%Y")} - {fecha_f.strftime("%d/%m/%Y")}'
    else:
        datos = report_generator.generate_pacientes_report()
        titulo = 'Reporte de Pacientes'
    
    # Agregar metadatos
    datos['titulo'] = titulo
    datos['fecha_generacion'] = datetime.now().strftime('%d/%m/%Y %H:%M')
    datos['generado_por'] = current_user.nombre_completo
    
    # Generar PDF
    pdf_data = report_generator.generate_pdf_report(datos)
    
    from flask import send_file
    return send_file(
        BytesIO(pdf_data),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'reporte_{tipo}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    )

@reportes_bp.route('/graficos')
@login_required
def graficos():
    """Página de gráficos"""
    
    return render_template('reportes/graficos.html',
                         title='Gráficos Estadísticos')

@reportes_bp.route('/api/graficos/consultas-mensuales')
@login_required
def api_graficos_consultas_mensuales():
    """API para gráfico de consultas mensuales"""
    
    año = request.args.get('año', datetime.now().year, type=int)
    
    consultas_mensuales = db.session.query(
        db.func.extract('month', Consulta.fecha_consulta).label('mes'),
        db.func.count(Consulta.id).label('total')
    ).filter(
        db.func.extract('year', Consulta.fecha_consulta) == año
    ).group_by('mes').order_by('mes').all()
    
    # Completar meses sin consultas
    datos = []
    for mes in range(1, 13):
        total = next((c.total for c in consultas_mensuales if c.mes == mes), 0)
        datos.append({
            'mes': f'{mes:02d}/{año}',
            'total': total
        })
    
    return jsonify(datos)

@reportes_bp.route('/api/graficos/pacientes-edad')
@login_required
def api_graficos_pacientes_edad():
    """API para gráfico de pacientes por edad"""
    
    grupos = [
        (0, 12, '0-12'),
        (13, 19, '13-19'),
        (20, 39, '20-39'),
        (40, 59, '40-59'),
        (60, 120, '60+')
    ]
    
    datos = []
    for min_edad, max_edad, etiqueta in grupos:
        count = Paciente.query.filter(
            db.func.extract('year', db.func.age(Paciente.fecha_nacimiento)).between(min_edad, max_edad),
            Paciente.activo == True
        ).count()
        
        datos.append({
            'grupo': etiqueta,
            'total': count
        })
    
    return jsonify(datos)

@reportes_bp.route('/api/graficos/citas-estado')
@login_required
def api_graficos_citas_estado():
    """API para gráfico de citas por estado"""
    
    # Último mes
    fecha_inicio = datetime.now() - timedelta(days=30)
    
    citas_por_estado = db.session.query(
        Cita.estado,
        db.func.count(Cita.id).label('total')
    ).filter(
        Cita.fecha_cita >= fecha_inicio
    ).group_by(Cita.estado).all()
    
    datos = [{
        'estado': estado.value,
        'total': total
    } for estado, total in citas_por_estado]
    
    return jsonify(datos)

@reportes_bp.route('/exportar-excel')
@login_required
def exportar_excel():
    """Exportar datos a Excel"""
    
    tipo = request.args.get('tipo')
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    
    try:
        fecha_ini = datetime.strptime(fecha_inicio, '%Y-%m-%d')
        fecha_f = datetime.strptime(fecha_fin, '%Y-%m-%d')
    except:
        fecha_f = datetime.today()
        fecha_ini = fecha_f - timedelta(days=30)
    
    report_generator = ReportGenerator()
    
    if tipo == 'consultas':
        datos = report_generator.generate_consultas_report(fecha_ini, fecha_f)
        # Convertir a DataFrame para Excel
        import pandas as pd
        
        # Crear DataFrame de consultas por día
        df = pd.DataFrame(datos['consultas_por_dia'])
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Consultas por Día', index=False)
            
            # Agregar hojas adicionales
            df_medicos = pd.DataFrame(datos['consultas_por_medico'])
            df_medicos.to_excel(writer, sheet_name='Por Médico', index=False)
            
            df_diagnosticos = pd.DataFrame(datos['diagnosticos_comunes'])
            df_diagnosticos.to_excel(writer, sheet_name='Diagnósticos', index=False)
        
        nombre_archivo = f'consultas_{fecha_ini.strftime("%Y%m%d")}_{fecha_f.strftime("%Y%m%d")}.xlsx'
        
    else:
        # Otros tipos de exportación
        output = BytesIO()
        nombre_archivo = f'reporte_{tipo}_{datetime.now().strftime("%Y%m%d")}.xlsx'
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=nombre_archivo
    )