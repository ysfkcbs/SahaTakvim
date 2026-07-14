from datetime import date, datetime, timedelta

from flask import Blueprint, current_app, render_template, request, send_from_directory
from flask_login import current_user, login_required
from sqlalchemy import case, extract, func

from app.calendar.utils import WEEKDAY_NAMES_TR, business_hours, hour_label, week_start_for
from app.finance.services import daily_closing_total_for_month
from app.main.utils import role_required
from app.models import DailyClosing, Expense, Field, Income, Reservation


main_bp = Blueprint("main", __name__)


def _public_occupancy(start, field):
    end = start + timedelta(days=6)
    days = [start + timedelta(days=i) for i in range(7)]
    hours = business_hours(field.open_hour, field.close_hour) if field else business_hours()

    occupied = set()
    if field:
        rows = (
            Reservation.query.with_entities(Reservation.reservation_date, Reservation.reservation_hour, Reservation.reservation_type)
            .filter(Reservation.field_id == field.id, Reservation.status == "active")
            .filter(Reservation.reservation_date.between(start, end) | (Reservation.reservation_type == "abone"))
            .all()
        )
        for r_date, r_hour, r_type in rows:
            if r_type == "abone":
                for day in days:
                    if day >= r_date and day.weekday() == r_date.weekday():
                        occupied.add((day, r_hour))
            elif start <= r_date <= end:
                occupied.add((r_date, r_hour))

    total_slots = len(days) * len(hours)
    occupancy_rate = round((len(occupied) / total_slots) * 100) if total_slots else 0

    return {
        "days": days,
        "hours": hours,
        "occupied": occupied,
        "occupancy_rate": occupancy_rate,
    }


@main_bp.route("/manifest.webmanifest")
def web_manifest():
    return send_from_directory(current_app.static_folder, "manifest.webmanifest", mimetype="application/manifest+json")


@main_bp.route("/service-worker.js")
def service_worker():
    response = send_from_directory(current_app.static_folder, "service-worker.js", mimetype="application/javascript")
    response.headers["Cache-Control"] = "no-cache"
    return response


@main_bp.route("/")
def index():
    if not current_user.is_authenticated:
        return public_landing()
    return admin_dashboard() if current_user.role == "admin" else employee_dashboard()


def public_landing():
    start_str = request.args.get("start")
    selected_field_id = request.args.get("field", type=int)
    start = week_start_for(datetime.strptime(start_str, "%Y-%m-%d").date()) if start_str else week_start_for(date.today())

    fields = Field.query.filter_by(is_active=True).order_by(Field.name.asc()).all()
    if not selected_field_id and fields:
        selected_field_id = fields[0].id
    selected_field = next((f for f in fields if f.id == selected_field_id), None)

    occupancy = _public_occupancy(start, selected_field)

    return render_template(
        "main/public_landing.html",
        week_start=start,
        week_end=start + timedelta(days=6),
        weekday_names_tr=WEEKDAY_NAMES_TR,
        hour_label=hour_label,
        fields=fields,
        selected_field=selected_field_id,
        selected_field_obj=selected_field,
        prev_week=start - timedelta(days=7),
        next_week=start + timedelta(days=7),
        **occupancy,
    )


@main_bp.route("/admin-dashboard")
@login_required
@role_required("admin")
def admin_dashboard():
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    reservations_week = Reservation.query.filter(Reservation.reservation_date.between(week_start, week_end)).count()
    reservations_month = Reservation.query.filter(
        extract("year", Reservation.reservation_date) == today.year,
        extract("month", Reservation.reservation_date) == today.month,
    ).count()

    reservation_income = (
        Reservation.query.join(Field)
        .with_entities(
            func.coalesce(
                func.sum(
                    case((Reservation.reservation_type == "abone", Field.subscription_price), else_=Field.rental_price)
                ),
                0,
            )
        )
        .filter(
            extract("year", Reservation.reservation_date) == today.year,
            extract("month", Reservation.reservation_date) == today.month,
            Reservation.status == "active",
        )
        .scalar()
    )

    other_income = Income.query.with_entities(func.coalesce(func.sum(Income.amount), 0)).filter(
        extract("year", Income.date) == today.year,
        extract("month", Income.date) == today.month,
    ).scalar()

    expenses = Expense.query.with_entities(func.coalesce(func.sum(Expense.amount), 0)).filter(
        extract("year", Expense.date) == today.year,
        extract("month", Expense.date) == today.month,
    ).scalar()

    daily_income = daily_closing_total_for_month(today.year, today.month)
    month_income = float(reservation_income or 0) + float(other_income or 0) + daily_income
    month_expenses = float(expenses or 0)

    upcoming = Reservation.query.filter(Reservation.reservation_date >= today, Reservation.status == "active").order_by(
        Reservation.reservation_date.asc(), Reservation.reservation_hour.asc()
    ).limit(8)

    context = {
        "reservations_week": reservations_week,
        "reservations_month": reservations_month,
        "month_income": month_income,
        "month_expenses": month_expenses,
        "net_result": month_income - month_expenses,
        "paid_deposits": Reservation.query.filter_by(deposit_paid=True, status="active").count(),
        "unpaid_deposits": Reservation.query.filter_by(deposit_paid=False, status="active").count(),
        "active_subscribers": Reservation.query.filter_by(reservation_type="abone", status="active").count(),
        "active_fields": Field.query.filter_by(is_active=True).count(),
        "upcoming": upcoming,
        "daily_closings": DailyClosing.query.order_by(DailyClosing.closing_date.desc()).limit(7),
    }
    return render_template("main/admin_dashboard.html", **context)


@main_bp.route("/employee-dashboard")
@login_required
def employee_dashboard():
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    weekly_reservations = (
        Reservation.query.join(Field)
        .filter(
            Reservation.reservation_date.between(week_start, week_end),
            Reservation.status == "active",
        )
        .order_by(Reservation.reservation_date.asc(), Reservation.reservation_hour.asc(), Field.name.asc())
        .all()
    )
    return render_template(
        "main/employee_dashboard.html",
        today=today,
        week_start=week_start,
        week_end=week_end,
        reservations=weekly_reservations,
    )
