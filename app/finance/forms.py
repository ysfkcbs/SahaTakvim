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


class LocalizedDecimalField(DecimalField):
    def process_formdata(self, valuelist):
        if valuelist:
            normalized = normalize_decimal_input(valuelist[0])
            if isinstance(normalized, Decimal):
                valuelist = [str(normalized)]
            else:
                valuelist = [normalized]
        super().process_formdata(valuelist)


class DailyClosingForm(FlaskForm):
    closing_date = DateField("Tarih", default=date.today, validators=[DataRequired()])
    card_total = LocalizedDecimalField("Kart", validators=[Optional(), NumberRange(min=0)])
    cash_total = LocalizedDecimalField("Nakit", validators=[Optional(), NumberRange(min=0)])
    iban_total = LocalizedDecimalField("IBAN", validators=[Optional(), NumberRange(min=0)])
    notes = TextAreaField("Not", validators=[Optional()])
    submit = SubmitField("Kapanışı Kaydet")


    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False

        amount_fields = [self.card_total, self.cash_total, self.iban_total]
        if not any(field.data is not None for field in amount_fields):
            self.cash_total.errors.append("Nakit, kart veya IBAN alanlarindan en az biri girilmelidir.")
            return False

        for field in amount_fields:
            if field.data is None:
                field.data = Decimal("0")

        return True


class TransactionForm(FlaskForm):
    transaction_kind = SelectField("İşlem Türü", choices=[("income", "Gelir"), ("expense", "Gider")], validators=[DataRequired()])
    title = StringField("Başlık", validators=[DataRequired()])
    amount = DecimalField("Tutar", validators=[DataRequired(), NumberRange(min=0)], filters=[normalize_decimal_input])
    date = DateField("Tarih", validators=[DataRequired()], default=date.today)
    income_category_id = SelectField("Kategori", coerce=int, validators=[Optional()])
    expense_category_id = SelectField("Kategori", coerce=int, validators=[Optional()])
    description = TextAreaField("Açıklama", validators=[Optional()])
    is_recurring = BooleanField("Sabit (Tekrarlayan)")
    is_paid = BooleanField("Ödendi")
    recurrence = SelectField("Tekrar", choices=[("monthly", "Aylık"), ("yearly", "Yıllık")])
    submit = SubmitField("Kaydet")
