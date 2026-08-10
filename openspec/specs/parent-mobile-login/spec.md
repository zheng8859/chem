## Purpose

Provide the parent-side authentication entry point: a dual-mode (login / register) mobile page that authenticates parents via phone number and password, or registers new parents with an additional 6-digit bind code, then redirects to the parent dashboard.

## Requirements

### Requirement: Dual-mode login/register page

The system SHALL present a single mobile-optimized page with a toggle to switch between "Login" and "Register" modes, both accepting phone number as the primary identifier.

#### Scenario: User switches between login and register modes
- **WHEN** the user taps the "Login" or "Register" tab
- **THEN** the form fields SHALL update to reflect the selected mode (login: phone + password; register: phone + password + bind code)
- **AND** the submit button label SHALL update accordingly

#### Scenario: Already authenticated user opens the page
- **WHEN** a user with a valid JWT token accesses the login page
- **THEN** the page SHALL redirect to `parent.html` immediately without showing the form

### Requirement: Parent login with phone and password

The system SHALL allow registered parents to log in using their phone number and password via `POST /api/auth/login`.

#### Scenario: Successful login
- **WHEN** a parent enters a registered phone number and correct password, then submits
- **THEN** the system SHALL call `POST /api/auth/login`, save the JWT token via `ChemAuth.login()`, and redirect to `parent.html`

#### Scenario: Wrong credentials
- **WHEN** a parent enters incorrect phone or password
- **THEN** the system SHALL display an error message without revealing whether the phone number exists

#### Scenario: Empty fields
- **WHEN** a parent submits with empty phone or password
- **THEN** the system SHALL show inline validation errors before sending the request

### Requirement: Parent registration with bind code

The system SHALL allow new parents to register with phone, password, and a 6-digit numeric bind code via `POST /api/auth/register/parent`.

#### Scenario: Successful registration
- **WHEN** a parent enters a valid phone, password (≥6 chars), and a bind code matching an active student
- **THEN** the system SHALL call `POST /api/auth/register/parent`, receive JWT tokens, and redirect to `parent.html`

#### Scenario: Invalid bind code
- **WHEN** a parent enters a bind code that does not match any student
- **THEN** the system SHALL display "绑定码无效，请检查后重试"

#### Scenario: Duplicate phone
- **WHEN** a parent enters a phone number already registered
- **THEN** the system SHALL display "该手机号已注册，请直接登录"

#### Scenario: Bind code format validation
- **WHEN** a parent enters a bind code that is not exactly 6 digits
- **THEN** the system SHALL show inline validation error before submitting
