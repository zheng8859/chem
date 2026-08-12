## Purpose

Manages Agent conversation context to prevent token explosion in long-running dialogues through a three-layer trimming strategy, and injects student-specific profile data as System Messages for the Student persona.

## ADDED Requirements

### Requirement: Three-layer context trimming

The system SHALL trim conversation messages when the count exceeds 30: (Layer 1) unconditionally retain the most recent 6 messages; (Layer 2) additionally retain earlier messages containing at least one of 15 teaching-related keywords; (Layer 3) when 10 or more messages are discarded, invoke LLM summarization to compress discarded messages into ≤ 200 Chinese characters and prepend the summary to the retained messages. Trimming SHALL execute before each Agent invocation.

#### Scenario: No trimming when under threshold
- **WHEN** a conversation has 25 messages
- **THEN** the system SHALL pass all messages to the Agent unchanged

#### Scenario: Recent messages always retained
- **WHEN** a conversation has 40 messages and trimming is triggered
- **THEN** the most recent 6 messages SHALL be present in the output regardless of keyword matches

#### Scenario: Teaching keyword messages retained
- **WHEN** trimming is triggered and messages 7-34 contain the keywords "诊断", "障碍", or "考试"
- **THEN** those messages SHALL be retained in addition to the recent 6

#### Scenario: LLM summary generated for large discard
- **WHEN** 15 messages are discarded during trimming
- **THEN** the system SHALL invoke an LLM call to summarize them into ≤ 200 Chinese characters and prepend the summary to the output

#### Scenario: Summary failure handled gracefully
- **WHEN** the LLM summary call fails
- **THEN** the discarded messages SHALL be dropped silently and trimming SHALL proceed with only keyword-filtered + recent messages

#### Scenario: Output message order
- **WHEN** trimming completes
- **THEN** the output message order SHALL be: summary message (if any) → keyword-matched historical messages → 6 recent messages → current user input

### Requirement: Student context injection

The system SHALL, when persona="student", query the student's profile (name, class, barrier profile, weak knowledge points, active learning plan, practice statistics) and inject it as a System Message block before the Persona system prompt. The context SHALL be enclosed in HTML comment markers `<!-- STUDENT_CONTEXT_START -->` and `<!-- STUDENT_CONTEXT_END -->`.

#### Scenario: Full student context injected
- **WHEN** an Agent conversation starts for a student with barrier profile, learning plan, and practice history
- **THEN** the System Message SHALL include all fields: name, class, barrier_profile (concept/reading/expression), weak_kps (top 5), active_plan (title + progress), practice_stats (count + weighted accuracy)

#### Scenario: Student with no data
- **WHEN** a student has no diagnosis, no plan, and no practice history
- **THEN** the context block SHALL still be injected but SHALL indicate data unavailability with "暂无数据" for each section

#### Scenario: Non-student persona unaffected
- **WHEN** persona is teacher, tutor, or parent
- **THEN** the student context injection SHALL be skipped entirely

#### Scenario: Practice accuracy uses exponential decay weighting
- **WHEN** computing overall accuracy for student context
- **THEN** the system SHALL apply exponential decay with half-life of 1 week (ln(2)/604800 per second) to weight recent sessions more heavily
