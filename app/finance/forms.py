from datetime import date

from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, DecimalField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Optional


class DailyClosingForm(FlaskForm):
    closing_date = DateField("Tarih", default=date.today, validators=[DataRequired()])
    card_total = DecimalField("Kart", validators=[DataRequired(), NumberRange(min=0)])
    cash_total = DecimalField("Nakit", validators=[DataRequired(), NumberRange(min=0)])
    iban_total = DecimalField("IBAN", validators=[DataRequired(), NumberRange(min=0)])
    notes = TextAreaField("Not", validators=[Optional()])
    submit = SubmitField("Kapanışı Kaydet")


class IncomeForm(FlaskForm):
    title = StringField("Başlık", validators=[DataRequired()])
    category = StringField("Kategori", validators=[Optional()])
    amount = DecimalField("Tutar", validators=[DataRequired(), NumberRange(min=0)])
    date = DateField("Tarih", validators=[DataRequired()], default=date.today)
    description = TextAreaField("Açıklama", validators=[Optional()])
    is_recurring = BooleanField("Sabit (Tekrarlayan)")
    recurrence = SelectField("Tekrar", choices=[("monthly", "Aylık"), ("yearly", "Yıllık")])
    submit = SubmitField("Gelir Kaydet")


class ExpenseForm(FlaskForm):
    title = StringField("Başlık", validators=[DataRequired()])
    category = StringField("Kategori", validators=[Optional()])
    amount = DecimalField("Tutar", validators=[DataRequired(), NumberRange(min=0)])
    date = DateField("Tarih", validators=[DataRequired()], default=date.today)
    description = TextAreaField("Açıklama", validators=[Optional()])
    is_recurring = BooleanField("Sabit (Tekrarlayan)")
    recurrence = SelectField("Tekrar", choices=[("monthly", "Aylık"), ("yearly", "Yıllık")])
    submit = SubmitField("Gider Kaydet")
