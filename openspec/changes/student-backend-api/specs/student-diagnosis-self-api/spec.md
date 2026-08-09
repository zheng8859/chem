## Purpose

Exposes a student self-view diagnosis endpoint so students can see their own barrier profile, dominant barrier type, and top weak knowledge points without requiring teacher mediation.

## ADDED Requirements

### Requirement: Student self-view diagnosis endpoint

The system SHALL provide an endpoint for a student to retrieve their own barrier profile, including per-barrier-type rates and trend, dominant barrier type, and top 5 weakest knowledge points.

#### Scenario: Student views own diagnosis
- **WHEN** a student requests GET /api/v1/diagnosis/student/{student_id}
- **THEN** the system SHALL return barrier_profile (concept_barrier, reading_barrier, expression_barrier each with rate and trend), dominant_type (string), weak_kps (top 5 knowledge points ordered by error rate descending, each with name and error_rate), and last_diagnosis_date (ISO date or null)

#### Scenario: Student has no diagnosis history
- **WHEN** a student has never been diagnosed
- **THEN** the system SHALL return barrier_profile with all rates=null, dominant_type=null, weak_kps=[], and last_diagnosis_date=null

#### Scenario: Barrier trend calculation
- **WHEN** a student has multiple diagnosis records over time
- **THEN** the trend for each barrier type SHALL be one of "up" (improving, rate decreasing), "down" (worsening, rate increasing), or "stable" (rate change within ±5%), computed from the two most recent diagnosis records

### Requirement: Weak knowledge point aggregation

The system SHALL aggregate weak knowledge points from all diagnosed student answers, using both ExamRecord and PracticeSession data sources.

#### Scenario: Weak KPs from multiple sources
- **WHEN** a student has diagnosed answers from both exams and practice sessions
- **THEN** the system SHALL merge and rank all knowledge points by error rate, returning the top 5

#### Scenario: Insufficient data for weak KPs
- **WHEN** a student has fewer than 5 diagnosed knowledge points
- **THEN** the system SHALL return all available knowledge points, even if fewer than 5

### Requirement: Student self-data isolation for diagnosis

The system SHALL enforce that students can only access their own diagnosis data.

#### Scenario: Student accesses own diagnosis
- **WHEN** student with account_id=101 requests GET /api/v1/diagnosis/student/101
- **THEN** the system SHALL return the student's diagnosis data

#### Scenario: Unauthorized access attempt
- **WHEN** a non-student user or mismatched student attempts to access diagnosis data
- **THEN** the system SHALL return 403 FORBIDDEN
