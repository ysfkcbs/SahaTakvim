from datetime import date, timedelta

from sqlalchemy import text

from app.extensions import db
from app.models import Reservation

WEEKDAY_NAMES_TR = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]


def week_start_for(day: date):
    return day - timedelta(days=day.weekday())


def business_hours(open_hour=17, close_hour=2):
    hours = []
    h = open_hour
    while h != close_hour:
        hours.append(h)
        h = (h + 1) % 24
    return hours


def hour_label(hour):
    return f"{hour:02d}:00"


def lock_field_hour(field_id, hour):
    # Serializes concurrent check-then-insert races (exact slot and recurring
    # subscription checks alike) for this field+hour; Postgres-only because the
    # subscription conflict check has no backing unique constraint to fall back on.
    if db.engine.dialect.name == "postgresql":
        db.session.execute(text("SELECT pg_advisory_xact_lock(:field_id, :hour)"), {"field_id": field_id, "hour": hour})


def matching_subscription_query(field_id, reservation_date, reservation_hour, exclude_id=None):
    query = Reservation.query.filter(
        Reservation.field_id == field_id,
        Reservation.reservation_hour == reservation_hour,
        Reservation.reservation_type == "abone",
        Reservation.status == "active",
        Reservation.reservation_date <= reservation_date,
    )
    if exclude_id:
        query = query.filter(Reservation.id != exclude_id)
    return [reservation for reservation in query.all() if reservation.reservation_date.weekday() == reservation_date.weekday()]


def future_slot_conflicts_for_subscription(field_id, reservation_date, reservation_hour, exclude_id=None):
    query = Reservation.query.filter(
        Reservation.field_id == field_id,
        Reservation.reservation_hour == reservation_hour,
        Reservation.status == "active",
        Reservation.reservation_date >= reservation_date,
    )
    if exclude_id:
        query = query.filter(Reservation.id != exclude_id)
    return [reservation for reservation in query.all() if reservation.reservation_date.weekday() == reservation_date.weekday()]


def has_slot_conflict(field_id, reservation_date, reservation_hour, reservation_type, exclude_id=None):
    exact_query = Reservation.query.filter_by(
        field_id=field_id,
        reservation_date=reservation_date,
        reservation_hour=reservation_hour,
        status="active",
    )
    if exclude_id:
        exact_query = exact_query.filter(Reservation.id != exclude_id)
    if exact_query.first():
        return True

    if matching_subscription_query(field_id, reservation_date, reservation_hour, exclude_id):
        return True

    if reservation_type == "abone":
        return bool(future_slot_conflicts_for_subscription(field_id, reservation_date, reservation_hour, exclude_id))

    return False
