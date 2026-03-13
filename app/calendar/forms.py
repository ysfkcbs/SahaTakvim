from datetime import date

from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional


class ReservationForm(FlaskForm):
    field_id = SelectField("Saha", coerce=int, validators=[DataRequired()])
    reservation_type = SelectField(
        "Rezervasyon Türü",
        choices=[("abone", "Abone"), ("tek_saatlik", "Tek Saatlik Maç")],
        validators=[DataRequired()],
    )
    customer_name = StringField("Kişi Adı", validators=[DataRequired(), Length(max=120)])
    phone = StringField("Telefon", validators=[Optional(), Length(max=30)])
    deposit_paid = BooleanField("Kapora Alındı")
    reservation_date = DateField("Tarih", validators=[DataRequired()], default=date.today)
    reservation_hour = SelectField("Saat", coerce=int, validators=[DataRequired()])
    notes = TextAreaField("Notlar", validators=[Optional(), Length(max=1000)])
    submit = SubmitField("Kaydet")
