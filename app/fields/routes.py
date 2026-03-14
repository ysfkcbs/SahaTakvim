from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import login_required

from app.extensions import db
from app.fields.forms import FieldForm
from app.main.utils import role_required
from app.models import Field


fields_bp = Blueprint("fields", __name__)


@fields_bp.route("/")
@login_required
@role_required("admin")
def list_fields():
    return render_template("fields/list.html", fields=Field.query.order_by(Field.name.asc()).all())


@fields_bp.route("/create", methods=["GET", "POST"])
@login_required
@role_required("admin")
def create_field():
    form = FieldForm()
    if form.validate_on_submit():
        field = Field()
        form.populate_obj(field)
        db.session.add(field)
        db.session.commit()
        flash("Saha eklendi.", "success")
        return redirect(url_for("fields.list_fields"))
    return render_template("fields/form.html", form=form, title="Yeni Saha")


@fields_bp.route("/<int:field_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_field(field_id):
    field = Field.query.get_or_404(field_id)
    form = FieldForm(obj=field)
    if form.validate_on_submit():
        form.populate_obj(field)
        db.session.commit()
        flash("Saha güncellendi.", "success")
        return redirect(url_for("fields.list_fields"))
    return render_template("fields/form.html", form=form, title="Saha Düzenle")
