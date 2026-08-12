## ADDED Requirements

### Requirement: Chemical equilibrium tutor tool

The system SHALL register an equilibrium_tutor Agent tool using the tutoring factory, implementing Socratic interaction for chemical equilibrium problems (analyze equilibrium system → apply Le Chatelier's principle → three-line table calculation) for the Student persona. The tool SHALL support rendering a three-line equilibrium table (initial/change/equilibrium) in its tool_result.

#### Scenario: Student enters equilibrium tutoring mode
- **WHEN** a student triggers equilibrium_tutor without providing an equation
- **THEN** the tool SHALL prompt the student to provide a chemical equilibrium problem

#### Scenario: Student provides equilibrium problem
- **WHEN** a student provides an equilibrium equation and problem statement
- **THEN** the tool SHALL return step=1 guidance for analyzing the equilibrium system (identifying reactants, products, and conditions)

#### Scenario: Student responds and receives step 2 guidance
- **WHEN** a student provides their analysis for step 1
- **THEN** the tool SHALL return feedback + step=2 guidance for applying Le Chatelier's principle and performing three-line calculations

#### Scenario: Tool result includes equilibrium table data
- **WHEN** the tool returns with table_data containing initial/change/equilibrium rows
- **THEN** the frontend SHALL render a three-line HTML table in the tool result card

### Requirement: Ionic equation tutor tool

The system SHALL register an ionic_equation_tutor Agent tool using the tutoring factory, implementing Socratic interaction for ionic reaction problems (identify dissociable species → write as ions → remove spectator ions → verify charge/atom conservation) for the Student persona.

#### Scenario: Student enters ionic equation tutoring mode
- **WHEN** a student triggers ionic_equation_tutor without providing an equation
- **THEN** the tool SHALL prompt the student to provide an ionic reaction equation

#### Scenario: Student provides ionic equation
- **WHEN** a student provides a molecular equation like "NaOH + HCl"
- **THEN** the tool SHALL return step=1 guidance for identifying which species dissociate into ions

#### Scenario: Four-step ionic tutoring completes
- **WHEN** the student completes all four steps (dissociate → ion form → remove spectators → verify conservation)
- **THEN** the tool SHALL confirm the final net ionic equation and provide a correctness assessment

### Requirement: Redox tutor tool

The system SHALL register a redox_tutor Agent tool using the tutoring factory, implementing Socratic interaction for redox reaction problems (assign oxidation states → identify oxidation/reduction → balance by electron conservation) for the Student persona.

#### Scenario: Student enters redox tutoring mode
- **WHEN** a student triggers redox_tutor without providing a reaction
- **THEN** the tool SHALL prompt the student to provide a redox reaction equation

#### Scenario: Student provides redox equation
- **WHEN** a student provides "KMnO4 + HCl"
- **THEN** the tool SHALL return step=1 guidance for assigning oxidation states to each element

#### Scenario: Three-step redox tutoring completes
- **WHEN** the student completes all three steps (oxidation states → identify changes → electron conservation balancing)
- **THEN** the tool SHALL confirm the balanced redox equation

### Requirement: Stoichiometry tutor tool

The system SHALL register a stoichiometry_tutor Agent tool using the tutoring factory, implementing Socratic interaction for stoichiometry calculation problems (extract known quantities → select formula → set up proportion → step-by-step calculation) for the Student persona.

#### Scenario: Student enters stoichiometry tutoring mode
- **WHEN** a student triggers stoichiometry_tutor without providing a problem
- **THEN** the tool SHALL prompt the student to provide a stoichiometry calculation problem

#### Scenario: Student provides stoichiometry problem
- **WHEN** a student provides a problem with known masses/moles/volumes
- **THEN** the tool SHALL return step=1 guidance for extracting known quantities from the problem statement

#### Scenario: Four-step stoichiometry tutoring completes
- **WHEN** the student completes all four steps (extract → select formula → set up proportion → calculate)
- **THEN** the tool SHALL confirm the calculated result and provide a correctness assessment

### Requirement: Tool registration and chem_skills engines

The system SHALL register all four new tutoring tools in TOOL_META with persona=["student"] and call_limit=5, add them to the Student persona YAML available_skills, and implement their backing chem_skills engines (chemistry_equilibrium/engine/, chemistry_ionic/engine/, chemistry_redox/engine/, chemistry_stoichiometry/engine/).

#### Scenario: Four new tools in Student persona tool set
- **WHEN** the Agent factory builds the Student persona's tool set
- **THEN** the resulting tool set SHALL include equilibrium_tutor, ionic_equation_tutor, redox_tutor, and stoichiometry_tutor in addition to the existing 8 tutoring tools

#### Scenario: New tools not available to non-student personas
- **WHEN** the Agent factory builds tool sets for teacher, tutor, or parent personas
- **THEN** equilibrium_tutor, ionic_equation_tutor, redox_tutor, and stoichiometry_tutor SHALL NOT be included

#### Scenario: Chem_skills engine exports validated
- **WHEN** each new chem_skills engine __init__.py is imported
- **THEN** it SHALL export at minimum a factory-compatible tutor function and any supporting data models
