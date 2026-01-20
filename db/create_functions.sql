-- +======================+
-- | GET BOOK_ID BY TITLE |
-- +======================+
CREATE OR REPLACE FUNCTION get_book_id(p_title TEXT)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_book_id BIGINT;
BEGIN
    SELECT id INTO v_book_id
    FROM book
    WHERE title = p_title
    LIMIT 1;

    IF v_book_id IS NULL THEN
        RAISE EXCEPTION 'Book with title "%" does not exist', p_title;
    END IF;

    RETURN v_book_id;
END;
$$;

-- +==========================+
-- | GET PUBLISHER_ID BY NAME |
-- +==========================+
CREATE OR REPLACE FUNCTION get_publisher_id(p_name TEXT)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_publisher_id BIGINT;
BEGIN
    SELECT id INTO v_publisher_id
    FROM publisher
    WHERE name = p_name
    LIMIT 1;

    IF v_publisher_id IS NULL THEN
        RAISE EXCEPTION 'Publisher "%" does not exist', p_name;
    END IF;

    RETURN v_publisher_id;
END;
$$;

-- +==========================+
-- | GET READER_ID BY CARD_NO |
-- +==========================+
CREATE OR REPLACE FUNCTION get_reader_id(p_card_no CHAR(20))
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_reader_id BIGINT;
BEGIN
    SELECT id INTO v_reader_id
    FROM reader
    WHERE card_no = p_card_no
    LIMIT 1;

    IF v_reader_id IS NULL THEN
        RAISE EXCEPTION 'Reader with card number "%" does not exist', p_card_no;
    END IF;

    RETURN v_reader_id;
END;
$$;

-- +=====================+
-- | GET ROLE_ID BY NAME |
-- +=====================+
CREATE OR REPLACE FUNCTION get_role_id(r_name TEXT)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_role_id BIGINT;
BEGIN
    SELECT id INTO v_role_id
    FROM app_role
    WHERE name = r_name
    LIMIT 1;

    IF v_role_id IS NULL THEN
        RAISE EXCEPTION 'Role "%" does not exist', r_name;
    END IF;

    RETURN v_role_id;
END;
$$;

-- +=========================+
-- | GET USER_ID BY USERNAME |
-- +=========================+
CREATE OR REPLACE FUNCTION get_user_id(u_name TEXT)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_user_id BIGINT;
BEGIN
    SELECT id INTO v_user_id
    FROM app_user
    WHERE name = u_name
    LIMIT 1;

    IF v_user_id IS NULL THEN
        RAISE EXCEPTION 'Role "%" does not exist', u_name;
    END IF;

    RETURN v_user_id;
END;
$$;

-- +===========================+
-- | GET PERMISSION_ID BY NAME |
-- +===========================+
CREATE OR REPLACE FUNCTION get_permission_id(p_name TEXT)
RETURNS BIGINT
LANGUAGE plpgsql
AS $$
DECLARE
    v_permission_id BIGINT;
BEGIN
    SELECT id INTO v_permission_id
    FROM entity_permission
    WHERE name = p_name
    LIMIT 1;

    IF v_permission_id IS NULL THEN
        RAISE EXCEPTION 'Role "%" does not exist', p_name;
    END IF;

    RETURN v_permission_id;
END;
$$;