## ADDED Requirements

### Requirement: OCR pipeline entity fields

The system SHALL extend the UploadSession model with fields for file metadata, progress tracking, fallback tracking, and error handling: original_filename (String 500, the uploaded file's original name), mime_type (String 50, the file's MIME type), file_path (String 500, relative filesystem path to the stored file), detected_type (String 20, "PDF" or "IMAGE" auto-detected from file extension), ocr_result_json (JSON, intermediate OCR recognition results), grading_result_json (JSON, final grading results), total_pages (Integer, total pages for PDF), completed_pages (Integer, currently processed pages), fallback_used (Boolean, default false, whether degradation engine was triggered), version (Integer, default 1, optimistic locking), and error_message (Text, error description on failure).

#### Scenario: UploadSession with full file metadata
- **WHEN** a teacher uploads "答题卡_001.jpg" (image/jpeg)
- **THEN** the UploadSession SHALL have original_filename="答题卡_001.jpg", mime_type="image/jpeg", detected_type="IMAGE", and file_path pointing to the stored file

#### Scenario: Optimistic locking version increment
- **WHEN** an UploadSession's status or progress is updated
- **THEN** the system SHALL increment the version field for concurrent access control

### Requirement: OCRTask extended entity fields

The system SHALL extend the OCRTask model with fields for teacher association, image location, student identity extraction, progress tracking, and confirmation: teacher_id (FK to teacher, for direct teacher-task queries), image_path (String 500, path to the answer sheet image on disk), title (String 200, human-readable task label), student_id_raw (String 50, nullable, student ID extracted by OCR), student_name_raw (String 50, nullable, student name extracted by OCR), progress (Integer, default 0, processing percentage 0-100), confirmed (Boolean, default false, teacher confirmation flag), error_message (Text, nullable, error description on failure), and completed_at (DateTime, nullable, processing completion timestamp).

#### Scenario: OCRTask with student identity extracted
- **WHEN** OCR successfully extracts student ID "202401001" and name "张三"
- **THEN** the OCRTask SHALL have student_id_raw="202401001" and student_name_raw="张三"

#### Scenario: OCRTask with extraction failure
- **WHEN** OCR cannot identify student information from the image
- **THEN** the OCRTask SHALL have student_id_raw=null and student_name_raw=null

#### Scenario: Progress tracking through pipeline stages
- **WHEN** the scheduler picks up a pending task, it SHALL set progress=10
- **WHEN** OCR completes, progress SHALL be 100
- **WHEN** a task fails, progress SHALL remain at the last successful value and error_message SHALL be populated
