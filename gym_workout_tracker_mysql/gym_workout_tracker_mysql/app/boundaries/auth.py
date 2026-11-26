from flask import Blueprint, jsonify, request
from flask_login import current_user, login_user, logout_user
from flask_wtf.csrf import generate_csrf

from app.controllers.services import AuthController
from app.serializers import user_summary

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.get("/csrf")
def csrf_token():
    return jsonify(csrf_token=generate_csrf())


@bp.post("/register")
def register():
    member = AuthController.register_member(request.get_json(silent=True) or {})
    return jsonify(message="Member registered.", user=user_summary(member)), 201


@bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    user = AuthController.authenticate(payload.get("email"), payload.get("password"))
    login_user(user, remember=bool(payload.get("remember", False)))
    return jsonify(
        message="Login successful.",
        user=user_summary(user),
        csrf_token=generate_csrf(),
    ), 200


@bp.post("/logout")
def logout():
    if not current_user.is_authenticated:
        return jsonify(error="Authentication required."), 401
    logout_user()
    return jsonify(message="Logout successful."), 200


@bp.get("/me")
def me():
    if not current_user.is_authenticated:
        return jsonify(error="Authentication required."), 401
    return jsonify(user=user_summary(current_user)), 200
