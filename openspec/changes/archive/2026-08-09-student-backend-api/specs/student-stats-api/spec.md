## Purpose

Provides aggregated practice statistics for the student's "我的" (Profile) page, including total practices, weighted accuracy, streak days, wrong question count, and due review count.

## ADDED Requirements

### Requirement: Student practice statistics endpoint

The system SHALL provide an endpoint returning aggregated practice statistics for a student: total completed practices, weighted accuracy, consecutive streak days, wrong question inventory count, and due review count.

#### Scenario: Full statistics for active student
- **WHEN** a student requests GET /api/v1/student/{id}/stats
- **THEN** the system SHALL return total_practices (integer), overall_accuracy (float, exponentially weighted), streak_days (integer), total_wrong_questions (integer), and review_due_today (integer)

#### Scenario: Student with no practice history
- **WHEN** a student has no completed practice sessions
- **THEN** the system SHALL return all fields with zero or null defaults (total_practices=0, overall_accuracy=null, streak_days=0, total_wrong_questions=0, review_due_today=0)

#### Scenario: Streak calculation with gap
- **WHEN** a student has practice records on consecutive days followed by a gap day before resuming
- **THEN** streak_days SHALL be calculated from the most recent unbroken chain of days with at least one practice submission

### Requirement: Weighted accuracy calculation

The system SHALL calculate overall_accuracy using exponential decay weighting, with recent practices weighted higher than older ones, consistent with the teacher Panel API's class average formula.

#### Scenario: Multiple practice sessions weighted
- **WHEN** a student has 5 practice sessions with accuracies [0.6, 0.7, 0.8, 0.9, 1.0] ordered oldest to newest
- **THEN** overall_accuracy SHALL give more weight to the most recent session (1.0) than the oldest (0.6)

### Requirement: Student self-data isolation

The system SHALL enforce that students can only access their own statistics. The student_id in the URL path MUST match the authenticated user's JWT identity.

#### Scenario: Student accesses own stats
- **WHEN** student with account_id=101 requests GET /api/v1/student/101/stats
- **THEN** the system SHALL return the student's statistics

#### Scenario: Student attempts to access other student's stats
- **WHEN** student with account_id=101 requests GET /api/v1/student/102/stats
- **THEN** the system SHALL return 403 FORBIDDEN
