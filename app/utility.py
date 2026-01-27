# utility.py
from sqlalchemy import text
from pathlib import Path
import json
import os

def get_table_metadata(conn, table_name):
    # Get all columns
    columns = conn.execute(text("""
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default,
            udt_name,
            is_identity
        FROM information_schema.columns
        WHERE table_name = :table
        ORDER BY ordinal_position
    """), {"table": table_name}).mappings().all()

    # Get primary key
    pk = conn.execute(text("""
        SELECT a.attname
        FROM pg_index i
        JOIN pg_attribute a
            ON a.attrelid = i.indrelid
           AND a.attnum = ANY(i.indkey)
        WHERE i.indrelid = to_regclass(:table)
          AND i.indisprimary
    """), {"table": table_name}).scalar()

    # Get foreign keys
    fk_columns = {}
    for col in columns:
        col_name = col["column_name"]
        fk = conn.execute(text("""
            SELECT
                ccu.table_name AS ref_table,
                ccu.column_name AS ref_column
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
               AND tc.table_name = kcu.table_name
            JOIN information_schema.constraint_column_usage ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
              AND tc.table_name = :table
              AND kcu.column_name = :col
        """), {"table": table_name, "col": col_name}).mappings().first()

        if fk:
            fk_columns[col_name] = fk

    return columns, pk, fk_columns

# Helper to prepare editable columns, FK values, and enum options
def prepare_columns(conn, columns, fk_columns):
    editable_columns = [
        col for col in columns
        if col['is_identity'] != 'YES'
    ]

    fk_info = {}
    enum_info = {}

    for col in editable_columns:
        col_name = col["column_name"]

        if col_name in fk_columns:
            ref_table = fk_columns[col_name]["ref_table"]
            ref_column = fk_columns[col_name]["ref_column"]
            fk_info[col_name] = conn.execute(text(f"SELECT {ref_column} FROM {ref_table}")).scalars().all()

        enum_type = col.get('udt_name', None)
        if enum_type:
            rows = conn.execute(text("""
                SELECT enumlabel, enumsortorder
                FROM pg_enum
                JOIN pg_type ON pg_type.oid = pg_enum.enumtypid
                WHERE pg_type.typname = :enum_type
            """), {"enum_type": enum_type}).all()
            enum_values = [row[0] for row in sorted(rows, key=lambda r: r[1])]
            if enum_values:
                enum_info[col_name] = enum_values

    return editable_columns, fk_info, enum_info


def load_table_registry():
    TABLES_FILE = Path(__file__).resolve().parent / "table_registry.json"
    if not TABLES_FILE.exists():
        return dict()
    with open(TABLES_FILE) as f:
        tables = json.load(f)
    return tables

# Helper function: is role a superadmin
def is_superadmin_role(conn, role_id):
    return conn.execute(
        text("""
            SELECT :role_id = get_role_id(:superadmin_role)
        """),
        {
            "role_id": role_id,
            "superadmin_role": os.getenv("APP_SUPERADMIN_ROLE", "superadmin"),
        }
    ).scalar()
    
