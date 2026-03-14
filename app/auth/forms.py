from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional


class LoginForm(FlaskForm):
    username = StringField("Kullanıcı Adı", validators=[DataRequired(), Length(max=80)])
    password = PasswordField("Şifre", validators=[DataRequired()])
    submit = SubmitField("Giriş Yap")


class UserCreateForm(FlaskForm):
    username = StringField("Kullanıcı Adı", validators=[DataRequired(), Length(max=80)])
    password = PasswordField("Şifre", validators=[Optional(), Length(min=6, max=128)])
    role = SelectField("Rol", choices=[("admin", "Admin"), ("employee", "Çalışan")], validators=[DataRequired()])
    is_active_user = BooleanField("Aktif", default=True)
    submit = SubmitField("Kullanıcı Ekle")


class UserUpdateForm(FlaskForm):
    username = StringField("Kullanıcı Adı", validators=[DataRequired(), Length(max=80)])
    password = PasswordField("Yeni Şifre (opsiyonel)", validators=[Optional(), Length(min=6, max=128)])
    role = SelectField("Rol", choices=[("admin", "Admin"), ("employee", "Çalışan")], validators=[DataRequired()])
    is_active_user = BooleanField("Aktif")
    submit = SubmitField("Değişiklikleri Kaydet")
