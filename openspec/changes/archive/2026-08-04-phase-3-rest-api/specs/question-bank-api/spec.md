## Purpose

Provides REST API endpoints for question bank management — folder-based organization (QuestionSet), folder-item associations, and historical exam retrieval for RAG knowledge base access.

## ADDED Requirements

### Requirement: Question set CRUD
The system SHALL support creating, listing, updating, and deleting question set folders. Each folder belongs to a teacher.

#### Scenario: Teacher creates a question set folder
- **WHEN** a teacher sends POST /api/v1/question-sets with teacher_id, name, description
- **THEN** the system creates the QuestionSet and returns QuestionSetRead with HTTP 201

#### Scenario: Teacher lists own question sets
- **WHEN** a teacher sends GET /api/v1/question-sets?teacher_id={id}
- **THEN** the system returns all question sets for that teacher

#### Scenario: Delete an empty question set
- **WHEN** a teacher sends DELETE /api/v1/question-sets/{id}
- **THEN** the system deletes the question set and all its items, returns HTTP 204

### Requirement: Question set item management
The system SHALL support adding questions to folders, reordering items, and removing items from folders.

#### Scenario: Add question to folder
- **WHEN** a teacher sends POST /api/v1/question-sets/{set_id}/items with question_id and sort_order
- **THEN** the system adds the question to the folder and returns QuestionSetItemRead

#### Scenario: List items in a folder
- **WHEN** a teacher sends GET /api/v1/question-sets/{set_id}/items
- **THEN** the system returns all items in sort_order, with the full question data embedded

#### Scenario: Remove item from folder
- **WHEN** a teacher sends DELETE /api/v1/question-sets/{set_id}/items/{item_id}
- **THEN** the system removes the item, does NOT delete the question

### Requirement: Historical exam browsing
The system SHALL provide endpoints to list and filter historical exams (全国卷 2008-2020, 湖南卷 2021-2025) with pagination and filtering by source, year, and difficulty.

#### Scenario: List all historical exams
- **WHEN** a user sends GET /api/v1/historical-exams?limit=20&offset=0
- **THEN** the system returns paginated HistoricalExam records

#### Scenario: Filter historical exams by source and year
- **WHEN** a user sends GET /api/v1/historical-exams?source=全国卷&year=2020
- **THEN** the system returns only matching exams

#### Scenario: Search historical exams by knowledge point
- **WHEN** a user sends GET /api/v1/historical-exams?knowledge_point=氧化还原反应
- **THEN** the system returns exams tagged with that knowledge point
