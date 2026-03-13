from flask_wtf import FlaskForm
from wtforms import PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    username = StringField("Kullanıcı Adı", validators=[DataRequired(), Length(max=80)])
    password = PasswordField("Şifre", validators=[DataRequired()])
    submit = SubmitField("Giriş Yap")


class UserForm(FlaskForm):
    username = StringField("Kullanıcı Adı", validators=[DataRequired(), Length(max=80)])
    password = PasswordField("Şifre")
    role = SelectField("Rol", choices=[("admin", "Admin"), ("employee", "Çalışan")], validators=[DataRequired()])
    submit = SubmitField("Kaydet")
