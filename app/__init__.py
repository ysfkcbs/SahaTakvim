import os
from urllib.parse import urlparse

from dotenv import load_dotenv
from flask import Flask, request

from .extensions import csrf, db, login_manager, migrate


def _database_log_context(database_uri):
    parsed = urlparse(database_uri)
    return {
        "scheme": parsed.scheme or "unknown",
        "host": parsed.hostname or "local-file",
        "database": (parsed.path or "").lstrip("/") or "memory",
        "uses_sqlite": parsed.scheme.startswith("sqlite"),
    }


def create_app(config_name=None):
    load_dotenv()
    app = Flask(__name__, instance_relative_config=True)

    os.makedirs(app.instance_path, exist_ok=True)

    env = config_name or os.getenv("FLASK_ENV", "development")
    from .config import config_map

    app.config.from_object(config_map.get(env, config_map["default"]))
    db_context = _database_log_context(app.config["SQLALCHEMY_DATABASE_URI"])
    app.logger.warning(
        "DATABASE_CONFIG env=%s scheme=%s host=%s database=%s uses_sqlite=%s",
        env,
        db_context["scheme"],
        db_context["host"],
        db_context["database"],
        db_context["uses_sqlite"],
    )

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    @app.after_request
    def disable_dynamic_html_cache(response):
        # Keep authenticated calendar/dashboard pages fresh across mobile browsers and PWA shells.
        if request.method == "GET" and response.mimetype == "text/html":
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response

    @login_manager.user_loader
    def load_user(user_id):
        from .models import User

        return db.session.get(User, int(user_id))

    register_blueprints(app)
    register_shell_context(app)
    register_cli_commands(app)

    return app


def register_blueprints(app):
    from .auth.routes import auth_bp
    from .fields.routes import fields_bp
    from .finance.routes import finance_bp
    from .main.routes import main_bp
    from .partners.routes import partners_bp
    from .reports.routes import reports_bp
    from .tournaments.routes import tournaments_bp

    # Import calendar module defensively to avoid environment-specific symbol import issues.
    from .calendar import routes as calendar_routes

    calendar_bp = getattr(calendar_routes, "calendar_bp", None) or getattr(calendar_routes, "bp", None)
    if calendar_bp is None:
        raise RuntimeError("Calendar blueprint could not be loaded from app.calendar.routes")

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(calendar_bp, url_prefix="/calendar")
    app.register_blueprint(fields_bp, url_prefix="/fields")
    app.register_blueprint(finance_bp, url_prefix="/finance")
    app.register_blueprint(partners_bp, url_prefix="/partners")
    app.register_blueprint(reports_bp, url_prefix="/reports")
    app.register_blueprint(tournaments_bp, url_prefix="/tournaments")


def register_shell_context(app):
    from . import models
    from .extensions import db

    @app.shell_context_processor
    def shell_context():
        return {"db": db, "models": models}


def register_cli_commands(app):
    import click
    from werkzeug.security import generate_password_hash

    from .extensions import db
    from .models import ExpenseCategory, Field, IncomeCategory, Setting, User

    @app.cli.command("seed-admin")
    def seed_admin():
        username = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
        password = os.getenv("DEFAULT_ADMIN_PASSWORD", "Admin123!")

        admin = User.query.filter_by(username=username).first()
        if not admin:
            admin = User(username=username, role="admin", password_hash=generate_password_hash(password))
            db.session.add(admin)

        if Field.query.count() == 0:
            db.session.add(Field(name="Merkez Saha", rental_price=2500, subscription_price=2000, open_hour=19, close_hour=2))

        if Setting.query.count() == 0:
            db.session.add_all(
                [
                    Setting(key="currency", value="TRY"),
                    Setting(key="default_open_hour", value="19"),
                    Setting(key="default_close_hour", value="2"),
                ]
            )

        if IncomeCategory.query.count() == 0:
            db.session.add_all([IncomeCategory(name=name) for name in ("Kira Geliri", "Turnuva Geliri")])

        if ExpenseCategory.query.count() == 0:
            db.session.add_all(
                [
                    ExpenseCategory(name=name)
                    for name in ("Kira Gideri", "Kredi Kartı Gideri", "Muhasebe Gideri", "Harici Gider")
                ]
            )

        db.session.commit()
        click.echo(f"Admin ready: {username}")
