## Purpose

Implements Ebbinghaus-based spaced repetition with a 6-level spiral review model (Level 0–5), automatic ReviewTask creation from wrong answers, upgrade/downgrade rules with consecutive-correct/error counters, overdue detection, and mastery marking.

## ADDED Requirements

### Requirement: Ebbinghaus 6-level spiral review model

The system SHALL manage ReviewTask records across 6 levels (0 through 5), where each level corresponds to an increasing review interval: Level 0 = immediate (same day), Level 1 = 1 day later, Level 2 = 3 days later, Level 3 = 7 days later, Level 4 = 14 days later, Level 5 = mastered (no further review).

#### Scenario: New ReviewTask starts at Level 0 with immediate availability
- **WHEN** a ReviewTask is created for a wrong answer
- **THEN** the system SHALL set level=0, status=pending, next_review_date=now(), consecutive_correct=0, consecutive_wrong=0

#### Scenario: Level 5 marks task as mastered
- **WHEN** a ReviewTask reaches level=5
- **THEN** the system SHALL set status=completed and next_review_date=NULL

#### Scenario: Interval is computed from current time, not last review date
- **WHEN** a student completes a review and the task level-up results in a 3-day interval
- **THEN** the system SHALL set next_review_date = now() + 3 days

### Requirement: Upgrade and downgrade by consecutive correctness

The system SHALL evaluate upgrade/downgrade after each review based on correctness and consecutive counters, applied in order: (1) judge correctness, (2) update counters, (3) evaluate level change.

#### Scenario: Upgrade after 2 consecutive correct answers
- **WHEN** a student answers correctly and consecutive_correct reaches 2 (after increment) AND level < 5
- **THEN** the system SHALL increment level by 1, reset consecutive_correct to 0, and set next_review_date to now() + interval for the new level

#### Scenario: Single correct answer without upgrade
- **WHEN** a student answers correctly and consecutive_correct becomes 1
- **THEN** the system SHALL keep level unchanged and consecutive_wrong SHALL be reset to 0

#### Scenario: Wrong answer at Level > 0 triggers downgrade
- **WHEN** a student answers incorrectly and level > 0
- **THEN** the system SHALL decrement level by 1, reset consecutive_wrong to 0, reset consecutive_correct to 0, and set next_review_date to now() + interval for the new level

#### Scenario: Wrong answer at Level 0 stays at Level 0
- **WHEN** a student answers incorrectly and level == 0
- **THEN** the system SHALL keep level unchanged, reset consecutive_correct to 0, and increment consecutive_wrong by 1

#### Scenario: Single correct followed by wrong does not downgrade
- **WHEN** consecutive_correct was 1 and the student answers incorrectly
- **THEN** the system SHALL reset consecutive_correct to 0, set consecutive_wrong to 1, and keep level unchanged (no downgrade — the single correct is not enough to trigger upgrade, and the single wrong after it could be carelessness)

### Requirement: Automatic sync from wrong answers with deduplication

The system SHALL automatically create ReviewTask records when a student answers a question incorrectly, deduplicating by (student_id, question_id).

#### Scenario: New wrong answer creates ReviewTask
- **WHEN** a student answers a question incorrectly and no ReviewTask exists for (student_id, question_id)
- **THEN** the system SHALL create a ReviewTask with level=0, status=pending, next_review_date=now()

#### Scenario: Duplicate wrong answer does not create second task
- **WHEN** a student answers a question incorrectly and a ReviewTask already exists for (student_id, question_id) with status=pending or overdue
- **THEN** the system SHALL NOT create a new ReviewTask

#### Scenario: Wrong answer after mastery pulls task back to Level 0
- **WHEN** a student answers a question incorrectly and a ReviewTask already exists with status=completed (level=5)
- **THEN** the system SHALL reset the ReviewTask to level=0, status=pending, next_review_date=now(), consecutive_correct=0, consecutive_wrong=0

### Requirement: Overdue detection

The system SHALL classify ReviewTask records whose next_review_date is in the past and status is not completed as overdue.

#### Scenario: Task becomes overdue
- **WHEN** a ReviewTask has next_review_date < now() and status=pending
- **THEN** the system SHALL treat the task as overdue and include it in due task queries

#### Scenario: Student can still complete overdue tasks
- **WHEN** a student completes a review on an overdue task
- **THEN** the system SHALL apply normal upgrade/downgrade rules and set the task back to status=pending with the appropriate next_review_date

### Requirement: Mastery marking

The system SHALL allow a student or system to mark a specific question as mastered, bypassing the normal review cycle.

#### Scenario: Mark as mastered with existing ReviewTask
- **WHEN** a student marks question Q as mastered and a ReviewTask exists for (student_id, Q)
- **THEN** the system SHALL set ReviewTask.level=5, status=completed, next_review_date=NULL

#### Scenario: Mark as mastered without existing ReviewTask
- **WHEN** a student marks question Q as mastered and no ReviewTask exists for (student_id, Q)
- **THEN** the system SHALL create a ReviewTask with level=5, status=completed, next_review_date=NULL

### Requirement: Review history recording

The system SHALL append a ReviewHistory record after every review completion, capturing the level at the time of review, the result, and the timestamp.

#### Scenario: Review history recorded on completion
- **WHEN** a student completes a review with result=true at level=2
- **THEN** the system SHALL create a ReviewHistory with review_task_id, level=2, result=true, review_date=now()
