from werkzeug.security import generate_password_hash
from sqlalchemy import text
import os
import click
from . import db

# CLI command for creating a user with superadmin role
def register_commands(app):
    @app.cli.command("create-superadmin")
    @click.argument("username")
    @click.password_option()
    def create_superadmin(username, password):
        app_superadmin_role = os.getenv("APP_SUPERADMIN_ROLE", "superadmin")
        with db.engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO app_role (name, description)
                    VALUES (:superadmin_role, 'Full system access')
                    ON CONFLICT (name) DO NOTHING
                """),
                {"superadmin_role": app_superadmin_role}
            )
            conn.execute(
                text("""
                    INSERT INTO app_user (username, password_hash, role_id)
                    VALUES (:username, :pswd_hash, get_role_id(:superadmin_role))
                    ON CONFLICT (username) DO UPDATE
                        SET
                            password_hash = EXCLUDED.password_hash,
                            role_id = get_role_id(:superadmin_role)
                """),
                {"username": username, "pswd_hash": generate_password_hash(password), "superadmin_role": app_superadmin_role}
            )
        click.echo(f"Created {app_superadmin_role}: {username}")
