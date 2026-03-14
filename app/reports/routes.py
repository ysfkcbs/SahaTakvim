from flask import Blueprint, render_template, request
from flask_login import login_required

from app.main.utils import role_required
from app.models import Field, Reservation


reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/reservations")
@login_required
@role_required("admin")
def reservation_report():
    q = Reservation.query
    field_id = request.args.get("field", type=int)
    r_type = request.args.get("type")
    deposit = request.args.get("deposit")

    if field_id:
        q = q.filter_by(field_id=field_id)
    if r_type:
        q = q.filter_by(reservation_type=r_type)
    if deposit in {"paid", "unpaid"}:
        q = q.filter_by(deposit_paid=deposit == "paid")

    records = q.order_by(Reservation.reservation_date.desc(), Reservation.reservation_hour.desc()).all()
    return render_template("reports/reservations.html", records=records, fields=Field.query.all())
