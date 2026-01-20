from flask import render_template, session, abort, request, redirect, url_for, flash
from sqlalchemy import text
from functools import wraps
from . import db

RAW_TABLES = {
    "book": "Books",
    "author": "Authors",
    "category": "Categories",
    "book_author": "Books-Authors bridge table",
    "book_category": "Books-Categories bridge table",
    "publisher": "Publishers",
    "book_copy": "Book copies",
    "reader": "Readers",
    "reservation": "Reservations",
    "issue": "Issues",
    "rating": "Ratings",
    "app_notification": "Notifications",
    "app_role": "Roles",
    "entity_permission": "Permissions",
    "app_user": "Users",
    "app_role_entity_permission": "Role permissions"
}

def register_routes(app):
    # Auth wrappers
    def login_required(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            return f(*args, **kwargs)
        return wrapper

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
                            FROM app_role_entity_permission rp
                            JOIN entity_permission p
                              ON p.id = rp.permission_id
                            WHERE rp.role_id = :role_id
                              AND p.entity = :entity
                              AND p.access_level = :access_level
                        """),
                        {
                            "role_id": session["role_id"],
                            "entity": entity,
                            "access_level": access_level
                        }
                    ).first()

                if not allowed:
                    abort(403)

                return f(*args, **kwargs)
            return wrapper
        return decorator
    
    # Homepage
    @app.route('/')
    def index():
        return "Welcome to our library!"
    
    # Login page
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]

            with db.engine.connect() as conn:
                user = conn.execute(
                    text("""
                        SELECT id, username, password_hash, role_id, is_active
                        FROM app_user
                        WHERE username = :username
                    """),
                    {"username": username}
                ).mappings().first()

            if not user or not user["is_active"]:
                flash("Invalid credentials")
                return redirect(url_for("login"))

            from werkzeug.security import check_password_hash
            if not check_password_hash(user["password_hash"], password):
                flash("Invalid credentials")
                return redirect(url_for("login"))

            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role_id"] = user["role_id"]

            return redirect(url_for("index"))

        return render_template("login.html")

    # Logout page
    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    # Superadmin panel
    @app.route("/superadmin_panel")
    @login_required
    @require_permission("superadmin_panel", "read")
    def admin():
        return render_template("superadmin_panel.html", tables=RAW_TABLES)

    # Raw-table viewer
    @app.route("/superadmin_panel/table/<table_name>")
    @login_required
    @require_permission("superadmin_panel", "read")
    def admin_table(table_name):
        if table_name not in RAW_TABLES.keys():
            return "Table not found", 404

        with db.engine.connect() as conn:
            result = conn.execute(text(f"SELECT * FROM {table_name}"))
            rows = result.fetchall()
            columns = result.keys()

        return render_template(
            "table_list.html",
            table_name=RAW_TABLES[table_name],
            columns=columns,
            rows=rows
        )
