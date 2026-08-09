## Purpose

Provides OCR text recognition from answer sheet images using a three-engine architecture (Baidu OCR, MinerU, VLM) with automatic fallback routing and APScheduler-based task processing.

## ADDED Requirements

### Requirement: Three-engine OCR architecture

The system SHALL support three OCR engines — Baidu OCR (doc_analysis API, primary for images), MinerU (local CLI, primary for PDFs), and VLM multi-modal models (GLM-4V/MiMo, final fallback) — with engine selection routed by file type via EngineRouter.

#### Scenario: Image file routes to Baidu OCR
- **WHEN** an image file (JPG/PNG/BMP/WEBP) is submitted for OCR
- **THEN** the EngineRouter SHALL attempt Baidu OCR first

#### Scenario: PDF file routes to MinerU
- **WHEN** a PDF file is submitted for OCR and MinerU is available
- **THEN** the EngineRouter SHALL attempt MinerU parse_by_cli first

#### Scenario: Baidu OCR failure triggers VLM fallback
- **WHEN** Baidu OCR API call fails or returns an error
- **THEN** the EngineRouter SHALL attempt VLM recognition and mark the result fallback_used=true

#### Scenario: MinerU failure triggers PDF-to-image conversion
- **WHEN** MinerU parse fails for a PDF
- **THEN** the EngineRouter SHALL convert PDF pages to images and route each through the image fallback chain (Baidu → VLM)

#### Scenario: All engines unavailable returns partial result
- **WHEN** no OCR engine is configured or all engines fail
- **THEN** the system SHALL return an OCRResult with is_partial=true and an error message

### Requirement: Baidu OAuth 2.0 token management

The system SHALL manage Baidu API access tokens via memory cache with a 300-second safety margin before the 30-day expiry, refreshing automatically when the cached token nears expiration.

#### Scenario: First API call fetches new token
- **WHEN** the first Baidu API call is made after application startup
- **THEN** the system SHALL POST to the Baidu OAuth 2.0 token endpoint with client_credentials and cache the access_token

#### Scenario: Cached token reused within validity window
- **WHEN** a subsequent Baidu API call is made and the cached token has more than 300 seconds until expiry
- **THEN** the system SHALL reuse the cached token without making a new OAuth request

#### Scenario: Token refreshed near expiry
- **WHEN** a Baidu API call is made and the cached token has fewer than 300 seconds until expiry
- **THEN** the system SHALL request a new token and update the cache

### Requirement: Baidu OCR doc_analysis integration

The system SHALL call the Baidu doc_analysis OCR API with handprint_mix mode for Chinese handwriting, recg_formula enabled for chemical formulas, and language_type=CHN_ENG.

#### Scenario: Successful OCR returns structured result
- **WHEN** Baidu doc_analysis successfully processes an answer sheet image
- **THEN** the system SHALL return an OCRResult with raw_text, confidence score, words_result array, and engine="baidu_doc_analysis"

#### Scenario: Low-confidence partial result
- **WHEN** doc_analysis returns raw_text with fewer than 10 characters
- **THEN** the system SHALL set is_partial=true and mark student_id_raw="unknown"

#### Scenario: API returns business error
- **WHEN** doc_analysis returns error_code != 0 in the response body
- **THEN** the system SHALL treat it as an engine failure and trigger the fallback chain

### Requirement: MinerU PDF parsing

The system SHALL invoke MinerU CLI (`mineru parse`) as a subprocess for PDF document parsing with hybrid-auto engine mode, capturing stdout/stderr and reading output markdown files.

#### Scenario: MinerU available check
- **WHEN** the system checks MinerU availability via `mineru --version` or model directory existence
- **THEN** the system SHALL report availability status in GET /api/v1/ocr/services/status

#### Scenario: Successful MinerU parse
- **WHEN** MinerU successfully parses a PDF
- **THEN** the system SHALL return an OCRResult with raw_text from the output markdown files and engine="mineru_hybrid_auto"

#### Scenario: MinerU parse timeout
- **WHEN** MinerU parse exceeds the PARSE_TIMEOUT (120 seconds)
- **THEN** the system SHALL kill the subprocess and trigger the fallback chain

### Requirement: VLM multi-modal fallback

The system SHALL use vision-language models (ZhiPu GLM-4V or Xiaomi MiMo) as a final fallback by sending base64-encoded images with a structured extraction prompt, returning results annotated with fallback_used=true.

#### Scenario: VLM extracts student info and answers
- **WHEN** VLM processes an answer sheet image
- **THEN** the system SHALL send a prompt requesting student ID, student name, and per-question answers, and parse the JSON response

#### Scenario: VLM unavailable
- **WHEN** no VLM provider (ZHIPU_API_KEY or MIMO_API_KEY) is configured
- **THEN** the system SHALL return a partial OCR result with is_partial=true

### Requirement: APScheduler OCR task processing

The system SHALL run an APScheduler IntervalTrigger job every 5 seconds that claims up to 5 pending OCRTask records, updates their status to processing, executes OCR via EngineRouter, and updates the task to done or failed with results.

#### Scenario: Job claims pending tasks
- **WHEN** the OCR processor job fires and there are 3 pending OCR tasks
- **THEN** the system SHALL SELECT up to 3 tasks ORDER BY created_at ASC, UPDATE their status to processing and progress to 10

#### Scenario: Job skips when no pending tasks
- **WHEN** the OCR processor job fires and there are zero tasks with status=pending
- **THEN** the system SHALL return immediately without error

#### Scenario: Successful OCR updates task to done
- **WHEN** EngineRouter returns a successful OCRResult
- **THEN** the system SHALL UPDATE the task status to done, progress to 100, ocr_raw_result with the structured result, student_id_raw and student_name_raw from extraction, and completed_at to current timestamp

#### Scenario: Failed OCR updates task to failed
- **WHEN** EngineRouter raises an exception or returns a failure result
- **THEN** the system SHALL UPDATE the task status to failed and error_message with the error detail

#### Scenario: Concurrent API calls limited by semaphore
- **WHEN** 5 OCR tasks are being processed concurrently
- **THEN** at most 5 simultaneous Baidu API calls SHALL be in flight, controlled by asyncio.Semaphore(5)

### Requirement: OCRTask entity fields

The system SHALL persist for each OCRTask: id, upload_session_id (FK), teacher_id (FK), image_path, title, status (pending/processing/done/failed), progress (0-100), ocr_raw_result (JSON), grading_result (JSON), student_id_raw (nullable string), student_name_raw (nullable string), confirmed (boolean), error_message (text), completed_at, created_at, and updated_at.

#### Scenario: Task progress updated during processing
- **WHEN** the scheduler picks up a pending task
- **THEN** the task SHALL have progress=10 (OCR started)
- **WHEN** OCR completes successfully
- **THEN** the task SHALL have progress=100

#### Scenario: Failed task retains error context
- **WHEN** OCR processing fails with a Baidu API error
- **THEN** the task SHALL have status=failed, error_message containing the API error description, and progress frozen at the last value

### Requirement: Student information extraction from OCR text

The system SHALL extract student ID and name from OCR raw text using engine-specific regex patterns: Baidu engine uses label-prefixed patterns plus a "202[4-9]\\d{4,7}" fallback; MinerU engine uses label-prefixed patterns plus a generic "\\b\\d{8,10}\\b" fallback; unmatched values SHALL be set to null.

#### Scenario: Label-based student ID extraction
- **WHEN** OCR text contains "学号: 202401001" or "学号：202401001"
- **THEN** the system SHALL extract student_id_raw="202401001"

#### Scenario: Label-based name extraction
- **WHEN** OCR text contains "姓名: 张三" or "姓名：张三"
- **THEN** the system SHALL extract student_name_raw="张三"

#### Scenario: Baidu-specific fallback for unlabeled student ID
- **WHEN** no "学号:" label is found but the text contains "202401001" matching the Baidu pattern
- **THEN** the system SHALL extract student_id_raw="202401001"

#### Scenario: Unmatched student info returns null
- **WHEN** neither label patterns nor fallback patterns match
- **THEN** the system SHALL set student_id_raw=null and/or student_name_raw=null

### Requirement: OCR service status endpoint

The system SHALL expose GET /api/v1/ocr/services/status returning the availability status of all three OCR engines (ocr, mineru, vision) and the current degradation chain configuration.

#### Scenario: All engines available
- **WHEN** Baidu API keys are configured, MinerU models are downloaded, and VLM keys are set
- **THEN** the response SHALL report ocr.available=true, mineru.available=true, vision.available=true

#### Scenario: MinerU unavailable
- **WHEN** MinerU models are not downloaded
- **THEN** the response SHALL report mineru.available=false with reason "MinerU 模型未下载"
