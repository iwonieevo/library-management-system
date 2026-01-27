# auth.py
from flask import session, abort, redirect, url_for
from sqlalchemy import text
from functools import wraps
from . import db
from .utility import is_superadmin_role

# Require logined user
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper

# Require superadmin role
def require_superadmin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("is_superadmin"):
            abort(403)
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
                if not session.get("is_superadmin"):
                    allowed = not conn.execute(
                        text("""
                            SELECT 1
                            FROM app_role_entity_permission rp
                            JOIN entity_permission p
                                ON p.id = rp.permission_id
                            WHERE rp.role_id = :role_id
                                AND p.entity = :entity
                                AND p.access_level >= :access_level
                        """),
                        {
                            "role_id": session["role_id"],
                            "entity": entity,
                            "access_level": access_level
                        }
                    ).scalar()

                    if not allowed:
                        abort(403)

            return f(*args, **kwargs)
        return wrapper
    return decorator
