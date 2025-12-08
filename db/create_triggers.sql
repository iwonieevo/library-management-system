-- +==========================+
-- | MAX RESERVATIONS TRIGGER |
-- +==========================+
CREATE OR REPLACE FUNCTION check_max_reservations() RETURNS trigger AS $$
DECLARE
    active_count INT;
BEGIN
    SELECT COUNT(*) INTO active_count
    FROM Reservation
    WHERE reader_id = NEW.reader_id AND to_datetime >= CURRENT_TIMESTAMP;

    IF active_count >= 5 THEN
        RAISE EXCEPTION 'Reader cannot have more than 5 active reservations';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_max_reservations
BEFORE INSERT OR UPDATE ON Reservation
FOR EACH ROW EXECUTE FUNCTION check_max_reservations();

-- +====================+
-- | MAX ISSUES TRIGGER |
-- +====================+
CREATE OR REPLACE FUNCTION check_max_issues() RETURNS trigger AS $$
DECLARE
    active_count INT;
BEGIN
    SELECT COUNT(*) INTO active_count
    FROM Issue
    WHERE reader_id = NEW.reader_id AND return_datetime IS NULL;

    IF active_count >= 5 THEN
        RAISE EXCEPTION 'Reader cannot have more than 5 active issues';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_max_issues
BEFORE INSERT OR UPDATE ON Issue
FOR EACH ROW EXECUTE FUNCTION check_max_issues();

-- +=================================+
-- | NO OVERLAP RESERVATIONS TRIGGER |
-- +=================================+
CREATE OR REPLACE FUNCTION check_reservation_conflicts()
RETURNS trigger AS $$
BEGIN
    -- Overlapping reservation:
    IF EXISTS (
        SELECT 1
        FROM Reservation r
        WHERE r.book_copy_id = NEW.book_copy_id
          AND r.id <> NEW.id
          AND ((r.from_datetime, r.to_datetime) 
                OVERLAPS (NEW.from_datetime, NEW.to_datetime))
    ) THEN
        RAISE EXCEPTION 'Current reservation period overlaps with an existing reservation for this book copy.';
    END IF;

    -- Overlapping issue:
    IF EXISTS (
        SELECT 1
        FROM Issue i
        WHERE i.book_copy_id = NEW.book_copy_id
          AND ((i.issue_datetime, COALESCE(i.return_datetime, 'infinity'::timestamp)) 
                OVERLAPS (NEW.from_datetime, NEW.to_datetime))
    ) THEN
        RAISE EXCEPTION 'Current reservation period overlaps with an existing issue for this book copy.';
    END IF;  

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_reservation_conflicts
BEFORE INSERT OR UPDATE ON Reservation
FOR EACH ROW EXECUTE FUNCTION check_reservation_conflicts();

-- +===========================+
-- | NO OVERLAP ISSUES TRIGGER |
-- +===========================+
CREATE OR REPLACE FUNCTION check_issue_conflicts()
RETURNS trigger AS $$
BEGIN
    -- Overlapping reservation:
    IF EXISTS (
        SELECT 1
        FROM Reservation r
        WHERE r.book_copy_id = NEW.book_copy_id
          AND ((r.from_datetime, r.to_datetime) 
                OVERLAPS (NEW.issue_datetime, COALESCE(NEW.return_datetime, 'infinity'::timestamp)))
    ) THEN
        RAISE EXCEPTION 'Current issue period overlaps with an existing reservation for this book copy.';
    END IF;

    -- Overlapping issue:
    IF EXISTS (
        SELECT 1
        FROM Issue i
        WHERE i.book_copy_id = NEW.book_copy_id
          AND i.id <> NEW.id
          AND ((i.issue_datetime, COALESCE(i.return_datetime, 'infinity'::timestamp)) 
                OVERLAPS (NEW.issue_datetime, COALESCE(NEW.return_datetime, 'infinity'::timestamp)))
    ) THEN
        RAISE EXCEPTION 'Current issue period overlaps with an existing issue for this book copy.';
    END IF;  

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_issue_conflicts
BEFORE INSERT OR UPDATE ON Issue
FOR EACH ROW EXECUTE FUNCTION check_issue_conflicts();
