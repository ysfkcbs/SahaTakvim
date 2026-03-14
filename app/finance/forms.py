from datetime import date

from flask_wtf import FlaskForm
from wtforms import BooleanField, DateField, DecimalField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, NumberRange, Optional


def normalize_decimal_input(value):
    """Accept both Turkish and international decimal formats.

    Examples accepted:
    - 1250.50
    - 1250,50
    - 1.250,50
    - 1,250.50
    """
    if value is None:
        return value

    if isinstance(value, (int, float)):
        return str(value)

    text = str(value).strip().replace(" ", "")
    if not text:
        return text

    has_dot = "." in text
    has_comma = "," in text

    if has_dot and has_comma:
        # whichever appears last is likely decimal separator
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif has_comma and not has_dot:
        text = text.replace(".", "").replace(",", ".")

    return text


class DailyClosingForm(FlaskForm):
    closing_date = DateField("Tarih", default=date.today, validators=[DataRequired()])
    card_total = DecimalField("Kart", validators=[DataRequired(), NumberRange(min=0)], filters=[normalize_decimal_input])
    cash_total = DecimalField("Nakit", validators=[DataRequired(), NumberRange(min=0)], filters=[normalize_decimal_input])
    iban_total = DecimalField("IBAN", validators=[DataRequired(), NumberRange(min=0)], filters=[normalize_decimal_input])
    notes = TextAreaField("Not", validators=[Optional()])
    submit = SubmitField("Kapanışı Kaydet")


class IncomeForm(FlaskForm):
    title = StringField("Başlık", validators=[DataRequired()])
    category = StringField("Kategori", validators=[Optional()])
    amount = DecimalField("Tutar", validators=[DataRequired(), NumberRange(min=0)], filters=[normalize_decimal_input])
    date = DateField("Tarih", validators=[DataRequired()], default=date.today)
    description = TextAreaField("Açıklama", validators=[Optional()])
    is_recurring = BooleanField("Sabit (Tekrarlayan)")
    recurrence = SelectField("Tekrar", choices=[("monthly", "Aylık"), ("yearly", "Yıllık")])
    submit = SubmitField("Gelir Kaydet")


class ExpenseForm(FlaskForm):
    title = StringField("Başlık", validators=[DataRequired()])
    category = StringField("Kategori", validators=[Optional()])
    amount = DecimalField("Tutar", validators=[DataRequired(), NumberRange(min=0)], filters=[normalize_decimal_input])
    date = DateField("Tarih", validators=[DataRequired()], default=date.today)
    description = TextAreaField("Açıklama", validators=[Optional()])
    is_recurring = BooleanField("Sabit (Tekrarlayan)")
    recurrence = SelectField("Tekrar", choices=[("monthly", "Aylık"), ("yearly", "Yıllık")])
    submit = SubmitField("Gider Kaydet")
