from werkzeug.security import generate_password_hash
from sqlalchemy import text
from . import db

def register_commands(app):
    @app.cli.command("seed-users")
    def seed_users():
        users = [
            ("root", "superpassword", "superadmin"),
            ("lib_admin", "adminpassword", "admin"),
            ("lib_worker", "librarianpassword", "librarian"),
            ("lib_member", "memberpassword", "member"),
        ]

        with db.engine.begin() as conn:
            for username, password, role in users:
                conn.execute(
                    text("""
                        INSERT INTO app_user (username, password_hash, role_id)
                        VALUES (:u, :p, get_role_id(:r))
                        ON CONFLICT (username) DO NOTHING
                    """),
                    {"u": username, "p": generate_password_hash(password), "r": role}
                )

        print("Seed users created.")
