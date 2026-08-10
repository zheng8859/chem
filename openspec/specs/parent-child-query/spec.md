## Purpose

Enables parents to view their bound children's learning data: a study overview with key metrics, a learning characteristics analysis in plain language, and a weekly learning timeline.

## ADDED Requirements

### Requirement: Child study overview endpoint

The system SHALL provide an endpoint returning key learning metrics for a bound child: weekly practice count, accuracy rate, consecutive study days, and cumulative practice total.

#### Scenario: Full overview for active child
- **WHEN** a parent requests GET /api/v1/parent/child/{student_id}/report
- **THEN** the system SHALL verify the parent-child binding is active, then return: weekly_practice_count (int), accuracy_rate (float), streak_days (int), total_practice_count (int), weak_knowledge_points (list of strings with plain-language descriptions), and last_practice_time (datetime or null)

#### Scenario: Child has no practice data
- **WHEN** a parent requests overview for a child who has never practiced
- **THEN** the system SHALL return all fields with zero or null defaults and a message "该学生暂无练习记录"

#### Scenario: Unauthorized parent access
- **WHEN** a parent requests data for a student they are not bound to
- **THEN** the system SHALL return 403 with detail "未绑定该学生"

### Requirement: Child learning characteristics endpoint

The system SHALL return the child's barrier distribution and learning characteristics in parent-friendly language.

#### Scenario: Learning characteristics with data
- **WHEN** a parent requests GET /api/v1/parent/child/{student_id}/report
- **THEN** the response SHALL include a `characteristics` field describing the child's barrier distribution in plain language (e.g., "概念理解较扎实，在读题时偶尔会漏看条件"), NOT using technical terms like "审题障碍型占比15%"

#### Scenario: Learning characteristics without diagnosis data
- **WHEN** a child has no diagnosis records
- **THEN** the `characteristics` field SHALL contain a message indicating insufficient data for analysis

### Requirement: Child learning timeline endpoint

The system SHALL return a week-by-week timeline of the child's practice activity for the past 4 weeks.

#### Scenario: Active child timeline
- **WHEN** a parent requests GET /api/v1/parent/child/{student_id}/timeline
- **THEN** the system SHALL return an array of weekly summaries, each containing week_start (date), week_end (date), practice_count (int), accuracy (float), and topics_covered (list of strings with plain-language topic names)

#### Scenario: Child with no recent activity
- **WHEN** a child has no practice in the past 4 weeks
- **THEN** the system SHALL return an empty timeline array

### Requirement: Parent self-data isolation for child queries

The system SHALL enforce that parents can only access data of children they are actively bound to.

#### Scenario: Parent accesses bound child
- **WHEN** a parent requests data for a child with an active StudentParentBinding
- **THEN** the system SHALL return the child's data

#### Scenario: Cross-parent access denied
- **WHEN** a parent requests data for a child bound to a different parent
- **THEN** the system SHALL return 403 FORBIDDEN
