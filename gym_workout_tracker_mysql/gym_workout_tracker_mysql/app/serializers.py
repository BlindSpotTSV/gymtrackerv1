def user_summary(user):
    return {
        "id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "coach_id": user.coach_id,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def exercise_dict(exercise):
    return {
        "id": exercise.id,
        "name": exercise.name,
        "muscle_group": exercise.muscle_group,
        "equipment": exercise.equipment,
        "difficulty": exercise.difficulty,
        "instructions": exercise.instructions,
        "is_active": exercise.is_active,
    }


def workout_dict(workout, include_sets=True):
    data = {
        "id": workout.id,
        "user_id": workout.user_id,
        "plan_id": workout.plan_id,
        "name": workout.name,
        "notes": workout.notes,
        "started_at": workout.started_at.isoformat() if workout.started_at else None,
        "ended_at": workout.ended_at.isoformat() if workout.ended_at else None,
    }
    if include_sets:
        data["sets"] = [
            {
                "id": item.id,
                "exercise_id": item.exercise_id,
                "exercise_name": item.exercise.name,
                "set_number": item.set_number,
                "reps": item.reps,
                "weight_kg": float(item.weight_kg),
                "rpe": float(item.rpe) if item.rpe is not None else None,
                "is_warmup": item.is_warmup,
            }
            for item in workout.sets
        ]
    return data


def plan_request_dict(record):
    return {
        "id": record.id,
        "member_id": record.member_id,
        "member_name": record.member.full_name,
        "coach_id": record.coach_id,
        "coach_name": record.coach.full_name,
        "goal": record.goal,
        "notes": record.notes,
        "status": record.status,
        "created_at": record.created_at.isoformat(),
    }


def workout_plan_dict(plan):
    return {
        "id": plan.id,
        "coach_id": plan.coach_id,
        "member_id": plan.member_id,
        "title": plan.title,
        "description": plan.description,
        "status": plan.status,
        "created_at": plan.created_at.isoformat(),
        "exercises": [
            {
                "exercise_id": item.exercise_id,
                "exercise_name": item.exercise.name,
                "order_index": item.order_index,
                "target_sets": item.target_sets,
                "target_reps": item.target_reps,
                "rest_seconds": item.rest_seconds,
            }
            for item in plan.plan_exercises
        ],
    }
