from datetime import date, datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.calendar.forms import ReservationForm
from app.calendar.utils import business_hours, hour_label, week_start_for
from app.extensions import db
from app.models import Field, Reservation


calendar_bp = Blueprint("calendar", __name__)


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

    hours = business_hours()
    days = [start + timedelta(days=i) for i in range(7)]

    reservations = (
        Reservation.query.filter(Reservation.reservation_date.between(start, end), Reservation.status == "active")
        .filter(Reservation.field_id == selected_field if selected_field else True)
        .all()
    )

    slot_map = {(r.reservation_date, r.reservation_hour): r for r in reservations}

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
        hours=hours,
        hour_label=hour_label,
        slot_map=slot_map,
        fields=fields,
        selected_field=selected_field,
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
    form.reservation_hour.choices = [(h, hour_label(h)) for h in business_hours()]

    if form.validate_on_submit():
        exists = Reservation.query.filter_by(
            field_id=form.field_id.data,
            reservation_date=form.reservation_date.data,
            reservation_hour=form.reservation_hour.data,
            status="active",
        ).first()
        if exists:
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
            flash("Rezervasyon oluşturuldu.", "success")

    return redirect(url_for("calendar.weekly", start=form.reservation_date.data.isoformat(), field=form.field_id.data))


@calendar_bp.route("/reservations/<int:reservation_id>/edit", methods=["GET", "POST"])
@login_required
def edit_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    form = ReservationForm(obj=reservation)
    fields = Field.query.filter_by(is_active=True).order_by(Field.name.asc()).all()
    form.field_id.choices = [(f.id, f.name) for f in fields]
    form.reservation_hour.choices = [(h, hour_label(h)) for h in business_hours()]

    if form.validate_on_submit():
        conflict = (
            Reservation.query.filter_by(
                field_id=form.field_id.data,
                reservation_date=form.reservation_date.data,
                reservation_hour=form.reservation_hour.data,
                status="active",
            )
            .filter(Reservation.id != reservation.id)
            .first()
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
