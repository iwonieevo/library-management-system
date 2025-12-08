-- +======================+
-- | BOOK AGGREGATED INFO |
-- +======================+
CREATE OR REPLACE VIEW book_aggregated_info AS
SELECT
    b.id AS "book_id",
    b.title,
    COALESCE(b.description, '') AS "description",
    COALESCE(a.authors, '') AS "author",
    COALESCE(c.categories, '') AS "category",
    COALESCE(tc.total_amount, 0) AS "total_amount",
    COALESCE(ac.available_amount, 0) AS "available_amount"
FROM Book b

-- Concatenate authors
LEFT JOIN (
    SELECT ba.book_id, STRING_AGG(a.unique_name, ', ') AS authors
    FROM Book_author ba
    JOIN Author a ON ba.author_id = a.id
    GROUP BY ba.book_id
) a ON b.id = a.book_id

-- Concatenate categories
LEFT JOIN (
    SELECT bc.book_id, STRING_AGG(c.name, ', ') AS categories
    FROM Book_category bc
    JOIN Category c ON bc.category_id = c.id
    GROUP BY bc.book_id
) c ON b.id = c.book_id

-- Total amount of copies
LEFT JOIN (
    SELECT book_id, COUNT(*) AS total_amount
    FROM Book_copy
    GROUP BY book_id
) tc ON b.id = tc.book_id

-- Available amount of copies (not issued and not reserved)
LEFT JOIN (
    SELECT bc.book_id, COUNT(*) AS available_amount
    FROM Book_copy bc
    WHERE NOT EXISTS (
        SELECT 1
        FROM Issue i
        WHERE i.book_copy_id = bc.id
          AND COALESCE(i.return_datetime, 'infinity'::timestamp) > CURRENT_TIMESTAMP
    )
      AND NOT EXISTS (
        SELECT 1
        FROM Reservation r
        WHERE r.book_copy_id = bc.id
          AND r.to_datetime >= CURRENT_TIMESTAMP
    )
    GROUP BY bc.book_id
) ac ON b.id = ac.book_id;

-- +===========================+
-- | BOOK COPY AGGREGATED INFO |
-- +===========================+
CREATE OR REPLACE VIEW book_copy_aggregated_info AS
SELECT
    bc.id AS "book_copy_id",
    b.title AS "book_title",
    COALESCE(a.authors, '') AS "book_authors",
    COALESCE(c.categories, '') AS "book_categories",
    COALESCE(b.description, '') AS "book_description",
    bc.isbn,
    bc.year_published,
    COALESCE(bc.place_of_publication, '') AS "place_of_publication",
    p.name AS "publisher_name",
    bc.purchase_datetime,
    bc.purchase_price,
    -- Available if NOT issued (return_datetime IS NULL) AND NOT reserved (to_datetime >= now)
    NOT EXISTS (
        SELECT 1
        FROM Issue i
        WHERE i.book_copy_id = bc.id 
          AND COALESCE(i.return_datetime, 'infinity'::timestamp) > CURRENT_TIMESTAMP
    ) AND NOT EXISTS (
        SELECT 1
        FROM Reservation r
        WHERE r.book_copy_id = bc.id 
          AND r.to_datetime >= CURRENT_TIMESTAMP
    ) AS available
FROM Book_copy bc
JOIN Book b ON bc.book_id = b.id
JOIN Publisher p ON bc.publisher_id = p.id

-- Aggregate authors for the book
LEFT JOIN (
    SELECT ba.book_id, STRING_AGG(a.unique_name, ', ') AS authors
    FROM Book_author ba
    JOIN Author a ON ba.author_id = a.id
    GROUP BY ba.book_id
) a ON b.id = a.book_id

-- Aggregate categories for the book
LEFT JOIN (
    SELECT bc.book_id, STRING_AGG(c.name, ', ') AS categories
    FROM Book_category bc
    JOIN Category c ON bc.category_id = c.id
    GROUP BY bc.book_id
) c ON b.id = c.book_id;

-- +========================+
-- | READER AGGREGATED INFO |
-- +========================+
CREATE OR REPLACE VIEW reader_aggregated_info AS
SELECT
    r.id AS reader_id,
    r.card_no AS library_card,
    COALESCE(r.first_name, '') AS "first_name",
    COALESCE(r.last_name, '') AS "last_name",
    COALESCE(total_issues.count, 0) AS "total_issues",
    COALESCE(active_issues.count, 0) AS "active_issues",
    COALESCE(total_res.count, 0) AS "total_reservations",
    COALESCE(active_res.count, 0) AS "active_reservations",
    COALESCE(total_ratings.count, 0) AS "total_ratings",
    COALESCE(neg_ratings.count, 0) AS "negative_ratings",
    COALESCE(pos_ratings.count, 0) AS "positive_ratings"
FROM Reader r

-- Total issues
LEFT JOIN (
    SELECT reader_id, COUNT(*) AS count
    FROM Issue
    GROUP BY reader_id
) total_issues ON r.id = total_issues.reader_id

-- Active issues (not returned)
LEFT JOIN (
    SELECT reader_id, COUNT(*) AS count
    FROM Issue
    WHERE COALESCE(return_datetime, 'infinity'::timestamp) > CURRENT_TIMESTAMP
    GROUP BY reader_id
) active_issues ON r.id = active_issues.reader_id

-- Total reservations
LEFT JOIN (
    SELECT reader_id, COUNT(*) AS count
    FROM Reservation
    GROUP BY reader_id
) total_res ON r.id = total_res.reader_id

-- Active reservations (not past)
LEFT JOIN (
    SELECT reader_id, COUNT(*) AS count
    FROM Reservation
    WHERE to_datetime >= CURRENT_TIMESTAMP
    GROUP BY reader_id
) active_res ON r.id = active_res.reader_id

-- Total ratings
LEFT JOIN (
    SELECT reader_id, COUNT(*) AS count
    FROM Rating
    GROUP BY reader_id
) total_ratings ON r.id = total_ratings.reader_id

-- Negative ratings (1-3)
LEFT JOIN (
    SELECT reader_id, COUNT(*) AS count
    FROM Rating
    WHERE rating <= 3
    GROUP BY reader_id
) neg_ratings ON r.id = neg_ratings.reader_id

-- Positive ratings (8-10)
LEFT JOIN (
    SELECT reader_id, COUNT(*) AS count
    FROM Rating
    WHERE rating >= 8
    GROUP BY reader_id
) pos_ratings ON r.id = pos_ratings.reader_id;


