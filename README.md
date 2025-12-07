# Library Management System

This project was created as part of the Databases course at Wrocław University of Science and Technology.
It is a basic library management system built as a web application using Django and PostgreSQL, running in Docker containers.

---

## Technologies Used

* Django (Python)
* PostgreSQL
* Docker & Docker Compose

---

## Setup

1. **Clone the repository**

```bash
git clone https://github.com/iwonieevo/library-management-system
cd library-management-system
```

2. **Create a `.env` file**

Copy the provided `.env.example` and fill in the required fields:

```bash
cp .env.example .env
```

---

## Environment Variables

### PostgreSQL Configuration

* `DB_NAME` – Name of the PostgreSQL database
* `DB_USER` – PostgreSQL username
* `DB_PASSWORD` – Database password (leave blank for local development)
* `DB_EXPOSED_PORT` – Port on your **host machine** for connecting to PostgreSQL
* `DB_PORT` – Internal PostgreSQL port inside the Docker network (default: 5432)
* `DB_IMAGE` – Docker image for PostgreSQL (can specify version, e.g., `postgres:18`)
* `POSTGRES_DATA_VOLUME` – Docker volume name for PostgreSQL data persistence

### Django Settings

* `CORE_SECRET_KEY` – Django secret key
* `DEBUG` – Enable Django debug mode (`1` = on, `0` = off)
* `DJANGO_ALLOWED_HOSTS` – Comma-separated list of allowed hosts for Django
* `WEB_PORT` – Port on your **host machine** mapped to Django’s internal container port (`8000` inside container)

---

3. **Start Docker containers**

```bash
docker-compose up --build
```

This will start two services:

* `web` – the Django application
* `db` – the PostgreSQL database

4. **Apply Django migrations**
   In a new terminal:

```bash
docker-compose exec web python manage.py migrate
```


5. **Access the app**

Open your browser at:

```
http://<WEB_HOST>:<WEB_PORT>
```

* `<WEB_HOST>` is your host machine’s address (e.g., `localhost` for local development, or your domain name for production).
* `<WEB_PORT>` is the port mapped to the Django container (set in your `.env` file as `WEB_PORT`, default `8000`).

For production with a domain and standard HTTP/HTTPS ports, you can set `WEB_PORT=80` (HTTP) or `WEB_PORT=443` (HTTPS) and configure `DJANGO_ALLOWED_HOSTS` to include your domain. In that case, users can access your site via the domain without specifying a port.
