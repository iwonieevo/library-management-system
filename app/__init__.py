# __init__.py
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from urllib.parse import quote_plus
import os

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")

    DB_USER = quote_plus(os.getenv("DB_USER", "postgres"))
    DB_PASSWORD = quote_plus(os.getenv("DB_PASSWORD", "password"))
    DB_NAME = quote_plus(os.getenv("DB_NAME", "postgres"))
    DB_HOST = quote_plus(os.getenv("DB_HOST", "db"))
    DB_PORT = os.getenv("DB_INTERNAL_PORT", "5432")

    app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    
    from .commands import register_commands
    register_commands(app)

    from .routes import register_routes
    register_routes(app)

    return app
