# routes.py
from flask import render_template, abort, session, request, redirect, url_for, flash
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import check_password_hash
from . import db
from .auth import login_required, require_superadmin
from .utility import get_table_metadata, load_table_registry, prepare_columns, is_superadmin_role

def register_routes(app):
    TABLE_REGISTRY = load_table_registry()

    # Context processor for templates
    @app.context_processor
    def inject_user_flags():
        return dict(is_superadmin=session.get("is_superadmin", False))
    
    # Main page
    @app.route("/")
    def index():
        return render_template("index.html")

    # Login page
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET" and "user_id" in session:
            flash("You are already logged in!", "info")
            return redirect(url_for("index"))
        elif request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]

            with db.engine.connect() as conn:
                user = conn.execute(
                    text("""
                        SELECT id, username, password_hash, role_id, is_active
                        FROM app_user
                        WHERE username = :username
                    """), {"username": username}
                ).mappings().first()

                if not user or not user["is_active"]:
                    flash("Invalid credentials", "error")
                    return redirect(url_for("login"))

                if not check_password_hash(user["password_hash"], password):
                    flash("Invalid credentials", "error")
                    return redirect(url_for("login"))
                
                session.clear()
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session["role_id"] = user["role_id"]
                session["is_superadmin"] = is_superadmin_role(conn, user["role_id"])

            return redirect(url_for("index"))

        return render_template("login.html")

    # Logout page
    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("index"))

    # Superadmin panel
    @app.route("/superadmin_panel")
    @login_required
    @require_superadmin
    def admin():
        return render_template("superadmin/superadmin_panel.html", tables=TABLE_REGISTRY)

    # Raw-table viewer
    @app.route("/superadmin_panel/table/<table_name>")
    @login_required
    @require_superadmin
    def admin_table(table_name):
        if table_name not in TABLE_REGISTRY:
            return "Table not found", 404

        try:
            with db.engine.connect() as conn:
                _, pk, _ = get_table_metadata(conn, table_name)
                result = conn.execute(text(f"SELECT * FROM {table_name}"))
                rows = result.mappings().all()
                column_names = result.keys()
        except Exception as e:
            flash(f"Failed to fetch table data: {str(e)}", "error")
            return redirect(url_for("admin"))

        return render_template(
            "superadmin/table_list.html",
            table_name=TABLE_REGISTRY[table_name],
            raw_table_name=table_name,
            columns=column_names,
            rows=rows,
            pk=pk
        )

    # Edit row
    @app.route('/superadmin_panel/table/<table_name>/<int:row_id>/edit', methods=["GET", "POST"])
    @login_required
    @require_superadmin
    def admin_edit_row(table_name, row_id):
        if table_name not in TABLE_REGISTRY:
            abort(404)

        with db.engine.begin() as conn:
            columns, pk, fk_columns = get_table_metadata(conn, table_name)
            if pk is None:
                abort(400, "Table has no primary key")

            row = conn.execute(text(f"SELECT * FROM {table_name} WHERE {pk} = :id"), {"id": row_id}).mappings().first()
            if not row:
                abort(404)

            editable_columns, fk_info, enum_info = prepare_columns(conn, columns, fk_columns)

            if request.method == "POST":
                updates = {col["column_name"]: request.form.get(col["column_name"]) or None for col in editable_columns}
                updates["id"] = row_id
                set_clause = ", ".join(f"{c} = :{c}" for c in updates if c != "id")

                try:
                    conn.execute(text(f"UPDATE {table_name} SET {set_clause} WHERE {pk} = :id"), updates)
                    flash("Row updated successfully", "success")
                    return redirect(url_for("admin_table", table_name=table_name))
                except SQLAlchemyError as e:
                    flash(f"Failed to update row: {str(getattr(e, 'orig', e))}", "error")

            return render_template(
                "superadmin/edit_row.html",
                table_name=TABLE_REGISTRY[table_name],
                raw_table_name=table_name,
                pk=pk,
                row=row,
                columns=editable_columns,
                fk_info=fk_info,
                enum_info=enum_info
            )

    # Add row
    @app.route('/superadmin_panel/table/<table_name>/add', methods=["GET", "POST"])
    @login_required
    @require_superadmin
    def admin_add_row(table_name):
        if table_name not in TABLE_REGISTRY:
            abort(404)

        with db.engine.begin() as conn:
            columns, _, fk_columns = get_table_metadata(conn, table_name)
            editable_columns, fk_info, enum_info = prepare_columns(conn, columns, fk_columns)

            if request.method == "POST":
                insert_data = {col["column_name"]: request.form.get(col["column_name"]) or None for col in editable_columns}

                if insert_data:
                    cols_str = ", ".join(insert_data.keys())
                    placeholders = ", ".join(f":{c}" for c in insert_data.keys())
                    try:
                        conn.execute(text(f"INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders})"), insert_data)
                        flash("Row inserted successfully", "success")
                        return redirect(url_for("admin_table", table_name=table_name))
                    except SQLAlchemyError as e:
                        flash(f"Failed to update row: {str(getattr(e, 'orig', e))}", "error")

            return render_template(
                "superadmin/add_row.html",
                table_name=TABLE_REGISTRY[table_name],
                raw_table_name=table_name,
                columns=editable_columns,
                fk_info=fk_info,
                enum_info=enum_info
            )
        
    # Delete row
    @app.route('/superadmin_panel/table/<table_name>/<int:row_id>/delete', methods=["POST"])
    @login_required
    @require_superadmin
    def admin_delete_row(table_name, row_id):
        if table_name not in TABLE_REGISTRY:
            abort(404)

        with db.engine.begin() as conn:
            _, pk, _ = get_table_metadata(conn, table_name)
            if pk is None:
                abort(400, "Table has no primary key")

            try:
                conn.execute(text(f"DELETE FROM {table_name} WHERE {pk} = :id"), {"id": row_id})
                flash("Row deleted successfully", "success")
            except SQLAlchemyError as e:
                flash(f"Failed to delete row: {str(getattr(e, 'orig', e))}", "error")

        return redirect(url_for("admin_table", table_name=table_name))

