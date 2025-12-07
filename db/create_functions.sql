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
    FROM Book
    WHERE title = p_title;

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
    FROM Publisher
    WHERE name = p_name;

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
    FROM Reader
    WHERE card_no = p_card_no;

    IF v_reader_id IS NULL THEN
        RAISE EXCEPTION 'Reader with card number "%" does not exist', p_card_no;
    END IF;

    RETURN v_reader_id;
END;
$$;