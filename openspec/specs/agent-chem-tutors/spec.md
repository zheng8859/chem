## Purpose

Registers two additional Socratic tutoring tools (periodic_law_tutor for periodic law reasoning and organic_tutor for organic inference) in the Student persona's available tool set, completing the 8-tool chemistry tutoring suite defined in the Agent design.

## ADDED Requirements

### Requirement: Periodic law tutor tool

The system SHALL register a periodic_law_tutor Agent tool using the existing tutoring factory, implementing a three-mode Socratic interaction (position → structure → property inference) for the Student persona.

#### Scenario: Student enters periodic law tutoring mode
- **WHEN** a student sends a message triggering the periodic_law_tutor tool without providing an equation or problem
- **THEN** the tool SHALL return a prompt asking the student to provide a periodic law problem or element description

#### Scenario: Student provides a periodic law problem
- **WHEN** a student sends a problem statement (e.g., "推断元素X在周期表中的位置") to the periodic_law_tutor
- **THEN** the tool SHALL return step=1 guidance prompting the student to identify the element's atomic structure

#### Scenario: Student responds to periodic law step
- **WHEN** a student provides their reasoning for Step 1
- **THEN** the tool SHALL return feedback on the student's answer plus step=2 guidance for property inference

### Requirement: Organic tutor tool

The system SHALL register an organic_tutor Agent tool using the existing tutoring factory, implementing a three-mode Socratic interaction (retrosynthetic analysis and functional group transformation) for the Student persona.

#### Scenario: Student enters organic tutoring mode
- **WHEN** a student sends a message triggering the organic_tutor tool without providing a problem
- **THEN** the tool SHALL return a prompt asking the student to provide an organic chemistry inference problem

#### Scenario: Student provides an organic problem
- **WHEN** a student sends an organic synthesis or inference problem to the organic_tutor
- **THEN** the tool SHALL return step=1 guidance prompting the student to analyze the functional groups involved

#### Scenario: Student responds to organic step
- **WHEN** a student provides their reasoning for Step 1
- **THEN** the tool SHALL return feedback on the student's answer plus step=2 guidance for the transformation pathway

### Requirement: Tool registration in Student persona

The system SHALL register periodic_law_tutor and organic_tutor in the tool metadata registry with persona=["student"] and call_limit=5, and SHALL add them to the Student persona's available_skills YAML configuration.

#### Scenario: Tools in Student persona tool set
- **WHEN** the Agent factory builds the Student persona's tool set
- **THEN** the resulting tool set SHALL include periodic_law_tutor and organic_tutor in addition to the existing 6 tutoring tools

#### Scenario: Tools not available to non-student personas
- **WHEN** the Agent factory builds the tool set for teacher, tutor, or parent personas
- **THEN** periodic_law_tutor and organic_tutor SHALL NOT be included
