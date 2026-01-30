# routes.py
from flask import render_template, session, request, redirect, url_for, flash
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import random
from . import db
from .auth import login_required, require_superadmin
from .utility import get_table_metadata, load_table_registry, prepare_columns, is_superadmin_role

def register_routes(app):
    TABLE_REGISTRY = load_table_registry()

    # Context processor for templates: user flags
    @app.context_processor
    def inject_user_flags():
        return dict(is_superadmin=session.get("is_superadmin", False))
    
    # Context processor for templates: notifications
    @app.context_processor
    def inject_notifications():
        if "card_no" not in session or "user_id" not in session:
            return {}

        try:
            with db.engine.connect() as conn:
                reader_id = conn.execute(text("""SELECT reader_id FROM app_user WHERE app_user.id = :user_id LIMIT 1"""), {"user_id": session["user_id"]}).scalar_one_or_none()

                if not reader_id:
                    return {}

                notifications = conn.execute(
                    text("""
                        SELECT id, sent_datetime, subject, body, read
                        FROM app_notification
                        WHERE reader_id = :reader_id
                        ORDER BY sent_datetime DESC
                        LIMIT 11
                    """),
                    {"reader_id": reader_id}
                ).mappings().all()

                unread_count = conn.execute(
                text("""
                        SELECT COUNT(*) 
                        FROM app_notification
                        WHERE reader_id = :reader_id AND read = FALSE
                    """), {"reader_id": reader_id}
                ).scalar_one()

                return {
                    "notifications": notifications[:10],
                    "has_more": len(notifications) > 10,
                    "unread_count": unread_count
                }

        except SQLAlchemyError:
            return {}
    
    # Main page
    @app.route("/")
    def index():
        return render_template("index.html")

    # Login page
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET" and "user_id" in session:
            flash("You are already logged in!", "warning")
            return redirect(url_for("index"))
        elif request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]

            with db.engine.connect() as conn:
                user = conn.execute(
                    text("""
                        SELECT app_user.id, app_user.username, app_user.password_hash, app_user.role_id, app_user.is_active, reader.card_no
                        FROM app_user
                        LEFT JOIN reader ON reader.id = app_user.reader_id
                        WHERE app_user.username = :username
                    """), {"username": username}
                ).mappings().first()

                if not user or not user["is_active"]:
                    flash("User isn't active or doesn't exist", "error")
                    return redirect(url_for("login"))

                if not check_password_hash(user["password_hash"], password):
                    flash("Invalid credentials", "error")
                    return redirect(url_for("login"))
                
                session.clear()
                session["user_id"] = user["id"]
                session["username"] = user["username"]
                session["role_id"] = user["role_id"]
                session["is_superadmin"] = is_superadmin_role(conn, user["role_id"])
                session["card_no"] = user["card_no"]

            return redirect(url_for("index"))

        return render_template("login.html")

    # Logout page
    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("index"))
    
    # Register page
    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "GET" and "user_id" in session:
            flash("You are already logged in!", "warning")
            return redirect(url_for("index"))
        elif request.method == "POST":
            first_name = request.form.get("first_name", "").strip()
            last_name = request.form.get("last_name", "").strip()
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password")

            if not all([first_name, last_name, username, password, confirm_password]):
                flash("All fields are required", "error")
                return redirect(url_for("register"))

            if password != confirm_password:
                flash("Passwords do not match", "error")
                return redirect(url_for("register"))

            password_hash = generate_password_hash(password)

            # card_no: YYYYMMDDHHMM + random 3 digits -> length = 15
            now = datetime.now()
            card_no = f"{now:%Y%m%d%H%M}{random.randint(0, 999):03d}"

            try:
                with db.engine.begin() as conn:
                    # check username uniqueness
                    existing = conn.execute(
                        text("SELECT 1 FROM app_user WHERE username = :username"),
                        {"username": username}
                    ).first()

                    if existing:
                        flash("This username is already in use", "error")
                        return redirect(url_for("register"))

                    # create reader
                    reader_id = conn.execute(
                        text("""
                            INSERT INTO reader (first_name, last_name, card_no)
                            VALUES (:first_name, :last_name, :card_no)
                            RETURNING id
                        """),
                        {
                            "first_name": first_name,
                            "last_name": last_name,
                            "card_no": card_no
                        }
                    ).scalar_one()

                    # create app_user (no role assigned)
                    conn.execute(
                        text("""
                            INSERT INTO app_user (username, password_hash, reader_id, is_active)
                            VALUES (:username, :password_hash, :reader_id, true)
                        """),
                        {
                            "username": username,
                            "password_hash": password_hash,
                            "reader_id": reader_id
                        }
                    )

                flash("Registration successful. You can now log in.", "success")
                return redirect(url_for("login"))

            except SQLAlchemyError as e:
                flash(f"Registration failed: {str(getattr(e, 'orig', e))}", "error")

        return render_template("register.html")

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
            flash(f"The table doesn't exist", "error")
            return redirect(url_for("admin"))

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
            flash(f"The table doesn't exist", "error")
            return redirect(url_for("admin"))

        with db.engine.begin() as conn:
            columns, pk, fk_columns = get_table_metadata(conn, table_name)
            if pk is None:
                flash(f"The table doesn't have a PK", "error")
                return redirect(url_for("admin"))

            row = conn.execute(text(f"SELECT * FROM {table_name} WHERE {pk} = :id"), {"id": row_id}).mappings().first()
            if not row:
                flash(f"The row doesn't exist", "error")
                return redirect(url_for("admin"))

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
            flash(f"The table doesn't exist", "error")
            return redirect(url_for("admin"))

        with db.engine.begin() as conn:
            columns, _, fk_columns = get_table_metadata(conn, table_name)
            editable_columns, fk_info, enum_info = prepare_columns(conn, columns, fk_columns)

            insert_data = {}
            if request.method == "POST":
                for col in editable_columns:
                    name = col["column_name"]
                    value = request.form.get(name)

                    if value == "" or value is None:
                        continue

                    insert_data[name] = value

                if insert_data:
                    cols_str = ", ".join(insert_data.keys())
                    placeholders = ", ".join(f":{c}" for c in insert_data.keys())
                    try:
                        conn.execute(text(f"INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders})"), insert_data)
                        flash("Row inserted successfully", "success")
                        return redirect(url_for("admin_table", table_name=table_name))
                    except SQLAlchemyError as e:
                        flash(f"Failed to insert row: {str(getattr(e, 'orig', e))}", "error")

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
            flash(f"The table doesn't exist", "error")
            return redirect(url_for("admin"))

        with db.engine.begin() as conn:
            _, pk, _ = get_table_metadata(conn, table_name)
            if pk is None:
                flash(f"The table doesn't have a PK", "error")
                return redirect(url_for("admin"))

            try:
                conn.execute(text(f"DELETE FROM {table_name} WHERE {pk} = :id"), {"id": row_id})
                flash("Row deleted successfully", "success")
            except SQLAlchemyError as e:
                flash(f"Failed to delete row: {str(getattr(e, 'orig', e))}", "error")

        return redirect(url_for("admin_table", table_name=table_name))
    
    # All user notifications page
    @app.route("/notifications")
    @login_required
    def notifications():
        if "card_no" not in session:
            flash(f"Your user doesn't have a library card number", "error")
            return redirect(url_for("index"))

        with db.engine.begin() as conn:
            reader_id = conn.execute(text("""SELECT reader_id FROM app_user WHERE app_user.id = :user_id LIMIT 1"""), {"user_id": session["user_id"]}).scalar_one_or_none()

            if not reader_id:
                flash(f"Your user doesn't have a library card number", "error")
                return redirect(url_for("index"))

            notifications = conn.execute(
                text("""
                    SELECT id, sent_datetime, subject, body, read
                    FROM app_notification
                    WHERE reader_id = :reader_id
                    ORDER BY sent_datetime DESC
                """),
                {"reader_id": reader_id}
            ).mappings().all()

        return render_template(
            "reader/notifications.html",
            notifications=notifications
        )
    
    # Toggle read/unread for a single notification
    @app.route("/notification/<int:notif_id>/toggle", methods=["POST"])
    @login_required
    def toggle_notification_read(notif_id):
        with db.engine.begin() as conn:
            current = conn.execute(
                text("SELECT read FROM app_notification WHERE id = :id"),
                {"id": notif_id}
            ).scalar_one_or_none()

            if current is None:
                flash("Notification not found", "error")
                return redirect(url_for("notifications"))

            conn.execute(
                text("UPDATE app_notification SET read = :new WHERE id = :id"),
                {"new": not current, "id": notif_id}
            )

        return redirect(url_for("notifications") + f"#notif-{notif_id}")
    
    # Browse books page
    @app.route("/books")
    def browse_books():
        searches = {
            "b.title": request.args.get("title", "").strip(),
            "a.unique_name": request.args.get("authors", "").strip(),
            "c.name": request.args.get("categories", "").strip(),
            "b.description": request.args.get("description", "").strip()
        }

        conditions = []
        params = {}
        param_counter = 0

        for column, search_string in searches.items():
            local_conditions = []
            for pattern in search_string.split("||"):
                if not pattern:
                    continue

                param = f"p{param_counter}"
                param_counter += 1
                local_conditions.append("{column} ILIKE :{param}".format(column=column, param=param))
                params[param] = f"{pattern}"

            if local_conditions:
                conditions.append(" OR ".join(local_conditions))

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        
        with db.engine.begin() as conn:
            rows = conn.execute(
                text(f"""
                    SELECT DISTINCT b.id
                    FROM book b
                    LEFT JOIN book_author ba ON ba.book_id = b.id
                    LEFT JOIN author a ON a.id = ba.author_id
                    LEFT JOIN book_category bc ON bc.book_id = b.id
                    LEFT JOIN category c ON c.id = bc.category_id
                    {where_clause}
                """),
                params
            ).all()

            book_ids = [r[0] for r in rows]
            view_where_clause = ""
            view_params = {}

            if book_ids:
                view_where_clause = f"WHERE book_id = ANY(:book_ids)"
                view_params = {"book_ids": book_ids}
                if request.args.get("available_only") == "1":
                    view_where_clause += " AND (total_copies - currently_issued_copies - currently_reserved_copies) > 0"
            elif conditions:
                view_where_clause = "WHERE 1 = 0"
            
            books = conn.execute(
                text(f"""
                    SELECT *
                    FROM book_info_view
                    {view_where_clause}
                    ORDER BY title
                """),
                view_params
            ).mappings().all()

            return render_template(
                "reader/books.html",
                books=books,
                filters=request.args
            )


