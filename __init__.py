from .auth_forms import LoginForm, RegisterForm, ChangePasswordForm
from .paciente_forms import PacienteForm, SearchPacienteForm
from .consulta_forms import ConsultaForm, PrescripcionForm, ExamenFisicoForm
from .cita_forms import CitaForm, HorarioForm, BloqueoForm
from .laboratorio_forms import (
    SolicitudLaboratorioForm, ResultadoLabForm,
    TipoAnalisisForm, LaboratorioForm
)

__all__ = [
    'LoginForm', 'RegisterForm', 'ChangePasswordForm',
    'PacienteForm', 'SearchPacienteForm',
    'ConsultaForm', 'PrescripcionForm', 'ExamenFisicoForm',
    'CitaForm', 'HorarioForm', 'BloqueoForm',
    'SolicitudLaboratorioForm', 'ResultadoLabForm',
    'TipoAnalisisForm', 'LaboratorioForm'
]