## Purpose

Enables teachers to batch-upload answer sheet images, manages their lifecycle through an UploadSession state machine, and validates file integrity before OCR processing begins.

## ADDED Requirements

### Requirement: Batch file upload with multipart form data

The system SHALL accept multiple answer sheet images via `POST /api/v1/ocr/tasks/batch` as multipart/form-data with files, teacher_id, class_id, and optional exam_name and exam_paper_id fields.

#### Scenario: Successful batch upload
- **WHEN** a teacher uploads 5 JPG images with teacher_id=1, class_id=3
- **THEN** the system SHALL create one UploadSession (status=uploaded) and 5 OCRTask records (status=pending), store files to `data/ocr_uploads/{teacher_id}/{date}/{uuid}.{ext}`, and return 201 with batch_id and task list

#### Scenario: Empty file list rejection
- **WHEN** a teacher triggers upload with zero files
- **THEN** the system SHALL return HTTP 400 with error_code "EMPTY_BATCH"

#### Scenario: Unsupported file type rejection
- **WHEN** a teacher uploads a .docx file
- **THEN** the system SHALL return HTTP 415 with error_code "UNSUPPORTED_TYPE"

#### Scenario: File size exceeds limit
- **WHEN** a teacher uploads an image larger than 10MB
- **THEN** the system SHALL return HTTP 413 with error_code "FILE_TOO_LARGE"

#### Scenario: Batch size exceeds soft limit
- **WHEN** a teacher uploads more than OCR_MAX_BATCH_SIZE files in a single request
- **THEN** the system SHALL return HTTP 400 with error_code "BATCH_TOO_LARGE"

### Requirement: UploadSession state machine

The system SHALL manage UploadSession through a 10-state lifecycle: uploaded → previewing → ready, with branching to importing→imported→done or grading→graded→done, plus discarded and error terminal states reachable from any non-terminal state.

#### Scenario: Session created on upload
- **WHEN** files are successfully uploaded and stored
- **THEN** the UploadSession SHALL have status=uploaded

#### Scenario: Session transitions to ready after OCR preview
- **WHEN** all OCR tasks in the session reach status=done
- **THEN** the UploadSession SHALL transition to ready, presenting the teacher with import-to-bank or grade options

#### Scenario: Session enters grading
- **WHEN** the teacher triggers grading for the session
- **THEN** the UploadSession SHALL transition to grading

#### Scenario: Session reaches done
- **WHEN** all tasks are graded AND the teacher confirms save
- **THEN** the UploadSession SHALL transition to done and set completed_at timestamp

#### Scenario: Session discarded by teacher
- **WHEN** the teacher cancels the session from any non-terminal state
- **THEN** the UploadSession SHALL transition to discarded

#### Scenario: Session enters error state
- **WHEN** an unrecoverable error occurs during processing
- **THEN** the UploadSession SHALL transition to error with error_message populated

### Requirement: UploadSession entity fields

The system SHALL persist for each UploadSession: id, teacher_id (FK), status, original_filename, mime_type, file_path, detected_type (PDF/IMAGE), ocr_result_json (JSON), grading_result_json (JSON), total_pages, completed_pages, fallback_used (boolean), version (integer for optimistic locking), error_message (text), completed_at, created_at, and updated_at.

#### Scenario: PDF upload sets detected_type
- **WHEN** a PDF file is uploaded
- **THEN** the UploadSession SHALL have detected_type="PDF"

#### Scenario: Image upload sets detected_type
- **WHEN** a JPG/PNG/BMP/WEBP file is uploaded
- **THEN** the UploadSession SHALL have detected_type="IMAGE"

#### Scenario: File metadata captured
- **WHEN** a file named "答题卡_001.jpg" with MIME type "image/jpeg" is uploaded
- **THEN** the UploadSession SHALL store original_filename="答题卡_001.jpg" and mime_type="image/jpeg"

#### Scenario: Fallback engine usage tracked
- **WHEN** the primary OCR engine fails and VLM fallback is used
- **THEN** the UploadSession SHALL have fallback_used=true

### Requirement: File storage on filesystem

The system SHALL store uploaded answer sheet images on the local filesystem at `{OCR_UPLOAD_DIR}/{teacher_id}/{YYYY-MM-DD}/{uuid}.{ext}`, and persist only the relative path string in the database.

#### Scenario: File path stored as relative path
- **WHEN** a file is saved to `data/ocr_uploads/1/2026-08-09/a1b2c3d4.jpg`
- **THEN** the database SHALL store the relative path "ocr_uploads/1/2026-08-09/a1b2c3d4.jpg"

#### Scenario: UUID naming prevents collisions
- **WHEN** two teachers upload files named "答题卡_01.jpg" simultaneously
- **THEN** the system SHALL generate distinct UUID-based filenames to avoid overwrites
