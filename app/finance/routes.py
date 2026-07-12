from datetime import date
from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.finance.forms import DailyClosingForm, TransactionForm
from app.finance.services import actual_total, forecast_next_months, reservation_income_for_month
from app.main.utils import role_required
from app.models import DailyClosing, Expense, ExpenseCategory, Income, IncomeCategory


finance_bp = Blueprint("finance", __name__)


def _flash_form_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"{getattr(form, field).label.text}: {error}", "danger")


def _set_category_choices(form):
    form.income_category_id.choices = [(0, "Kategori seçin")] + [
        (c.id, c.name) for c in IncomeCategory.query.order_by(IncomeCategory.name.asc()).all()
    ]
    form.expense_category_id.choices = [(0, "Kategori seçin")] + [
        (c.id, c.name) for c in ExpenseCategory.query.order_by(ExpenseCategory.name.asc()).all()
    ]


def _build_transaction_rows():
    rows = []
    for record in Income.query.order_by(Income.date.desc(), Income.id.desc()).all():
        rows.append(
            {
                "id": record.id,
                "kind": "income",
                "kind_label": "Gelir",
                "title": record.title,
                "amount": record.amount,
                "date": record.date,
                "description": record.description,
                "category": record.category.name if record.category else None,
                "is_recurring": record.is_recurring,
                "is_paid": record.is_paid,
                "edit_url": url_for("finance.edit_income", record_id=record.id),
                "delete_url": url_for("finance.delete_income", record_id=record.id),
            }
        )

    for record in Expense.query.order_by(Expense.date.desc(), Expense.id.desc()).all():
        rows.append(
            {
                "id": record.id,
                "kind": "expense",
                "kind_label": "Gider",
                "title": record.title,
                "amount": record.amount,
                "date": record.date,
                "description": record.description,
                "category": record.category.name if record.category else None,
                "is_recurring": record.is_recurring,
                "is_paid": record.is_paid,
                "edit_url": url_for("finance.edit_expense", record_id=record.id),
                "delete_url": url_for("finance.delete_expense", record_id=record.id),
            }
        )

    rows.sort(key=lambda item: (item["date"], item["id"]), reverse=True)
    return rows


def _render_balance_page(form, editing_record=None, form_mode_title="Yeni Kayıt", submit_label="Kaydet"):
    from datetime import date

    today = date.today()
    month_income = reservation_income_for_month(today.year, today.month) + actual_total(Income, today.year, today.month)
    month_expense = actual_total(Expense, today.year, today.month)
    projection = forecast_next_months(3)
    return render_template(
        "finance/forecast.html",
        month_income=month_income,
        month_expense=month_expense,
        projection=projection,
        form=form,
        records=_build_transaction_rows(),
        editing_record=editing_record,
        form_mode_title=form_mode_title,
        submit_label=submit_label,
        cancel_url=url_for("finance.forecast"),
    )


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
        return redirect(
            url_for(
                "finance.daily_closing",
                year=form.closing_date.data.year,
                month=form.closing_date.data.month,
            )
        )
    elif form.is_submitted():
        _flash_form_errors(form)

    today = date.today()
    selected_year = request.args.get("year", today.year, type=int)
    selected_month = request.args.get("month", today.month, type=int)
    if selected_month < 1 or selected_month > 12:
        selected_year = today.year
        selected_month = today.month

    if selected_month == 1:
        prev_year, prev_month = selected_year - 1, 12
    else:
        prev_year, prev_month = selected_year, selected_month - 1

    if selected_month == 12:
        next_year, next_month = selected_year + 1, 1
    else:
        next_year, next_month = selected_year, selected_month + 1

    all_closings = DailyClosing.query.order_by(DailyClosing.closing_date.desc()).all()
    month_closings = [
        closing
        for closing in all_closings
        if closing.closing_date.year == selected_year and closing.closing_date.month == selected_month
    ]
    closings = month_closings
    month_card_total = sum((closing.card_total or Decimal("0")) for closing in month_closings)
    month_cash_total = sum((closing.cash_total or Decimal("0")) for closing in month_closings)
    month_iban_total = sum((closing.iban_total or Decimal("0")) for closing in month_closings)
    default_closing_date = today if (selected_year == today.year and selected_month == today.month) else date(selected_year, selected_month, 1)
    return render_template(
        "finance/daily_closing.html",
        form=form,
        closings=closings,
        month_card_total=month_card_total,
        month_cash_total=month_cash_total,
        month_iban_total=month_iban_total,
        current_month_label=f"{selected_month:02d}.{selected_year}",
        default_closing_date=default_closing_date,
        prev_month_url=url_for("finance.daily_closing", year=prev_year, month=prev_month),
        next_month_url=url_for("finance.daily_closing", year=next_year, month=next_month),
    )


@finance_bp.route("/incomes")
@login_required
@role_required("admin")
def incomes():
    return redirect(url_for("finance.forecast"))


@finance_bp.route("/expenses")
@login_required
@role_required("admin")
def expenses():
    return redirect(url_for("finance.forecast"))


@finance_bp.route("/incomes/<int:record_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_income(record_id):
    record = Income.query.get_or_404(record_id)
    form = TransactionForm(
        transaction_kind="income",
        title=record.title,
        amount=record.amount,
        date=record.date,
        income_category_id=record.category_id or 0,
        description=record.description,
        is_recurring=record.is_recurring,
        is_paid=record.is_paid,
        recurrence=record.recurrence,
    )
    _set_category_choices(form)

    if form.validate_on_submit():
        record.title = form.title.data
        record.amount = form.amount.data
        record.date = form.date.data
        record.category_id = form.income_category_id.data or None
        record.description = form.description.data
        record.is_recurring = form.is_recurring.data
        record.is_paid = form.is_paid.data
        record.recurrence = form.recurrence.data
        db.session.commit()
        flash("Gelir kaydı güncellendi.", "success")
        return redirect(url_for("finance.forecast"))
    elif form.is_submitted():
        _flash_form_errors(form)

    return _render_balance_page(form, editing_record=record, form_mode_title="Gelir Düzenle", submit_label="Kaydı Güncelle")


@finance_bp.route("/expenses/<int:record_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_expense(record_id):
    record = Expense.query.get_or_404(record_id)
    form = TransactionForm(
        transaction_kind="expense",
        title=record.title,
        amount=record.amount,
        date=record.date,
        expense_category_id=record.category_id or 0,
        description=record.description,
        is_recurring=record.is_recurring,
        is_paid=record.is_paid,
        recurrence=record.recurrence,
    )
    _set_category_choices(form)

    if form.validate_on_submit():
        record.title = form.title.data
        record.amount = form.amount.data
        record.date = form.date.data
        record.category_id = form.expense_category_id.data or None
        record.description = form.description.data
        record.is_recurring = form.is_recurring.data
        record.is_paid = form.is_paid.data
        record.recurrence = form.recurrence.data
        db.session.commit()
        flash("Gider kaydı güncellendi.", "success")
        return redirect(url_for("finance.forecast"))
    elif form.is_submitted():
        _flash_form_errors(form)

    return _render_balance_page(form, editing_record=record, form_mode_title="Gider Düzenle", submit_label="Kaydı Güncelle")


@finance_bp.route("/incomes/<int:record_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_income(record_id):
    record = Income.query.get_or_404(record_id)
    db.session.delete(record)
    db.session.commit()
    flash("Gelir kaydı silindi.", "warning")
    return redirect(url_for("finance.forecast"))


@finance_bp.route("/expenses/<int:record_id>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_expense(record_id):
    record = Expense.query.get_or_404(record_id)
    db.session.delete(record)
    db.session.commit()
    flash("Gider kaydı silindi.", "warning")
    return redirect(url_for("finance.forecast"))


@finance_bp.route("/forecast", methods=["GET", "POST"])
@login_required
@role_required("admin")
def forecast():
    form = TransactionForm()
    _set_category_choices(form)
    if form.validate_on_submit():
        is_income = form.transaction_kind.data == "income"
        model = Income if is_income else Expense
        category_id = (form.income_category_id.data if is_income else form.expense_category_id.data) or None
        record = model(
            title=form.title.data,
            amount=form.amount.data,
            date=form.date.data,
            category_id=category_id,
            description=form.description.data,
            is_recurring=form.is_recurring.data,
            is_paid=form.is_paid.data,
            recurrence=form.recurrence.data,
        )
        db.session.add(record)
        db.session.commit()
        flash("Kayıt eklendi.", "success")
        return redirect(url_for("finance.forecast"))
    elif form.is_submitted():
        _flash_form_errors(form)

    return _render_balance_page(form, editing_record=None, form_mode_title="Yeni Kayıt", submit_label="Kaydet")
