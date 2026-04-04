from datetime import date
from decimal import Decimal, InvalidOperation

from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, DecimalField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Optional


def normalize_decimal_input(value):
    if value is None:
        return value

    if isinstance(value, Decimal):
        return value

    if isinstance(value, (int, float)):
        try:
            return Decimal(str(value))
        except InvalidOperation:
            return value

    text = str(value).strip().replace(" ", "")
    if not text:
        return text

    has_dot = "." in text
    has_comma = "," in text

    if has_dot and has_comma:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif has_comma and not has_dot:
        text = text.replace(",", ".")

    try:
        return Decimal(text)
    except InvalidOperation:
        return value


class DailyClosingForm(FlaskForm):
    closing_date = DateField("Tarih", default=date.today, validators=[DataRequired()])
    card_total = DecimalField("Kart", validators=[DataRequired(), NumberRange(min=0)], filters=[normalize_decimal_input])
    cash_total = DecimalField("Nakit", validators=[DataRequired(), NumberRange(min=0)], filters=[normalize_decimal_input])
    iban_total = DecimalField("IBAN", validators=[DataRequired(), NumberRange(min=0)], filters=[normalize_decimal_input])
    notes = TextAreaField("Not", validators=[Optional()])
    submit = SubmitField("Kapanışı Kaydet")


class TransactionForm(FlaskForm):
    transaction_kind = SelectField("Kategori", choices=[("income", "Gelir"), ("expense", "Gider")], validators=[DataRequired()])
    title = StringField("Başlık", validators=[DataRequired()])
    amount = DecimalField("Tutar", validators=[DataRequired(), NumberRange(min=0)], filters=[normalize_decimal_input])
    date = DateField("Tarih", validators=[DataRequired()], default=date.today)
    description = TextAreaField("Açıklama", validators=[Optional()])
    is_recurring = BooleanField("Sabit (Tekrarlayan)")
    is_paid = BooleanField("Ödendi")
    recurrence = SelectField("Tekrar", choices=[("monthly", "Aylık"), ("yearly", "Yıllık")])
    submit = SubmitField("Kaydet")
