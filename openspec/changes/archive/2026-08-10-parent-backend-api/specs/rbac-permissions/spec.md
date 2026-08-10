## ADDED Requirements

### Requirement: Parent binding permission enforcement

The system SHALL provide a FastAPI dependency that verifies the authenticated parent has an active binding to the requested child before allowing data access.

#### Scenario: Parent with active binding passes check
- **WHEN** an endpoint decorated with `Depends(require_parent_binding())` is called by a parent who has an active StudentParentBinding to the child in the URL path
- **THEN** the dependency SHALL return the resolved parent_id and student_id for the service layer

#### Scenario: Parent without binding receives 403
- **WHEN** a parent requests data for a student they are not bound to
- **THEN** the dependency SHALL raise HTTPException(403, "未绑定该学生")

#### Scenario: Non-parent role receives 403
- **WHEN** a teacher or student accesses an endpoint using require_parent_binding
- **THEN** the dependency SHALL raise HTTPException(403, "仅家长角色可访问")

#### Scenario: Inactive binding treated as no binding
- **WHEN** a parent has a binding with status=inactive to the requested child
- **THEN** the dependency SHALL raise HTTPException(403, "未绑定该学生")
