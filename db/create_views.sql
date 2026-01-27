-- create_views.sql

-- +================+
-- | BOOK COPY INFO |
-- +================+
CREATE OR REPLACE VIEW book_copy_info_view AS
SELECT
    bc.id AS "book_copy_id",
    b.id AS "book_id",
    b.title AS "title",
    COALESCE(a.authors, '') AS "authors",
    COALESCE(c.categories, '') AS "categories",
    COALESCE(b.description, '') AS "description",
    bc.isbn,
    bc.year_published,
    COALESCE(bc.place_of_publication, '') AS "place_of_publication",
    p.name AS "publisher_name",
    bc.purchase_datetime,
    bc.purchase_price,
    EXISTS (
        SELECT 1
        FROM issue i
        WHERE i.book_copy_id = bc.id 
          AND COALESCE(i.return_datetime, 'infinity'::timestamp) > CURRENT_TIMESTAMP
    ) AS "currently_issued",
    EXISTS (
        SELECT 1
        FROM reservation r
        WHERE r.book_copy_id = bc.id 
          AND r.to_datetime >= CURRENT_TIMESTAMP
    ) AS "currently_reserved"
FROM book_copy bc
JOIN book b ON bc.book_id = b.id
JOIN publisher p ON bc.publisher_id = p.id

-- Aggregate authors
LEFT JOIN (
    SELECT ba.book_id, STRING_AGG(a.unique_name, ', ' ORDER BY a.unique_name) AS "authors"
    FROM book_author ba
    JOIN author a ON ba.author_id = a.id
    GROUP BY ba.book_id
) a ON b.id = a.book_id

-- Aggregate categories
LEFT JOIN (
    SELECT bc.book_id, STRING_AGG(c.name, ', ' ORDER BY c.name) AS "categories"
    FROM book_category bc
    JOIN category c ON bc.category_id = c.id
    GROUP BY bc.book_id
) c ON b.id = c.book_id;

-- +===========+
-- | BOOK INFO |
-- +===========+
CREATE OR REPLACE VIEW book_info_view AS
SELECT
    bcv.title,
    bcv.authors,
    bcv.categories,
    bcv.description,
    bcv.isbn,
    bcv.year_published,
    bcv.place_of_publication,
    bcv.publisher_name,
    bcv.purchase_datetime,
    bcv.purchase_price,
    COUNT(bcv.book_id) AS "total_copies",
    COUNT(bcv.currently_issued) AS "currently_issued_copies",
    COUNT(bcv.currently_reserved) AS "currently_reserved_copies"
FROM book_copy_info_view bcv
GROUP BY bcv.book_id, bcv.title, bcv.authors, bcv.categories, bcv.description, bcv.isbn, bcv.year_published, bcv.place_of_publication, bcv.publisher_name, bcv.purchase_datetime, bcv.purchase_price;

-- +=============+
-- | READER INFO |
-- +=============+
CREATE OR REPLACE VIEW reader_info_view AS
SELECT
    r.id AS "reader_id",
    r.card_no AS "library_card",
    COALESCE(r.first_name, '') AS "first_name",
    COALESCE(r.last_name, '') AS "last_name",
    COALESCE(total_issues.count, 0) AS "total_issues",
    COALESCE(active_issues.count, 0) AS "active_issues",
    COALESCE(total_res.count, 0) AS "total_reservations",
    COALESCE(active_res.count, 0) AS "active_reservations",
    COALESCE(total_ratings.count, 0) AS "total_ratings"
FROM reader r

-- Total issues
LEFT JOIN (
    SELECT reader_id, COUNT(*) AS count
    FROM issue
    GROUP BY reader_id
) total_issues ON r.id = total_issues.reader_id

-- Active issues (not returned)
LEFT JOIN (
    SELECT reader_id, COUNT(*) AS count
    FROM issue
    WHERE COALESCE(return_datetime, 'infinity'::timestamp) > CURRENT_TIMESTAMP
    GROUP BY reader_id
) active_issues ON r.id = active_issues.reader_id

-- Total reservations
LEFT JOIN (
    SELECT reader_id, COUNT(*) AS count
    FROM reservation
    GROUP BY reader_id
) total_res ON r.id = total_res.reader_id

-- Active reservations (not past)
LEFT JOIN (
    SELECT reader_id, COUNT(*) AS count
    FROM reservation
    WHERE to_datetime >= CURRENT_TIMESTAMP
    GROUP BY reader_id
) active_res ON r.id = active_res.reader_id

-- Total ratings
LEFT JOIN (
    SELECT reader_id, COUNT(*) AS count
    FROM rating
    GROUP BY reader_id
) total_ratings ON r.id = total_ratings.reader_id;

-- +======================+
-- | ROLE PERMISSION INFO |
-- +======================+
CREATE OR REPLACE VIEW role_permission_info_view AS
WITH perms_per_access AS (
    SELECT
        r.id AS "role_id",
        r.name AS "role_name",
        p.access_level::text AS "access_level",
        STRING_AGG(p.entity, ', ' ORDER BY p.entity) AS "entities"
    FROM app_role r
    JOIN app_role_entity_permission rp ON r.id = rp.role_id
    JOIN entity_permission p ON rp.permission_id = p.id
    GROUP BY r.id, r.name, p.access_level
)
SELECT
    role_id,
    role_name,
    STRING_AGG(access_level || ': ' || entities, '; ' ORDER BY access_level, entities) AS aggregate_permissions
FROM perms_per_access
GROUP BY role_id, role_name;

-- +===========+
-- | USER INFO |
-- +===========+
CREATE OR REPLACE VIEW user_info_view AS
SELECT
    u.id AS "user_id",
    u.username AS "username",
    COALESCE(rd.card_no, '') AS "library_card",
    rpiv.role_name,
    rpiv.aggregate_permissions
FROM app_user u
LEFT JOIN reader rd ON u.reader_id = rd.id
LEFT JOIN role_permission_info_view rpiv ON u.role_id = rpiv.role_id;