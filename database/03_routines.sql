USE recruitment_management_system;

DROP FUNCTION IF EXISTS fn_application_count_by_position;
DROP FUNCTION IF EXISTS fn_candidate_application_count;
DROP FUNCTION IF EXISTS fn_employer_pass_rate;
DROP FUNCTION IF EXISTS fn_average_interview_score;

DROP PROCEDURE IF EXISTS sp_create_job_position;
DROP PROCEDURE IF EXISTS sp_update_job_status;
DROP PROCEDURE IF EXISTS sp_submit_application;
DROP PROCEDURE IF EXISTS sp_schedule_interview;
DROP PROCEDURE IF EXISTS sp_record_interview_result;

DELIMITER $$

CREATE FUNCTION fn_application_count_by_position(
    p_position_id INT
)
RETURNS INT
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_count INT DEFAULT 0;

    SELECT COUNT(*)
    INTO v_count
    FROM Applications
    WHERE PositionID = p_position_id;

    RETURN COALESCE(v_count, 0);
END $$


CREATE FUNCTION fn_candidate_application_count(
    p_candidate_id INT
)
RETURNS INT
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_count INT DEFAULT 0;

    SELECT COUNT(*)
    INTO v_count
    FROM Applications
    WHERE CandidateID = p_candidate_id;

    RETURN COALESCE(v_count, 0);
END $$


CREATE FUNCTION fn_employer_pass_rate(
    p_employer_id INT
)
RETURNS DECIMAL(5,2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_total INT DEFAULT 0;
    DECLARE v_passed INT DEFAULT 0;

    SELECT COUNT(*)
    INTO v_total
    FROM Interviews AS i
    INNER JOIN Applications AS a
        ON a.ApplicationID = i.ApplicationID
    INNER JOIN JobPositions AS jp
        ON jp.PositionID = a.PositionID
    WHERE jp.EmployerID = p_employer_id;

    IF v_total = 0 THEN
        RETURN 0.00;
    END IF;

    SELECT COUNT(*)
    INTO v_passed
    FROM Interviews AS i
    INNER JOIN Applications AS a
        ON a.ApplicationID = i.ApplicationID
    INNER JOIN JobPositions AS jp
        ON jp.PositionID = a.PositionID
    WHERE jp.EmployerID = p_employer_id
      AND i.Result = 'Pass';

    RETURN ROUND((v_passed * 100.0) / v_total, 2);
END $$


CREATE FUNCTION fn_average_interview_score(
    p_employer_id INT
)
RETURNS DECIMAL(5,2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_average_score DECIMAL(5,2) DEFAULT 0.00;

    SELECT ROUND(COALESCE(AVG(i.Score), 0), 2)
    INTO v_average_score
    FROM Interviews AS i
    INNER JOIN Applications AS a
        ON a.ApplicationID = i.ApplicationID
    INNER JOIN JobPositions AS jp
        ON jp.PositionID = a.PositionID
    WHERE jp.EmployerID = p_employer_id
      AND i.Score IS NOT NULL;

    RETURN COALESCE(v_average_score, 0.00);
END $$


CREATE PROCEDURE sp_create_job_position(
    IN p_employer_id INT,
    IN p_title VARCHAR(120),
    IN p_job_description TEXT,
    IN p_requirements TEXT,
    IN p_status VARCHAR(10)
)
MODIFIES SQL DATA
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM Employers
        WHERE EmployerID = p_employer_id
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Employer does not exist.';
    END IF;

    IF p_title IS NULL OR TRIM(p_title) = '' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Job title is required.';
    END IF;

    IF p_job_description IS NULL OR TRIM(p_job_description) = '' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Job description is required.';
    END IF;

    IF p_status NOT IN ('Open', 'Closed') THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Job status must be Open or Closed.';
    END IF;

    INSERT INTO JobPositions (
        EmployerID,
        Title,
        JobDescription,
        Requirements,
        Status
    )
    VALUES (
        p_employer_id,
        TRIM(p_title),
        TRIM(p_job_description),
        NULLIF(TRIM(p_requirements), ''),
        p_status
    );

    SELECT
        LAST_INSERT_ID() AS PositionID,
        'Job position created successfully.' AS Message;
END $$


CREATE PROCEDURE sp_update_job_status(
    IN p_position_id INT,
    IN p_status VARCHAR(10)
)
MODIFIES SQL DATA
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM JobPositions
        WHERE PositionID = p_position_id
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Job position does not exist.';
    END IF;

    IF p_status NOT IN ('Open', 'Closed') THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Job status must be Open or Closed.';
    END IF;

    UPDATE JobPositions
    SET Status = p_status
    WHERE PositionID = p_position_id;

    SELECT
        p_position_id AS PositionID,
        p_status AS UpdatedStatus,
        'Job status updated successfully.' AS Message;
END $$


CREATE PROCEDURE sp_submit_application(
    IN p_candidate_id INT,
    IN p_position_id INT
)
MODIFIES SQL DATA
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM Candidates
        WHERE CandidateID = p_candidate_id
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Candidate does not exist.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM JobPositions
        WHERE PositionID = p_position_id
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Job position does not exist.';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM JobPositions
        WHERE PositionID = p_position_id
          AND Status = 'Open'
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Applications can only be submitted to open positions.';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM Applications
        WHERE CandidateID = p_candidate_id
          AND PositionID = p_position_id
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Candidate has already applied for this job position.';
    END IF;

    INSERT INTO Applications (
        CandidateID,
        PositionID,
        ApplicationDate,
        Status
    )
    VALUES (
        p_candidate_id,
        p_position_id,
        NOW(),
        'Pending'
    );

    SELECT
        LAST_INSERT_ID() AS ApplicationID,
        'Application submitted successfully.' AS Message;
END $$


CREATE PROCEDURE sp_schedule_interview(
    IN p_application_id INT,
    IN p_interview_date DATETIME,
    IN p_location_or_link VARCHAR(255),
    IN p_notes TEXT
)
MODIFIES SQL DATA
BEGIN
    DECLARE v_application_date DATETIME;

    IF NOT EXISTS (
        SELECT 1
        FROM Applications
        WHERE ApplicationID = p_application_id
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Application does not exist.';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM Interviews
        WHERE ApplicationID = p_application_id
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Interview already exists for this application.';
    END IF;

    IF p_interview_date IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Interview date is required.';
    END IF;

    SELECT ApplicationDate
    INTO v_application_date
    FROM Applications
    WHERE ApplicationID = p_application_id;

    IF p_interview_date <= v_application_date THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Interview date must be after the application date.';
    END IF;

    INSERT INTO Interviews (
        ApplicationID,
        InterviewDate,
        LocationOrLink,
        Result,
        Score,
        Notes
    )
    VALUES (
        p_application_id,
        p_interview_date,
        NULLIF(TRIM(p_location_or_link), ''),
        'Pending',
        NULL,
        NULLIF(TRIM(p_notes), '')
    );

    SELECT
        LAST_INSERT_ID() AS InterviewID,
        'Interview scheduled successfully.' AS Message;
END $$


CREATE PROCEDURE sp_record_interview_result(
    IN p_application_id INT,
    IN p_result VARCHAR(10),
    IN p_score DECIMAL(5,2),
    IN p_notes TEXT
)
MODIFIES SQL DATA
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM Interviews
        WHERE ApplicationID = p_application_id
    ) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Interview does not exist for this application.';
    END IF;

    IF p_result NOT IN ('Pending', 'Pass', 'Fail') THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Interview result must be Pending, Pass, or Fail.';
    END IF;

    IF p_result = 'Pending' AND p_score IS NOT NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Pending interview results must not have a score.';
    END IF;

    IF p_result IN ('Pass', 'Fail')
       AND (p_score IS NULL OR p_score < 0 OR p_score > 10) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Final interview results require a score between 0 and 10.';
    END IF;

    UPDATE Interviews
    SET
        Result = p_result,
        Score = CASE
            WHEN p_result = 'Pending' THEN NULL
            ELSE p_score
        END,
        Notes = COALESCE(NULLIF(TRIM(p_notes), ''), Notes)
    WHERE ApplicationID = p_application_id;

    SELECT
        p_application_id AS ApplicationID,
        p_result AS InterviewResult,
        'Interview result recorded successfully.' AS Message;
END $$

DELIMITER ;
