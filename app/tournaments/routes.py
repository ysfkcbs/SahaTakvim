from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.calendar.utils import WEEKDAY_NAMES_TR, business_hours, hour_label
from app.extensions import db
from app.main.utils import role_required
from app.models import Field, Reservation, Tournament

from .forms import TournamentForm
from .services import generate_tournament_slots


tournaments_bp = Blueprint("tournaments", __name__)


def _parse_slot_grid(form_data, prefix):
    """'{prefix}_{weekday}_{hour}' adlı checkbox girişlerini (weekday, hour) çiftlerine çevirir."""
    pairs = []
    for key in form_data:
        if not key.startswith(prefix + "_"):
            continue
        try:
            weekday_str, hour_str = key[len(prefix) + 1 :].split("_")
            pairs.append((int(weekday_str), int(hour_str)))
        except ValueError:
            continue
    return pairs


@tournaments_bp.route("/create", methods=["GET", "POST"])
@login_required
@role_required("admin")
def create():
    form = TournamentForm()
    fields = Field.query.filter_by(is_active=True).order_by(Field.name.asc()).all()
    form.field_id.choices = [(f.id, f.name) for f in fields]
    posted_field_id = request.form.get("field_id", type=int)
    selected_field = next((f for f in fields if f.id == posted_field_id), fields[0] if fields else None)
    hours = business_hours(selected_field.open_hour, selected_field.close_hour) if selected_field else business_hours()

    if form.validate_on_submit():
        week_count = form.week_count.data
        if form.format.data == "lig":
            pairs = _parse_slot_grid(request.form, "slot")
            week_plan = [pairs for _ in range(week_count)]
        else:
            week_plan = [_parse_slot_grid(request.form, f"slot_w{w}") for w in range(week_count)]

        if not any(week_plan):
            flash("En az bir gün/saat seçmelisiniz.", "danger")
        else:
            tournament = Tournament(
                field_id=form.field_id.data,
                name=form.name.data,
                format=form.format.data,
                customer_name=form.customer_name.data,
                phone=form.phone.data,
                deposit_paid=form.deposit_paid.data,
                notes=form.notes.data,
                created_by_user_id=current_user.id,
            )
            db.session.add(tournament)
            db.session.flush()

            created, skipped = generate_tournament_slots(tournament, form.start_date.data, week_plan, current_user.id)

            if not created:
                db.session.rollback()
                flash("Seçilen tüm slotlar çakışma nedeniyle atlandı, turnuva oluşturulamadı.", "danger")
            else:
                db.session.commit()
                if skipped:
                    flash(f"{len(created)} slot oluşturuldu, {len(skipped)} slot çakışma nedeniyle atlandı.", "warning")
                else:
                    flash(f"{len(created)} slot oluşturuldu.", "success")
                return redirect(url_for("tournaments.detail", tournament_id=tournament.id))

    return render_template(
        "tournaments/create.html",
        form=form,
        hours=hours,
        weekday_names_tr=WEEKDAY_NAMES_TR,
        hour_label=hour_label,
        week_range=range(12),
    )


@tournaments_bp.route("/")
@login_required
@role_required("admin")
def list_tournaments():
    tournaments = Tournament.query.order_by(Tournament.created_at.desc()).all()
    return render_template("tournaments/list.html", tournaments=tournaments)


@tournaments_bp.route("/<int:tournament_id>")
@login_required
@role_required("admin")
def detail(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    slots = tournament.reservations.order_by(Reservation.reservation_date.asc(), Reservation.reservation_hour.asc()).all()
    return render_template("tournaments/detail.html", tournament=tournament, slots=slots, hour_label=hour_label)


@tournaments_bp.route("/<int:tournament_id>/cancel", methods=["POST"])
@login_required
@role_required("admin")
def cancel(tournament_id):
    tournament = Tournament.query.get_or_404(tournament_id)
    tournament.reservations.filter_by(status="active").update({"status": "cancelled"})
    tournament.status = "cancelled"
    db.session.commit()
    flash("Turnuva ve bağlı tüm slotlar iptal edildi.", "warning")
    return redirect(url_for("tournaments.detail", tournament_id=tournament.id))
