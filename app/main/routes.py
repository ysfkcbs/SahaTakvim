from datetime import date, datetime, timedelta

from flask import Blueprint, render_template
from flask_login import current_user, login_required
from sqlalchemy import case, extract, func

from app.models import DailyClosing, Expense, Field, Income, Reservation


main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def index():
    return admin_dashboard() if current_user.role == "admin" else employee_dashboard()


@main_bp.route("/admin-dashboard")
@login_required
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

    month_income = float(reservation_income or 0) + float(other_income or 0)
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
    todays = Reservation.query.filter_by(reservation_date=today).order_by(Reservation.reservation_hour.asc()).all()
    return render_template("main/employee_dashboard.html", today=today, todays=todays)
