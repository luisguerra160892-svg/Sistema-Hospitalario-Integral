# api_mobile.py
@app.route('/api/mobile/login', methods=['POST'])
def api_mobile_login():
    data = request.get_json()
    
    user = Usuario.query.filter_by(
        username=data.get('username'), 
        activo=True
    ).first()
    
    if user and user.check_password(data.get('password')):
        # Generar token JWT
        token = generate_jwt_token(user.id)
        
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': user.id,
                'nombre': user.nombre,
                'rol': user.rol,
                'especialidad': user.especialidad
            }
        })
    
    return jsonify({'success': False, 'error': 'Credenciales inválidas'}), 401

@app.route('/api/mobile/citas/hoy')
@jwt_required
def api_mobile_citas_hoy():
    user_id = get_jwt_identity()
    fecha = datetime.now().date()
    
    citas = Cita.query.filter(
        db.func.date(Cita.fecha_cita) == fecha,
        Cita.medico_id == user_id
    ).order_by(Cita.fecha_cita.asc()).all()
    
    return jsonify({
        'citas': [{
            'id': cita.id,
            'hora': cita.fecha_cita.strftime('%H:%M'),
            'paciente': f"{cita.paciente.nombre} {cita.paciente.apellidos}",
            'tipo_consulta': cita.tipo_consulta,
            'estado': cita.estado
        } for cita in citas]
    })

@app.route('/api/mobile/pacientes/<int:id>')
@jwt_required
def api_mobile_paciente(id):
    paciente = Paciente.query.get_or_404(id)
    
    return jsonify({
        'paciente': {
            'id': paciente.id,
            'nombre': f"{paciente.nombre} {paciente.apellidos}",
            'cedula': paciente.cedula,
            'edad': (date.today() - paciente.fecha_nacimiento).days // 365,
            'grupo_sanguineo': paciente.grupo_sanguineo,
            'alergias': paciente.alergias,
            'enfermedades_cronicas': paciente.enfermedades_cronicas
        },
        'ultimas_consultas': [{
            'fecha': consulta.fecha_consulta.strftime('%d/%m/%Y'),
            'diagnostico': consulta.diagnostico,
            'tratamiento': consulta.tratamiento
        } for consulta in paciente.consultas[:3]],
        'analisis_pendientes': [{
            'tipo': analisis.tipo_analisis,
            'fecha_solicitud': analisis.fecha_solicitud.strftime('%d/%m/%Y'),
            'estado': analisis.estado
        } for analisis in paciente.analisis if analisis.estado == 'pendiente']
    })

@app.route('/api/mobile/consultas/nueva', methods=['POST'])
@jwt_required
def api_mobile_nueva_consulta():
    data = request.get_json()
    user_id = get_jwt_identity()
    
    try:
        consulta = Consulta(
            paciente_id=data['paciente_id'],
            medico_id=user_id,
            motivo_consulta=data['motivo_consulta'],
            sintomas=data.get('sintomas', ''),
            diagnostico=data.get('diagnostico', ''),
            tratamiento=data.get('tratamiento', ''),
            prescripciones=data.get('prescripciones', '')
        )
        
        db.session.add(consulta)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'consulta_id': consulta.id
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Funciones JWT
def generate_jwt_token(user_id):
    expiration = datetime.utcnow() + timedelta(days=30)
    token = jwt.encode({
        'user_id': user_id,
        'exp': expiration
    }, app.config['SECRET_KEY'], algorithm='HS256')
    
    return token

def jwt_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            kwargs['user_id'] = payload['user_id']
        except:
            return jsonify({'error': 'Token inválido'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def get_jwt_identity():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    return payload['user_id']