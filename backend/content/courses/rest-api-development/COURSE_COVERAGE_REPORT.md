# REST API Development — Syllabus Coverage Report

**Source syllabus:** supplied `REST API.pdf` (49 pages).
**Course slug:** `rest-api-development`.
**Review date:** 2026-10-19.

## Coverage totals

- Modules: **24**.
- Main numbered lessons: **240**.
- Subtopics preserved in lesson files: **975**.
- Formal applied exercises: **30** (30 B/I/A exercises from the PDF).
- Projects: **11** (10 progression projects plus multi-vendor commerce capstone).
- Knowledge-check sets: 240 lesson-linked files, three questions per set (720 prompts total); all questions are draft and answers remain in protected course files.
- Assessment blueprint: one 120-minute, 50-question intended final exam blueprint; not connected to the existing production learner exam flow yet.
- Visuals: 264 original SVGs: one module overview per module and one concept map per lesson.

## PDF topic mapping

Each listed main lesson and all its decimal subtopics have been preserved in the separate lesson JSON file. The lesson order is continuous across modules and follows the PDF Section B. Topic titles are listed below for traceability.

### Module 1: Introduction to REST API Development (PDF lessons 1–8)

- **1. Introduction to REST API Development** — What this course covers; How APIs connect software applications; Understanding API providers and consumers
- **2. What Is an API?** — Application Programming Interface; API contracts and operations; Public, partner, private, and internal APIs
- **3. What Is REST?** — Meaning of Representational State Transfer; REST as an architectural style; REST versus an API protocol; RESTful APIs versus REST-inspired APIs
- **4. What Is a REST API?** — Resources and representations; HTTP-based communication; Clients, servers, and intermediaries
- **5. Why REST APIs Are Used** — Connecting frontend and backend applications; Sharing data between services; Integrating mobile apps and external platforms; Supporting independent application development
- **6. Real-World Applications of REST APIs** — E-commerce and order management; Authentication and user management; Payments and delivery integrations; Content management and media services; Analytics and third-party integrations
- **7. Advantages, Limitations, and Trade-offs** — Interoperability and platform independence; Resource-based interfaces; Network latency and payload overhead; Managing API contracts and changes
- **8. Prerequisites and Learning Environment** — Basic programming concepts; Basic web and networking concepts; Introduction to JSON; Overview of development tools; Choosing an implementation language and framework

### Module 2: Web Networking and HTTP Fundamentals (PDF lessons 9–18)

- **9. How the Web Works** — Clients, servers, and internet communication; Request-response interaction; Domain names, DNS, and IP addresses; Ports, connections, and network endpoints
- **10. Understanding URLs and URIs** — Uniform Resource Identifier and Uniform Resource Locator; Scheme, host, port, path, and query; URI fragments and their behavior in HTTP requests; Percent encoding and reserved characters
- **11. Introduction to HTTP** — HTTP as an application-layer protocol; HTTP requests and responses; Stateless communication; HTTP specifications and semantics
- **12. Structure of an HTTP Request** — Request method and target; Request headers; Request body; Request metadata and content length
- **13. Structure of an HTTP Response** — Status line and status code; Response headers; Response body; Metadata and content negotiation
- **14. HTTP Versions and Transport** — HTTP/1.1 fundamentals; HTTP/2 and multiplexing; HTTP/3 and QUIC fundamentals; How protocol versions affect deployment and performance
- **15. HTTPS and TLS** — HTTP versus HTTPS; TLS encryption and integrity; Certificates and certificate validation; Secure communication in development and production
- **16. Headers, Media Types, and Content Negotiation** — General, request, and response headers; Content-Type and Accept; Character encoding; JSON media types; Unsupported media types and representations
- **17. Browsers, CORS, and Preflight Requests** — Same-origin policy; Cross-Origin Resource Sharing; Preflight OPTIONS requests; Allowed origins, methods, and headers; CORS versus authentication and authorization
- **18. Cookies, Sessions, and Client State** — HTTP cookies; Server-side sessions; Statelessness and externalized state; Cookies versus bearer tokens; Cross-site request forgery fundamentals

### Module 3: REST Architectural Principles (PDF lessons 19–28)

- **19. History and Evolution of REST** — Origins of REST; Roy Fielding's architectural model; REST and HTTP's evolution; Modern API design conventions
- **20. Resources and Resource Identification** — Resource concepts; Resource identifiers; Resource representations; Resource state versus application behavior
- **21. The Client-Server Constraint** — Separation of responsibilities; Independent client and server development; Interface boundaries
- **22. The Stateless Constraint** — Independent request processing; State carried in each request; Persistent business data versus session state; Implications for scaling
- **23. Cacheability** — Why caching exists; Cacheable versus non-cacheable responses; Freshness and validation; Cache behavior and consistency
- **24. The Uniform Interface** — Resource identification; Manipulation through representations; Self-descriptive messages; Hypermedia as the engine of application state
- **25. Layered System Architecture** — Proxies, gateways, and load balancers; Separation across architectural layers; Intermediary behavior and trust boundaries
- **26. Code on Demand** — Optional REST constraint; Downloadable executable behavior; Applicability and limitations
- **27. REST Constraints and REST Maturity** — Understanding the architectural constraints together; Resource-oriented HTTP API design; Hypermedia and discovery; Distinguishing strict REST from pragmatic HTTP APIs
- **28. REST API Design Principles** — Consistency and predictability; Resource-oriented modeling; Explicit behavior and contracts; Simplicity and evolvability

### Module 4: Resource Modeling and URL Design (PDF lessons 29–38)

- **29. Identifying Resources from Business Requirements** — Finding core domain entities; Distinguishing resources from operations; Mapping business requirements to API resources
- **30. Designing Resource Collections and Individual Resources** — Collection endpoints; Individual resource endpoints; Nested resources; Relationships between resources
- **31. Naming Resource Paths** — Nouns and plural collection names; Consistent casing and naming conventions; Path depth and readability; Meaningful identifiers
- **32. Path Parameters and Query Parameters** — Identifying a specific resource; Filtering and controlling a collection; Choosing between path and query parameters; Required and optional parameters
- **33. Resource Identifiers** — Sequential IDs, UUIDs, and opaque identifiers; Identifier immutability; Public IDs versus internal database IDs; Identifier enumeration and security implications
- **34. Modeling Relationships** — One-to-one relationships; One-to-many relationships; Many-to-many relationships; Nested endpoints versus top-level relationship resources
- **35. Designing Action-Oriented Operations** — Modeling commands through HTTP methods; State transitions and explicit action resources; Operations that do not fit ordinary CRUD; Avoiding misleading endpoint names
- **36. URL Encoding and Path Normalization** — Encoding reserved characters; Trailing slashes and redirect behavior; Case sensitivity and path normalization; Consistent canonical URLs
- **37. Endpoint Naming Anti-Patterns** — Unnecessary verbs in resource paths; Deeply nested paths; Inconsistent collection names; Ambiguous or overlapping resources
- **38. Creating an API Resource Map** — Identifying entities and relationships; Mapping operations to HTTP methods; Building an endpoint inventory; Reviewing resource boundaries

### Module 5: HTTP Methods and Operation Semantics (PDF lessons 39–47)

- **39. Understanding HTTP Methods** — Method semantics; Safe and unsafe methods; Idempotent and non-idempotent operations; Method selection principles
- **40. The GET Method** — Retrieving representations; Querying collections; GET request bodies and interoperability concerns; Safe behavior and cacheability
- **41. The POST Method** — Creating resources; Submitting commands and processing requests; Server-assigned identifiers; POST responses and Location headers
- **42. The PUT Method** — Creating or replacing a resource at a known URI; Full replacement semantics; Idempotency expectations; PUT versus POST
- **43. The PATCH Method** — Partial resource updates; JSON Merge Patch; JSON Patch; Conflict handling and patch validation
- **44. The DELETE Method** — Deleting a resource; Idempotent semantics; Hard deletion and soft deletion; Deletion responses and repeated requests
- **45. The HEAD and OPTIONS Methods** — HEAD and metadata-only responses; OPTIONS and supported operations; CORS preflight usage; Capability discovery
- **46. Choosing Methods for Real Operations** — Mapping CRUD operations to HTTP; Managing status transitions; Handling bulk operations; Avoiding custom method misuse
- **47. Idempotency and Safe Retry Design** — Idempotent versus safe behavior; Duplicate requests and repeated submissions; Idempotency keys for supported operations; Retry behavior after uncertain outcomes

### Module 6: HTTP Status Codes and Response Headers (PDF lessons 48–54)

- **48. Understanding HTTP Status Code Classes** — Informational responses; Successful responses; Redirection responses; Client errors; Server errors
- **49. Successful Response Codes** — 200 OK; 201 Created; 202 Accepted; 204 No Content; Selecting success codes by operation semantics
- **50. Client Error Status Codes** — 400 Bad Request; 401 Unauthorized; 403 Forbidden; 404 Not Found; 405 Method Not Allowed; 409 Conflict; 412 Precondition Failed; 413 Content Too Large; 415 Unsupported Media Type; 422 Unprocessable Content; 429 Too Many Requests
- **51. Server and Gateway Error Codes** — 500 Internal Server Error; 501 Not Implemented; 502 Bad Gateway; 503 Service Unavailable; 504 Gateway Timeout
- **52. Response Headers for API Behavior** — Location; Allow; Retry-After; WWW-Authenticate; Vary; ETag and Last-Modified
- **53. Cache-Control and Security Headers** — Cache-Control; Expires; X-Content-Type-Options; Content security considerations for API responses; Cache directives for sensitive data
- **54. Status Code Decision Making** — Choosing consistent responses; Distinguishing authentication from authorization failures; Error responses for missing and conflicting resources; Avoiding success responses for failed operations

### Module 7: JSON and Data Representations (PDF lessons 55–62)

- **55. Introduction to JSON** — JSON objects and arrays; Strings, numbers, booleans, and null; Nested data structures; Valid JSON syntax
- **56. Designing Response Representations** — Defining response schemas; Stable field names; Representing identifiers and relationships; Choosing between flattened and nested structures
- **57. Designing Request Bodies** — Create request schemas; Update request schemas; Read-only and server-generated fields; Optional, required, and nullable fields
- **58. JSON Data Type Decisions** — Integers and numeric values; Floating-point precision; Dates and timestamps; Time zones and consistent date representations; Money, currency, and decimal precision
- **59. Resource Representation Boundaries** — Entity data versus computed fields; Embedded representations and references; Omitting internal and sensitive fields; Derived attributes and response consistency
- **60. Representing Collections and Empty Values** — Empty arrays and empty objects; Null versus missing properties; Empty collections versus not-found resources; Backward compatibility of response fields
- **61. Serialization and Deserialization** — Converting application objects to JSON; Parsing incoming JSON; Handling invalid JSON; Serialization errors and unsupported values
- **62. Alternative Representations and Content Negotiation** — JSON as the common API representation; Vendor-specific media types; Versioned media types; XML and other representations when required; 406 Not Acceptable and 415 Unsupported Media Type

### Module 8: Implementing CRUD APIs (PDF lessons 63–71)

- **63. Planning a CRUD Resource** — Resource schema; Endpoint matrix; Request and response contracts; Access rules for each operation
- **64. Building a Create Endpoint** — Parsing and validating input; Persisting new records; Generating identifiers; Returning 201 Created and resource location
- **65. Building a Read Endpoint** — Retrieving individual records; Listing a collection; Handling missing records; Returning suitable representations
- **66. Building an Update Endpoint** — PUT replacement semantics; PATCH partial updates; Preventing accidental field overwrites; Validating the resulting resource state
- **67. Building a Delete Endpoint** — Deletion workflow; Existence and permission checks; Soft deletion and restoration policies; Consistent deletion responses
- **68. Managing Resource State Transitions** — Draft, active, archived, and deleted states; Valid and invalid transitions; State-dependent authorization; Enforcing business invariants
- **69. Collection and Bulk Operations** — Batch creation and updates; Bulk deletion; Per-item results versus all-or-nothing behavior; Payload size and resource limits
- **70. Relationship Endpoints** — Assigning related resources; Listing child resources; Updating and removing relationships; Handling invalid or missing references
- **71. CRUD API Implementation Review** — Endpoint consistency; Validation and error handling; Authorization at each operation; CRUD behavior acceptance tests

### Module 9: Filtering, Sorting, Searching, and Pagination (PDF lessons 72–81)

- **72. Filtering Collections** — Equality filters; Multiple filter parameters; Range filters; Enumerated values and filter validation
- **73. Sorting and Ordering** — Sort fields and direction; Multiple sort keys; Default ordering; Stable ordering for pagination
- **74. Searching Resources** — Exact-match and full-text search; Search query parameters; Partial matching; Search behavior and relevance
- **75. Offset and Limit Pagination** — Page-based pagination; Offset and limit; Maximum page-size restrictions; Performance considerations
- **76. Cursor-Based Pagination** — Cursor concepts; Opaque continuation tokens; Stable ordering and pagination consistency; Cursor expiration and validation
- **77. Pagination Response Design** — Items and metadata; Total counts; Next and previous links; Continuation tokens and Link headers
- **78. Advanced Filtering Patterns** — Date and timestamp ranges; Nested properties; Filter expressions; Validation of complex query syntax
- **79. Field Selection and Response Shaping** — Selecting returned fields; Expanding related resources; Avoiding excessive data retrieval; Authorization implications of field selection
- **80. Aggregate and Summary Endpoints** — Counts and grouped results; Summaries and computed metrics; Aggregation constraints; Reporting APIs versus resource APIs
- **81. Query Performance and Abuse Prevention** — Index-aware filtering; Limiting expensive query expressions; Preventing unbounded data retrieval; Query timeouts and complexity budgets

### Module 10: Validation, Error Handling, and API Consistency (PDF lessons 82–91)

- **82. Input Validation Fundamentals** — Required fields and allowed types; String length and numeric ranges; Enumeration and format checks; Rejecting unexpected properties
- **83. Schema Validation** — Request schema enforcement; Nested object and array validation; Conditional constraints; Shared validation rules
- **84. Business Rule Validation** — Domain invariants; Cross-field validation; Resource existence and relationships; State-dependent validation
- **85. Sanitization and Data Handling** — Validation versus sanitization; Safe handling of user-provided strings; SQL and command injection prevention concepts; Preventing unsafe deserialization
- **86. Error Response Design** — Consistent error structures; Error codes and human-readable messages; Field-level validation details; Machine-readable error responses
- **87. Problem Details for HTTP APIs** — RFC 9457 problem details; Problem type, title, status, and detail; Instance identifiers and extension members; Representing validation errors consistently
- **88. Exception Handling** — Expected versus unexpected errors; Centralized exception handling; Safe error mapping; Preventing stack traces and secrets from reaching clients
- **89. Conflict and Concurrency Errors** — Duplicate resource conflicts; Invalid state transitions; Optimistic concurrency failures; Conflict resolution strategies
- **90. Request and Response Size Limits** — Payload size validation; Upload and batch limits; Protection against resource exhaustion; Returning appropriate error responses
- **91. API Consistency and Error Quality** — Shared error conventions; Consistent status codes; Correlation and support identifiers; Error response contract testing

### Module 11: Backend Architecture for REST APIs (PDF lessons 92–103)

- **92. Understanding an API Server** — Request entry points; Routing and request dispatch; Business logic execution; Response generation
- **93. Setting Up an API Development Environment** — Installing a runtime and backend framework; Creating a project structure; Running a local server; Managing configuration and environment variables
- **94. Routing and Endpoint Registration** — Mapping methods and paths to handlers; Route parameters and query parameters; Route matching and precedence; API route organization
- **95. Request Parsing and Response Construction** — Parsing JSON and form data; Reading headers and parameters; Constructing status codes, headers, and response bodies; Handling unsupported request formats
- **96. Middleware and Request Pipelines** — Middleware concepts; Request IDs and logging middleware; Authentication and authorization middleware; Validation and error middleware; Middleware ordering and short-circuit behavior
- **97. Separation of Concerns** — Route handlers and controllers; Service or use-case layer; Repository or data-access layer; Shared utilities and infrastructure code
- **98. Layered Architecture** — Presentation and transport layer; Application layer; Domain layer; Persistence and infrastructure layer
- **99. Dependency Management and Configuration** — Dependencies and package managers; Configuration by environment; Secret management; Dependency locking and updates
- **100. Request Lifecycle and Context** — Request-scoped data; Authenticated identity propagation; Cancellation and timeouts; Context propagation across service boundaries
- **101. Business Logic and Use Cases** — Keeping business rules outside controllers; Reusable use-case functions; Input and output boundaries; Maintaining domain invariants
- **102. Dependency Injection and Testability** — Constructor and function injection; Replacing external dependencies in tests; Configuration-driven implementations; Avoiding unnecessary abstraction
- **103. Building a Reusable API Structure** — Shared response and error handling; Reusable validation and authentication components; Modular feature organization; Maintaining a growing API codebase

### Module 12: Databases and Persistence (PDF lessons 104–111)

- **104. Database Fundamentals for API Developers** — Relational and non-relational databases; Tables, documents, and records; Keys and relationships; Persistence and data ownership
- **105. Data Modeling for API Resources** — Domain entities and persistence models; Database schema design; Normalization and relationships; Mapping between database records and API representations
- **106. Database Access Patterns** — Queries and data-access functions; ORM and query-builder concepts; Parameterized queries; Transactions and connection management
- **107. Integrity and Constraints** — Primary and foreign keys; Unique and check constraints; Referential integrity; Enforcing rules in both application and database layers
- **108. Transactions and Consistency** — Atomicity and rollback; Transaction boundaries; Isolation and concurrent requests; Handling failed multi-step operations
- **109. Database Migrations and Seeding** — Version-controlled schema changes; Applying and reversing migrations; Seed data and test fixtures; Safe schema changes in production
- **110. Database Performance** — Indexes and query plans; N+1 query problems; Connection pooling; Pagination and large result sets
- **111. Data Lifecycle and Persistence Reliability** — Soft deletion and retention; Backup and restore fundamentals; Handling database unavailability; Data consistency across multiple services

### Module 13: Authentication, Authorization, and Identity (PDF lessons 112–123)

- **112. Authentication and Authorization Fundamentals** — Authentication: identifying a caller; Authorization: determining permitted actions; Identity, permissions, and resource ownership; Why successful login does not imply full access
- **113. API Keys and Basic Authentication** — API keys and their intended use cases; Key storage, rotation, and revocation; HTTP Basic authentication concepts; Limitations of long-lived shared credentials
- **114. Session-Based Authentication** — Login and session creation; Cookies and session identifiers; Session expiration and revocation; CSRF protections for cookie-based sessions
- **115. Token-Based Authentication** — Access tokens and refresh tokens; Bearer-token requests; Token expiration and renewal; Secure token storage and transmission
- **116. JSON Web Tokens** — JWT structure and claims; Signature verification; Issuer, audience, expiration, and not-before checks; Key rotation and algorithm selection; JWTs versus opaque tokens
- **117. OAuth 2.0 Fundamentals** — Authorization servers and resource servers; OAuth clients and resource owners; Authorization Code Flow with PKCE; Client Credentials Flow; Scopes and delegated versus application access
- **118. OpenID Connect** — Authentication built on OAuth 2.0; ID tokens versus access tokens; Discovery and issuer configuration; Login integration and identity claims
- **119. Passwords, Credentials, and Account Security** — Secure password hashing concepts; Login and credential validation; Account recovery and reset tokens; Multi-factor authentication integration
- **120. Role-Based Access Control** — Roles and permissions; Role assignment and evaluation; Administrative versus regular-user permissions; Least-privilege design
- **121. Attribute-Based and Resource-Based Authorization** — Ownership rules; Tenant and organization boundaries; Attribute-based policies; Field-level permissions
- **122. Multi-Tenant API Security** — Tenant identification; Tenant-scoped queries; Preventing cross-tenant access; Tenant-aware logging and testing
- **123. Identity Lifecycle and Credential Revocation** — Logout and session invalidation; Refresh-token rotation; Expired and revoked credentials; Signing-key rotation and account deactivation

### Module 14: REST API Security (PDF lessons 124–136)

- **124. API Threat Modeling** — Identifying assets and trust boundaries; Mapping entry points and data flows; Identifying abuse cases; Prioritizing mitigations by risk
- **125. Broken Object-Level Authorization** — Resource ownership checks; Authorization on every ID-based operation; Preventing horizontal privilege escalation; Testing access between user accounts and tenants
- **126. Broken Function-Level Authorization** — Protecting administrative endpoints; Role and permission checks; Preventing privileged actions through alternate routes; Authorization policy testing
- **127. Object Property Authorization and Mass Assignment** — Explicit request schemas; Allowlisted writable fields; Protecting internal, financial, and administrative attributes; Controlling sensitive fields in responses
- **128. Injection Vulnerabilities** — SQL injection prevention; NoSQL injection concepts; Command injection and unsafe subprocess use; Template and expression injection; Parameterized queries and safe data handling
- **129. Cross-Site Request Forgery and Cross-Origin Risks** — CSRF threat model; SameSite cookies and anti-CSRF tokens; CORS misconfiguration; Distinguishing browser-based risks from general API access
- **130. Server-Side Request Forgery** — Risks from user-supplied URLs; Validating destinations and URL schemes; Blocking access to internal services and metadata endpoints; Redirects, DNS changes, and outbound network controls
- **131. Resource Exhaustion and Abuse** — Request size and execution limits; Rate limiting and concurrency controls; Costly queries and computational abuse; Protecting resource-intensive business operations
- **132. Secrets and Sensitive Data Protection** — Managing credentials and API secrets; Avoiding tokens and sensitive information in URLs; PII minimization and data exposure; Redaction in logs and error responses
- **133. Security Misconfiguration** — Debug modes and production configuration; CORS and security-header configuration; Default credentials and unused endpoints; Dependency and configuration reviews
- **134. Secure File Uploads and Downloads** — Content-type validation; File size and format limits; Safe storage and access-controlled downloads; Malicious file and path traversal risks
- **135. Webhook and External-Service Security** — Authenticating inbound webhooks; Signature verification and replay protection; Validating third-party responses; Restricting trust in external data
- **136. API Security Assessment** — Applying the OWASP API Security Top 10; Security-focused test cases; Vulnerability triage and remediation; Security review before release

### Module 15: API Contracts and Documentation (PDF lessons 137–145)

- **137. Why API Documentation Matters** — Developer experience; Discoverability and onboarding; Keeping documentation aligned with implementation
- **138. Introduction to OpenAPI** — OpenAPI document structure; Paths and operations; Parameters, request bodies, and responses; Components and reusable schemas
- **139. Writing OpenAPI Specifications** — YAML and JSON formats; Operation IDs, tags, and summaries; Request and response schemas; Required, nullable, and optional fields
- **140. Documenting Authentication and Errors** — Security schemes; Operation-level security requirements; Standard status codes; Shared error schemas and examples
- **141. Reusable OpenAPI Components** — Schema components and references; Reusable parameters and responses; Shared security schemes; Avoiding excessive schema duplication
- **142. API Documentation Interfaces** — Interactive API documentation; Request examples and response examples; Authentication within documentation tools; Publishing documentation safely
- **143. Contract-First API Development** — Designing the API before implementation; Reviewing schemas and endpoints; Generating server stubs and client SDKs; Mock servers and parallel frontend-backend work
- **144. Contract Validation and Drift Detection** — Validating OpenAPI documents; Comparing implementation against contract; Detecting undocumented behavior; Breaking-change checks in CI
- **145. API Reference and Developer Guides** — Quick-start documentation; Authentication setup instructions; Tutorials, examples, and troubleshooting; Changelog and migration guides

### Module 16: Testing and Quality Assurance (PDF lessons 146–157)

- **146. API Testing Fundamentals** — Functional and non-functional testing; Test environments and fixtures; Testable API contracts; Positive and negative test cases
- **147. Manual API Testing Tools** — curl and command-line HTTP clients; Graphical API clients; Headers, bodies, and authentication; Environments, variables, and reusable collections
- **148. Unit Testing** — Testing validation logic; Testing business rules; Testing error handling; Mocking external dependencies
- **149. Integration Testing** — Testing database integration; Testing routes and middleware; Testing authentication and authorization; Test databases and cleanup
- **150. End-to-End API Testing** — Testing complete request flows; Creating and updating dependent resources; Cross-endpoint workflows; Cleaning test data safely
- **151. Schema and Contract Testing** — Request validation tests; Response schema validation; Provider contract tests; Consumer-driven contract testing concepts
- **152. Authentication and Authorization Testing** — Unauthenticated request tests; Permission boundary tests; Object ownership tests; Token expiry and revocation tests
- **153. Boundary and Negative Testing** — Invalid types and malformed JSON; Missing fields and unexpected fields; Boundary values and unusually large inputs; Invalid states and duplicate requests
- **154. Concurrency and Idempotency Testing** — Repeated requests; Concurrent updates; Duplicate creation and payment-like operations; Optimistic concurrency conflicts
- **155. Performance and Load Testing** — Response latency measurement; Throughput and concurrent users; Stress and endurance testing; Interpreting bottlenecks and saturation
- **156. Fuzz, Property-Based, and Security Testing** — Generated input testing; Invariant-based testing; API security scanning; Handling test findings responsibly
- **157. Test Automation and Continuous Integration** — Running test suites automatically; Test reports and quality gates; Managing test secrets; Preventing regressions before release

### Module 17: Caching, Conditional Requests, and Performance (PDF lessons 158–168)

- **158. HTTP Caching Fundamentals** — Private and shared caches; Freshness and cache reuse; Cacheability of HTTP methods and responses; Caching versus application-level storage
- **159. Cache-Control Directives** — max-age and freshness lifetimes; no-cache , no-store , and private; public and shared-cache considerations; Caching sensitive or personalized data safely
- **160. ETags and Conditional Requests** — Entity tags and representation validators; If-None-Match; If-Match; 304 Not Modified and cache revalidation
- **161. Optimistic Concurrency Control** — Lost updates and conflicting writes; ETag-based update preconditions; Version columns and conditional mutations; Returning appropriate precondition failures
- **162. Response Compression and Payload Optimization** — Gzip and Brotli concepts; Compression overhead and trade-offs; Avoiding redundant fields; Choosing suitable response granularity
- **163. Database and Application Performance** — Query efficiency; Connection pools; Application-level caches; Avoiding redundant computation
- **164. API Latency and Throughput** — Measuring response times; Average and percentile latency; Network, application, and database delays; Bottleneck analysis
- **165. Efficient API Client Interactions** — Reducing unnecessary requests; Batching and bulk operations; Avoiding chatty resource interfaces; Client-side pagination and caching behavior
- **166. Asynchronous Processing for Performance** — Background job queues; Moving slow work outside request handling; Polling job status; Managing task state and failures
- **167. Connection and Timeout Management** — Client and server timeouts; Connection reuse; Cancellation and resource cleanup; Timeouts across dependency chains
- **168. Performance Profiling and Optimization** — Profiling route handlers; Identifying slow queries; Load-test-driven optimization; Measuring improvements against a baseline

### Module 18: Asynchronous APIs, Webhooks, and External Integrations (PDF lessons 169–178)

- **169. Long-Running Operations** — Recognizing operations that exceed request time limits; Returning 202 Accepted; Operation-status resources; Completion, failure, and cancellation states
- **170. Background Jobs and Task APIs** — Submitting jobs; Polling job status; Retrieving job results; Retry, expiry, and cleanup policies
- **171. Webhook Fundamentals** — Event-driven notifications; Registering webhook subscriptions; Event payload design; Delivery failures and retries
- **172. Webhook Authentication and Reliability** — Signature verification; Replay protection; Duplicate event handling; Retry schedules and dead-letter handling
- **173. Idempotent Event Processing** — Event identifiers; Deduplication; Ordering and out-of-order events; Safe event reprocessing
- **174. Integrating Third-Party REST APIs** — External API authentication; Request mapping and response parsing; Handling provider-specific errors; Managing credentials and quotas
- **175. Resilient External-Service Calls** — Timeout budgets; Retry policies and exponential backoff; Circuit breakers and bulkheads; Avoiding retry storms
- **176. Uploading and Downloading Files** — Multipart form data; Binary response bodies; Direct-to-storage upload patterns; Signed URLs and scoped access
- **177. Event Notifications and Callback URLs** — Callback registration; Delivery status and retry tracking; Validating callback destinations; Notification lifecycle management
- **178. Reliable Multi-Step Workflows** — Workflows spanning several services; Compensating actions and sagas; Partial failures; Reconciliation and recovery

### Module 19: API Versioning and Lifecycle Management (PDF lessons 179–187)

- **179. Why APIs Need Versioning** — Contract evolution; Client compatibility; Breaking and non-breaking changes
- **180. API Versioning Strategies** — URI path versioning; Query-parameter versioning; Header and media-type versioning; Trade-offs between approaches
- **181. Backward-Compatible Changes** — Adding optional request fields; Adding response properties; Changes to default behavior; Compatibility risks of enums and validation rules
- **182. Breaking Changes and Migration** — Renaming or removing fields; Changing types or semantics; Migrating clients to a new contract; Deprecation notices and migration windows
- **183. Deprecation and Sunset Planning** — Identifying affected clients; Announcing deprecations; Supporting parallel API versions; Retiring old endpoints safely
- **184. API Change Management** — Contract reviews; Automated breaking-change detection; Changelog maintenance; Release coordination
- **185. Data and Schema Evolution** — Database schema evolution; Expand-and-contract migrations; Mixed-version application instances; API and event schema compatibility
- **186. Maintaining Multiple API Versions** — Shared business logic across versions; Version-specific request and response mapping; Avoiding duplicated implementations; Monitoring usage of older versions
- **187. API Lifecycle Governance** — Design, preview, stable, and retired states; Release-readiness criteria; Support policies; Version ownership and lifecycle documentation

### Module 20: Rate Limiting, Reliability, and Resilience (PDF lessons 188–197)

- **188. Rate Limiting Fundamentals** — Why APIs need limits; Per-user, per-client, and per-IP policies; Fixed-window and sliding-window approaches; Token-bucket and leaky-bucket concepts
- **189. Implementing Rate Limits** — Limit configuration; Distributed counters; Burst allowance; Returning 429 Too Many Requests
- **190. Quotas and Usage Plans** — Daily and monthly quotas; Subscription-based limits; Usage metering; Quota reset and reporting
- **191. Retry-After and Backoff** — Interpreting retry guidance; Exponential backoff and jitter; Safe retries for different HTTP methods; Coordinating client and server retry policies
- **192. Idempotency Keys in Distributed Operations** — Key generation and scope; Storing operation results; Duplicate and concurrent key handling; Expiry and replay policy
- **193. Circuit Breakers and Fault Isolation** — Closed, open, and half-open states; Protecting unhealthy dependencies; Bulkheads and concurrency limits; Fallback behavior and its risks
- **194. Timeouts and Failure Budgets** — End-to-end time budgets; Propagating cancellation; Avoiding unlimited waits; Choosing suitable timeout policies
- **195. Graceful Degradation** — Identifying optional dependencies; Partial responses and reduced functionality; Fallback data; Communicating temporary service limitations
- **196. Availability and Recovery** — Health endpoints; Readiness and liveness checks; Graceful shutdown; Recovery after dependency failures
- **197. Consistency and Distributed Failures** — Eventual consistency concepts; Duplicate and delayed events; Reconciliation and retry safety; Communicating asynchronous completion

### Module 21: Deployment, Monitoring, and Operations (PDF lessons 198–209)

- **198. Development, Staging, and Production Environments** — Environment separation; Configuration differences; Safe test data and secrets; Production parity considerations
- **199. Preparing an API for Production** — Configuration validation; Disabling debug behavior; Validating required dependencies; Readiness checks and startup failures
- **200. Environment Variables and Secret Management** — Externalized configuration; Secret stores and restricted access; Secret rotation; Avoiding secrets in source control and logs
- **201. Containers and API Deployment** — Container images and runtime configuration; Exposed ports and process execution; Environment-specific settings; Container health checks
- **202. Reverse Proxies and Load Balancers** — Request routing; TLS termination; Forwarded headers and client IPs; Trusting proxy information safely
- **203. Domains, DNS, and TLS Deployment** — Domain configuration; HTTPS certificates; Certificate renewal; Redirects and secure transport
- **204. Continuous Integration and Deployment** — Automated builds and tests; Deployment pipelines; Environment-specific secrets; Approval and release checks
- **205. Deployment Strategies** — Rolling deployments; Blue-green deployments; Canary releases; Rollback and database compatibility
- **206. Logging and Correlation** — Structured logging; Request and trace identifiers; Log levels and actionable events; Redacting credentials and sensitive information
- **207. API Metrics and Monitoring** — Request rate, errors, and latency; Percentile response times; Dependency and database metrics; Dashboards and alert thresholds
- **208. Distributed Tracing** — Traces, spans, and trace context; Following requests across services; Identifying latency bottlenecks; OpenTelemetry concepts
- **209. Incident Response and Production Troubleshooting** — Diagnosing 4xx and 5xx errors; Investigating latency spikes; Incident communication and remediation; Post-incident reviews

### Module 22: Advanced API Design and Distributed Architecture (PDF lessons 210–220)

- **210. API Gateways** — Routing and reverse proxy behavior; Authentication and policy enforcement; Rate limits and request transformation; Gateway versus application responsibilities
- **211. Backend-for-Frontend and API Composition** — Client-specific API layers; Combining data from multiple services; Avoiding excessive backend coupling; BFF trade-offs and maintenance
- **212. Service-Oriented and Microservice APIs** — Service boundaries; Synchronous REST communication; Inter-service authentication; Managing distributed dependencies
- **213. Resource Modeling for Complex Domains** — Aggregate boundaries; State machines and domain invariants; Representing workflows; Modeling actions without arbitrary endpoint proliferation
- **214. Hypermedia and API Discoverability** — Links in representations; Relationship types and navigable resources; Hypermedia formats; Benefits and costs of hypermedia-driven clients
- **215. Content Negotiation and Specialized Representations** — Vendor media types; Representation variants; Representation metadata; Schema evolution through negotiated formats
- **216. HTTP Range Requests and Large Resources** — Range requests and partial content; 206 Partial Content; Resumable downloads; Storage-backed large-file delivery
- **217. Bulk APIs and Asynchronous Batching** — Bulk operation contracts; Per-item validation and results; Partial-success semantics; Large-scale batch job management
- **218. Long-Running Operations and Workflow Patterns** — Operation resource design; Polling versus notifications; Cancellation and timeout behavior; Durable workflow state and recovery
- **219. REST APIs and Alternative API Styles** — REST versus RPC-style HTTP APIs; REST versus GraphQL; REST versus gRPC; Choosing a communication style based on requirements
- **220. Distributed System Design Considerations** — Network partitions and timeouts; Duplicate requests and retries; Eventual consistency; Service ownership and failure isolation

### Module 23: Specialized REST API Patterns (PDF lessons 221–230)

- **221. Payment and Transaction APIs** — Modeling payment resources and state transitions; Idempotency for transaction creation; Handling pending and failed results; Verifying asynchronous payment notifications
- **222. E-commerce and Order APIs** — Products, carts, orders, and order items; Inventory reservation and concurrency; Order state transitions; Cancellation, refunds, and reconciliation
- **223. Multi-Vendor and Multi-Tenant APIs** — Tenant and supplier boundaries; Ownership and organization-level access; Scoped querying; Tenant isolation tests
- **224. Search and Discovery APIs** — Query contracts; Filters, sorting, and facets; Cursor pagination; Search indexing versus source-of-truth data
- **225. Media and File APIs** — Metadata resources and binary content; Upload session design; Authorization and signed download links; Content processing and asynchronous status
- **226. Notification APIs** — Notification resources; Delivery and read states; Preference and subscription management; Duplicate notification prevention
- **227. Reporting and Analytics APIs** — Aggregated data resources; Asynchronous report generation; Export formats and downloads; Access control and query limits
- **228. Administrative APIs** — Privileged operations; Audit events; Approval and confirmation workflows; Administrative access separation
- **229. Geospatial and Time-Based APIs** — Coordinates and location formats; Distance and geographic filters; Time zones and time intervals; Time-based pagination and query boundaries
- **230. API Integration Patterns** — Adapters for external providers; Mapping provider data to internal models; Provider errors and unavailable dependencies; Idempotent synchronization jobs

### Module 24: API Governance, Teamwork, and Professional Practices (PDF lessons 231–240)

- **231. API Design Guidelines** — Naming and consistency standards; Error, pagination, and authentication conventions; Resource and schema review; Enforcing standards across teams
- **232. API Design Reviews** — Reviewing endpoint catalogs; Reviewing request and response contracts; Identifying ambiguity and edge cases; Recording decisions and trade-offs
- **233. Version Control and Collaboration** — Git workflows; Code review; Branches, pull requests, and merge conflicts; Coordinating contract and implementation changes
- **234. API Governance and Inventory** — Maintaining an API registry; Cataloging endpoints and versions; Identifying abandoned and shadow APIs; Ownership and responsibility
- **235. Privacy, Compliance, and Data Governance** — Data minimization; Retention and deletion policies; Handling personal and sensitive data; Auditability and applicable legal requirements
- **236. Accessibility and Developer Experience** — Clear documentation language; Predictable error messages; Consistent onboarding; Making API behavior easy to discover
- **237. Cost Management** — Infrastructure and database costs; Request-volume and storage costs; Expensive operations and quotas; Observability and cost attribution
- **238. Technical Debt and API Maintenance** — Identifying design inconsistencies; Refactoring without breaking clients; Dependency and framework upgrades; Long-term ownership and support
- **239. API Release Readiness** — Functional and contract tests; Security and performance checks; Documentation and operational readiness; Release criteria and rollback planning
- **240. Professional API Engineering Review** — Design trade-offs and decision records; Reviewing reliability and security; Assessing maintainability and extensibility; Final API quality checklist

## PDF sections outside the 240 numbered core lessons

- **Section A — Course Overview:** retained in `course.json` as audience, prerequisites, learning outcomes, scope, version assumptions and the 80–140-hour estimated range; this draft uses 120 hours as its working estimate.
- **Section C — Exercises:** 30 separate exercise files are mapped to appropriate lesson IDs and use grader types supported by the existing CodeLeaf importer. Protected reference solutions are in separate solution files.
- **Section D — Projects:** all ten progressive projects plus the multi-vendor commerce capstone are separate project briefs. Each has milestones, testing/acceptance criteria, and a rubric totaling 100; starter files use formats supported by the existing download endpoint.
- **Section E — Advanced and optional topics:** retained in `references/specializations.json` as optional specialization outlines; the current course importer has no distinct specialization-track entity, so these are reference-only and not yet rendered as separate platform tracks.
- **Section F — Learning path:** retained in `course.json` as an eight-stage roadmap with module groupings and checkpoints.
- **Section G — Coverage checklist and standards references:** mapped to the reference index, lesson references, status notes and this coverage report.

## Standards/version notes and corrections

- The PDF’s HTTP semantics coverage is taught against RFC 9110, and caching against RFC 9111.
- Problem Details uses RFC 9457, the current specification that supersedes RFC 7807; older RFC 7807-only examples should be reviewed before release.
- OAuth 2.0 security lessons reference RFC 9700 (OAuth 2.0 Security Best Current Practice) rather than relying solely on older flow recommendations.
- The official OpenAPI Initiative site listed OAS 3.2.1 at the time of preparation (2026-10-19). The draft mostly uses OpenAPI 3.1.2-compatible fragments to maximize current tooling interoperability. Before publication, validate examples with the specific toolchain and state the chosen version explicitly.
- REST is taught as an architectural style, distinct from HTTP and from common REST-style JSON endpoints. The course does not claim a typical JSON API necessarily satisfies every REST constraint.
- No syllabus main lesson was deliberately excluded. Corrections/compatibility choices above are explicit, and optional specialization topics are retained as reference-only rather than presented as complete separate tracks.

## Official references

- [RFC 9110 — HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110.html) — IETF / RFC Editor (checked 2026-10-19).
- [RFC 9111 — HTTP Caching](https://www.rfc-editor.org/rfc/rfc9111.html) — IETF / RFC Editor (checked 2026-10-19).
- [RFC 9457 — Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457.html) — IETF / RFC Editor (checked 2026-10-19).
- [RFC 9700 — OAuth 2.0 Security Best Current Practice](https://www.rfc-editor.org/rfc/rfc9700.html) — IETF / RFC Editor (checked 2026-10-19).
- [OpenAPI Specification v3.2.1](https://spec.openapis.org/oas/v3.2.1.html) — OpenAPI Initiative (checked 2026-10-19).
- [OpenAPI Specification index and versions](https://spec.openapis.org/oas/) — OpenAPI Initiative (checked 2026-10-19).
- [OWASP API Security Top 10 (2023)](https://owasp.org/API-Security/editions/2023/en/0x00-header/) — OWASP Foundation (checked 2026-10-19).
- [OWASP REST Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html) — OWASP Foundation (checked 2026-10-19).
- [RFC 3986 — Uniform Resource Identifier (URI): Generic Syntax](https://www.rfc-editor.org/rfc/rfc3986.html) — IETF / RFC Editor (checked 2026-10-19).
- [RFC 8259 — The JavaScript Object Notation (JSON) Data Interchange Format](https://www.rfc-editor.org/rfc/rfc8259.html) — IETF / RFC Editor (checked 2026-10-19).
- [RFC 6750 — The OAuth 2.0 Authorization Framework: Bearer Token Usage](https://www.rfc-editor.org/rfc/rfc6750.html) — IETF / RFC Editor (checked 2026-10-19).
- [OpenID Connect Core 1.0](https://openid.net/specs/openid-connect-core-1_0.html) — OpenID Foundation (checked 2026-10-19).
- [Microsoft REST API Guidelines](https://github.com/microsoft/api-guidelines/blob/vNext/Guidelines.md) — Microsoft (checked 2026-10-19).
- [HTTP Status Code Registry](https://www.iana.org/assignments/http-status-codes/http-status-codes.xhtml) — IANA (checked 2026-10-19).
- [RFC 6585 — Additional HTTP Status Codes](https://www.rfc-editor.org/rfc/rfc6585.html) — IETF / RFC Editor (checked 2026-10-19).
- [RFC 8594 — The Sunset HTTP Header Field](https://www.rfc-editor.org/rfc/rfc8594.html) — IETF / RFC Editor (checked 2026-10-19).
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/) — OWASP Foundation (checked 2026-10-19).
- [OpenTelemetry Documentation](https://opentelemetry.io/docs/) — Cloud Native Computing Foundation project (checked 2026-10-19).
- [GraphQL Specification](https://spec.graphql.org/) — GraphQL Foundation (checked 2026-10-19).
- [gRPC Documentation](https://grpc.io/docs/) — gRPC project (checked 2026-10-19).
- [CloudEvents Specification](https://cloudevents.io/) — Cloud Native Computing Foundation project (checked 2026-10-19).
- [Google SRE Books](https://sre.google/books/) — Google (checked 2026-10-19).
- [OWASP Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/) — OWASP Foundation (checked 2026-10-19).
