USE recruitment_management_system;

DROP ROLE IF EXISTS 'hr_staff';
DROP ROLE IF EXISTS 'interviewer';
DROP ROLE IF EXISTS 'admin_user';

CREATE ROLE 'hr_staff';
CREATE ROLE 'interviewer';
CREATE ROLE 'admin_user';

GRANT SELECT ON recruitment_management_system.Employers TO 'hr_staff';
GRANT SELECT ON recruitment_management_system.Candidates TO 'hr_staff';
GRANT SELECT, INSERT, UPDATE ON recruitment_management_system.JobPositions TO 'hr_staff';
GRANT SELECT, INSERT, UPDATE ON recruitment_management_system.Applications TO 'hr_staff';
GRANT SELECT, INSERT, UPDATE ON recruitment_management_system.Interviews TO 'hr_staff';

GRANT SELECT ON recruitment_management_system.vw_open_job_positions TO 'hr_staff';
GRANT SELECT ON recruitment_management_system.vw_candidate_application_tracker TO 'hr_staff';
GRANT SELECT ON recruitment_management_system.vw_shortlisted_candidates TO 'hr_staff';
GRANT SELECT ON recruitment_management_system.vw_job_application_summary TO 'hr_staff';
GRANT SELECT ON recruitment_management_system.vw_interview_results TO 'hr_staff';
GRANT SELECT ON recruitment_management_system.vw_employer_dashboard_metrics TO 'hr_staff';

GRANT SELECT ON recruitment_management_system.Employers TO 'interviewer';
GRANT SELECT ON recruitment_management_system.Candidates TO 'interviewer';
GRANT SELECT ON recruitment_management_system.JobPositions TO 'interviewer';
GRANT SELECT ON recruitment_management_system.Applications TO 'interviewer';
GRANT SELECT, UPDATE ON recruitment_management_system.Interviews TO 'interviewer';

GRANT SELECT ON recruitment_management_system.vw_open_job_positions TO 'interviewer';
GRANT SELECT ON recruitment_management_system.vw_candidate_application_tracker TO 'interviewer';
GRANT SELECT ON recruitment_management_system.vw_interview_results TO 'interviewer';
GRANT SELECT ON recruitment_management_system.vw_job_application_summary TO 'interviewer';

GRANT ALL PRIVILEGES ON recruitment_management_system.* TO 'admin_user';

GRANT EXECUTE ON PROCEDURE recruitment_management_system.sp_create_job_position TO 'hr_staff';
GRANT EXECUTE ON PROCEDURE recruitment_management_system.sp_update_job_status TO 'hr_staff';
GRANT EXECUTE ON PROCEDURE recruitment_management_system.sp_submit_application TO 'hr_staff';
GRANT EXECUTE ON PROCEDURE recruitment_management_system.sp_schedule_interview TO 'hr_staff';
GRANT EXECUTE ON PROCEDURE recruitment_management_system.sp_record_interview_result TO 'hr_staff';

GRANT EXECUTE ON PROCEDURE recruitment_management_system.sp_schedule_interview TO 'interviewer';
GRANT EXECUTE ON PROCEDURE recruitment_management_system.sp_record_interview_result TO 'interviewer';

GRANT EXECUTE ON FUNCTION recruitment_management_system.fn_application_count_by_position TO 'hr_staff';
GRANT EXECUTE ON FUNCTION recruitment_management_system.fn_candidate_application_count TO 'hr_staff';
GRANT EXECUTE ON FUNCTION recruitment_management_system.fn_employer_pass_rate TO 'hr_staff';
GRANT EXECUTE ON FUNCTION recruitment_management_system.fn_average_interview_score TO 'hr_staff';

GRANT EXECUTE ON FUNCTION recruitment_management_system.fn_application_count_by_position TO 'interviewer';
GRANT EXECUTE ON FUNCTION recruitment_management_system.fn_candidate_application_count TO 'interviewer';
GRANT EXECUTE ON FUNCTION recruitment_management_system.fn_employer_pass_rate TO 'interviewer';
GRANT EXECUTE ON FUNCTION recruitment_management_system.fn_average_interview_score TO 'interviewer';

GRANT EXECUTE ON PROCEDURE recruitment_management_system.sp_create_job_position TO 'admin_user';
GRANT EXECUTE ON PROCEDURE recruitment_management_system.sp_update_job_status TO 'admin_user';
GRANT EXECUTE ON PROCEDURE recruitment_management_system.sp_submit_application TO 'admin_user';
GRANT EXECUTE ON PROCEDURE recruitment_management_system.sp_schedule_interview TO 'admin_user';
GRANT EXECUTE ON PROCEDURE recruitment_management_system.sp_record_interview_result TO 'admin_user';

GRANT EXECUTE ON FUNCTION recruitment_management_system.fn_application_count_by_position TO 'admin_user';
GRANT EXECUTE ON FUNCTION recruitment_management_system.fn_candidate_application_count TO 'admin_user';
GRANT EXECUTE ON FUNCTION recruitment_management_system.fn_employer_pass_rate TO 'admin_user';
GRANT EXECUTE ON FUNCTION recruitment_management_system.fn_average_interview_score TO 'admin_user';

-- Owner-based isolation for employers and candidates still needs to be enforced
-- in backend query logic by filtering on AccountID, EmployerID, and CandidateID.
