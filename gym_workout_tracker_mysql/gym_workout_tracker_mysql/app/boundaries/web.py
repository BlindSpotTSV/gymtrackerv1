from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.controllers.errors import DomainError
from app.controllers.services import (
    AdminController,
    AuthController,
    CoachController,
    WorkoutController,
)
from app.models.entities import WorkoutPlan
from app.repositories import ExerciseRepository, UserRepository

bp = Blueprint("web", __name__)


def web_role_required(*roles):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if not current_user.is_active or current_user.role not in roles:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


@bp.get("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("web.dashboard"))
    return redirect(url_for("web.login"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("web.dashboard"))
    if request.method == "POST":
        try:
            user = AuthController.authenticate(
                request.form.get("email"),
                request.form.get("password"),
            )
            login_user(user, remember=bool(request.form.get("remember")))
            flash("Login berhasil.", "success")
            return redirect(url_for("web.dashboard"))
        except DomainError as error:
            flash(error.message, "danger")
    return render_template("login.html")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            AuthController.register_member(request.form)
            flash("Registrasi berhasil. Silakan login.", "success")
            return redirect(url_for("web.login"))
        except DomainError as error:
            flash(error.message, "danger")
    return render_template("register.html")


@bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("Anda telah logout.", "info")
    return redirect(url_for("web.login"))


@bp.get("/dashboard")
@login_required
def dashboard():
    if current_user.role == "member":
        recent_workouts = WorkoutController.history(current_user.id)[:5]
        plans = WorkoutController.member_plans(current_user.id)
        return render_template(
            "dashboard.html",
            recent_workouts=recent_workouts,
            plans=plans,
        )
    if current_user.role == "coach":
        clients = CoachController.clients(current_user.id)
        requests_list = CoachController.plan_requests(current_user.id)
        return render_template(
            "dashboard.html",
            clients=clients,
            requests_list=requests_list,
        )
    status = AdminController.system_status()
    return render_template("dashboard.html", status=status)


@bp.get("/member/exercises")
@web_role_required("member")
def member_exercises():
    exercises = ExerciseRepository.active_exercises()
    return render_template("member_exercises.html", exercises=exercises)


@bp.route("/member/workouts/new", methods=["GET", "POST"])
@web_role_required("member")
def new_workout():
    exercises = ExerciseRepository.active_exercises()
    plans = WorkoutController.member_plans(current_user.id)

    if request.method == "POST":
        exercise_ids = request.form.getlist("exercise_id")
        set_numbers = request.form.getlist("set_number")
        reps_list = request.form.getlist("reps")
        weights = request.form.getlist("weight_kg")
        warmups = request.form.getlist("is_warmup")

        sets_payload = []
        for i, exercise_id in enumerate(exercise_ids):
            if not exercise_id:
                continue
            sets_payload.append({
                "exercise_id": exercise_id,
                "set_number": set_numbers[i],
                "reps": reps_list[i],
                "weight_kg": weights[i],
                "is_warmup": str(i) in warmups,
            })

        try:
            WorkoutController.log_workout(
                current_user,
                {
                    "name": request.form.get("name"),
                    "notes": request.form.get("notes"),
                    "plan_id": request.form.get("plan_id") or None,
                    "sets": sets_payload,
                },
            )
            flash("Workout berhasil disimpan.", "success")
            return redirect(url_for("web.workout_history"))
        except (DomainError, ValueError) as error:
            message = error.message if isinstance(error, DomainError) else str(error)
            flash(message, "danger")

    return render_template(
        "workout_form.html",
        exercises=exercises,
        plans=plans,
    )


@bp.get("/member/workouts")
@web_role_required("member")
def workout_history():
    workouts = WorkoutController.history(current_user.id)
    return render_template("workouts.html", workouts=workouts)


@bp.route("/member/plan-request", methods=["GET", "POST"])
@web_role_required("member")
def plan_request():
    coaches = UserRepository.active_coaches()
    if request.method == "POST":
        try:
            WorkoutController.request_plan(current_user, request.form)
            flash("Permintaan program latihan berhasil dikirim.", "success")
            return redirect(url_for("web.dashboard"))
        except DomainError as error:
            flash(error.message, "danger")
    return render_template("plan_request.html", coaches=coaches)


@bp.get("/coach/clients")
@web_role_required("coach")
def coach_clients():
    clients = CoachController.clients(current_user.id)
    return render_template("coach_clients.html", clients=clients)


@bp.get("/coach/requests")
@web_role_required("coach")
def coach_requests():
    requests_list = CoachController.plan_requests(current_user.id)
    return render_template("coach_requests.html", requests_list=requests_list)


@bp.post("/coach/requests/<int:request_id>/decision")
@web_role_required("coach")
def coach_decision(request_id):
    accept = request.form.get("decision") == "accept"
    try:
        CoachController.decide_plan_request(current_user.id, request_id, accept)
        flash("Permintaan berhasil diproses.", "success")
    except DomainError as error:
        flash(error.message, "danger")
    return redirect(url_for("web.coach_requests"))


@bp.route("/coach/plans/new", methods=["GET", "POST"])
@web_role_required("coach")
def coach_create_plan():
    clients = CoachController.clients(current_user.id)
    exercises = ExerciseRepository.active_exercises()

    if request.method == "POST":
        exercise_ids = request.form.getlist("exercise_id")
        target_sets = request.form.getlist("target_sets")
        target_reps = request.form.getlist("target_reps")
        rests = request.form.getlist("rest_seconds")
        plan_exercises = []
        for i, exercise_id in enumerate(exercise_ids):
            if exercise_id:
                plan_exercises.append({
                    "exercise_id": exercise_id,
                    "target_sets": target_sets[i],
                    "target_reps": target_reps[i],
                    "rest_seconds": rests[i],
                })
        try:
            CoachController.create_plan(
                current_user.id,
                {
                    "member_id": request.form.get("member_id"),
                    "title": request.form.get("title"),
                    "description": request.form.get("description"),
                    "exercises": plan_exercises,
                },
            )
            flash("Workout plan berhasil dibuat dan diberikan kepada Member.", "success")
            return redirect(url_for("web.coach_clients"))
        except DomainError as error:
            flash(error.message, "danger")

    return render_template(
        "coach_plan_form.html",
        clients=clients,
        exercises=exercises,
    )


@bp.get("/coach/clients/<int:member_id>/progress")
@web_role_required("coach")
def coach_progress(member_id):
    try:
        progress = CoachController.client_progress(current_user.id, member_id)
    except DomainError as error:
        abort(error.status_code, description=error.message)
    return render_template("coach_progress.html", progress=progress)


@bp.route("/admin/exercises", methods=["GET", "POST"])
@web_role_required("admin")
def admin_exercises():
    if request.method == "POST":
        try:
            AdminController.create_exercise(request.form)
            flash("Exercise berhasil ditambahkan.", "success")
            return redirect(url_for("web.admin_exercises"))
        except DomainError as error:
            flash(error.message, "danger")
    exercises = AdminController.exercises()
    return render_template("admin_exercises.html", exercises=exercises)


@bp.route("/admin/users", methods=["GET", "POST"])
@web_role_required("admin")
def admin_users():
    if request.method == "POST":
        try:
            AdminController.create_user(request.form)
            flash("Pengguna berhasil dibuat.", "success")
            return redirect(url_for("web.admin_users"))
        except DomainError as error:
            flash(error.message, "danger")
    users = AdminController.users()
    coaches = UserRepository.active_coaches()
    return render_template("admin_users.html", users=users, coaches=coaches)


@bp.post("/admin/users/<int:user_id>/update")
@web_role_required("admin")
def admin_update_user(user_id):
    payload = {"is_active": request.form.get("is_active") == "1"}
    if request.form.get("coach_id") is not None:
        coach_value = request.form.get("coach_id", "").strip()
        if coach_value:
            payload["coach_id"] = coach_value
        else:
            payload["coach_id"] = None

    if user_id == current_user.id and payload["is_active"] is False:
        flash("Admin tidak dapat menonaktifkan akunnya sendiri.", "danger")
        return redirect(url_for("web.admin_users"))

    try:
        AdminController.update_user(user_id, payload)
        flash("Data pengguna berhasil diperbarui.", "success")
    except DomainError as error:
        flash(error.message, "danger")
    return redirect(url_for("web.admin_users"))


@bp.post("/admin/exercises/<int:exercise_id>/toggle")
@web_role_required("admin")
def admin_toggle_exercise(exercise_id):
    exercise = ExerciseRepository.get_by_id(exercise_id)
    if not exercise:
        abort(404)
    try:
        AdminController.update_exercise(
            exercise_id,
            {"is_active": not exercise.is_active},
        )
        flash("Status exercise berhasil diperbarui.", "success")
    except DomainError as error:
        flash(error.message, "danger")
    return redirect(url_for("web.admin_exercises"))


@bp.get("/admin/status")
@web_role_required("admin")
def admin_status():
    status = AdminController.system_status()
    return render_template("admin_status.html", status=status)
