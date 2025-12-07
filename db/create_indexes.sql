-- https://www.postgresql.org/docs/current/indexes-types.html#INDEXES-TYPES

-- Enable pg_trgm for trigram indexes
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Book.title (GIN trigram index)
CREATE INDEX IF NOT EXISTS idx_book_title_trgm ON Book USING gin(title gin_trgm_ops);

-- Book.description (GIN trigram index)
CREATE INDEX IF NOT EXISTS idx_book_description_trgm ON Book USING gin(description gin_trgm_ops);

-- Book.id FK's
CREATE INDEX IF NOT EXISTS idx_book_author_book_id ON Book_author(book_id);
CREATE INDEX IF NOT EXISTS idx_book_category_book_id ON Book_category(book_id);
CREATE INDEX IF NOT EXISTS idx_book_copy_book_id ON Book_copy(book_id);
CREATE INDEX IF NOT EXISTS idx_rating_book_id ON Rating(book_id);

-- Author.unique_name (GIN trigram index)
CREATE INDEX IF NOT EXISTS idx_author_unique_name_trgm ON Author USING gin(unique_name gin_trgm_ops);

-- Author.bio (GIN trigram index)
CREATE INDEX IF NOT EXISTS idx_author_bio_trgm ON Author USING gin(bio gin_trgm_ops);

-- Author.first_name
CREATE INDEX IF NOT EXISTS idx_author_first_name ON Author(first_name);

-- Author.last_name
CREATE INDEX IF NOT EXISTS idx_author_last_name ON Author(last_name);

-- Author.id FK
CREATE INDEX IF NOT EXISTS idx_book_author_author_id ON Book_author(author_id);

-- Category.description (GIN trigram index)
CREATE INDEX IF NOT EXISTS idx_category_description_trgm ON Category USING gin(description gin_trgm_ops);

-- Category.id FK
CREATE INDEX IF NOT EXISTS idx_book_category_category_id ON Book_category(category_id);

-- Publisher.name (GIN trigram index)
CREATE INDEX IF NOT EXISTS idx_publisher_name_trgm ON Publisher USING gin(name gin_trgm_ops);

-- Publisher.description (GIN trigram index)
CREATE INDEX IF NOT EXISTS idx_publisher_description_trgm ON Publisher USING gin(description gin_trgm_ops);

-- Publisher.id FK
CREATE INDEX IF NOT EXISTS idx_book_copy_publisher_id ON Book_copy(publisher_id);

-- Reader.id FK's
CREATE INDEX IF NOT EXISTS idx_issue_reader_id ON Issue(reader_id);
CREATE INDEX IF NOT EXISTS idx_reservation_reader_id ON Reservation(reader_id);
CREATE INDEX IF NOT EXISTS idx_rating_reader_id ON Rating(reader_id);
CREATE INDEX IF NOT EXISTS idx_notification_reader_id ON Notification(reader_id);

-- Book_copy.isbn
CREATE INDEX IF NOT EXISTS idx_book_copy_isbn ON Book_copy(isbn);

-- Book_copy.id FK's
CREATE INDEX IF NOT EXISTS idx_reservation_book_copy_id ON Reservation(book_copy_id);
CREATE INDEX IF NOT EXISTS idx_issue_book_copy_id ON Issue(book_copy_id);

-- Reservation.from_datetime
CREATE INDEX IF NOT EXISTS idx_reservation_from_datetime ON Reservation(from_datetime);

-- Reservation.to_datetime
CREATE INDEX IF NOT EXISTS idx_reservation_to_datetime ON Reservation(to_datetime);

-- Issue.issue_datetime
CREATE INDEX IF NOT EXISTS idx_issue_issue_datetime ON Issue(issue_datetime);

-- Issue.due_datetime
CREATE INDEX IF NOT EXISTS idx_issue_due_datetime ON Issue(due_datetime);

-- Issue.return_datetime
CREATE INDEX IF NOT EXISTS idx_issue_return_datetime ON Issue(return_datetime);

-- Notification.sent_time (BRIN index)
CREATE INDEX IF NOT EXISTS idx_notification_sent_datetime_brin ON Notification USING brin(sent_datetime) WITH (pages_per_range = 16);
