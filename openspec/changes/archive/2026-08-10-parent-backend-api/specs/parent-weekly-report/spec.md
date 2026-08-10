## Purpose

Generates parent-friendly weekly learning reports using LLM, with strict prompt engineering to convert technical chemistry terminology into plain language, and caches reports in the database for deduplication within the same week.

## ADDED Requirements

### Requirement: Weekly report generation via LLM

The system SHALL generate a weekly learning report for a student by constructing an LLM prompt with the student's aggregated practice data, then storing the structured result.

#### Scenario: Successful report generation
- **WHEN** a weekly report is generated for a student with practice data this week
- **THEN** the system SHALL: (1) aggregate practice data for the current week (Mon-Sun), (2) construct a prompt following the parent-friendly language rules (no rankings, no negative terms, chemical terms converted to everyday language), (3) call LLM to generate the report as JSON with fields summary, detail, advice, and no_data=false, (4) return the report

#### Scenario: Report generation with no practice data
- **WHEN** a student has zero practice records in the current week
- **THEN** the system SHALL return a report with no_data=true and a single summary message "本周暂无练习记录", without calling LLM

#### Scenario: Report stored in database
- **WHEN** a report is generated
- **THEN** the system SHALL persist it as a WeeklyReport record with student_id, week_start, week_end, summary, detail, advice content, generated_at, and generated_by

### Requirement: Weekly report deduplication

The system SHALL return the cached report when a report for the same student and same week already exists.

#### Scenario: Duplicate request returns cached report
- **WHEN** a report is requested twice for the same student within the same calendar week
- **THEN** the system SHALL return the existing WeeklyReport without calling LLM again

#### Scenario: New week generates new report
- **WHEN** a report is requested for a new calendar week for the same student
- **THEN** the system SHALL generate a new report (the old one remains in the database as history)

### Requirement: Manual report generation trigger

The system SHALL allow a parent to manually request report generation for a bound child.

#### Scenario: Manual trigger
- **WHEN** a parent sends POST /api/v1/parent/child/{student_id}/weekly/generate
- **THEN** the system SHALL generate or return the cached weekly report for that student

#### Scenario: Cron auto-trigger
- **WHEN** the weekly Cron job fires (Monday 08:00 Asia/Shanghai)
- **THEN** the system SHALL generate weekly reports for all students who have active parent bindings and had practice activity in the past week

### Requirement: Parent-friendly language conversion

The system SHALL construct LLM prompts that require: (1) no rankings or comparisons, (2) no negative terms like "差" or "落后", (3) chemical terminology converted to everyday language per a conversion table, (4) at least one positive observation before any suggestions, (5) 1-2 specific, actionable family support suggestions.

#### Scenario: Prompt enforces language rules
- **WHEN** the system prompt is constructed for weekly report generation
- **THEN** it SHALL include the terminology conversion table (e.g., "氧化还原反应" → "物质与氧气反应/电子的转移") and the rule "先肯定进步，再给出建议"

### Requirement: Report retrieval endpoint

The system SHALL allow parents to retrieve the current week's report and historical reports for a bound child.

#### Scenario: Get current week report
- **WHEN** a parent requests GET /api/v1/parent/child/{student_id}/weekly
- **THEN** the system SHALL return the WeeklyReport for the current calendar week, or 404 if none exists

#### Scenario: Get historical reports
- **WHEN** a parent requests GET /api/v1/parent/child/{student_id}/weekly?history=true&limit=10
- **THEN** the system SHALL return the most recent weekly reports for that child, ordered by week_start descending
