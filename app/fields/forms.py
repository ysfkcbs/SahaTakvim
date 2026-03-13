from flask_wtf import FlaskForm
from wtforms import BooleanField, DecimalField, IntegerField, StringField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class FieldForm(FlaskForm):
    name = StringField("Saha Adı", validators=[DataRequired()])
    rental_price = DecimalField("Tek Saatlik Fiyat", validators=[DataRequired(), NumberRange(min=0)])
    subscription_price = DecimalField("Abone Fiyat", validators=[DataRequired(), NumberRange(min=0)])
    open_hour = IntegerField("Açılış Saati", validators=[DataRequired(), NumberRange(min=0, max=23)])
    close_hour = IntegerField("Kapanış Saati", validators=[DataRequired(), NumberRange(min=0, max=23)])
    is_active = BooleanField("Aktif")
    submit = SubmitField("Kaydet")
