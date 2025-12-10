from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import enum

class RolUsuario(enum.Enum):
    ADMINISTRADOR = 'administrador'
    MEDICO = 'medico'
    ENFERMERO = 'enfermero'
    LABORATORIO = 'laboratorio'
    RECEPCION = 'recepcion'
    FARMACIA = 'farmacia'

class Sexo(enum.Enum):
    MASCULINO = 'masculino'
    FEMENINO = 'femenino'
    OTRO = 'otro'

class EstadoCivil(enum.Enum):
    SOLTERO = 'soltero'
    CASADO = 'casado'
    DIVORCIADO = 'divorciado'
    VIUDO = 'viudo'
    UNION_LIBRE = 'union_libre'

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    cedula = db.Column(db.String(11), unique=True)
    telefono = db.Column(db.String(15))
    direccion = db.Column(db.String(200))
    fecha_nacimiento = db.Column(db.Date)
    sexo = db.Column(db.Enum(Sexo))
    rol = db.Column(db.Enum(RolUsuario), nullable=False, default=RolUsuario.MEDICO)
    especialidad = db.Column(db.String(100))
    numero_colegiado = db.Column(db.String(50))
    fecha_contratacion = db.Column(db.Date, default=date.today)
    salario = db.Column(db.Float, default=0.0)
    activo = db.Column(db.Boolean, default=True)
    foto = db.Column(db.String(200))
    ultimo_acceso = db.Column(db.DateTime)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    consultas = db.relationship('Consulta', backref='medico', lazy='dynamic')
    citas = db.relationship('Cita', backref='medico', lazy='dynamic')
    prescripciones = db.relationship('Prescripcion', backref='medico', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellidos}"
    
    @property
    def edad(self):
        if self.fecha_nacimiento:
            today = date.today()
            return today.year - self.fecha_nacimiento.year - (
                (today.month, today.day) < 
                (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
            )
        return None
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'nombre_completo': self.nombre_completo,
            'cedula': self.cedula,
            'telefono': self.telefono,
            'rol': self.rol.value,
            'especialidad': self.especialidad,
            'activo': self.activo,
            'edad': self.edad
        }
    
    def __repr__(self):
        return f'<Usuario {self.username}>'

class Paciente(db.Model):
    __tablename__ = 'pacientes'
    
    id = db.Column(db.Integer, primary_key=True)
    cedula = db.Column(db.String(11), unique=True, nullable=False, index=True)
    nombre = db.Column(db.String(100), nullable=False)
    apellidos = db.Column(db.String(100), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    sexo = db.Column(db.Enum(Sexo), nullable=False)
    estado_civil = db.Column(db.Enum(EstadoCivil))
    direccion = db.Column(db.String(200))
    telefono = db.Column(db.String(15))
    telefono_emergencia = db.Column(db.String(15))
    email = db.Column(db.String(120))
    ocupacion = db.Column(db.String(100))
    lugar_trabajo = db.Column(db.String(200))
    grupo_sanguineo = db.Column(db.String(5))
    rh_factor = db.Column(db.String(3))  # +, -, nulo
    alergias = db.Column(db.Text)
    enfermedades_cronicas = db.Column(db.Text)
    medicamentos_actuales = db.Column(db.Text)
    antecedentes_familiares = db.Column(db.Text)
    antecedentes_personales = db.Column(db.Text)
    habitos = db.Column(db.Text)  # tabaco, alcohol, drogas, etc.
    contacto_emergencia_nombre = db.Column(db.String(100))
    contacto_emergencia_parentesco = db.Column(db.String(50))
    contacto_emergencia_telefono = db.Column(db.String(15))
    notas = db.Column(db.Text)
    activo = db.Column(db.Boolean, default=True)
    foto = db.Column(db.String(200))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    consultas = db.relationship('Consulta', backref='paciente', lazy='dynamic', cascade='all, delete-orphan')
    citas = db.relationship('Cita', backref='paciente', lazy='dynamic', cascade='all, delete-orphan')
    solicitudes_lab = db.relationship('SolicitudLaboratorio', backref='paciente', lazy='dynamic')
    facturas = db.relationship('Factura', backref='paciente', lazy='dynamic')
    
    @property
    def nombre_completo(self):
        return f"{self.nombre} {self.apellidos}"
    
    @property
    def edad(self):
        today = date.today()
        return today.year - self.fecha_nacimiento.year - (
            (today.month, today.day) < 
            (self.fecha_nacimiento.month, self.fecha_nacimiento.day)
        )
    
    @property
    def edad_meses(self):
        today = date.today()
        meses = (today.year - self.fecha_nacimiento.year) * 12
        meses += today.month - self.fecha_nacimiento.month
        if today.day < self.fecha_nacimiento.day:
            meses -= 1
        return meses
    
    def to_dict(self):
        return {
            'id': self.id,
            'cedula': self.cedula,
            'nombre_completo': self.nombre_completo,
            'edad': self.edad,
            'sexo': self.sexo.value,
            'telefono': self.telefono,
            'email': self.email,
            'grupo_sanguineo': f"{self.grupo_sanguineo}{self.rh_factor}" if self.grupo_sanguineo else None,
            'activo': self.activo,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None
        }
    
    def __repr__(self):
        return f'<Paciente {self.cedula}>'

class Consulta(db.Model):
    __tablename__ = 'consultas'
    
    id = db.Column(db.Integer, primary_key=True)
    codigo_consulta = db.Column(db.String(20), unique=True, nullable=False)
    paciente_id = db.Column(db.Integer, db.ForeignKey('pacientes.id'), nullable=False)
    medico_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    fecha_consulta = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    motivo_consulta = db.Column(db.Text, nullable=False)
    sintomas = db.Column(db.Text)
    historia_enfermedad_actual = db.Column(db.Text)
    examen_fisico_id = db.Column(db.Integer, db.ForeignKey('examenes_fisicos.id'))
    diagnostico_principal = db.Column(db.String(200))
    diagnosticos_secundarios = db.Column(db.Text)
    cie10_codigo = db.Column(db.String(10))  # Código CIE-10
    tratamiento = db.Column(db.Text)
    recomendaciones = db.Column(db.Text)
    notas_medicas = db.Column(db.Text)
    proxima_cita = db.Column(db.Date)
    peso = db.Column(db.Float)  # kg
    altura = db.Column(db.Float)  # cm
    imc = db.Column(db.Float)
    estado = db.Column(db.String(20), default='completada')  # pendiente, completada, cancelada
    creado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    examen_fisico = db.relationship('ExamenFisico', backref='consulta', uselist=False)
    prescripciones = db.relationship('Prescripcion', backref='consulta', lazy='dynamic')
    examenes_solicitados = db.relationship('SolicitudLaboratorio', backref='consulta', lazy='dynamic')
    creador = db.relationship('Usuario', foreign_keys=[creado_por])
    
    def to_dict(self):
        return {
            'id': self.id,
            'codigo_consulta': self.codigo_consulta,
            'paciente': self.paciente.to_dict() if self.paciente else None,
            'medico': self.medico.to_dict() if self.medico else None,
            'fecha_consulta': self.fecha_consulta.isoformat() if self.fecha_consulta else None,
            'motivo_consulta': self.motivo_consulta,
            'diagnostico_principal': self.diagnostico_principal,
            'tratamiento': self.tratamiento,
            'proxima_cita': self.proxima_cita.isoformat() if self.proxima_cita else None,
            'estado': self.estado,
            'peso': self.peso,
            'altura': self.altura,
            'imc': self.imc
        }
    
    def __repr__(self):
        return f'<Consulta {self.codigo_consulta}>'

class ExamenFisico(db.Model):
    __tablename__ = 'examenes_fisicos'
    
    id = db.Column(db.Integer, primary_key=True)
    signos_vitales = db.Column(db.Text)  # JSON de signos vitales
    cabeza = db.Column(db.Text)
    cuello = db.Column(db.Text)
    torax = db.Column(db.Text)
    abdomen = db.Column(db.Text)
    extremidades = db.Column(db.Text)
    sistema_nervioso = db.Column(db.Text)
    piel = db.Column(db.Text)
    otros = db.Column(db.Text)
    notas = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'signos_vitales': json.loads(self.signos_vitales) if self.signos_vitales else {},
            'cabeza': self.cabeza,
            'cuello': self.cuello,
            'torax': self.torax,
            'abdomen': self.abdomen,
            'extremidades': self.extremidades,
            'sistema_nervioso': self.sistema_nervioso,
            'piel': self.piel,
            'otros': self.otros,
            'notas': self.notas
        }

class Prescripcion(db.Model):
    __tablename__ = 'prescripciones'
    
    id = db.Column(db.Integer, primary_key=True)
    consulta_id = db.Column(db.Integer, db.ForeignKey('consultas.id'), nullable=False)
    medico_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    medicamento = db.Column(db.String(200), nullable=False)
    dosis = db.Column(db.String(100))
    frecuencia = db.Column(db.String(100))
    duracion = db.Column(db.String(100))
    via_administracion = db.Column(db.String(50))
    indicaciones = db.Column(db.Text)
    fecha_inicio = db.Column(db.Date)
    fecha_fin = db.Column(db.Date)
    estado = db.Column(db.String(20), default='activa')  # activa, completada, cancelada
    creado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    creador = db.relationship('Usuario', foreign_keys=[creado_por])
    
    def to_dict(self):
        return {
            'id': self.id,
            'medicamento': self.medicamento,
            'dosis': self.dosis,
            'frecuencia': self.frecuencia,
            'duracion': self.duracion,
            'via_administracion': self.via_administracion,
            'indicaciones': self.indicaciones,
            'fecha_inicio': self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            'fecha_fin': self.fecha_fin.isoformat() if self.fecha_fin else None,
            'estado': self.estado
        }