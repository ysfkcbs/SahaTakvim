from datetime import date
from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.main.utils import role_required
from app.models import PARTNER_NAMES, PartnerShare

from .forms import MONTH_CHOICES, PartnerShareForm


partners_bp = Blueprint("partners", __name__)


@partners_bp.route("/ledger", methods=["GET", "POST"])
@login_required
@role_required("admin")
def ledger():
    form = PartnerShareForm()
    if form.validate_on_submit():
        share = PartnerShare.query.filter_by(
            year=form.year.data, month=form.month.data, partner_name=form.partner_name.data
        ).first()
        if not share:
            share = PartnerShare(year=form.year.data, month=form.month.data, partner_name=form.partner_name.data)
            db.session.add(share)
        share.amount = form.amount.data
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("Bu ay/ortak için kayıt az önce başka bir kullanıcı tarafından güncellendi. Sayfayı yenileyip tekrar deneyin.", "danger")
        else:
            flash("Ortaklık payı kaydedildi.", "success")
            return redirect(url_for("partners.ledger", year=form.year.data))

    selected_year = request.args.get("year", date.today().year, type=int)

    shares = PartnerShare.query.filter_by(year=selected_year).all()
    by_month = {month: {name: Decimal("0") for name in PARTNER_NAMES} for month, _ in MONTH_CHOICES}
    for share in shares:
        by_month[share.month][share.partner_name] = share.amount

    month_rows = []
    yearly_totals = {name: Decimal("0") for name in PARTNER_NAMES}
    for month, month_label in MONTH_CHOICES:
        amounts = by_month[month]
        for name in PARTNER_NAMES:
            yearly_totals[name] += amounts[name]
        month_rows.append(
            {
                "month": month,
                "label": month_label,
                "amounts": amounts,
                "total": sum(amounts.values()),
            }
        )

    return render_template(
        "partners/ledger.html",
        form=form,
        partner_names=PARTNER_NAMES,
        month_rows=month_rows,
        yearly_totals=yearly_totals,
        yearly_grand_total=sum(yearly_totals.values()),
        selected_year=selected_year,
        prev_year=selected_year - 1,
        next_year=selected_year + 1,
    )
