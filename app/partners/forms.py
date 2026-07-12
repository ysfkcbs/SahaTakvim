from datetime import date

from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange

from app.finance.forms import LocalizedDecimalField
from app.models import PARTNER_NAMES

MONTH_CHOICES = [
    (1, "Ocak"), (2, "Şubat"), (3, "Mart"), (4, "Nisan"), (5, "Mayıs"), (6, "Haziran"),
    (7, "Temmuz"), (8, "Ağustos"), (9, "Eylül"), (10, "Ekim"), (11, "Kasım"), (12, "Aralık"),
]


class PartnerShareForm(FlaskForm):
    year = IntegerField("Yıl", default=date.today().year, validators=[DataRequired(), NumberRange(min=2000, max=2100)])
    month = SelectField("Ay", coerce=int, choices=MONTH_CHOICES, default=date.today().month, validators=[DataRequired()])
    partner_name = SelectField("Ortak", choices=[(name, name) for name in PARTNER_NAMES], validators=[DataRequired()])
    amount = LocalizedDecimalField("Tutar", validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField("Kaydet")
