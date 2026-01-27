# commands.py
from werkzeug.security import generate_password_hash
from sqlalchemy import text
import os
import click
from . import db
from .utility import load_table_registry

def register_commands(app):
    # CLI command for creating a user with superadmin role
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

    # CLI command for syncing permissions
    @app.cli.command("sync-permissions")
    def sync_permissions():
        tables = load_table_registry()
        if not tables:
            click.echo("table_registry.json not found or empty", err=True)
            return

        with db.engine.begin() as conn:
            # Fetch valid enum values from Postgres
            valid_levels = {
                row[0]
                for row in conn.execute(text("""
                    SELECT enumlabel
                    FROM pg_enum
                    JOIN pg_type ON pg_type.oid = pg_enum.enumtypid
                    WHERE pg_type.typname = 'access_level_enum'
                """))
            }

            created = 0

            for entity_name, alias in tables.items():
                for level in valid_levels:
                    perm_name = f"{alias} {level.title()}"

                    conn.execute(
                        text("""
                            INSERT INTO entity_permission (name, entity, access_level)
                            VALUES (:name, :entity, :level)
                            ON CONFLICT (name) DO UPDATE
                            SET entity = EXCLUDED.entity,
                                access_level = EXCLUDED.access_level
                        """),
                        {
                            "name": perm_name,
                            "entity": entity_name,
                            "level": level,
                        }
                    )
                    created += 1

        click.echo(f"Synced {created} permissions")

    @app.cli.command("clear-orphan-permissions")
    @click.option("--dry-run", is_flag=True, help="Show permissions that would be deleted without deleting them")
    def clear_orphan_permissions(dry_run):
        tables = load_table_registry()
        if not tables:
            click.echo("table_registry.json not found or empty", err=True)
            return

        valid_entities = set(tables.keys())

        with db.engine.begin() as conn:
            # Fetch valid enum values
            valid_levels = {
                row[0]
                for row in conn.execute(text("""
                    SELECT enumlabel
                    FROM pg_enum
                    JOIN pg_type ON pg_type.oid = pg_enum.enumtypid
                    WHERE pg_type.typname = 'access_level_enum'
                """))
            }

            # Find orphan permissions
            orphan_permissions = conn.execute(text("""
                SELECT id, name, entity, access_level
                FROM entity_permission
                WHERE entity NOT IN :entities
                OR access_level NOT IN :levels
            """), {
                "entities": tuple(valid_entities),
                "levels": tuple(valid_levels),
            }).mappings().all()

            if not orphan_permissions:
                click.echo("No orphan permissions found")
                return

            if dry_run:
                click.echo("Permissions that would be deleted:")
                for p in orphan_permissions:
                    click.echo(
                        f" - {p['name']} "
                        f"(entity={p['entity']}, level={p['access_level']})"
                    )
                click.echo(f"Total: {len(orphan_permissions)}")
                return

            # Delete orphans (role mappings cascade automatically)
            conn.execute(
                text("""
                    DELETE FROM entity_permission
                    WHERE id = ANY(:ids)
                """),
                {"ids": [p["id"] for p in orphan_permissions]}
            )

        click.echo(f"Deleted {len(orphan_permissions)} orphan permissions")

