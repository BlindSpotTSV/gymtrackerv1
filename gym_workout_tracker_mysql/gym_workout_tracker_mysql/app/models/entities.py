from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


def utc_now():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    __tablename__ = "users"
    __table_args__ = (
        db.CheckConstraint("role IN ('member', 'coach', 'admin')", name="ck_users_role"),
    )

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="member")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    coach_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    coach = db.relationship(
        "User", remote_side=[id], back_populates="members", foreign_keys=[coach_id]
    )
    members = db.relationship("User", back_populates="coach", foreign_keys=[coach_id])
    workouts = db.relationship("Workout", back_populates="user", cascade="all, delete-orphan")
    created_plans = db.relationship(
        "WorkoutPlan", back_populates="coach", foreign_keys="WorkoutPlan.coach_id"
    )
    received_plans = db.relationship(
        "WorkoutPlan", back_populates="member", foreign_keys="WorkoutPlan.member_id"
    )
    plan_requests_sent = db.relationship(
        "PlanRequest", back_populates="member", foreign_keys="PlanRequest.member_id"
    )
    plan_requests_received = db.relationship(
        "PlanRequest", back_populates="coach", foreign_keys="PlanRequest.coach_id"
    )

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)


class Exercise(db.Model):
    __tablename__ = "exercises"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    muscle_group = db.Column(db.String(80), nullable=False)
    equipment = db.Column(db.String(80))
    difficulty = db.Column(db.String(30), nullable=False, default="beginner")
    instructions = db.Column(db.Text)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)


class WorkoutPlan(db.Model):
    __tablename__ = "workout_plans"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('draft', 'assigned', 'archived')",
            name="ck_workout_plans_status",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    coach_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    member_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default="assigned")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    assigned_at = db.Column(db.DateTime(timezone=True))

    coach = db.relationship("User", back_populates="created_plans", foreign_keys=[coach_id])
    member = db.relationship("User", back_populates="received_plans", foreign_keys=[member_id])
    plan_exercises = db.relationship(
        "WorkoutPlanExercise",
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="WorkoutPlanExercise.order_index",
    )
    workouts = db.relationship("Workout", back_populates="plan")


class WorkoutPlanExercise(db.Model):
    __tablename__ = "workout_plan_exercises"
    __table_args__ = (
        db.UniqueConstraint("plan_id", "order_index", name="uq_plan_exercise_order"),
        db.CheckConstraint("target_sets > 0", name="ck_plan_target_sets_positive"),
        db.CheckConstraint("rest_seconds >= 0", name="ck_plan_rest_nonnegative"),
    )

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("workout_plans.id", ondelete="CASCADE"), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercises.id", ondelete="RESTRICT"), nullable=False)
    order_index = db.Column(db.Integer, nullable=False)
    target_sets = db.Column(db.Integer, nullable=False)
    target_reps = db.Column(db.String(30), nullable=False)
    rest_seconds = db.Column(db.Integer, nullable=False, default=90)

    plan = db.relationship("WorkoutPlan", back_populates="plan_exercises")
    exercise = db.relationship("Exercise")


class PlanRequest(db.Model):
    __tablename__ = "plan_requests"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('pending', 'accepted', 'rejected')",
            name="ck_plan_requests_status",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    coach_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    goal = db.Column(db.String(150), nullable=False)
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default="pending")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)

    member = db.relationship("User", back_populates="plan_requests_sent", foreign_keys=[member_id])
    coach = db.relationship("User", back_populates="plan_requests_received", foreign_keys=[coach_id])


class Workout(db.Model):
    __tablename__ = "workouts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("workout_plans.id", ondelete="SET NULL"), nullable=True, index=True)
    name = db.Column(db.String(150), nullable=False)
    notes = db.Column(db.Text)
    started_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utc_now)
    ended_at = db.Column(db.DateTime(timezone=True))

    user = db.relationship("User", back_populates="workouts")
    plan = db.relationship("WorkoutPlan", back_populates="workouts")
    sets = db.relationship(
        "WorkoutSet",
        back_populates="workout",
        cascade="all, delete-orphan",
        order_by="WorkoutSet.set_number",
    )


class WorkoutSet(db.Model):
    __tablename__ = "workout_sets"
    __table_args__ = (
        db.UniqueConstraint(
            "workout_id", "exercise_id", "set_number",
            name="uq_workout_exercise_set_number",
        ),
        db.CheckConstraint("set_number > 0", name="ck_set_number_positive"),
        db.CheckConstraint("reps > 0", name="ck_reps_positive"),
        db.CheckConstraint("weight_kg >= 0", name="ck_weight_nonnegative"),
        db.CheckConstraint(
            "rpe IS NULL OR (rpe >= 1 AND rpe <= 10)",
            name="ck_rpe_range",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(db.Integer, db.ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False, index=True)
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercises.id", ondelete="RESTRICT"), nullable=False, index=True)
    set_number = db.Column(db.Integer, nullable=False)
    reps = db.Column(db.Integer, nullable=False)
    weight_kg = db.Column(db.Numeric(7, 2), nullable=False, default=0)
    rpe = db.Column(db.Numeric(3, 1))
    is_warmup = db.Column(db.Boolean, nullable=False, default=False)

    workout = db.relationship("Workout", back_populates="sets")
    exercise = db.relationship("Exercise")
