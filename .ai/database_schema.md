# Database Schema

## Database Name
`recruitment_management_system`

## Core Architecture & Constraints
The database is strictly normalized to 3NF/BCNF. Authentication is completely separated from user profiles to ensure strict data isolation and security.

## Main Tables

### Accounts
Purpose: Manages secure login credentials and role-based access for the entire system.

Columns:
- `AccountID` INT, primary key, auto increment
- `Email` VARCHAR(150), not null, unique
- `PasswordHash` VARCHAR(255), not null
- `Role` ENUM('Employer', 'Candidate'), not null
- `CreatedAt` TIMESTAMP, not null, default current timestamp

### Employers
Purpose: Stores organization profiles linked to employer accounts.

Columns:
- `EmployerID` INT, primary key, auto increment
- `AccountID` INT, foreign key to `Accounts.AccountID`, unique
- `CompanyName` VARCHAR(120), not null
- `ContactNumber` VARCHAR(20), nullable
- `Address` TEXT, nullable
- `Description` TEXT, nullable

Constraints:
- Foreign key `AccountID` references `Accounts(AccountID)`
  - `ON UPDATE CASCADE`
  - `ON DELETE CASCADE`
- Unique constraint on `AccountID` enforces a 1:1 relationship.

### Candidates
Purpose: Stores personal profiles for job applicants linked to candidate accounts.

Columns:
- `CandidateID` INT, primary key, auto increment
- `AccountID` INT, foreign key to `Accounts.AccountID`, unique
- `FullName` VARCHAR(120), not null
- `DateOfBirth` DATE, nullable
- `PhoneNumber` VARCHAR(20), nullable
- `ResumeURL` VARCHAR(255), nullable

Constraints:
- Foreign key `AccountID` references `Accounts(AccountID)`
  - `ON UPDATE CASCADE`
  - `ON DELETE CASCADE`
- Unique constraint on `AccountID` enforces a 1:1 relationship.

### JobPositions
Purpose: Stores job postings published by specific employers.

Columns:
- `PositionID` INT, primary key, auto increment
- `EmployerID` INT, foreign key to `Employers.EmployerID`
- `Title` VARCHAR(120), not null
- `JobDescription` TEXT, not null
- `Requirements` TEXT, nullable
- `Status` ENUM('Open', 'Closed'), not null, default 'Open'
- `PostedDate` DATETIME, not null, default current timestamp

Constraints:
- Foreign key `EmployerID` references `Employers(EmployerID)`
  - `ON UPDATE CASCADE`
  - `ON DELETE RESTRICT`

### Applications
Purpose: Stores applications submitted by candidates to specific job positions.

Columns:
- `ApplicationID` INT, primary key, auto increment
- `CandidateID` INT, foreign key to `Candidates.CandidateID`
- `PositionID` INT, foreign key to `JobPositions.PositionID`
- `ApplicationDate` DATETIME, not null, default current timestamp
- `Status` ENUM('Pending', 'Reviewed', 'Interviewing', 'Rejected', 'Accepted'), not null, default 'Pending'

Constraints:
- Foreign key `CandidateID` references `Candidates(CandidateID)`
  - `ON UPDATE CASCADE`
  - `ON DELETE CASCADE`
- Foreign key `PositionID` references `JobPositions(PositionID)`
  - `ON UPDATE CASCADE`
  - `ON DELETE RESTRICT`
- Unique constraint on `(CandidateID, PositionID)` to prevent a candidate from applying to the same job twice.

### Interviews
Purpose: Stores scheduled interviews and their outcomes tied to specific applications.

Columns:
- `InterviewID` INT, primary key, auto increment
- `ApplicationID` INT, foreign key to `Applications.ApplicationID`, unique
- `InterviewDate` DATETIME, not null
- `LocationOrLink` VARCHAR(255), nullable
- `Result` ENUM('Pending', 'Pass', 'Fail'), not null, default 'Pending'
- `Score` DECIMAL(5,2), nullable, expected range `0` to `10`
- `Notes` TEXT, nullable

Constraints:
- Foreign key `ApplicationID` references `Applications(ApplicationID)`
  - `ON UPDATE CASCADE`
  - `ON DELETE CASCADE`
- Unique constraint on `ApplicationID` assumes one final interview result per application record.
- Check constraint: `Score IS NULL OR (Score >= 0 AND Score <= 10)`

## Relationships
- One `Account` has exactly one `Employer` OR one `Candidate` (1:1).
- One `Employer` can post many `JobPositions` (1:N).
- One `Candidate` can submit many `Applications` (1:N).
- One `JobPosition` can receive many `Applications` (1:N).
- One `Application` has one `Interview` (1:1 based on the unique constraint).

## Indexes
Recommended indexes for query optimization:
- `idx_jobpositions_status` on `JobPositions(Status)`
- `idx_applications_status` on `Applications(Status)`
- `idx_accounts_email` on `Accounts(Email)`
- `idx_interviews_date` on `Interviews(InterviewDate)`

## Security Roles
System defined access levels:
- `hr_staff`: Full read/write access to Employer workflows.
- `interviewer`: Read access to assigned applications and write access to Interview results.
- `admin_user`: System-wide access.
- Strict Row-Level Security / Application Logic must ensure `Employers` and `Candidates` only access data linked to their respective `AccountID`.

## Notes
- The application status lifecycle is a key business rule and must be strictly enforced.
- Triggers should be implemented to automatically update `Applications.Status` based on changes to `Interviews.Result`.
- Interview scoring is included so SQL functions and dashboard reports can calculate average interview performance.
