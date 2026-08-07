## Purpose

Computes each student's Zone of Proximal Development (ZPD) difficulty level from recent answer history, extracts weak knowledge points, and identifies the dominant barrier type — producing the parameters needed to assign personalized practice questions.

## ADDED Requirements

### Requirement: ZPD difficulty calculation from 30-question sliding window

The system SHALL calculate a student's ZPD difficulty level by querying their 30 most recent StudentAnswer records (ordered by created_at descending), computing the accuracy ratio, and mapping it to a 3-tier difficulty output.

#### Scenario: Below 40% accuracy returns easy
- **WHEN** a student's accuracy across the most recent 30 answers is less than 40%
- **THEN** the system SHALL return "easy" as the ZPD difficulty level

#### Scenario: Between 40% and 70% accuracy (inclusive) returns medium
- **WHEN** a student's accuracy is exactly 40%
- **THEN** the system SHALL return "medium"

#### Scenario: Between 40% and 70% accuracy (inclusive) returns medium
- **WHEN** a student's accuracy is exactly 70%
- **THEN** the system SHALL return "medium"

#### Scenario: Above 70% accuracy returns hard
- **WHEN** a student's accuracy is greater than 70%
- **THEN** the system SHALL return "hard"

#### Scenario: No answer history (cold start) returns medium
- **WHEN** a student has fewer than 5 StudentAnswer records (including zero)
- **THEN** the system SHALL return "medium" as the default ZPD difficulty level

#### Scenario: Competition difficulty is never auto-assigned
- **WHEN** the ZPD calculation produces any output
- **THEN** the system SHALL NOT return "competition" — this level is reserved for manual teacher assignment

### Requirement: Weak knowledge point extraction

The system SHALL identify the most frequent knowledge points from ALL incorrect StudentAnswer records (no time window limit), grouped by knowledge point tag, and return the top N by error count.

#### Scenario: Top 3 weak knowledge points returned
- **WHEN** a student has incorrect answers across 5 distinct knowledge points with error counts [8, 6, 4, 2, 1]
- **THEN** the system SHALL return the top 3 knowledge point names by descending error count

#### Scenario: Fewer than N weak points available
- **WHEN** a student has incorrect answers across only 2 distinct knowledge points
- **THEN** the system SHALL return all available knowledge points (fewer than the default N=3)

#### Scenario: No wrong answer history
- **WHEN** a student has zero incorrect StudentAnswer records
- **THEN** the system SHALL return an empty list

#### Scenario: Questions with multiple knowledge points
- **WHEN** a single incorrect Question is tagged with ["氧化还原反应", "电子转移"]
- **THEN** the system SHALL increment the error count for BOTH knowledge points independently

### Requirement: Dominant barrier type identification

The system SHALL extract the dominant barrier type from the Student's barrier_type JSON field, returning the key with the highest score.

#### Scenario: Dominant barrier from weighted scores
- **WHEN** Student.barrier_type is {"concept": 0.7, "reading": 0.15, "expression": 0.15}
- **THEN** the system SHALL return "concept" as the dominant barrier type

#### Scenario: Missing barrier_type defaults to concept
- **WHEN** Student.barrier_type is NULL or empty
- **THEN** the system SHALL return "concept" as the default barrier type

#### Scenario: Malformed barrier_type data
- **WHEN** Student.barrier_type is not a valid JSON object or has no valid barrier type keys
- **THEN** the system SHALL return "concept" as the default barrier type

### Requirement: Adaptive strategy matrix mapping

The system SHALL apply barrier-type-specific strategies to adjust difficulty, knowledge point selection, and question type distribution when assembling practice parameters.

#### Scenario: Concept barrier reduces difficulty
- **WHEN** the dominant barrier is "concept"
- **THEN** the system SHALL lower the ZPD-calculated difficulty by one tier (hard→medium, medium→easy, easy stays easy), prioritize foundational knowledge points, and increase the proportion of choice and fill-blank question types

#### Scenario: Reading barrier keeps difficulty and adds traps
- **WHEN** the dominant barrier is "reading"
- **THEN** the system SHALL keep the ZPD-calculated difficulty unchanged, mix knowledge points across chapters, and increase the proportion of inference and trap-option choice questions

#### Scenario: Expression barrier keeps difficulty and adds writing
- **WHEN** the dominant barrier is "expression"
- **THEN** the system SHALL keep the ZPD-calculated difficulty unchanged, prioritize knowledge points requiring equation writing, and increase the proportion of calculation and experiment question types
