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
BEGIN
    -- Insert the book
    INSERT INTO Book(title, description)
    VALUES (p_title, p_description)
    RETURNING id INTO v_book_id;

    -- Check if all authors exist
    IF COALESCE(array_length(p_author_unique_names, 1), 0) IS DISTINCT FROM 
    (SELECT COUNT(*) FROM Author WHERE unique_name = ANY(p_author_unique_names)) THEN
        RAISE EXCEPTION 'One or more authors do not exist';
    END IF;

    -- Check if all categories exist
    IF COALESCE(array_length(p_category_names, 1), 0) IS DISTINCT FROM 
    (SELECT COUNT(*) FROM Category WHERE name = ANY(p_category_names)) THEN
        RAISE EXCEPTION 'One or more categories do not exist';
    END IF;

    -- Associate authors
    INSERT INTO Book_author(book_id, author_id)
    SELECT v_book_id, Author.id
    FROM Author
    WHERE unique_name = ANY(p_author_unique_names);

    -- Associate categories
    INSERT INTO Book_category(book_id, category_id)
    SELECT v_book_id, Category.id
    FROM Category
    WHERE name = ANY(p_category_names);
END;
$$;

-- +=============+
-- | UPDATE BOOK |
-- +=============+
CREATE OR REPLACE PROCEDURE update_book(
    p_book_id BIGINT,
    p_title TEXT,
    p_description TEXT,
    p_author_unique_names TEXT[],
    p_category_names TEXT[]
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_author_ids BIGINT[];
    v_category_ids BIGINT[];
BEGIN
    -- Check if book exists
    IF NOT EXISTS (SELECT 1 FROM Book WHERE id = p_book_id) THEN
        RAISE EXCEPTION 'Book with id % does not exist', p_book_id;
    END IF;

    -- Update title and description if provided
    IF p_title IS NOT NULL THEN
        UPDATE Book SET title = p_title WHERE id = p_book_id;
    END IF;

    IF p_description IS NOT NULL THEN
        UPDATE Book SET description = p_description WHERE id = p_book_id;
    END IF;

    -- Process authors if provided
    IF p_author_unique_names IS NOT NULL THEN
        -- Check if all authors exist
        SELECT COALESCE(ARRAY_AGG(id), '{}') INTO v_author_ids
        FROM Author
        WHERE unique_name = ANY(p_author_unique_names);

        IF array_length(v_author_ids, 1) IS DISTINCT FROM array_length(p_author_unique_names, 1) THEN
            RAISE EXCEPTION 'One or more authors do not exist';
        END IF;

        -- Delete authors no longer in the list
        DELETE FROM Book_author
        WHERE book_id = p_book_id 
          AND author_id <> ALL(v_author_ids);

        -- Insert new authors not already linked
        INSERT INTO Book_author(book_id, author_id)
        SELECT p_book_id, Author.id
        FROM Author
        WHERE Author.id = ANY(v_author_ids)
          AND NOT EXISTS (
            SELECT 1 FROM Book_author
            WHERE book_id = p_book_id AND author_id = Author.id
          );
    END IF;

    -- Process categories if provided
    IF p_category_names IS NOT NULL THEN
        -- Check all categories exist
        SELECT COALESCE(ARRAY_AGG(id), '{}') INTO v_category_ids
        FROM Category
        WHERE name = ANY(p_category_names);

        IF array_length(v_category_ids, 1) IS DISTINCT FROM array_length(p_category_names, 1) THEN
            RAISE EXCEPTION 'One or more categories do not exist';
        END IF;

        -- Delete categories no longer in the list
        DELETE FROM Book_category
        WHERE book_id = p_book_id 
          AND category_id <> ALL(v_category_ids);

        -- Insert new categories not already linked
        INSERT INTO Book_category(book_id, category_id)
        SELECT p_book_id, Category.id
        FROM Category
        WHERE Category.id = ANY(v_category_ids)
          AND NOT EXISTS (
            SELECT 1 FROM Book_category
            WHERE book_id = p_book_id AND category_id = Category.id
          );
    END IF;
END;
$$;

