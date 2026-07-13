from datetime import date

from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, IntegerField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

from app.models import TOURNAMENT_FORMATS


class TournamentForm(FlaskForm):
    field_id = SelectField("Saha", coerce=int, validators=[DataRequired()])
    name = StringField("Turnuva Adı", validators=[DataRequired(), Length(max=120)])
    format = SelectField("Format", choices=TOURNAMENT_FORMATS, validators=[DataRequired()])
    customer_name = StringField("Organizatör Adı", validators=[DataRequired(), Length(max=120)])
    phone = StringField("Telefon", validators=[Optional(), Length(max=30)])
    deposit_paid = BooleanField("Kapora Alındı")
    notes = TextAreaField("Not", validators=[Optional(), Length(max=1000)])
    start_date = DateField("Başlangıç Tarihi (1. Hafta)", validators=[DataRequired()], default=date.today)
    week_count = IntegerField("Hafta Sayısı", default=1, validators=[DataRequired(), NumberRange(min=1, max=12)])
    submit = SubmitField("Turnuva Oluştur")
