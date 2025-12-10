import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from io import BytesIO
import base64
from flask import render_template
from app import db
from app.models import *
from sqlalchemy import func, extract, case, and_, or_

class ReportGenerator:
    
    @staticmethod
    def generate_consultas_report(start_date, end_date, medico_id=None):
        """Genera reporte de consultas"""
        query = Consulta.query.filter(
            Consulta.fecha_consulta.between(start_date, end_date)
        )
        
        if medico_id:
            query = query.filter_by(medico_id=medico_id)
        
        consultas = query.all()
        
        # Estadísticas básicas
        total_consultas = len(consultas)
        medicos_count = len(set(c.medico_id for c in consultas))
        pacientes_count = len(set(c.paciente_id for c in consultas))
        
        # Consultas por médico
        consultas_por_medico = db.session.query(
            Usuario.nombre_completo,
            func.count(Consulta.id).label('total')
        ).join(Consulta, Usuario.id == Consulta.medico_id)\
         .filter(Consulta.fecha_consulta.between(start_date, end_date))\
         .group_by(Usuario.id, Usuario.nombre_completo)\
         .order_by(func.count(Consulta.id).desc()).all()
        
        # Consultas por día
        consultas_por_dia = db.session.query(
            func.date(Consulta.fecha_consulta).label('fecha'),
            func.count(Consulta.id).label('total')
        ).filter(Consulta.fecha_consulta.between(start_date, end_date))\
         .group_by(func.date(Consulta.fecha_consulta))\
         .order_by('fecha').all()
        
        # Diagnósticos más comunes
        diagnosticos_comunes = db.session.query(
            Consulta.diagnostico_principal,
            func.count(Consulta.id).label('total')
        ).filter(
            Consulta.fecha_consulta.between(start_date, end_date),
            Consulta.diagnostico_principal.isnot(None)
        ).group_by(Consulta.diagnostico_principal)\
         .order_by(func.count(Consulta.id).desc()).limit(10).all()
        
        return {
            'periodo': f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}",
            'total_consultas': total_consultas,
            'medicos_count': medicos_count,
            'pacientes_count': pacientes_count,
            'consultas_por_medico': [
                {'medico': medico, 'total': total} 
                for medico, total in consultas_por_medico
            ],
            'consultas_por_dia': [
                {'fecha': fecha.strftime('%d/%m/%Y'), 'total': total}
                for fecha, total in consultas_por_dia
            ],
            'diagnosticos_comunes': [
                {'diagnostico': diag, 'total': total}
                for diag, total in diagnosticos_comunes
            ]
        }
    
    @staticmethod
    def generate_pacientes_report():
        """Genera reporte de pacientes"""
        total_pacientes = Paciente.query.count()
        pacientes_activos = Paciente.query.filter_by(activo=True).count()
        
        # Por sexo
        pacientes_por_sexo = db.session.query(
            Paciente.sexo,
            func.count(Paciente.id).label('total')
        ).group_by(Paciente.sexo).all()
        
        # Por grupo etario
        grupos_etarios = [
            (0, 12, 'Niños (0-12)'),
            (13, 19, 'Adolescentes (13-19)'),
            (20, 39, 'Jóvenes (20-39)'),
            (40, 59, 'Adultos (40-59)'),
            (60, 120, 'Adultos Mayores (60+)')
        ]
        
        pacientes_por_edad = []
        for min_edad, max_edad, label in grupos_etarios:
            count = Paciente.query.filter(
                extract('year', func.age(Paciente.fecha_nacimiento)).between(min_edad, max_edad)
            ).count()
            pacientes_por_edad.append({'grupo': label, 'total': count})
        
        # Nuevos pacientes por mes (últimos 12 meses)
        doce_meses_atras = datetime.now() - timedelta(days=365)
        nuevos_por_mes = db.session.query(
            extract('year', Paciente.fecha_registro).label('año'),
            extract('month', Paciente.fecha_registro).label('mes'),
            func.count(Paciente.id).label('total')
        ).filter(Paciente.fecha_registro >= doce_meses_atras)\
         .group_by('año', 'mes')\
         .order_by('año', 'mes').all()
        
        return {
            'total_pacientes': total_pacientes,
            'pacientes_activos': pacientes_activos,
            'pacientes_inactivos': total_pacientes - pacientes_activos,
            'pacientes_por_sexo': [
                {'sexo': sexo.value if sexo else 'No especificado', 'total': total}
                for sexo, total in pacientes_por_sexo
            ],
            'pacientes_por_edad': pacientes_por_edad,
            'nuevos_por_mes': [
                {'periodo': f"{int(mes):02d}/{int(año)}", 'total': total}
                for año, mes, total in nuevos_por_mes
            ]
        }
    
    @staticmethod
    def generate_citas_report(start_date, end_date):
        """Genera reporte de citas"""
        citas = Cita.query.filter(
            Cita.fecha_cita.between(start_date, end_date)
        ).all()
        
        total_citas = len(citas)
        
        # Por estado
        citas_por_estado = db.session.query(
            Cita.estado,
            func.count(Cita.id).label('total')
        ).filter(Cita.fecha_cita.between(start_date, end_date))\
         .group_by(Cita.estado).all()
        
        # Por médico
        citas_por_medico = db.session.query(
            Usuario.nombre_completo,
            func.count(Cita.id).label('total')
        ).join(Cita, Usuario.id == Cita.medico_id)\
         .filter(Cita.fecha_cita.between(start_date, end_date))\
         .group_by(Usuario.id, Usuario.nombre_completo)\
         .order_by(func.count(Cita.id).desc()).all()
        
        # Tasa de no presentación
        citas_no_presentadas = db.session.query(
            func.count(Cita.id)
        ).filter(
            Cita.fecha_cita.between(start_date, end_date),
            Cita.estado == EstadoCita.NO_PRESENTADO
        ).scalar() or 0
        
        tasa_no_presentacion = (citas_no_presentadas / total_citas * 100) if total_citas > 0 else 0
        
        # Horarios más solicitados
        citas_por_hora = db.session.query(
            extract('hour', Cita.fecha_cita).label('hora'),
            func.count(Cita.id).label('total')
        ).filter(Cita.fecha_cita.between(start_date, end_date))\
         .group_by('hora')\
         .order_by('hora').all()
        
        return {
            'total_citas': total_citas,
            'citas_por_estado': [
                {'estado': estado.value, 'total': total}
                for estado, total in citas_por_estado
            ],
            'citas_por_medico': [
                {'medico': medico, 'total': total}
                for medico, total in citas_por_medico
            ],
            'tasa_no_presentacion': round(tasa_no_presentacion, 2),
            'citas_no_presentadas': citas_no_presentadas,
            'citas_por_hora': [
                {'hora': f"{int(hora):02d}:00", 'total': total}
                for hora, total in citas_por_hora
            ]
        }
    
    @staticmethod
    def generate_laboratorio_report(start_date, end_date):
        """Genera reporte de laboratorio"""
        solicitudes = SolicitudLaboratorio.query.filter(
            SolicitudLaboratorio.fecha_solicitud.between(start_date, end_date)
        ).all()
        
        total_solicitudes = len(solicitudes)
        solicitudes_completadas = sum(1 for s in solicitudes if s.completada)
        
        # Por prioridad
        solicitudes_por_prioridad = db.session.query(
            SolicitudLaboratorio.prioridad,
            func.count(SolicitudLaboratorio.id).label('total')
        ).filter(SolicitudLaboratorio.fecha_solicitud.between(start_date, end_date))\
         .group_by(SolicitudLaboratorio.prioridad).all()
        
        # Por tipo de análisis
        analisis_mas_solicitados = db.session.query(
            TipoAnalisisLab.nombre,
            func.count(DetalleSolicitudLab.id).label('total')
        ).join(DetalleSolicitudLab, TipoAnalisisLab.id == DetalleSolicitudLab.tipo_analisis_id)\
         .join(SolicitudLaboratorio, DetalleSolicitudLab.solicitud_id == SolicitudLaboratorio.id)\
         .filter(SolicitudLaboratorio.fecha_solicitud.between(start_date, end_date))\
         .group_by(TipoAnalisisLab.id, TipoAnalisisLab.nombre)\
         .order_by(func.count(DetalleSolicitudLab.id).desc()).limit(10).all()
        
        # Tiempo promedio de respuesta
        tiempos_respuesta = []
        for solicitud in solicitudes:
            if solicitud.tiempo_respuesta:
                tiempos_respuesta.append(solicitud.tiempo_respuesta)
        
        tiempo_promedio = sum(tiempos_respuesta) / len(tiempos_respuesta) if tiempos_respuesta else 0
        
        return {
            'total_solicitudes': total_solicitudes,
            'solicitudes_completadas': solicitudes_completadas,
            'solicitudes_pendientes': total_solicitudes - solicitudes_completadas,
            'solicitudes_por_prioridad': [
                {'prioridad': prioridad.value, 'total': total}
                for prioridad, total in solicitudes_por_prioridad
            ],
            'analisis_mas_solicitados': [
                {'analisis': nombre, 'total': total}
                for nombre, total in analisis_mas_solicitados
            ],
            'tiempo_promedio_respuesta': round(tiempo_promedio, 2),
            'tasa_completitud': round((solicitudes_completadas / total_solicitudes * 100), 2) if total_solicitudes > 0 else 0
        }
    
    @staticmethod
    def generate_chart(data, chart_type='bar', title='', x_label='', y_label=''):
        """Genera gráfico a partir de datos"""
        plt.figure(figsize=(10, 6))
        
        if chart_type == 'bar':
            x = [item['label'] for item in data]
            y = [item['value'] for item in data]
            plt.bar(x, y)
        elif chart_type == 'line':
            x = [item['label'] for item in data]
            y = [item['value'] for item in data]
            plt.plot(x, y, marker='o')
        elif chart_type == 'pie':
            labels = [item['label'] for item in data]
            sizes = [item['value'] for item in data]
            plt.pie(sizes, labels=labels, autopct='%1.1f%%')
        
        plt.title(title)
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # Convertir a base64 para HTML
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"
    
    @staticmethod
    def generate_pdf_report(report_data, template='report_template.html'):
        """Genera reporte PDF"""
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        elements.append(Paragraph("Reporte Hospitalario", styles['Title']))
        elements.append(Spacer(1, 12))
        
        # Información del reporte
        elements.append(Paragraph(f"Periodo: {report_data.get('periodo', '')}", styles['Normal']))
        elements.append(Paragraph(f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        elements.append(Spacer(1, 24))
        
        # Estadísticas principales
        elements.append(Paragraph("Estadísticas Principales", styles['Heading2']))
        
        stats_data = []
        if 'total_consultas' in report_data:
            stats_data.append(['Total Consultas', str(report_data['total_consultas'])])
        if 'total_citas' in report_data:
            stats_data.append(['Total Citas', str(report_data['total_citas'])])
        if 'total_pacientes' in report_data:
            stats_data.append(['Total Pacientes', str(report_data['total_pacientes'])])
        
        if stats_data:
            table = Table(stats_data, colWidths=[3*inch, 1.5*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 14),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)
        
        elements.append(Spacer(1, 36))
        
        # Construir PDF
        doc.build(elements)
        buffer.seek(0)
        
        return buffer.getvalue()