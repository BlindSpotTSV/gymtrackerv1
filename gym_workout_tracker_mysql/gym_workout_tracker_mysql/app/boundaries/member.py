from flask import Blueprint, jsonify, request
from flask_login import current_user

from app.boundaries.common import role_required
from app.controllers.services import WorkoutController
from app.repositories import ExerciseRepository, UserRepository
from app.serializers import (
    exercise_dict, plan_request_dict, user_summary, workout_dict, workout_plan_dict
)

bp = Blueprint("member", __name__, url_prefix="/api")


@bp.get("/exercises")
@role_required("member")
def list_exercises():
    items = ExerciseRepository.active_exercises()
    return jsonify(exercises=[exercise_dict(item) for item in items]), 200


@bp.post("/workouts")
@role_required("member")
def create_workout():
    workout = WorkoutController.log_workout(current_user, request.get_json(silent=True) or {})
    return jsonify(message="Workout saved.", workout=workout_dict(workout)), 201


@bp.get("/workout-plans")
@role_required("member")
def workout_plans():
    items = WorkoutController.member_plans(current_user.id)
    return jsonify(workout_plans=[workout_plan_dict(item) for item in items]), 200


@bp.get("/workouts")
@role_required("member")
def workout_history():
    items = WorkoutController.history(current_user.id)
    return jsonify(workouts=[workout_dict(item) for item in items]), 200


@bp.get("/workouts/<int:workout_id>")
@role_required("member")
def workout_detail(workout_id):
    item = WorkoutController.workout_detail(current_user.id, workout_id)
    return jsonify(workout=workout_dict(item)), 200


@bp.get("/coaches")
@role_required("member")
def list_coaches():
    items = UserRepository.active_coaches()
    return jsonify(coaches=[user_summary(item) for item in items]), 200


@bp.post("/plan-requests")
@role_required("member")
def request_plan():
    record = WorkoutController.request_plan(current_user, request.get_json(silent=True) or {})
    return jsonify(message="Workout plan request submitted.", request=plan_request_dict(record)), 201
