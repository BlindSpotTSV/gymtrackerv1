from flask import Blueprint, jsonify, request
from flask_login import current_user

from app.boundaries.common import role_required
from app.controllers.services import CoachController
from app.serializers import plan_request_dict, user_summary, workout_dict, workout_plan_dict

bp = Blueprint("coach", __name__, url_prefix="/api/coach")


@bp.get("/clients")
@role_required("coach")
def clients():
    items = CoachController.clients(current_user.id)
    return jsonify(clients=[user_summary(item) for item in items]), 200


@bp.get("/plan-requests")
@role_required("coach")
def plan_requests():
    items = CoachController.plan_requests(current_user.id)
    return jsonify(requests=[plan_request_dict(item) for item in items]), 200


@bp.post("/plan-requests/<int:request_id>/decision")
@role_required("coach")
def decide_plan_request(request_id):
    payload = request.get_json(silent=True) or {}
    accept = payload.get("accept")
    if not isinstance(accept, bool):
        return jsonify(error="accept must be a boolean."), 400
    record = CoachController.decide_plan_request(current_user.id, request_id, accept)
    return jsonify(message="Request processed.", request=plan_request_dict(record)), 200


@bp.post("/plans")
@role_required("coach")
def create_plan():
    plan = CoachController.create_plan(current_user.id, request.get_json(silent=True) or {})
    return jsonify(message="Workout plan assigned.", plan=workout_plan_dict(plan)), 201


@bp.get("/clients/<int:member_id>/progress")
@role_required("coach")
def client_progress(member_id):
    result = CoachController.client_progress(current_user.id, member_id)
    return jsonify(
        member=user_summary(result["member"]),
        workout_count=result["workout_count"],
        total_volume_kg_reps=result["total_volume_kg_reps"],
        recent_workouts=[workout_dict(item) for item in result["recent_workouts"]],
    ), 200
