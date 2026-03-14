from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db
from app.main.utils import role_required
from app.models import User

from .forms import LoginForm, UserCreateForm, UserUpdateForm


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
    form = UserCreateForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        if User.query.filter_by(username=username).first():
            flash("Bu kullanıcı adı zaten kullanılıyor.", "danger")
        else:
            user = User(username=username, role=form.role.data, is_active_user=form.is_active_user.data)
            user.set_password(form.password.data or "ChangeMe123!")
            db.session.add(user)
            db.session.commit()
            flash("Kullanıcı oluşturuldu.", "success")
            return redirect(url_for("auth.users"))

    user_list = User.query.order_by(User.created_at.desc()).all()
    return render_template("auth/users.html", form=form, users=user_list)


@auth_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = UserUpdateForm(obj=user)

    if form.validate_on_submit():
        username = form.username.data.strip()
        duplicate = User.query.filter(User.username == username, User.id != user.id).first()
        if duplicate:
            flash("Bu kullanıcı adı başka bir kullanıcıya ait.", "danger")
            return render_template("auth/user_edit.html", form=form, user=user)

        user.username = username
        user.role = form.role.data
        user.is_active_user = form.is_active_user.data

        if form.password.data:
            user.set_password(form.password.data)

        if user.id == current_user.id and not user.is_active_user:
            flash("Kendi hesabınızı pasife alamazsınız.", "danger")
            user.is_active_user = True

        db.session.commit()
        flash("Kullanıcı güncellendi.", "success")
        return redirect(url_for("auth.users"))

    return render_template("auth/user_edit.html", form=form, user=user)


@auth_bp.route("/users/<int:user_id>/toggle-status", methods=["POST"])
@login_required
@role_required("admin")
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id and user.is_active_user:
        flash("Kendi hesabınızı pasife alamazsınız.", "danger")
        return redirect(url_for("auth.users"))

    user.is_active_user = not user.is_active_user
    db.session.commit()
    flash("Kullanıcı durumu güncellendi.", "success")
    return redirect(url_for("auth.users"))
