-- Gym Workout Tracker - MySQL 8 / MariaDB (InnoDB)
-- Open phpMyAdmin, select the SQL tab, and execute this whole script.
CREATE DATABASE IF NOT EXISTS gym_workout_tracker
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE gym_workout_tracker;

CREATE TABLE IF NOT EXISTS users (
    id INT NOT NULL AUTO_INCREMENT,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('member', 'coach', 'admin') NOT NULL DEFAULT 'member',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    coach_id INT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_users_email (email),
    KEY ix_users_coach_id (coach_id),
    CONSTRAINT fk_users_coach
      FOREIGN KEY (coach_id) REFERENCES users(id)
      ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS exercises (
    id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(150) NOT NULL,
    muscle_group VARCHAR(80) NOT NULL,
    equipment VARCHAR(80) NULL,
    difficulty VARCHAR(30) NOT NULL DEFAULT 'beginner',
    instructions TEXT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_exercises_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS workout_plans (
    id INT NOT NULL AUTO_INCREMENT,
    coach_id INT NOT NULL,
    member_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    description TEXT NULL,
    status ENUM('draft', 'assigned', 'archived') NOT NULL DEFAULT 'assigned',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    assigned_at DATETIME NULL,
    PRIMARY KEY (id),
    KEY ix_workout_plans_coach_id (coach_id),
    KEY ix_workout_plans_member_id (member_id),
    CONSTRAINT fk_workout_plans_coach
      FOREIGN KEY (coach_id) REFERENCES users(id) ON DELETE RESTRICT,
    CONSTRAINT fk_workout_plans_member
      FOREIGN KEY (member_id) REFERENCES users(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS workout_plan_exercises (
    id INT NOT NULL AUTO_INCREMENT,
    plan_id INT NOT NULL,
    exercise_id INT NOT NULL,
    order_index INT NOT NULL,
    target_sets INT NOT NULL,
    target_reps VARCHAR(30) NOT NULL,
    rest_seconds INT NOT NULL DEFAULT 90,
    PRIMARY KEY (id),
    UNIQUE KEY uq_plan_exercise_order (plan_id, order_index),
    CONSTRAINT ck_plan_target_sets_positive CHECK (target_sets > 0),
    CONSTRAINT ck_plan_rest_nonnegative CHECK (rest_seconds >= 0),
    CONSTRAINT fk_plan_exercises_plan
      FOREIGN KEY (plan_id) REFERENCES workout_plans(id) ON DELETE CASCADE,
    CONSTRAINT fk_plan_exercises_exercise
      FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS plan_requests (
    id INT NOT NULL AUTO_INCREMENT,
    member_id INT NOT NULL,
    coach_id INT NOT NULL,
    goal VARCHAR(150) NOT NULL,
    notes TEXT NULL,
    status ENUM('pending', 'accepted', 'rejected') NOT NULL DEFAULT 'pending',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY ix_plan_requests_member_id (member_id),
    KEY ix_plan_requests_coach_id (coach_id),
    CONSTRAINT fk_plan_requests_member
      FOREIGN KEY (member_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_plan_requests_coach
      FOREIGN KEY (coach_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS workouts (
    id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    plan_id INT NULL,
    name VARCHAR(150) NOT NULL,
    notes TEXT NULL,
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at DATETIME NULL,
    PRIMARY KEY (id),
    KEY ix_workouts_user_id (user_id),
    KEY ix_workouts_plan_id (plan_id),
    CONSTRAINT fk_workouts_user
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_workouts_plan
      FOREIGN KEY (plan_id) REFERENCES workout_plans(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS workout_sets (
    id INT NOT NULL AUTO_INCREMENT,
    workout_id INT NOT NULL,
    exercise_id INT NOT NULL,
    set_number INT NOT NULL,
    reps INT NOT NULL,
    weight_kg DECIMAL(7,2) NOT NULL DEFAULT 0,
    rpe DECIMAL(3,1) NULL,
    is_warmup BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (id),
    UNIQUE KEY uq_workout_exercise_set_number (workout_id, exercise_id, set_number),
    KEY ix_workout_sets_workout_id (workout_id),
    KEY ix_workout_sets_exercise_id (exercise_id),
    CONSTRAINT ck_set_number_positive CHECK (set_number > 0),
    CONSTRAINT ck_reps_positive CHECK (reps > 0),
    CONSTRAINT ck_weight_nonnegative CHECK (weight_kg >= 0),
    CONSTRAINT ck_rpe_range CHECK (rpe IS NULL OR (rpe >= 1 AND rpe <= 10)),
    CONSTRAINT fk_workout_sets_workout
      FOREIGN KEY (workout_id) REFERENCES workouts(id) ON DELETE CASCADE,
    CONSTRAINT fk_workout_sets_exercise
      FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Starter exercise catalogue (safe to run more than once).
INSERT IGNORE INTO exercises (name, muscle_group, equipment, difficulty) VALUES
('Barbell Bench Press', 'Chest', 'Barbell', 'intermediate'),
('Incline Dumbbell Press', 'Chest', 'Dumbbell', 'beginner'),
('Back Squat', 'Quadriceps', 'Barbell', 'intermediate'),
('Romanian Deadlift', 'Hamstrings', 'Barbell', 'intermediate'),
('Lat Pulldown', 'Back', 'Cable', 'beginner'),
('Seated Cable Row', 'Back', 'Cable', 'beginner'),
('Overhead Press', 'Shoulders', 'Barbell', 'intermediate'),
('Dumbbell Biceps Curl', 'Biceps', 'Dumbbell', 'beginner'),
('Triceps Pushdown', 'Triceps', 'Cable', 'beginner'),
('Standing Calf Raise', 'Calves', 'Machine', 'beginner');
