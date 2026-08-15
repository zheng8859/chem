## ADDED Requirements

### Requirement: Browser tool URL validation (SSRF protection)

The system SHALL validate the URL passed to the `browse_navigate` browser tool before navigation to prevent Server-Side Request Forgery (SSRF). The validator SHALL reject any URL whose scheme is not http or https (e.g., file://, gopher://, ftp://). It SHALL resolve the hostname and reject any host that resolves to a loopback, link-local (including 169.254.169.254 cloud metadata), private, or otherwise reserved IP address. On rejection, the tool SHALL return an error result and SHALL NOT open a browser page.

#### Scenario: Non-http scheme rejected
- **WHEN** browse_navigate is called with "file:///etc/passwd"
- **THEN** the tool SHALL return an error and SHALL NOT navigate

#### Scenario: Loopback address rejected
- **WHEN** browse_navigate is called with "http://127.0.0.1:8000/admin"
- **THEN** the tool SHALL return an error and SHALL NOT navigate

#### Scenario: Cloud metadata endpoint rejected
- **WHEN** browse_navigate is called with "http://169.254.169.254/latest/meta-data/"
- **THEN** the tool SHALL return an error and SHALL NOT navigate

#### Scenario: Private network address rejected
- **WHEN** browse_navigate is called with "http://192.168.1.1/" or "http://10.0.0.5/"
- **THEN** the tool SHALL return an error and SHALL NOT navigate

#### Scenario: Public http(s) URL allowed
- **WHEN** browse_navigate is called with "https://example.com/chemistry"
- **THEN** the tool SHALL navigate to the URL
