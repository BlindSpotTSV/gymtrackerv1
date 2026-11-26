import pytest

from app import create_app
from app.extensions import db
from app.models.entities import Exercise, User


@pytest.fixture()
def app(tmp_path):
    database_path = tmp_path / "test.db"
    app = create_app({
        "TESTING": True,
        "SECRET_KEY": "test-secret",
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database_path}",
        "WTF_CSRF_ENABLED": False,
    })
    with app.app_context():
        db.create_all()
        member = User(
            full_name="Test Member",
            email="member@example.com",
            role="member",
            is_active=True,
        )
        member.set_password("test-password-123")
        coach = User(
            full_name="Test Coach",
            email="coach@example.com",
            role="coach",
            is_active=True,
        )
        coach.set_password("test-password-123")
        exercise = Exercise(
            name="Test Bench Press",
            muscle_group="Chest",
            equipment="Barbell",
            difficulty="beginner",
            is_active=True,
        )
        db.session.add_all([member, coach, exercise])
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()
