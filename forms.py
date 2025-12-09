from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, TextAreaField, DateField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional
from models import User
from utils.password_utils import password_validator

class LoginForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember_me = BooleanField('Lembrar de mim')
    submit = SubmitField('Entrar')

class RegistrationForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired()])  # Removido Email() para usar validação customizada
    full_name = StringField('Nome Completo', validators=[DataRequired(), Length(min=2, max=120)])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrar')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Este nome de usuário já está em uso.')
    
    def validate_email(self, email):
        """Validação customizada de email que aceita domínios .local"""
        import re
        # Padrão mais flexível que aceita .local, .internal, .lan, etc.
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email.data):
            raise ValidationError('Email inválido')
        
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Este email já está registrado.')

class UserEditForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired()])  # Removido Email() para usar validação customizada
    full_name = StringField('Nome Completo', validators=[DataRequired(), Length(min=2, max=120)])
    role = SelectField('Função', choices=[('user', 'Usuário'), ('admin', 'Administrador')])
    is_active = BooleanField('Usuário Ativo')
    must_change_password = BooleanField('Exigir alteração de senha no próximo login')
    submit = SubmitField('Atualizar')
    
    def validate_email(self, email):
        """Validação customizada de email que aceita domínios .local"""
        import re
        # Padrão mais flexível que aceita .local, .internal, .lan, etc.
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email.data):
            raise ValidationError('Email inválido')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Senha Atual', validators=[DataRequired()])
    new_password = PasswordField('Nova Senha', validators=[DataRequired(), Length(min=8)])
    confirm_new_password = PasswordField('Confirmar Nova Senha', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Alterar Senha')
    
    def validate_new_password(self, field):
        """Valida os requisitos da nova senha"""
        is_valid, errors = password_validator.validate_password(field.data)
        if not is_valid:
            raise ValidationError('; '.join(errors))

class AdminUserForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired()])  # Removido Email() para usar validação customizada
    full_name = StringField('Nome Completo', validators=[DataRequired(), Length(min=2, max=120)])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=8)])
    must_change_password = BooleanField('Exigir alteração de senha no primeiro login')
    role = SelectField('Função', choices=[('user', 'Usuário'), ('admin', 'Administrador')])
    is_active = BooleanField('Usuário Ativo')
    submit = SubmitField('Criar Usuário')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Este nome de usuário já está em uso.')
    
    def validate_email(self, email):
        """Validação customizada de email que aceita domínios .local"""
        import re
        # Padrão mais flexível que aceita .local, .internal, .lan, etc.
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email.data):
            raise ValidationError('Email inválido')
        
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Este email já está registrado.')
    
    def validate_password(self, field):
        """Valida os requisitos da senha"""
        is_valid, errors = password_validator.validate_password(field.data)
        if not is_valid:
            raise ValidationError('; '.join(errors))

class ReportFilterForm(FlaskForm):
    # Filtros de Data
    date_from = DateField('Data Inicial', validators=[Optional()])
    date_to = DateField('Data Final', validators=[Optional()])
    
    # Filtros de Usuário e Cliente
    user_id = SelectField('Atendente', coerce=str, validators=[Optional()])
    document_type_id = SelectField('Tipo de Documento', coerce=str, validators=[Optional()])
    client_name = StringField('Nome do Cliente', validators=[Optional(), Length(max=255)])
    client_cpf = StringField('CPF do Cliente', validators=[Optional(), Length(max=14)])
    
    # Filtros Técnicos
    device_type = SelectField('Tipo de Dispositivo', 
                             choices=[('', 'Todos'), ('Desktop', 'Desktop'), ('Mobile', 'Mobile'), ('Tablet', 'Tablet')],
                             validators=[Optional()])
    browser_name = SelectField('Navegador',
                              choices=[('', 'Todos'), ('Chrome', 'Chrome'), ('Firefox', 'Firefox'), 
                                     ('Safari', 'Safari'), ('Edge', 'Edge'), ('Opera', 'Opera')],
                              validators=[Optional()])
    operating_system = SelectField('Sistema Operacional',
                                  choices=[('', 'Todos'), ('Windows', 'Windows'), ('macOS', 'macOS'), 
                                         ('Linux', 'Linux'), ('Android', 'Android'), ('iOS', 'iOS')],
                                  validators=[Optional()])
    
    # Filtros de Status
    verification_status = SelectField('Status de Verificação',
                                    choices=[('', 'Todos'), ('verified', 'Verificado'), 
                                           ('pending', 'Pendente'), ('failed', 'Falhou')],
                                    validators=[Optional()])
    signature_method = SelectField('Método de Assinatura',
                                  choices=[('', 'Todos'), ('drawing', 'Desenho'), ('upload', 'Upload')],
                                  validators=[Optional()])
    
    # Botões
    submit = SubmitField('Aplicar Filtros')
    export = SubmitField('Exportar JSON')
    clear = SubmitField('Limpar Filtros')
