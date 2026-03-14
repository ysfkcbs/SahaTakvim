from datetime import datetime
from decimal import Decimal

from flask_login import UserMixin
from sqlalchemy import UniqueConstraint
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


class TimestampMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class User(UserMixin, TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="employee")
    is_active_user = db.Column(db.Boolean, default=True, nullable=False)

    reservations = db.relationship("Reservation", back_populates="created_by", lazy="dynamic")
    closings = db.relationship("DailyClosing", back_populates="entered_by", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, role_name):
        return self.role == role_name


class Field(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    rental_price = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("0"))
    subscription_price = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("0"))
    open_hour = db.Column(db.Integer, nullable=False, default=17)
    close_hour = db.Column(db.Integer, nullable=False, default=2)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    reservations = db.relationship("Reservation", back_populates="field", lazy="dynamic")


class Reservation(TimestampMixin, db.Model):
    __table_args__ = (UniqueConstraint("field_id", "reservation_date", "reservation_hour", name="uq_slot"),)

    id = db.Column(db.Integer, primary_key=True)
    field_id = db.Column(db.Integer, db.ForeignKey("field.id"), nullable=False)
    reservation_type = db.Column(db.String(20), nullable=False)  # abone / tek_saatlik
    customer_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    deposit_paid = db.Column(db.Boolean, nullable=False, default=False)
    reservation_date = db.Column(db.Date, nullable=False)
    reservation_hour = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default="active")
    created_by_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    field = db.relationship("Field", back_populates="reservations")
    created_by = db.relationship("User", back_populates="reservations")

    @property
    def display_time(self):
        return f"{self.reservation_hour:02d}:00"


class DailyClosing(TimestampMixin, db.Model):
    __table_args__ = (UniqueConstraint("closing_date", name="uq_daily_closing_date"),)

    id = db.Column(db.Integer, primary_key=True)
    closing_date = db.Column(db.Date, nullable=False)
    card_total = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("0"))
    cash_total = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("0"))
    iban_total = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal("0"))
    notes = db.Column(db.Text)
    entered_by_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    entered_by = db.relationship("User", back_populates="closings")


class IncomeCategory(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)


class ExpenseCategory(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)


class Income(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text)
    is_recurring = db.Column(db.Boolean, default=False, nullable=False)
    recurrence = db.Column(db.String(20), default="monthly", nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("income_category.id"), nullable=True)

    category = db.relationship("IncomeCategory")


class Expense(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text)
    is_recurring = db.Column(db.Boolean, default=False, nullable=False)
    recurrence = db.Column(db.String(20), default="monthly", nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("expense_category.id"), nullable=True)

    category = db.relationship("ExpenseCategory")


class Setting(TimestampMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)
