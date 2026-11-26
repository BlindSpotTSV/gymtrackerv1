from flask import Blueprint, jsonify, request
from flask_login import current_user

from app.boundaries.common import role_required
from app.controllers.errors import DomainError
from app.controllers.services import AdminController
from app.serializers import exercise_dict, user_summary

bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@bp.get("/exercises")
@role_required("admin")
def exercises():
    items = AdminController.exercises()
    return jsonify(exercises=[exercise_dict(item) for item in items]), 200


@bp.post("/exercises")
@role_required("admin")
def create_exercise():
    item = AdminController.create_exercise(request.get_json(silent=True) or {})
    return jsonify(message="Exercise created.", exercise=exercise_dict(item)), 201


@bp.patch("/exercises/<int:exercise_id>")
@role_required("admin")
def update_exercise(exercise_id):
    item = AdminController.update_exercise(exercise_id, request.get_json(silent=True) or {})
    return jsonify(message="Exercise updated.", exercise=exercise_dict(item)), 200


@bp.get("/users")
@role_required("admin")
def users():
    items = AdminController.users()
    return jsonify(users=[user_summary(item) for item in items]), 200


@bp.post("/users")
@role_required("admin")
def create_user():
    item = AdminController.create_user(request.get_json(silent=True) or {})
    return jsonify(message="User created.", user=user_summary(item)), 201


@bp.patch("/users/<int:user_id>")
@role_required("admin")
def update_user(user_id):
    payload = request.get_json(silent=True) or {}
    if user_id == current_user.id and payload.get("is_active") is False:
        raise DomainError("An administrator cannot deactivate their own account.", 409)
    item = AdminController.update_user(user_id, payload)
    return jsonify(message="User updated.", user=user_summary(item)), 200


@bp.get("/system-status")
@role_required("admin")
def system_status():
    return jsonify(status=AdminController.system_status()), 200
