-- create_indexes.sql

-- https://www.postgresql.org/docs/current/indexes-types.html#INDEXES-TYPES

-- Enable pg_trgm for trigram indexes
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- book.title (GIN trigram index)
CREATE INDEX IF NOT EXISTS idx_book_title_trgm ON book USING gin(title gin_trgm_ops);

-- book.description (GIN trigram index)
CREATE INDEX IF NOT EXISTS idx_book_description_trgm ON book USING gin(description gin_trgm_ops);

-- book.id FK's
CREATE INDEX IF NOT EXISTS idx_book_author_book_id ON book_author(book_id);
CREATE INDEX IF NOT EXISTS idx_book_category_book_id ON book_category(book_id);
CREATE INDEX IF NOT EXISTS idx_book_copy_book_id ON book_copy(book_id);
CREATE INDEX IF NOT EXISTS idx_rating_book_id ON rating(book_id);

-- author.unique_name (GIN trigram index)
CREATE INDEX IF NOT EXISTS idx_author_unique_name_trgm ON author USING gin(unique_name gin_trgm_ops);

-- author.bio (GIN trigram index)
CREATE INDEX IF NOT EXISTS idx_author_bio_trgm ON author USING gin(bio gin_trgm_ops);

-- author.first_name
CREATE INDEX IF NOT EXISTS idx_author_first_name ON author(first_name);

-- author.last_name
CREATE INDEX IF NOT EXISTS idx_author_last_name ON author(last_name);

-- author.id FK
CREATE INDEX IF NOT EXISTS idx_book_author_author_id ON book_author(author_id);

-- category.description (GIN trigram index)
CREATE INDEX IF NOT EXISTS idx_category_description_trgm ON category USING gin(description gin_trgm_ops);

-- category.id FK
CREATE INDEX IF NOT EXISTS idx_book_category_category_id ON book_category(category_id);

-- publisher.name (GIN trigram index)
CREATE INDEX IF NOT EXISTS idx_publisher_name_trgm ON publisher USING gin(name gin_trgm_ops);

-- publisher.description (GIN trigram index)
CREATE INDEX IF NOT EXISTS idx_publisher_description_trgm ON publisher USING gin(description gin_trgm_ops);

-- publisher.id FK
CREATE INDEX IF NOT EXISTS idx_book_copy_publisher_id ON book_copy(publisher_id);

-- reader.id FK's
CREATE INDEX IF NOT EXISTS idx_issue_reader_id ON issue(reader_id);
CREATE INDEX IF NOT EXISTS idx_reservation_reader_id ON reservation(reader_id);
CREATE INDEX IF NOT EXISTS idx_rating_reader_id ON rating(reader_id);
CREATE INDEX IF NOT EXISTS idx_app_notification_reader_id ON app_notification(reader_id);
CREATE INDEX IF NOT EXISTS idx_app_user_reader_id ON app_user(reader_id);

-- book_copy.isbn
CREATE INDEX IF NOT EXISTS idx_book_copy_isbn ON book_copy(isbn);

-- book_copy.id FK's
CREATE INDEX IF NOT EXISTS idx_reservation_book_copy_id ON reservation(book_copy_id);
CREATE INDEX IF NOT EXISTS idx_issue_book_copy_id ON issue(book_copy_id);

-- reservation.from_datetime
CREATE INDEX IF NOT EXISTS idx_reservation_from_datetime ON reservation(from_datetime);

-- reservation.to_datetime
CREATE INDEX IF NOT EXISTS idx_reservation_to_datetime ON reservation(to_datetime);

-- issue.issue_datetime
CREATE INDEX IF NOT EXISTS idx_issue_issue_datetime ON issue(issue_datetime);

-- issue.due_datetime
CREATE INDEX IF NOT EXISTS idx_issue_due_datetime ON issue(due_datetime);

-- issue.return_datetime
CREATE INDEX IF NOT EXISTS idx_issue_return_datetime ON issue(return_datetime);

-- app_notification.sent_time (BRIN index)
CREATE INDEX IF NOT EXISTS idx_app_notification_sent_datetime_brin ON app_notification USING brin(sent_datetime) WITH (pages_per_range = 16);

-- app_role.id FK's
CREATE INDEX IF NOT EXISTS idx_app_user_role_id ON app_user(role_id);
CREATE INDEX IF NOT EXISTS idx_app_role_entity_permission_role_id ON app_role_entity_permission(role_id);

-- entity_permission.id FK
CREATE INDEX IF NOT EXISTS idx_app_role_entity_permission_permission_id ON app_role_entity_permission(permission_id);
