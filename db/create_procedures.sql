-- create_procedures.sql

-- +==========+
-- | ADD BOOK |
-- +==========+
CREATE OR REPLACE PROCEDURE add_book(
    p_title TEXT,
    p_description TEXT,
    p_author_unique_names TEXT[],
    p_category_names TEXT[]
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_book_id BIGINT;
    v_author_unique_name TEXT;
    v_category_name TEXT;
BEGIN
    INSERT INTO book(title, description)
    VALUES (p_title, p_description)
    RETURNING id INTO v_book_id;

    FOREACH v_author_unique_name IN ARRAY p_author_unique_names
    LOOP
        INSERT INTO book_author(book_id, author_id)
        VALUES(v_book_id, get_author_id(v_author_unique_name));
    END LOOP;

    FOREACH v_category_name IN ARRAY p_category_names
    LOOP
        INSERT INTO book_category(book_id, category_id)
        VALUES(v_book_id, get_category_id(v_category_name));
    END LOOP;
END;
$$;

-- +=============+
-- | UPDATE BOOK |
-- +=============+
CREATE OR REPLACE PROCEDURE update_book(
    p_title TEXT,
    p_description TEXT,
    p_author_unique_names TEXT[],
    p_category_names TEXT[]
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_book_id BIGINT;

    v_old_author_ids BIGINT[];
    v_new_author_ids BIGINT[];
    v_old_category_ids BIGINT[];
    v_new_category_ids BIGINT[];

    v_author_name TEXT;
    v_category_name TEXT;
    v_old_author_id BIGINT;
    v_old_category_id BIGINT;
BEGIN
    v_book_id := get_book_id(p_title);

    IF p_title IS NOT NULL THEN
        UPDATE book SET title = p_title WHERE id = v_book_id;
    END IF;

    IF p_description IS NOT NULL THEN
        UPDATE book SET description = p_description WHERE id = v_book_id;
    END IF;

    IF p_author_unique_names IS NOT NULL THEN
        FOR v_old_author_id IN SELECT author_id FROM book_author WHERE book_id = v_book_id
        LOOP
            IF NOT EXISTS (
                SELECT 1
                FROM unnest(p_author_unique_names) n
                WHERE get_author_id(n) = v_old_author_id
            ) THEN
                DELETE FROM book_author
                WHERE book_id = v_book_id AND author_id = v_old_author_id;
            END IF;
        END LOOP;

        FOREACH v_author_name IN ARRAY p_author_unique_names LOOP
            IF NOT EXISTS (
                SELECT 1 FROM book_author
                WHERE book_id = v_book_id
                  AND author_id = get_author_id(v_author_name)
            ) THEN
                INSERT INTO book_author(book_id, author_id)
                VALUES (v_book_id, get_author_id(v_author_name));
            END IF;
        END LOOP;
    END IF;

    IF p_category_names IS NOT NULL THEN
        FOR v_old_category_id IN SELECT category_id FROM book_category WHERE book_id = v_book_id
        LOOP
            IF NOT EXISTS (
                SELECT 1
                FROM unnest(p_category_names) n
                WHERE get_category_id(n) = v_old_category_id
            ) THEN
                DELETE FROM book_category
                WHERE book_id = v_book_id AND category_id = v_old_category_id;
            END IF;
        END LOOP;

        FOREACH v_category_name IN ARRAY p_category_names LOOP
            IF NOT EXISTS (
                SELECT 1 FROM book_category
                WHERE book_id = v_book_id
                  AND category_id = get_category_id(v_category_name)
            ) THEN
                INSERT INTO book_category(book_id, category_id)
                VALUES (v_book_id, get_category_id(v_category_name));
            END IF;
        END LOOP;
    END IF;
END;
$$;
