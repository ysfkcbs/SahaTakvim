import os

from dotenv import load_dotenv
from flask import Flask

from .extensions import csrf, db, login_manager, migrate


def create_app(config_name=None):
    load_dotenv()
    app = Flask(__name__, instance_relative_config=True)

    os.makedirs(app.instance_path, exist_ok=True)

    env = config_name or os.getenv("FLASK_ENV", "development")
    from .config import config_map

    app.config.from_object(config_map.get(env, config_map["default"]))

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from .models import User

        return User.query.get(int(user_id))

    register_blueprints(app)
    register_shell_context(app)
    register_cli_commands(app)

    return app


def register_blueprints(app):
    from .auth.routes import auth_bp
    from .fields.routes import fields_bp
    from .finance.routes import finance_bp
    from .main.routes import main_bp
    from .reports.routes import reports_bp

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
    app.register_blueprint(reports_bp, url_prefix="/reports")


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
    from .models import Field, Setting, User

    @app.cli.command("seed-admin")
    def seed_admin():
        username = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
        password = os.getenv("DEFAULT_ADMIN_PASSWORD", "Admin123!")

        admin = User.query.filter_by(username=username).first()
        if not admin:
            admin = User(username=username, role="admin", password_hash=generate_password_hash(password))
            db.session.add(admin)

        if Field.query.count() == 0:
            db.session.add(Field(name="Merkez Saha", rental_price=2500, subscription_price=2000, open_hour=17, close_hour=2))

        if Setting.query.count() == 0:
            db.session.add_all(
                [
                    Setting(key="currency", value="TRY"),
                    Setting(key="default_open_hour", value="17"),
                    Setting(key="default_close_hour", value="2"),
                ]
            )

        db.session.commit()
        click.echo(f"Admin ready: {username}")
