from flask import render_template, abort, session, request, redirect, url_for, flash
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from . import db
from .auth import login_required, require_superadmin
from .utility import get_table_metadata, load_table_registry, prepare_columns

def register_routes(app):
    RAW_TABLES = load_table_registry()
    
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
                    """), {"username": username}
                ).mappings().first()

            if not user or not user["is_active"]:
                flash("Invalid credentials", "error")
                return redirect(url_for("login"))

            from werkzeug.security import check_password_hash
            if not check_password_hash(user["password_hash"], password):
                flash("Invalid credentials", "error")
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
        if table_name not in RAW_TABLES:
            return "Table not found", 404

        try:
            with db.engine.connect() as conn:
                columns, pk, _ = get_table_metadata(conn, table_name)
                result = conn.execute(text(f"SELECT * FROM {table_name}"))
                rows = result.mappings().all()
                column_names = result.keys()
        except Exception as e:
            flash(f"Failed to fetch table data: {str(e)}", "error")
            return redirect(url_for("admin"))

        return render_template(
            "table_list.html",
            table_name=RAW_TABLES[table_name],
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
        if table_name not in RAW_TABLES:
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
                "edit_row.html",
                table_name=RAW_TABLES[table_name],
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
        if table_name not in RAW_TABLES:
            abort(404)

        with db.engine.begin() as conn:
            columns, pk, fk_columns = get_table_metadata(conn, table_name)
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
                "add_row.html",
                table_name=RAW_TABLES[table_name],
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
        if table_name not in RAW_TABLES:
            abort(404)

        with db.engine.begin() as conn:
            columns, pk, _ = get_table_metadata(conn, table_name)
            if pk is None:
                abort(400, "Table has no primary key")

            try:
                conn.execute(text(f"DELETE FROM {table_name} WHERE {pk} = :id"), {"id": row_id})
                flash("Row deleted successfully", "success")
            except SQLAlchemyError as e:
                flash(f"Failed to delete row: {str(getattr(e, 'orig', e))}", "error")

        return redirect(url_for("admin_table", table_name=table_name))

