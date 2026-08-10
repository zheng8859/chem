## Purpose

Enables adaptive practice sessions driven by barrier type and ZPD, persisting session metadata while storing individual answers as StudentAnswer records and tracking variant question lineage.

## ADDED Requirements

### Requirement: Practice session tracking

The system SHALL create a PracticeSession record when a student begins an adaptive practice session, tracking the targeted barrier type, knowledge points, and outcomes.

#### Scenario: Practice session for concept barrier
- **WHEN** a student whose dominant barrier is concept starts an adaptive practice on redox reactions
- **THEN** the system SHALL create a PracticeSession with barrier_type=concept, knowledge_point_tags=["氧化还原反应"], status=in_progress

#### Scenario: Session completion
- **WHEN** the student answers all served questions
- **THEN** the PracticeSession SHALL transition to completed with questions_served and questions_correct populated

#### Scenario: Session abandonment
- **WHEN** a student exits practice without completing all questions
- **THEN** the PracticeSession SHALL transition to abandoned, preserving partial results

### Requirement: ZPD-based question selection

The system SHALL select practice questions within the student's Zone of Proximal Development, avoiding questions already mastered (mastery_threshold consecutive correct) or far beyond current level.

#### Scenario: Mastered knowledge point skipped
- **WHEN** a student has answered oxidation-reduction questions correctly 3 times consecutively (meeting mastery_threshold)
- **THEN** the practice engine SHALL NOT serve additional oxidation-reduction questions in the current session

#### Scenario: Too-difficult questions excluded
- **WHEN** selecting practice questions for a student whose current level maps to medium difficulty
- **THEN** the system SHALL NOT serve competition-level questions

### Requirement: Variant question generation and tracking

The system SHALL store LLM-generated variant questions in the Question table with a reference to the blueprint question and the dimensions that were varied.

#### Scenario: Variant created from blueprint
- **WHEN** the LLM generates a variant of question #42 by changing the substance from HCl to H₂SO₄
- **THEN** the system SHALL create a new Question with variant_of_question_id=42, variant_dimensions={"substance": true, "value": false, "stem": false, "options": false, "difficulty": false}, and source=ai_generated

#### Scenario: Variant dimensions guide audit
- **WHEN** an audit engine reviews a variant question
- **THEN** it SHALL focus on the dimensions flagged true in variant_dimensions, skipping unchanged dimensions
