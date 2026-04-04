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


def recurring_total(model, year, month, paid_only=None):
    items = model.query.filter_by(is_recurring=True).all()
    total = 0.0
    for item in items:
      if paid_only is not None and item.is_paid != paid_only:
          continue
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
        paid_income = recurring_total(Income, y, m, paid_only=True)
        pending_income = recurring_total(Income, y, m, paid_only=False)
        paid_expense = recurring_total(Expense, y, m, paid_only=True)
        pending_expense = recurring_total(Expense, y, m, paid_only=False)
        income = reservation_income_for_month(y, m) + paid_income + pending_income
        expense = paid_expense + pending_expense
        label = f"{y}-{m:02d}"
        data.append(
            {
                "month": label,
                "income": income,
                "expense": expense,
                "net": income - expense,
                "paid_income": paid_income,
                "pending_income": pending_income,
                "paid_expense": paid_expense,
                "pending_expense": pending_expense,
            }
        )
    return data
