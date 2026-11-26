import click
from flask import Flask, abort, jsonify, render_template
from flask_wtf.csrf import CSRFError

from app.config import Config
from app.extensions import csrf, db, login_manager
from app.controllers.errors import DomainError


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = "web.login"

    from app.models.entities import User, Exercise
    from app.repositories import UserRepository

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return UserRepository.get_by_id(int(user_id))
        except (TypeError, ValueError):
            return None

    from app.boundaries.auth import bp as auth_bp
    from app.boundaries.member import bp as member_bp
    from app.boundaries.coach import bp as coach_bp
    from app.boundaries.admin import bp as admin_bp
    from app.boundaries.web import bp as web_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(member_bp)
    app.register_blueprint(coach_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(web_bp)

    @app.errorhandler(DomainError)
    def handle_domain_error(error):
        return jsonify(error=error.message), error.status_code

    @app.errorhandler(CSRFError)
    def handle_csrf_error(_error):
        return jsonify(error="CSRF validation failed. Reload the page and try again."), 400

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("error.html", code=403, message="Akses ditolak."), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("error.html", code=404, message="Halaman tidak ditemukan."), 404

    @app.cli.command("init-db")
    def init_db_command():
        db.create_all()
        click.echo("Tabel SQLAlchemy berhasil dibuat.")

    @app.cli.command("create-admin")
    @click.option("--name", prompt="Nama administrator")
    @click.option("--email", prompt="Email administrator")
    @click.password_option()
    def create_admin_command(name, email, password):
        normalized_email = email.strip().lower()
        if UserRepository.get_by_email(normalized_email):
            raise click.ClickException("Email sudah digunakan.")
        if len(password) < 10:
            raise click.ClickException("Password minimal 10 karakter.")
        admin = User(
            full_name=name.strip(),
            email=normalized_email,
            role="admin",
            is_active=True,
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        click.echo(f"Admin {normalized_email} berhasil dibuat.")

    @app.cli.command("seed-exercises")
    def seed_exercises_command():
        starter = [
            ("Barbell Bench Press", "Chest", "Barbell", "intermediate"),
            ("Incline Dumbbell Press", "Chest", "Dumbbell", "beginner"),
            ("Back Squat", "Quadriceps", "Barbell", "intermediate"),
            ("Romanian Deadlift", "Hamstrings", "Barbell", "intermediate"),
            ("Lat Pulldown", "Back", "Cable", "beginner"),
            ("Seated Cable Row", "Back", "Cable", "beginner"),
            ("Overhead Press", "Shoulders", "Barbell", "intermediate"),
            ("Dumbbell Biceps Curl", "Biceps", "Dumbbell", "beginner"),
            ("Triceps Pushdown", "Triceps", "Cable", "beginner"),
            ("Standing Calf Raise", "Calves", "Machine", "beginner"),
        ]
        inserted = 0
        for name, muscle, equipment, difficulty in starter:
            if not Exercise.query.filter_by(name=name).first():
                db.session.add(Exercise(
                    name=name,
                    muscle_group=muscle,
                    equipment=equipment,
                    difficulty=difficulty,
                    is_active=True,
                ))
                inserted += 1
        db.session.commit()
        click.echo(f"{inserted} exercise baru berhasil ditambahkan.")

    return app
