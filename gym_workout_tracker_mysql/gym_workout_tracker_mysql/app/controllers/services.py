from decimal import Decimal, InvalidOperation

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.controllers.errors import DomainError
from app.extensions import db
from app.models.entities import (
    Exercise, PlanRequest, User, Workout, WorkoutPlan,
    WorkoutPlanExercise, WorkoutSet, utc_now,
)
from app.repositories import (
    ExerciseRepository, PlanRequestRepository, UserRepository, WorkoutRepository,
)


class AuthController:
    @staticmethod
    def register_member(payload):
        full_name = str(payload.get("full_name", "")).strip()
        email = str(payload.get("email", "")).strip().lower()
        password = str(payload.get("password", ""))

        if not full_name or len(full_name) > 120:
            raise DomainError("full_name is required and must be at most 120 characters.")
        if "@" not in email or len(email) > 255:
            raise DomainError("A valid email address is required.")
        if len(password) < 10:
            raise DomainError("Password must contain at least 10 characters.")
        if UserRepository.get_by_email(email):
            raise DomainError("An account with that email already exists.", 409)

        member = User(full_name=full_name, email=email, role="member", is_active=True)
        member.set_password(password)
        db.session.add(member)
        db.session.commit()
        return member

    @staticmethod
    def authenticate(email, password):
        user = UserRepository.get_by_email(str(email or "").strip().lower())
        if not user or not user.check_password(str(password or "")) or not user.is_active:
            raise DomainError("Invalid credentials or inactive account.", 401)
        return user


class WorkoutController:
    @staticmethod
    def log_workout(member, payload):
        name = str(payload.get("name", "Workout")).strip()
        sets_payload = payload.get("sets")
        plan_id = payload.get("plan_id")

        if not name or len(name) > 150:
            raise DomainError("Workout name is required and must be at most 150 characters.")
        if not isinstance(sets_payload, list) or not sets_payload:
            raise DomainError("sets must be a non-empty array.")

        plan = None
        if plan_id is not None:
            try:
                plan_id = int(plan_id)
            except (TypeError, ValueError):
                raise DomainError("plan_id must be an integer.")
            plan = WorkoutPlan.query.filter_by(
                id=plan_id, member_id=member.id, status="assigned"
            ).first()
            if not plan:
                raise DomainError("Workout plan not found or not assigned to this member.", 404)

        validated_sets = []
        seen = set()
        for index, item in enumerate(sets_payload, start=1):
            if not isinstance(item, dict):
                raise DomainError(f"sets[{index - 1}] must be an object.")
            try:
                exercise_id = int(item.get("exercise_id"))
                set_number = int(item.get("set_number", index))
                reps = int(item.get("reps"))
                weight = Decimal(str(item.get("weight_kg", 0)))
                rpe_raw = item.get("rpe")
                rpe = Decimal(str(rpe_raw)) if rpe_raw not in (None, "") else None
            except (TypeError, ValueError, InvalidOperation):
                raise DomainError(f"Invalid numeric value in sets[{index - 1}].")

            exercise = ExerciseRepository.get_active_by_id(exercise_id)
            if not exercise:
                raise DomainError(f"Exercise {exercise_id} does not exist or is inactive.", 422)
            if set_number <= 0 or reps <= 0 or weight < 0:
                raise DomainError("set_number and reps must be positive; weight_kg cannot be negative.")
            if rpe is not None and not (Decimal("1") <= rpe <= Decimal("10")):
                raise DomainError("rpe must be between 1 and 10.")
            warmup = item.get("is_warmup", False)
            if not isinstance(warmup, bool):
                raise DomainError("is_warmup must be a boolean.")

            key = (exercise_id, set_number)
            if key in seen:
                raise DomainError("set_number must be unique for each exercise within a workout.")
            seen.add(key)

            validated_sets.append({
                "exercise": exercise,
                "set_number": set_number,
                "reps": reps,
                "weight_kg": weight,
                "rpe": rpe,
                "is_warmup": warmup,
            })

        workout = Workout(
            user_id=member.id,
            plan_id=plan.id if plan else None,
            name=name,
            notes=payload.get("notes"),
            started_at=utc_now(),
            ended_at=utc_now(),
        )
        db.session.add(workout)

        try:
            db.session.flush()
            for item in validated_sets:
                db.session.add(WorkoutSet(
                    workout_id=workout.id,
                    exercise_id=item["exercise"].id,
                    set_number=item["set_number"],
                    reps=item["reps"],
                    weight_kg=item["weight_kg"],
                    rpe=item["rpe"],
                    is_warmup=item["is_warmup"],
                ))
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise DomainError("Workout could not be saved because of a data constraint.", 409)
        except Exception:
            db.session.rollback()
            raise
        return workout

    @staticmethod
    def history(member_id):
        return WorkoutRepository.list_for_user(member_id)

    @staticmethod
    def member_plans(member_id):
        return WorkoutPlan.query.filter_by(
            member_id=member_id,
            status="assigned",
        ).order_by(WorkoutPlan.created_at.desc()).all()

    @staticmethod
    def workout_detail(member_id, workout_id):
        workout = WorkoutRepository.get_owned(workout_id, member_id)
        if not workout:
            raise DomainError("Workout not found.", 404)
        return workout

    @staticmethod
    def request_plan(member, payload):
        try:
            coach_id = int(payload.get("coach_id"))
        except (TypeError, ValueError):
            raise DomainError("coach_id must be an integer.")

        goal = str(payload.get("goal", "")).strip()
        coach = User.query.filter_by(id=coach_id, role="coach", is_active=True).first()
        if not coach:
            raise DomainError("Coach not found or inactive.", 404)
        if not goal or len(goal) > 150:
            raise DomainError("goal is required and must be at most 150 characters.")

        request_record = PlanRequest(
            member_id=member.id,
            coach_id=coach.id,
            goal=goal,
            notes=payload.get("notes"),
            status="pending",
        )
        db.session.add(request_record)
        db.session.commit()
        return request_record

    @staticmethod
    def member_progress(member_id):
        member = User.query.filter_by(id=member_id, role="member").first()
        if not member:
            raise DomainError("Member not found.", 404)
        workout_count = Workout.query.filter_by(user_id=member_id).count()
        volume = (
            db.session.query(func.coalesce(func.sum(WorkoutSet.weight_kg * WorkoutSet.reps), 0))
            .join(Workout, Workout.id == WorkoutSet.workout_id)
            .filter(
                Workout.user_id == member_id,
                WorkoutSet.is_warmup.is_(False),
            )
            .scalar()
        )
        return {
            "member": member,
            "workout_count": workout_count,
            "total_volume_kg_reps": float(volume or 0),
            "recent_workouts": WorkoutRepository.list_for_member(member_id, limit=10),
        }


class CoachController:
    @staticmethod
    def clients(coach_id):
        return UserRepository.clients_for_coach(coach_id)

    @staticmethod
    def plan_requests(coach_id):
        return PlanRequestRepository.pending_for_coach(coach_id)

    @staticmethod
    def decide_plan_request(coach_id, request_id, accept):
        record = PlanRequest.query.filter_by(id=request_id, coach_id=coach_id).first()
        if not record:
            raise DomainError("Plan request not found.", 404)
        if record.status != "pending":
            raise DomainError("This request has already been processed.", 409)
        if accept:
            if record.member.coach_id not in (None, coach_id):
                raise DomainError("Member is already assigned to another coach.", 409)
            record.member.coach_id = coach_id
            record.status = "accepted"
        else:
            record.status = "rejected"
        db.session.commit()
        return record

    @staticmethod
    def create_plan(coach_id, payload):
        try:
            member_id = int(payload.get("member_id"))
        except (TypeError, ValueError):
            raise DomainError("member_id must be an integer.")
        member = UserRepository.member_for_coach(member_id, coach_id)
        if not member:
            raise DomainError("Member is not assigned to this coach.", 403)

        title = str(payload.get("title", "")).strip()
        items = payload.get("exercises")
        if not title or len(title) > 150:
            raise DomainError("Plan title is required and must be at most 150 characters.")
        if not isinstance(items, list) or not items:
            raise DomainError("exercises must be a non-empty array.")

        validated = []
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                raise DomainError(f"exercises[{index}] must be an object.")
            try:
                exercise_id = int(item.get("exercise_id"))
                target_sets = int(item.get("target_sets"))
                rest_seconds = int(item.get("rest_seconds", 90))
            except (TypeError, ValueError):
                raise DomainError(f"Invalid numeric value in exercises[{index}].")
            exercise = ExerciseRepository.get_active_by_id(exercise_id)
            target_reps = str(item.get("target_reps", "")).strip()
            if not exercise:
                raise DomainError(f"Exercise {exercise_id} does not exist or is inactive.", 422)
            if target_sets <= 0 or rest_seconds < 0 or not target_reps:
                raise DomainError("target_sets must be positive; target_reps is required; rest_seconds cannot be negative.")
            validated.append({
                "exercise": exercise,
                "target_sets": target_sets,
                "target_reps": target_reps,
                "rest_seconds": rest_seconds,
                "order_index": index + 1,
            })

        plan = WorkoutPlan(
            coach_id=coach_id,
            member_id=member_id,
            title=title,
            description=payload.get("description"),
            status="assigned",
            assigned_at=utc_now(),
        )
        db.session.add(plan)
        try:
            db.session.flush()
            for item in validated:
                db.session.add(WorkoutPlanExercise(
                    plan_id=plan.id,
                    exercise_id=item["exercise"].id,
                    order_index=item["order_index"],
                    target_sets=item["target_sets"],
                    target_reps=item["target_reps"],
                    rest_seconds=item["rest_seconds"],
                ))
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        return plan

    @staticmethod
    def client_progress(coach_id, member_id):
        if not UserRepository.member_for_coach(member_id, coach_id):
            raise DomainError("Member is not assigned to this coach.", 403)
        return WorkoutController.member_progress(member_id)


class AdminController:
    @staticmethod
    def exercises():
        return ExerciseRepository.all_exercises()

    @staticmethod
    def create_exercise(payload):
        name = str(payload.get("name", "")).strip()
        muscle = str(payload.get("muscle_group", "")).strip()
        if not name or not muscle:
            raise DomainError("name and muscle_group are required.")
        is_active = payload.get("is_active", True)
        if not isinstance(is_active, bool):
            raise DomainError("is_active must be a boolean.")
        exercise = Exercise(
            name=name,
            muscle_group=muscle,
            equipment=payload.get("equipment"),
            difficulty=payload.get("difficulty", "beginner"),
            instructions=payload.get("instructions"),
            is_active=is_active,
        )
        db.session.add(exercise)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise DomainError("Exercise name already exists.", 409)
        return exercise

    @staticmethod
    def update_exercise(exercise_id, payload):
        exercise = ExerciseRepository.get_by_id(exercise_id)
        if not exercise:
            raise DomainError("Exercise not found.", 404)
        allowed = {"name", "muscle_group", "equipment", "difficulty", "instructions", "is_active"}
        changes = {key: value for key, value in payload.items() if key in allowed}
        candidate_name = str(changes.get("name", exercise.name)).strip()
        candidate_muscle = str(changes.get("muscle_group", exercise.muscle_group)).strip()
        if not candidate_name or not candidate_muscle:
            raise DomainError("name and muscle_group cannot be empty.")
        if "is_active" in changes and not isinstance(changes["is_active"], bool):
            raise DomainError("is_active must be a boolean.")
        changes["name"] = candidate_name
        changes["muscle_group"] = candidate_muscle
        for key, value in changes.items():
            setattr(exercise, key, value)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            raise DomainError("Exercise name already exists.", 409)
        return exercise

    @staticmethod
    def users():
        return UserRepository.all_users()

    @staticmethod
    def create_user(payload):
        full_name = str(payload.get("full_name", "")).strip()
        email = str(payload.get("email", "")).strip().lower()
        password = str(payload.get("password", ""))
        role = str(payload.get("role", "")).strip().lower()
        if not full_name or len(full_name) > 120 or "@" not in email or len(email) > 255:
            raise DomainError("A valid full_name (max 120 chars) and email (max 255 chars) are required.")
        if len(password) < 10:
            raise DomainError("Password must contain at least 10 characters.")
        if role not in {"member", "coach", "admin"}:
            raise DomainError("role must be member, coach, or admin.")
        if UserRepository.get_by_email(email):
            raise DomainError("An account with that email already exists.", 409)

        coach_id = payload.get("coach_id")
        if role == "member" and coach_id is not None:
            try:
                coach_id = int(coach_id)
            except (TypeError, ValueError):
                raise DomainError("coach_id must be an integer.")
            coach = User.query.filter_by(id=coach_id, role="coach", is_active=True).first()
            if not coach:
                raise DomainError("Selected coach does not exist or is inactive.", 422)
        else:
            coach_id = None

        is_active = payload.get("is_active", True)
        if not isinstance(is_active, bool):
            raise DomainError("is_active must be a boolean.")
        user = User(
            full_name=full_name,
            email=email,
            role=role,
            coach_id=coach_id,
            is_active=is_active,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def update_user(user_id, payload):
        user = UserRepository.get_by_id(user_id)
        if not user:
            raise DomainError("User not found.", 404)
        new_is_active = user.is_active
        if "is_active" in payload:
            if not isinstance(payload["is_active"], bool):
                raise DomainError("is_active must be a boolean.")
            new_is_active = payload["is_active"]

        new_coach_id = user.coach_id
        if "coach_id" in payload:
            if user.role != "member":
                raise DomainError("Only members can be assigned to a coach.")
            coach_id = payload["coach_id"]
            if coach_id is None:
                new_coach_id = None
            else:
                try:
                    coach_id = int(coach_id)
                except (TypeError, ValueError):
                    raise DomainError("coach_id must be an integer.")
                coach = User.query.filter_by(id=coach_id, role="coach", is_active=True).first()
                if not coach:
                    raise DomainError("Selected coach does not exist or is inactive.", 422)
                new_coach_id = coach_id

        user.is_active = new_is_active
        user.coach_id = new_coach_id
        db.session.commit()
        return user

    @staticmethod
    def system_status():
        return {
            "users": User.query.count(),
            "members": User.query.filter_by(role="member").count(),
            "coaches": User.query.filter_by(role="coach").count(),
            "admins": User.query.filter_by(role="admin").count(),
            "exercises": Exercise.query.count(),
            "active_exercises": Exercise.query.filter_by(is_active=True).count(),
            "workouts": Workout.query.count(),
        }
