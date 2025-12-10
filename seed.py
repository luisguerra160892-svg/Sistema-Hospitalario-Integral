from app import db
from app.models.core import Usuario, Paciente, RolUsuario, Sexo
from app.models.laboratorio import Laboratorio, CategoriaAnalisis, TipoAnalisisLab
from app.models.citas import ConfiguracionCitas
from datetime import datetime, date
import random

def seed_database():
    """Poblar la base de datos con datos iniciales"""
    
    # Crear usuario admin si no existe
    if not Usuario.query.filter_by(username='admin').first():
        admin = Usuario(
            username='admin',
            email='admin@hospital.cu',
            nombre='Administrador',
            apellidos='del Sistema',
            rol=RolUsuario.ADMINISTRADOR,
            cedula='00000000000',
            telefono='+53712345678',
            fecha_nacimiento=date(1980, 1, 1),
            sexo=Sexo.MASCULINO
        )
        admin.set_password('admin123')
        db.session.add(admin)
        print("✅ Usuario admin creado")
    
    # Crear médicos de ejemplo
    if not Usuario.query.filter_by(rol=RolUsuario.MEDICO).first():
        medicos = [
            {
                'username': 'dr.perez',
                'email': 'dr.perez@hospital.cu',
                'nombre': 'Juan',
                'apellidos': 'Pérez Rodríguez',
                'especialidad': 'Medicina General',
                'cedula': '11111111111',
                'telefono': '+53711111111'
            },
            {
                'username': 'dra.lopez',
                'email': 'dra.lopez@hospital.cu',
                'nombre': 'María',
                'apellidos': 'López García',
                'especialidad': 'Pediatría',
                'cedula': '22222222222',
                'telefono': '+53722222222'
            },
            {
                'username': 'dr.gonzalez',
                'email': 'dr.gonzalez@hospital.cu',
                'nombre': 'Carlos',
                'apellidos': 'González Martínez',
                'especialidad': 'Cardiología',
                'cedula': '33333333333',
                'telefono': '+53733333333'
            }
        ]
        
        for i, data in enumerate(medicos):
            medico = Usuario(
                username=data['username'],
                email=data['email'],
                nombre=data['nombre'],
                apellidos=data['apellidos'],
                rol=RolUsuario.MEDICO,
                especialidad=data['especialidad'],
                cedula=data['cedula'],
                telefono=data['telefono'],
                fecha_nacimiento=date(1980 + i, 1, 1),
                sexo=Sexo.MASCULINO if i % 2 == 0 else Sexo.FEMENINO
            )
            medico.set_password('medico123')
            db.session.add(medico)
        
        print("✅ Médicos de ejemplo creados")
    
    # Crear laboratorio central
    if not Laboratorio.query.first():
        lab = Laboratorio(
            nombre='Laboratorio Central del Hospital',
            codigo='LAB-CENTRAL',
            direccion='Calle Principal #123, Ciudad',
            telefono='+53744444444',
            email='laboratorio@hospital.cu',
            contacto='Dr. Roberto Hernández',
            horario_atencion='Lunes a Viernes: 7:00 AM - 5:00 PM',
            servicios='Análisis clínicos, Microbiología, Hematología'
        )
        db.session.add(lab)
        print("✅ Laboratorio creado")
    
    # Crear categorías de análisis
    if not CategoriaAnalisis.query.first():
        categorias = [
            ('Hematología', 'HEMA', 'Estudios de sangre y células sanguíneas', '#dc3545'),
            ('Bioquímica', 'BIOQ', 'Química sanguínea y metabólica', '#28a745'),
            ('Microbiología', 'MICRO', 'Estudios microbiológicos y cultivos', '#007bff'),
            ('Inmunología', 'INMUNO', 'Pruebas inmunológicas y serológicas', '#ffc107'),
            ('Hormonas', 'HORM', 'Estudios hormonales y endocrinos', '#6f42c1'),
            ('Orina', 'ORINA', 'Análisis de orina y sedimento', '#17a2b8')
        ]
        
        for nombre, codigo, descripcion, color in categorias:
            cat = CategoriaAnalisis(
                nombre=nombre,
                codigo=codigo,
                descripcion=descripcion,
                color=color,
                icono='bi-droplet'
            )
            db.session.add(cat)
        
        print("✅ Categorías de análisis creadas")
    
    # Crear tipos de análisis comunes
    if not TipoAnalisisLab.query.first():
        tipos = [
            ('Hemograma completo', 'HEMO-001', 'Conteo sanguíneo completo', 1, 1500.00, 2),
            ('Glucosa en ayunas', 'GLU-001', 'Nivel de glucosa en sangre', 2, 800.00, 1),
            ('Perfil lipídico', 'LIP-001', 'Colesterol y triglicéridos', 2, 2500.00, 3),
            ('Urocultivo', 'URO-001', 'Cultivo de orina', 3, 1800.00, 5),
            ('HIV Elisa', 'HIV-001', 'Prueba de VIH', 4, 3000.00, 2),
            ('TSH', 'TSH-001', 'Hormona estimulante de tiroides', 5, 1200.00, 3),
            ('Examen general de orina', 'EGO-001', 'Análisis completo de orina', 6, 900.00, 1)
        ]
        
        for nombre, codigo, descripcion, categoria_id, precio, tiempo in tipos:
            tipo = TipoAnalisisLab(
                nombre=nombre,
                codigo=codigo,
                descripcion=descripcion,
                categoria_id=categoria_id,
                precio=precio,
                tiempo_entrega=tiempo,
                muestra_tipo='Sangre' if categoria_id in [1, 2, 4, 5] else 'Orina',
                requiere_ayuno=categoria_id in [2, 3],
                activo=True
            )
            db.session.add(tipo)
        
        print("✅ Tipos de análisis creados")
    
    # Configuración del sistema
    if not ConfiguracionCitas.query.first():
        configs = [
            ('duracion_cita_default', '30', 'Duración predeterminada de citas (minutos)'),
            ('hora_inicio_atencion', '08:00', 'Hora de inicio de atención'),
            ('hora_fin_atencion', '17:00', 'Hora de fin de atención'),
            ('max_citas_dia_medico', '20', 'Máximo de citas por médico al día'),
            ('dias_anticipacion_cita', '30', 'Días máximos de anticipación para citas'),
            ('recordatorio_horas_antes', '24', 'Horas antes para enviar recordatorio'),
            ('cancelacion_horas_minimo', '2', 'Horas mínimas para cancelar cita')
        ]
        
        for clave, valor, descripcion in configs:
            config = ConfiguracionCitas(
                clave=clave,
                valor=valor,
                descripcion=descripcion,
                categoria='citas'
            )
            db.session.add(config)
        
        print("✅ Configuración del sistema creada")
    
    # Crear pacientes de ejemplo (solo en desarrollo)
    if app.config.get('ENV') == 'development' and Paciente.query.count() < 10:
        from faker import Faker
        fake = Faker('es_ES')
        
        for _ in range(20):
            sexo = random.choice([Sexo.MASCULINO, Sexo.FEMENINO])
            fecha_nacimiento = fake.date_of_birth(minimum_age=18, maximum_age=90)
            
            paciente = Paciente(
                cedula=fake.unique.numerify('###########'),
                nombre=fake.first_name_male() if sexo == Sexo.MASCULINO else fake.first_name_female(),
                apellidos=fake.last_name() + ' ' + fake.last_name(),
                fecha_nacimiento=fecha_nacimiento,
                sexo=sexo,
                telefono=fake.phone_number(),
                email=fake.email(),
                direccion=fake.address(),
                grupo_sanguineo=random.choice(['A', 'B', 'AB', 'O']),
                rh_factor=random.choice(['+', '-']),
                alergias=random.choice(['Ninguna', 'Penicilina', 'Ácaros', 'Polen', 'Mariscos']),
                enfermedades_cronicas=random.choice(['Ninguna', 'Hipertensión', 'Diabetes', 'Asma', 'Artritis'])
            )
            db.session.add(paciente)
        
        print("✅ Pacientes de ejemplo creados")
    
    db.session.commit()