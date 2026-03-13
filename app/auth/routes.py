from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db
from app.main.utils import role_required
from app.models import User

from .forms import LoginForm, UserForm


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data) and user.is_active_user:
            login_user(user, remember=True)
            flash("Hoş geldiniz!", "success")
            return redirect(request.args.get("next") or url_for("main.index"))
        flash("Geçersiz giriş bilgileri.", "danger")
    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Oturum kapatıldı.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/users", methods=["GET", "POST"])
@login_required
@role_required("admin")
def users():
    form = UserForm()
    if form.validate_on_submit():
        user = User(username=form.username.data.strip(), role=form.role.data)
        user.set_password(form.password.data or "ChangeMe123!")
        db.session.add(user)
        db.session.commit()
        flash("Kullanıcı oluşturuldu.", "success")
        return redirect(url_for("auth.users"))

    user_list = User.query.order_by(User.created_at.desc()).all()
    return render_template("auth/users.html", form=form, users=user_list)
