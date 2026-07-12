from datetime import date

from flask import Blueprint, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import extract

from app.finance.services import actual_total, reservation_income_for_month
from app.main.utils import role_required
from app.models import Expense, Field, Reservation


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

    today = date.today()
    selected_year = request.args.get("year", today.year, type=int)
    selected_month = request.args.get("month", today.month, type=int)
    if selected_month == 1:
        prev_year, prev_month = selected_year - 1, 12
    else:
        prev_year, prev_month = selected_year, selected_month - 1
    if selected_month == 12:
        next_year, next_month = selected_year + 1, 1
    else:
        next_year, next_month = selected_year, selected_month + 1

    month_query = Reservation.query.filter(
        Reservation.status == "active",
        extract("year", Reservation.reservation_date) == selected_year,
        extract("month", Reservation.reservation_date) == selected_month,
    )
    single_count = month_query.filter_by(reservation_type="tek_saatlik").count()
    subscriber_count = month_query.filter_by(reservation_type="abone").count()

    summary = {
        "total_count": single_count + subscriber_count,
        "single_count": single_count,
        "subscriber_count": subscriber_count,
        "income": reservation_income_for_month(selected_year, selected_month),
        "expense": actual_total(Expense, selected_year, selected_month),
        "label": f"{selected_month:02d}.{selected_year}",
    }

    return render_template(
        "reports/reservations.html",
        records=records,
        fields=Field.query.all(),
        summary=summary,
        prev_month_url=url_for("reports.reservation_report", year=prev_year, month=prev_month),
        next_month_url=url_for("reports.reservation_report", year=next_year, month=next_month),
    )
