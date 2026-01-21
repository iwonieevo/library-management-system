from flask import session, abort, redirect, url_for
from sqlalchemy import text
from functools import wraps
import os
from . import db

# Require logined user
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

# Require specific permission
def require_permission(entity, access_level):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "role_id" not in session:
                abort(401)

            with db.engine.connect() as conn:
                allowed = conn.execute(
                    text("""
                        SELECT 1
                        WHERE :role_id = get_role_id(:superadmin_role)
                        OR EXIST (
                            SELECT 1
                            FROM app_role_entity_permission rp
                            JOIN entity_permission p
                                ON p.id = rp.permission_id
                            WHERE rp.role_id = :role_id
                                AND p.entity = :entity
                                AND p.access_level = :access_level
                        )
                    """),
                    {
                        "role_id": session["role_id"],
                        "entity": entity,
                        "access_level": access_level,
                        "superadmin_role": os.getenv("APP_SUPERADMIN_ROLE", "superadmin")
                    }
                ).scalar()

            if not allowed:
                abort(403)

            return f(*args, **kwargs)
        return wrapper
    return decorator

# Require superadmin role
def require_superadmin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "role_id" not in session:
            abort(401)

        with db.engine.connect() as conn:
            is_superadmin = conn.execute(
                text("""
                    SELECT :role_id = get_role_id(:superadmin_role)
                """),
                {
                    "role_id": session["role_id"],
                    "superadmin_role": os.getenv("APP_SUPERADMIN_ROLE", "superadmin"),
                }
            ).scalar()

        if not is_superadmin:
            abort(403)

        return f(*args, **kwargs)
    return wrapper