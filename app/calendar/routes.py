from datetime import date, datetime, timedelta

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.calendar.forms import ReservationForm
from app.calendar.utils import business_hours, hour_label, week_start_for
from app.extensions import db
from app.models import Field, Reservation


calendar_bp = Blueprint("calendar", __name__)


def _matching_subscription_query(field_id, reservation_date, reservation_hour, exclude_id=None):
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


def _future_slot_conflicts_for_subscription(field_id, reservation_date, reservation_hour, exclude_id=None):
    query = Reservation.query.filter(
        Reservation.field_id == field_id,
        Reservation.reservation_hour == reservation_hour,
        Reservation.status == "active",
        Reservation.reservation_date >= reservation_date,
    )
    if exclude_id:
        query = query.filter(Reservation.id != exclude_id)
    return [reservation for reservation in query.all() if reservation.reservation_date.weekday() == reservation_date.weekday()]


def _has_slot_conflict(field_id, reservation_date, reservation_hour, reservation_type, exclude_id=None):
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

    if _matching_subscription_query(field_id, reservation_date, reservation_hour, exclude_id):
        return True

    if reservation_type == "abone":
        return bool(_future_slot_conflicts_for_subscription(field_id, reservation_date, reservation_hour, exclude_id))

    return False

WEEKDAY_NAMES_TR = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]


@calendar_bp.route("/weekly")
@login_required
def weekly():
    start_str = request.args.get("start")
    selected_field = request.args.get("field", type=int)
    start = week_start_for(datetime.strptime(start_str, "%Y-%m-%d").date()) if start_str else week_start_for(date.today())
    end = start + timedelta(days=6)

    fields = Field.query.filter_by(is_active=True).order_by(Field.name.asc()).all()
    if not selected_field and fields:
        selected_field = fields[0].id
    selected_field_obj = next((field for field in fields if field.id == selected_field), None)

    hours = business_hours(
        selected_field_obj.open_hour if selected_field_obj else 17,
        selected_field_obj.close_hour if selected_field_obj else 2,
    )
    days = [start + timedelta(days=i) for i in range(7)]

    dated_reservations = (
        Reservation.query.filter(Reservation.reservation_date.between(start, end), Reservation.status == "active")
        .filter(Reservation.field_id == selected_field if selected_field else True)
        .all()
    )
    recurring_subscriptions = (
        Reservation.query.filter(
            Reservation.reservation_type == "abone",
            Reservation.reservation_date <= end,
            Reservation.status == "active",
        )
        .filter(Reservation.field_id == selected_field if selected_field else True)
        .all()
    )

    current_app.logger.warning(
        "CALENDAR_WEEKLY_VIEW user=%s role=%s field_id=%s field_name=%s start=%s end=%s reservations=%s ua=%s",
        current_user.username,
        current_user.role,
        selected_field,
        selected_field_obj.name if selected_field_obj else None,
        start.isoformat(),
        end.isoformat(),
        len(dated_reservations),
        request.headers.get("User-Agent", "")[:180],
    )

    slot_map = {}
    for reservation in recurring_subscriptions:
        for day in days:
            if day >= reservation.reservation_date and day.weekday() == reservation.reservation_date.weekday():
                slot_map.setdefault((day, reservation.reservation_hour), reservation)

    for reservation in dated_reservations:
        slot_map[(reservation.reservation_date, reservation.reservation_hour)] = reservation

    form = ReservationForm()
    form.field_id.choices = [(f.id, f.name) for f in fields]
    form.reservation_hour.choices = [(h, hour_label(h)) for h in hours]
    if selected_field:
        form.field_id.data = selected_field

    return render_template(
        "calendar/weekly.html",
        week_start=start,
        week_end=end,
        days=days,
        weekday_names_tr=WEEKDAY_NAMES_TR,
        hours=hours,
        hour_label=hour_label,
        slot_map=slot_map,
        fields=fields,
        selected_field=selected_field,
        selected_field_obj=selected_field_obj,
        form=form,
        prev_week=start - timedelta(days=7),
        next_week=start + timedelta(days=7),
    )


@calendar_bp.route("/reservations/create", methods=["POST"])
@login_required
def create_reservation():
    form = ReservationForm()
    fields = Field.query.filter_by(is_active=True).order_by(Field.name.asc()).all()
    form.field_id.choices = [(f.id, f.name) for f in fields]
    posted_field_id = request.form.get("field_id", type=int)
    selected_form_field = next((field for field in fields if field.id == posted_field_id), fields[0] if fields else None)
    form.reservation_hour.choices = [
        (h, hour_label(h)) for h in business_hours(
            selected_form_field.open_hour if selected_form_field else 17,
            selected_form_field.close_hour if selected_form_field else 2,
        )
    ]

    if form.validate_on_submit():
        current_app.logger.warning(
            "CALENDAR_CREATE_ATTEMPT user=%s role=%s field_id=%s date=%s hour=%s type=%s customer=%s ua=%s",
            current_user.username,
            current_user.role,
            form.field_id.data,
            form.reservation_date.data.isoformat() if form.reservation_date.data else None,
            form.reservation_hour.data,
            form.reservation_type.data,
            form.customer_name.data,
            request.headers.get("User-Agent", "")[:180],
        )
        if _has_slot_conflict(
            form.field_id.data,
            form.reservation_date.data,
            form.reservation_hour.data,
            form.reservation_type.data,
        ):
            current_app.logger.warning(
                "CALENDAR_CREATE_CONFLICT user=%s role=%s field_id=%s date=%s hour=%s",
                current_user.username,
                current_user.role,
                form.field_id.data,
                form.reservation_date.data.isoformat() if form.reservation_date.data else None,
                form.reservation_hour.data,
            )
            flash("Bu saha ve saat için mevcut bir rezervasyon var.", "danger")
        else:
            r = Reservation(
                field_id=form.field_id.data,
                reservation_type=form.reservation_type.data,
                customer_name=form.customer_name.data,
                phone=form.phone.data,
                deposit_paid=form.deposit_paid.data,
                reservation_date=form.reservation_date.data,
                reservation_hour=form.reservation_hour.data,
                notes=form.notes.data,
                created_by_user_id=current_user.id,
            )
            db.session.add(r)
            db.session.commit()
            current_app.logger.warning(
                "CALENDAR_CREATE_SUCCESS user=%s role=%s reservation_id=%s field_id=%s date=%s hour=%s type=%s",
                current_user.username,
                current_user.role,
                r.id,
                r.field_id,
                r.reservation_date.isoformat(),
                r.reservation_hour,
                r.reservation_type,
            )
            flash("Rezervasyon oluşturuldu.", "success")
    else:
        current_app.logger.warning(
            "CALENDAR_CREATE_INVALID user=%s role=%s field_id=%s date=%s hour=%s errors=%s ua=%s",
            current_user.username,
            current_user.role,
            form.field_id.data,
            form.reservation_date.data.isoformat() if form.reservation_date.data else None,
            form.reservation_hour.data,
            form.errors,
            request.headers.get("User-Agent", "")[:180],
        )

    return redirect(url_for("calendar.weekly", start=form.reservation_date.data.isoformat(), field=form.field_id.data))


@calendar_bp.route("/reservations/<int:reservation_id>/edit", methods=["GET", "POST"])
@login_required
def edit_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    form = ReservationForm(obj=reservation)
    fields = Field.query.filter_by(is_active=True).order_by(Field.name.asc()).all()
    form.field_id.choices = [(f.id, f.name) for f in fields]
    selected_field_id = request.form.get("field_id", type=int) if request.method == "POST" else reservation.field_id
    selected_form_field = next((field for field in fields if field.id == selected_field_id), None)
    form.reservation_hour.choices = [
        (h, hour_label(h)) for h in business_hours(
            selected_form_field.open_hour if selected_form_field else 17,
            selected_form_field.close_hour if selected_form_field else 2,
        )
    ]

    if form.validate_on_submit():
        conflict = _has_slot_conflict(
            form.field_id.data,
            form.reservation_date.data,
            form.reservation_hour.data,
            form.reservation_type.data,
            exclude_id=reservation.id,
        )
        if conflict:
            flash("Slot çakışması var.", "danger")
        else:
            form.populate_obj(reservation)
            db.session.commit()
            flash("Rezervasyon güncellendi.", "success")
            return redirect(url_for("calendar.weekly", start=form.reservation_date.data.isoformat(), field=form.field_id.data))

    return render_template("reservations/edit.html", form=form, reservation=reservation)


@calendar_bp.route("/reservations/<int:reservation_id>/delete", methods=["POST"])
@login_required
def delete_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    reservation.status = "cancelled"
    db.session.commit()
    flash("Rezervasyon iptal edildi.", "warning")
    return redirect(url_for("calendar.weekly", start=reservation.reservation_date.isoformat(), field=reservation.field_id))


# Backward-compatible alias for environments importing `bp` from this module.
bp = calendar_bp
__all__ = ["calendar_bp", "bp"]
