# Gym Workout Tracker — MySQL + PHPMyAdmin + Flask

A beginner-friendly Flask web application with a MySQL/MariaDB database. The project uses MVC and BCE:
- Boundary: `app/boundaries/` (HTTP routes and Jinja2 pages)
- Controller: `app/controllers/services.py` (use-case/business logic)
- Entity/Model: `app/models/entities.py` (SQLAlchemy ORM)
- Repository: `app/repositories.py` (database query helpers)
- View: `app/templates/` (HTML/Jinja2)

## A. Start MySQL using XAMPP

1. Start Apache and MySQL in XAMPP Control Panel.
2. Open `http://localhost/phpmyadmin`.
3. Select the SQL tab and run the contents of `schema.sql`.
4. The script creates `gym_workout_tracker`, seven relational tables, and starter exercises.

The example `.env` uses common XAMPP local defaults: MySQL user `root`, empty password, port `3306`. If your MySQL credentials differ, edit `DATABASE_URL`.

## B. Open in Visual Studio Code

Open the `gym_workout_tracker_mysql` project folder in VS Code. Install the Microsoft Python extension. Open Terminal > New Terminal.

### Windows PowerShell

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

If PowerShell blocks activation, use Command Prompt and run:

```bat
.venv\Scripts\activate.bat
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set a long random `SECRET_KEY`. Default local database URL:

```env
DATABASE_URL=mysql+pymysql://root:@127.0.0.1:3306/gym_workout_tracker?charset=utf8mb4
```

If your root user has a password, URL-encode special characters in it. For example `@` becomes `%40`.

## C. Create administrator and start the app

Run these commands from the project root, with the virtual environment active:

```bash
flask --app run.py create-admin
flask --app run.py run --debug
```

Open `http://127.0.0.1:5000`.

The SQL script creates tables directly. You do not need `flask init-db` when you have already run `schema.sql` in phpMyAdmin. `flask init-db` is available if you want SQLAlchemy to create missing tables in a fresh development database.

## D. User workflow

1. Register a Member using `/register`.
2. Admin creates Coach accounts at `/admin/users`.
3. Member logs in and submits a Coach request at `/member/plan-request`.
4. Coach accepts the request at `/coach/requests`.
5. Coach creates a workout plan at `/coach/plans/new`.
6. Member logs workouts at `/member/workouts/new` and reviews history.
7. Admin maintains exercises at `/admin/exercises`.

The first Admin is created using the CLI command, not public registration. Public registration only creates Member accounts.

## E. Important endpoints

### Web pages
- `/login`, `/register`, `/dashboard`
- `/member/exercises`, `/member/workouts/new`, `/member/workouts`
- `/member/plan-request`
- `/coach/clients`, `/coach/requests`, `/coach/plans/new`
- `/admin/users`, `/admin/exercises`, `/admin/status`

### JSON API
The API blueprints remain available:
- `/api/auth/*`
- `/api/exercises`, `/api/workouts`, `/api/workout-plans`
- `/api/coach/*`
- `/api/admin/*`

## F. Security and production notes

- Change `SECRET_KEY` before use.
- Do not expose phpMyAdmin or the local XAMPP database to the public internet.
- For production, create a dedicated least-privilege MySQL user instead of using root.
- Use HTTPS and set `SESSION_COOKIE_SECURE=1` behind HTTPS.
- Use Flask-Migrate/Alembic for schema migrations, backups, logging, rate limits, and integration tests.
- This is a functional starter application; validate and harden it before production deployment.
