from datetime import date

from sqlalchemy import extract, func

from app.models import Expense, Field, Income, Reservation


def reservation_income_for_month(year: int, month: int):
    rows = (
        Reservation.query.join(Field)
        .with_entities(Reservation.reservation_type, Field.rental_price, Field.subscription_price)
        .filter(
            extract("year", Reservation.reservation_date) == year,
            extract("month", Reservation.reservation_date) == month,
            Reservation.status == "active",
        )
        .all()
    )
    total = 0.0
    for r_type, rental, sub in rows:
        total += float(sub if r_type == "abone" else rental)
    return total


def recurring_total(model, year, month):
    items = model.query.filter_by(is_recurring=True).all()
    total = 0.0
    for item in items:
        if item.recurrence == "monthly":
            total += float(item.amount)
        elif item.recurrence == "yearly" and item.date.month == month:
            total += float(item.amount)
    return total


def actual_total(model, year, month):
    return float(
        model.query.with_entities(func.coalesce(func.sum(model.amount), 0)).filter(
            extract("year", model.date) == year, extract("month", model.date) == month
        ).scalar()
    )


def forecast_next_months(month_count=3):
    today = date.today()
    data = []
    for offset in range(month_count):
        m = ((today.month - 1 + offset) % 12) + 1
        y = today.year + ((today.month - 1 + offset) // 12)
        income = reservation_income_for_month(y, m) + recurring_total(Income, y, m)
        expense = recurring_total(Expense, y, m)
        label = f"{y}-{m:02d}"
        data.append({"month": label, "income": income, "expense": expense, "net": income - expense})
    return data
