USE recruitment_management_system;

DROP TRIGGER IF EXISTS trg_interviews_after_insert_status;
DROP TRIGGER IF EXISTS trg_interviews_after_update_status;

DELIMITER $$

CREATE TRIGGER trg_interviews_after_insert_status
AFTER INSERT ON Interviews
FOR EACH ROW
BEGIN
    UPDATE Applications
    SET Status = CASE
        WHEN NEW.Result = 'Pass' THEN 'Accepted'
        WHEN NEW.Result = 'Fail' THEN 'Rejected'
        ELSE 'Interviewing'
    END
    WHERE ApplicationID = NEW.ApplicationID;
END $$


CREATE TRIGGER trg_interviews_after_update_status
AFTER UPDATE ON Interviews
FOR EACH ROW
BEGIN
    UPDATE Applications
    SET Status = CASE
        WHEN NEW.Result = 'Pass' THEN 'Accepted'
        WHEN NEW.Result = 'Fail' THEN 'Rejected'
        ELSE 'Interviewing'
    END
    WHERE ApplicationID = NEW.ApplicationID;
END $$

DELIMITER ;
