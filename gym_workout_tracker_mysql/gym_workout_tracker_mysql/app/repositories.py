from app.models.entities import Exercise, PlanRequest, User, Workout


class UserRepository:
    @staticmethod
    def get_by_id(user_id):
        return User.query.get(user_id)

    @staticmethod
    def get_by_email(email):
        return User.query.filter_by(email=email).first()

    @staticmethod
    def active_coaches():
        return User.query.filter_by(role="coach", is_active=True).order_by(User.full_name).all()

    @staticmethod
    def clients_for_coach(coach_id):
        return User.query.filter_by(role="member", coach_id=coach_id).order_by(User.full_name).all()

    @staticmethod
    def member_for_coach(member_id, coach_id):
        return User.query.filter_by(id=member_id, role="member", coach_id=coach_id).first()

    @staticmethod
    def all_users():
        return User.query.order_by(User.created_at.desc()).all()


class ExerciseRepository:
    @staticmethod
    def get_by_id(exercise_id):
        return Exercise.query.get(exercise_id)

    @staticmethod
    def get_active_by_id(exercise_id):
        return Exercise.query.filter_by(id=exercise_id, is_active=True).first()

    @staticmethod
    def active_exercises():
        return Exercise.query.filter_by(is_active=True).order_by(
            Exercise.muscle_group, Exercise.name
        ).all()

    @staticmethod
    def all_exercises():
        return Exercise.query.order_by(Exercise.name).all()


class WorkoutRepository:
    @staticmethod
    def list_for_user(user_id, limit=100):
        return Workout.query.filter_by(user_id=user_id).order_by(
            Workout.started_at.desc()
        ).limit(limit).all()

    @staticmethod
    def get_owned(workout_id, user_id):
        return Workout.query.filter_by(id=workout_id, user_id=user_id).first()

    @staticmethod
    def list_for_member(member_id, limit=10):
        return Workout.query.filter_by(user_id=member_id).order_by(
            Workout.started_at.desc()
        ).limit(limit).all()


class PlanRequestRepository:
    @staticmethod
    def pending_for_coach(coach_id):
        return PlanRequest.query.filter_by(
            coach_id=coach_id, status="pending"
        ).order_by(PlanRequest.created_at.asc()).all()
