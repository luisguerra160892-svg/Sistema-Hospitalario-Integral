from flask_mail import Message
from app import mail, app
from threading import Thread

def send_async_email(app, msg):
    """Enviar email en segundo plano"""
    with app.app_context():
        mail.send(msg)

def send_email(subject, recipients, text_body, html_body=None):
    """Enviar email"""
    msg = Message(
        subject=subject,
        recipients=recipients,
        sender=app.config['MAIL_DEFAULT_SENDER']
    )
    msg.body = text_body
    if html_body:
        msg.html = html_body
    
    # Enviar en segundo plano
    Thread(target=send_async_email, args=(app, msg)).start()

def send_password_reset_email(user, token):
    """Enviar email para restablecer contraseña"""
    reset_url = f"{app.config['APP_URL']}/reset-password/{token}"
    
    subject = "Restablecer contraseña - Sistema Hospitalario"
    
    text_body = f"""Para restablecer tu contraseña, visita el siguiente enlace:
{reset_url}

Si no solicitaste restablecer tu contraseña, ignora este mensaje.

Este enlace expira en 24 horas."""

    html_body = f"""
    <h3>Restablecer contraseña</h3>
    <p>Para restablecer tu contraseña, haz clic en el siguiente enlace:</p>
    <p><a href="{reset_url}">{reset_url}</a></p>
    <p>Si no solicitaste restablecer tu contraseña, ignora este mensaje.</p>
    <p><em>Este enlace expira en 24 horas.</em></p>
    """
    
    send_email(subject, [user.email], text_body, html_body)

def send_appointment_confirmation(cita):
    """Enviar confirmación de cita"""
    subject = f"Confirmación de cita - {cita.codigo_cita}"
    
    text_body = f"""Su cita ha sido programada:

Fecha: {cita.fecha_cita.strftime('%d/%m/%Y')}
Hora: {cita.fecha_cita.strftime('%H:%M')}
Médico: {cita.medico.nombre_completo}
Tipo: {cita.tipo_consulta.value}

Por favor llegue 15 minutos antes.

Para cancelar o reprogramar, contacte al hospital."""

    html_body = f"""
    <h3>Confirmación de cita</h3>
    <p>Su cita ha sido programada:</p>
    <ul>
        <li><strong>Código:</strong> {cita.codigo_cita}</li>
        <li><strong>Fecha:</strong> {cita.fecha_cita.strftime('%d/%m/%Y')}</li>
        <li><strong>Hora:</strong> {cita.fecha_cita.strftime('%H:%M')}</li>
        <li><strong>Médico:</strong> {cita.medico.nombre_completo}</li>
        <li><strong>Tipo:</strong> {cita.tipo_consulta.value}</li>
    </ul>
    <p><em>Por favor llegue 15 minutos antes.</em></p>
    <p>Para cancelar o reprogramar, contacte al hospital.</p>
    """
    
    if cita.paciente.email:
        send_email(subject, [cita.paciente.email], text_body, html_body)

def send_appointment_reminder(cita):
    """Enviar recordatorio de cita"""
    subject = f"Recordatorio de cita - {cita.codigo_cita}"
    
    text_body = f"""Recordatorio de su cita programada para mañana:

Fecha: {cita.fecha_cita.strftime('%d/%m/%Y')}
Hora: {cita.fecha_cita.strftime('%H:%M')}
Médico: {cita.medico.nombre_completo}
Sala: {cita.sala or 'Por confirmar'}

Por favor confirme su asistencia."""

    html_body = f"""
    <h3>Recordatorio de cita</h3>
    <p>Recordatorio de su cita programada para mañana:</p>
    <ul>
        <li><strong>Código:</strong> {cita.codigo_cita}</li>
        <li><strong>Fecha:</strong> {cita.fecha_cita.strftime('%d/%m/%Y')}</li>
        <li><strong>Hora:</strong> {cita.fecha_cita.strftime('%H:%M')}</li>
        <li><strong>Médico:</strong> {cita.medico.nombre_completo}</li>
        <li><strong>Sala:</strong> {cita.sala or 'Por confirmar'}</li>
    </ul>
    <p><em>Por favor confirme su asistencia.</em></p>
    """
    
    if cita.paciente.email:
        send_email(subject, [cita.paciente.email], text_body, html_body)
    
    # También enviar SMS si está configurado
    send_appointment_sms(cita)

def send_appointment_sms(cita):
    """Enviar SMS de recordatorio (implementación básica)"""
    # Aquí integrarías con un servicio de SMS como Twilio
    pass

def send_lab_results_ready(solicitud):
    """Notificar que resultados de laboratorio están listos"""
    subject = f"Resultados de laboratorio listos - {solicitud.codigo_solicitud}"
    
    text_body = f"""Sus resultados de laboratorio están disponibles:

Código: {solicitud.colicitud.codigo_solicitud}
Fecha: {solicitud.fecha_solicitud.strftime('%d/%m/%Y')}
Paciente: {solicitud.paciente.nombre_completo}

Puede recogerlos en el laboratorio o acceder a través del portal."""

    html_body = f"""
    <h3>Resultados de laboratorio listos</h3>
    <p>Sus resultados de laboratorio están disponibles:</p>
    <ul>
        <li><strong>Código:</strong> {solicitud.codigo_solicitud}</li>
        <li><strong>Fecha:</strong> {solicitud.fecha_solicitud.strftime('%d/%m/%Y')}</li>
        <li><strong>Paciente:</strong> {solicitud.paciente.nombre_completo}</li>
    </ul>
    <p>Puede recogerlos en el laboratorio o acceder a través del portal.</p>
    """
    
    if solicitud.paciente.email:
        send_email(subject, [solicitud.paciente.email], text_body, html_body)