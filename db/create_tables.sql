CREATE TABLE IF NOT EXISTS book (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    title TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS author (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    unique_name TEXT NOT NULL UNIQUE,
    first_name TEXT,
    last_name TEXT,
    bio TEXT
);

CREATE TABLE IF NOT EXISTS category (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    suggested_min_age INTEGER,
    description TEXT,
    CONSTRAINT age_constraint CHECK (suggested_min_age IS NULL OR suggested_min_age > 0)
);

CREATE TABLE IF NOT EXISTS book_author (
    book_id BIGINT NOT NULL,
    author_id BIGINT NOT NULL,
    PRIMARY KEY (book_id, author_id),
    FOREIGN KEY (book_id) REFERENCES book(id) ON DELETE CASCADE,
    FOREIGN KEY (author_id) REFERENCES author(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS book_category (
    book_id BIGINT NOT NULL,
    category_id BIGINT NOT NULL,
    PRIMARY KEY (book_id, category_id),
    FOREIGN KEY (book_id) REFERENCES book(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES category(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS publisher (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description text,
    address TEXT,
    email TEXT,
    phone TEXT
);

CREATE TABLE IF NOT EXISTS book_copy (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    isbn CHAR(13),
    year_published SMALLINT,
    place_of_publication TEXT,
    book_id BIGINT NOT NULL,
    publisher_id BIGINT NOT NULL,
    purchase_datetime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    purchase_price NUMERIC(10, 2) NOT NULL,
    CONSTRAINT isbn_13_format CHECK (isbn IS NULL OR isbn ~ '^[0-9]{13}$'),
    CONSTRAINT non_negative_purch_price CHECK (purchase_price >= 0),
    FOREIGN KEY (book_id) REFERENCES book(id) ON DELETE CASCADE,
    FOREIGN KEY (publisher_id) REFERENCES publisher(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS reader (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    card_no VARCHAR(20) NOT NULL UNIQUE,
    first_name TEXT,
    last_name TEXT,
    CONSTRAINT card_no_fixed_length CHECK (LENGTH(card_no) = 20)
);

CREATE TABLE IF NOT EXISTS reservation (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    from_datetime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    to_datetime TIMESTAMP NOT NULL,
    book_copy_id BIGINT NOT NULL,
    reader_id BIGINT NOT NULL,
    CONSTRAINT to_datetime_check CHECK (from_datetime < to_datetime),
    FOREIGN KEY (book_copy_id) REFERENCES book_copy(id) ON DELETE RESTRICT,
    FOREIGN KEY (reader_id) REFERENCES reader(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS issue (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    issue_datetime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    due_datetime TIMESTAMP NOT NULL,
    return_datetime TIMESTAMP,
    book_copy_id BIGINT NOT NULL,
    reader_id BIGINT NOT NULL,
    CONSTRAINT due_datetime_check CHECK (issue_datetime < due_datetime),
    CONSTRAINT return_datetime_check CHECK (return_datetime IS NULL OR issue_datetime < return_datetime),
    FOREIGN KEY (book_copy_id) REFERENCES book_copy(id) ON DELETE RESTRICT,
    FOREIGN KEY (reader_id) REFERENCES reader(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS rating (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    book_id BIGINT NOT NULL,
    reader_id BIGINT NOT NULL,
    rating SMALLINT NOT NULL,
    review TEXT,
    post_datetime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT rating_check CHECK (rating > 0 AND rating <= 10),
    FOREIGN KEY (book_id) REFERENCES book(id) ON DELETE CASCADE,
    FOREIGN KEY (reader_id) REFERENCES reader(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS app_notification (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    sent_datetime TIMESTAMP NOT NULL,
    reader_id BIGINT NOT NULL,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    read BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (reader_id) REFERENCES reader(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS app_role (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TYPE access_level_enum AS ENUM (
    'read',
    'create',
    'update',
    'delete'
);

CREATE TABLE IF NOT EXISTS entity_permission (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    entity TEXT NOT NULL,
    access_level access_level_enum NOT NULL
);

CREATE TABLE IF NOT EXISTS app_user (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role_id BIGINT NOT NULL,
    reader_id BIGINT UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES app_role(id) ON DELETE RESTRICT,
    FOREIGN KEY (reader_id) REFERENCES reader(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS app_role_entity_permission (
    role_id BIGINT NOT NULL,
    permission_id BIGINT NOT NULL,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES app_role(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES entity_permission(id) ON DELETE CASCADE
);
