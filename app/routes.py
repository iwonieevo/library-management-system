from flask import render_template, session, request, redirect, url_for, flash
from sqlalchemy import text
from . import db
from .auth import login_required, require_permission, require_superadmin

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
    @require_superadmin
    def admin():
        return render_template("superadmin_panel.html", tables=RAW_TABLES)

    # Raw-table viewer
    @app.route("/superadmin_panel/table/<table_name>")
    @login_required
    @require_superadmin
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
