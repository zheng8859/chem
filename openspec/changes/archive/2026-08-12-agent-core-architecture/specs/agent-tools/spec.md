## Purpose

Defines the unified tool registration system for all 30 Agent tools across 4 Personas, including the TOOL_META registry, the @register_tool decorator, the tutoring factory pattern, and the two-layer Persona tool filtering mechanism.

## ADDED Requirements

### Requirement: Tool metadata registration

The system SHALL provide a @register_tool decorator that registers each Agent tool with metadata: name (unique), persona (list of allowed roles), call_limit (max calls per conversation), requires_approval (boolean), prerequisites (list of required parameter names), and description (tool docstring for LLM selection). The registry SHALL validate at startup that every registered tool has metadata and every metadata entry maps to an existing tool.

#### Scenario: Tool registration with full metadata
- **WHEN** a new tool function is decorated with @register_tool(name="search_exam_bank", persona=["teacher","tutor"], call_limit=3, prerequisites=["keyword"], description="Search exam bank by keyword")
- **THEN** the tool SHALL be added to TOOL_META and available to Teacher and Tutor personas via get_tools_for_persona()

#### Scenario: Startup validation catches orphan metadata
- **WHEN** the application starts and TOOL_META contains an entry whose func is missing
- **THEN** the system SHALL log an error and raise an exception to prevent startup

### Requirement: Persona tool filtering

The system SHALL compute each Persona's final tool set as the intersection of: (1) the tools registered in TOOL_META for that persona, and (2) the tools listed in the Persona's YAML available_skills. Tools not in the intersection SHALL be excluded. All Personas SHALL automatically receive 5 browser tools (browse_navigate, browse_read, browse_click, browse_input, browse_screenshot).

#### Scenario: Teacher persona tool set
- **WHEN** the Teacher persona Agent is built
- **THEN** the tool set SHALL include exactly: search_exam_bank, web_search, show_exam_workbench, diagnose_barrier, show_diagnosis, show_students, balance_equation, assign_adaptive_practice, save_to_bank, list_banks, delete_bank, generate_questions, query_ocr_progress, grade_answer_sheets, save_grading_results, memory_teacher_get, memory_student_get, weekly_report, generate_learning_plan, send_learning_plan, generate_parent_report, send_report_to_parent, chemistry_tutor, plus 5 browser tools

#### Scenario: YAML-only tool not in TOOL_META is excluded
- **WHEN** a Persona YAML lists a tool that is not registered in TOOL_META
- **THEN** that tool SHALL NOT appear in the final tool set

#### Scenario: All personas receive browser tools
- **WHEN** the Parent persona Agent is built with only 2 domain tools in its YAML
- **THEN** the final tool set SHALL include both domain tools plus all 5 browser tools

### Requirement: Tutoring factory for Socratic tools

The system SHALL provide a factory function that generates Socratic tutoring tools from a common template, accepting: name, title, step_guidance, step2_guidance, docstring, default_msg, and step_titles. Each generated tool SHALL implement three-mode interaction: no-args → prompt to provide input; equation/problem but no student_input → step 1 guidance; student_input + equation/problem → feedback + step 2 guidance.

#### Scenario: Factory generates ionic_equation_tutor
- **WHEN** the tutoring factory is called with parameters for ionic equation tutoring
- **THEN** the resulting tool SHALL return step=1 guidance when given an equation without student_input, and feedback + step=2 guidance when given both equation and student_input

#### Scenario: Factory-generated tool returns completion marker
- **WHEN** a factory-generated tool returns a response containing "guidance" or "step" keys
- **THEN** the SSE adapter SHALL detect the completion marker and skip subsequent LLM text for that round

### Requirement: Teacher tool set for 30号 §3.2-3.7

The system SHALL register all 30 Agent tools defined in document 30-Agent对话系统设计, organized into 7 categories: 出题与题库 (7 tools), 诊断与学生 (7 tools), 辅导 (8 tools), OCR与批改 (3 tools), 记忆 (2 tools), 家长报告 (2 tools), and 浏览器 (5 tools, auto-registered).

#### Scenario: All 30 tools registered
- **WHEN** the application starts
- **THEN** get_all_tools() SHALL return exactly 35 entries (30 domain tools + 5 browser tools)

#### Scenario: Each tool has at least one persona
- **WHEN** the application starts
- **THEN** every registered tool's persona list SHALL be non-empty
