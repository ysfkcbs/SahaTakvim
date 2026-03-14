from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.finance.forms import DailyClosingForm, ExpenseForm, IncomeForm
from app.finance.services import actual_total, forecast_next_months, reservation_income_for_month
from app.main.utils import role_required
from app.models import DailyClosing, Expense, ExpenseCategory, Income, IncomeCategory


finance_bp = Blueprint("finance", __name__)


@finance_bp.route("/daily-closing", methods=["GET", "POST"])
@login_required
def daily_closing():
    form = DailyClosingForm()
    if form.validate_on_submit():
        closing = DailyClosing.query.filter_by(closing_date=form.closing_date.data).first()
        if not closing:
            closing = DailyClosing(closing_date=form.closing_date.data, entered_by_user_id=current_user.id)
            db.session.add(closing)
        closing.card_total = form.card_total.data
        closing.cash_total = form.cash_total.data
        closing.iban_total = form.iban_total.data
        closing.notes = form.notes.data
        closing.entered_by_user_id = current_user.id
        db.session.commit()
        flash("Gün sonu kapanışı kaydedildi.", "success")
        return redirect(url_for("finance.daily_closing"))

    closings = DailyClosing.query.order_by(DailyClosing.closing_date.desc()).all()
    return render_template("finance/daily_closing.html", form=form, closings=closings)


@finance_bp.route("/incomes", methods=["GET", "POST"])
@login_required
@role_required("admin")
def incomes():
    form = IncomeForm()
    if form.validate_on_submit():
        cat = None
        if form.category.data:
            cat = IncomeCategory.query.filter_by(name=form.category.data.strip()).first()
            if not cat:
                cat = IncomeCategory(name=form.category.data.strip())
                db.session.add(cat)
                db.session.flush()
        db.session.add(
            Income(
                title=form.title.data,
                amount=form.amount.data,
                date=form.date.data,
                description=form.description.data,
                is_recurring=form.is_recurring.data,
                recurrence=form.recurrence.data,
                category_id=cat.id if cat else None,
            )
        )
        db.session.commit()
        flash("Gelir kaydı eklendi.", "success")
        return redirect(url_for("finance.incomes"))

    records = Income.query.order_by(Income.date.desc()).all()
    return render_template("finance/incomes.html", form=form, records=records)


@finance_bp.route("/expenses", methods=["GET", "POST"])
@login_required
@role_required("admin")
def expenses():
    form = ExpenseForm()
    if form.validate_on_submit():
        cat = None
        if form.category.data:
            cat = ExpenseCategory.query.filter_by(name=form.category.data.strip()).first()
            if not cat:
                cat = ExpenseCategory(name=form.category.data.strip())
                db.session.add(cat)
                db.session.flush()
        db.session.add(
            Expense(
                title=form.title.data,
                amount=form.amount.data,
                date=form.date.data,
                description=form.description.data,
                is_recurring=form.is_recurring.data,
                recurrence=form.recurrence.data,
                category_id=cat.id if cat else None,
            )
        )
        db.session.commit()
        flash("Gider kaydı eklendi.", "success")
        return redirect(url_for("finance.expenses"))

    records = Expense.query.order_by(Expense.date.desc()).all()
    return render_template("finance/expenses.html", form=form, records=records)


@finance_bp.route("/forecast")
@login_required
@role_required("admin")
def forecast():
    from datetime import date

    today = date.today()
    month_income = reservation_income_for_month(today.year, today.month) + actual_total(Income, today.year, today.month)
    month_expense = actual_total(Expense, today.year, today.month)
    projection = forecast_next_months(3)
    return render_template(
        "finance/forecast.html", month_income=month_income, month_expense=month_expense, projection=projection
    )
