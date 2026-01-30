# Library Management System
**Disclaimer:** This project was created as part of the Databases course at Wrocław University of Science and Technology.

A web-based library management system built with Flask and PostgreSQL, containerized with Docker. This system manages books, authors, categories, publishers, readers, reservations, issues, ratings, and user permissions through a structured database and web interface.

## Technologies
- **Backend:** Flask (Python)
- **Database:** PostgreSQL with PL/pgSQL
- **Containerization:** Docker & Docker Compose
- **ORM:** SQLAlchemy
- **Frontend:** HTML templates with CSS styling

## Features
- **Complete Database Schema:** 16 normalized tables with constraints
- **Data Integrity:** Triggers prevent overlapping reservations/issues
- **Performance:** GIN trigram indexes for text search, BRIN for time-series
- **Business Logic:** PL/pgSQL functions and stored procedures
- **Predefined Views:** For book info, reader info, user info, and permissions
- **Authentication:** RBAC (Role Based Access Control)
- **Admin Interface:** Superadmin panel for direct table management
- **CLI Tools:** Commands for user management and permission syncing

## Project Structure
```
library-management-system/
├── app/                       # Flask application
│   ├── static/                # CSS and favicon
│   ├── templates/             # HTML templates
│   ├── __init__.py            # App factory
│   ├── auth.py                # Authentication decorators
│   ├── commands.py            # CLI commands
│   ├── routes.py              # Route definitions
│   ├── table_registry.json    # Table name mappings
│   └── utility.py             # Helper functions
├── db/                        # Database schema
│   ├── create_tables.sql      # Table definitions
│   ├── create_indexes.sql     # Indexes
│   ├── create_views.sql       # Views
│   ├── create_triggers.sql    # Triggers
│   ├── create_functions.sql   # Functions
│   └── create_procedures.sql  # Procedures
├── .env.example               # Environment template
├── docker-compose.yml         # Docker services
├── Dockerfile                 # Web service image
├── requirements.txt           # Python dependencies
├── run.py                     # Application entry point
└── README.md                  # This file
```

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/iwonieevo/library-management-system
cd library-management-system
```

### 2. Configure Environment Variables

Copy the example environment file and edit it with your configuration:

```bash
cp .env.example .env
```

### 3. Build and Start the Application

Use Docker Compose to build and start the application:

```bash
docker-compose up --build
```


### 4. Initialize the Superadmin Account

```bash
docker-compose exec web flask create-superadmin
```

Follow the prompts to enter a username and password.

### 5. Sync Permissions (Optional)

Sync the permission system with the database tables:
```bash
docker-compose exec web flask sync-permissions
```

### 6. Access the Application
- **Web Application:** Open `http://localhost:8000` (or your configured `WEB_EXPOSED_PORT`)

- **Database:** Connect to `localhost:5433` (or your configured `DB_EXPOSED_PORT`) with your database credentials

## Environment Variables

The following environment variables can be configured in the `.env` file:
| Variable | Description | Default |
|-|-|-|
| `DB_NAME` | PostgreSQL database name | `postgres` |
| `DB_USER` | PostgreSQL username | `postgres` |
| `DB_PASSWORD` | PostgreSQL password | `password` |
| `DB_INTERNAL_PORT` | PostgreSQL port inside Docker | `5432` |
| `DB_EXPOSED_PORT` | PostgreSQL port exposed to host | `5433` |
| `WEB_INTERNAL_PORT` | Flask port inside Docker | `8000` |
| `WEB_EXPOSED_PORT` | Flask port exposed to host | `8000` |
| `SECRET_KEY` | Flask secret key for sessions | `dev-secret-change-me` |
| `FLASK_APP` | Flask application entry point | `app:create_app` |
| `APP_SUPERADMIN_ROLE` | Name of the superadmin role | `superadmin` |

## Database schema
The database includes 16 tables with proper normalization, foreign key constraints, and data validation rules.
![ERD](ERD.jpg)

## Database Reset

To completely reset the database:

```bash
docker-compose down -v
docker-compose up --build
```
This will remove all Docker volumes and recreate the database from scratch.