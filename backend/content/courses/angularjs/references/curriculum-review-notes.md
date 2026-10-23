# AngularJS Curriculum Review Notes

**Source:** `AngularJS(1).pdf` (37 pages, all pages rendered and text-extracted for review). **Course status:** draft; generated content requires technical/editorial review before publication.

## Version and lifecycle notes

- The PDF itself states that AngularJS officially reached end of support in January 2022; the official AngularJS documentation landing page confirms the framework is unsupported. This warning is repeated in course metadata and lessons.
- AngularJS 1.x and modern Angular are treated as separate products. `angular.dev` is listed only for comparison/migration research, not as an AngularJS API source.
- The lessons assume the archived AngularJS 1.8.4 documentation snapshot as a reference point, not that every existing application is on 1.8.4. Verify the exact app version and lockfile before changing code.
- Browser-runner execution is not claimed. Examples are marked `static-validation`; the existing CodeLeaf FastAPI process is not used to execute arbitrary learner code.

## PDF syllabus coverage

### Module 1: Introduction to AngularJS

- **1. Introduction to AngularJS** — What AngularJS is; AngularJS as a JavaScript framework; The meaning of AngularJS 1.x; AngularJS versus plain JavaScript; AngularJS versus jQuery-based development

- **2. History and Evolution of AngularJS** — Origins of AngularJS; Major AngularJS 1.x milestones; Introduction of component-based development; AngularJS support lifecycle; Understanding legacy framework documentation

- **3. Why AngularJS Was Developed** — Limitations of traditional static webpages; Dynamic user interfaces; Data-driven web applications; Separation of application logic and presentation; Declarative programming in the browser

- **4. AngularJS Use Cases** — Interactive dashboards; Administrative applications; Form-heavy web applications; Data-driven portals; Existing enterprise applications; Situations where AngularJS is unsuitable

- **5. Advantages and Limitations of AngularJS** — Data binding; Dependency injection; Reusable application components; Testing support; Legacy dependencies and maintenance risks; Browser compatibility and modern security expectations

- **6. AngularJS Architecture Overview** — Model, View, and Controller concepts; Model-View-Whatever terminology; Templates and expressions; Scopes and controllers; Services and dependency injection; Directives and the DOM; Application bootstrap and the digest cycle

- **7. AngularJS and Modern Angular** — AngularJS versus modern Angular; JavaScript-based AngularJS applications; TypeScript-oriented modern Angular development; Differences in components and templates; Differences in dependency injection; Differences in routing and testing; Choosing the appropriate learning path

- **8. AngularJS Prerequisites and Learning Resources** — Required HTML knowledge; Required CSS knowledge; Required JavaScript knowledge; Understanding JSON and HTTP; Using official API documentation; Reading framework source and error messages

### Module 2: Development Environment and First Application

- **9. Setting Up the Development Environment** — Choosing a code editor; Organizing a frontend project; Using a web browser for development; Opening browser developer tools; Setting up a local development server

- **10. Installing AngularJS** — Including AngularJS in an HTML document; Understanding the AngularJS script file; Using a pinned framework version; Including AngularJS through npm; Understanding the legacy AngularJS package ecosystem; Managing dependencies in an existing project

- **11. Creating Your First AngularJS Application** — Creating the HTML entry page; Loading the AngularJS library; Creating an AngularJS module; Connecting a module to an HTML page; Writing a simple controller; Displaying dynamic data in the browser

- **12. AngularJS Application Bootstrap** — What application bootstrap means; Automatic bootstrap using ng-app; Choosing the application root element; Manual bootstrap using angular.bootstrap(); Configuring strict dependency injection; Common bootstrap errors

- **13. AngularJS Project Structure** — Organizing application entry files; Separating modules, controllers, and services; Organizing templates; Feature-based folder structures; Separating shared and feature-specific code; Naming conventions for AngularJS files

- **14. Understanding the AngularJS Global API** — The global angular object; angular.module(); angular.bootstrap(); angular.copy(); angular.equals(); angular.isDefined() and related utility methods; angular.element(); Appropriate use of global utility methods

### Module 3: Modules, Application Configuration, and Initialization

- **15. Introduction to AngularJS Modules** — What a module represents; Creating a module; Retrieving an existing module; Declaring module dependencies; Registering application components; Understanding the core ng module

- **16. Module Dependencies** — Loading dependent modules; Dependency ordering and initialization; Built-in AngularJS modules; Third-party module dependencies; Missing module errors; Avoiding circular dependency problems

- **17. Application Configuration** — The configuration phase; Registering configuration blocks; Working with providers during configuration; Setting route configuration; Configuring HTTP defaults; Strict dependency injection configuration

- **18. Application Run Blocks** — The run phase; Registering run blocks; Injecting available services into run blocks; Application initialization tasks; Differences between configuration and run phases; Avoiding excessive startup logic

### Module 4: Templates, Expressions, and Data Binding

- **19. AngularJS Templates** — What an AngularJS template is; Static HTML and dynamic templates; Template expressions; Binding values into HTML; Template readability and organization; Separating presentation from application logic

- **20. AngularJS Expressions** — Expression syntax; Accessing variables and object properties; Working with arrays and array indexes; Arithmetic expressions; Comparison and logical expressions; Conditional expressions; Expressions versus ordinary JavaScript statements; Handling undefined and missing values

- **21. Interpolation** — Double-curly-brace interpolation; Displaying string and numeric values; Interpolating object properties; Combining interpolation with static text; Interpolation inside HTML attributes; When interpolation is not appropriate; Preventing untrusted content from being interpreted as HTML

- **22. Data Binding Fundamentals** — What data binding means; Model-to-view updates; View-to-model updates; Two-way data binding; One-time binding with ::; Binding values in nested structures; Common binding mistakes

- **23. Model and View Updates** — Understanding the application model; Modifying bound values; Updating arrays and objects; Rendering changed values; Understanding the digest cycle at a high level; External events and AngularJS-aware updates

- **24. Conditional and Repeated Rendering** — Using ng-if; Using ng-show and ng-hide; Using ng-switch; Repeating elements with ng-repeat; Using $index and repetition metadata; Empty lists and conditional content; Using track by with repeated elements; Choosing the correct rendering directive

### Module 5: Scopes, Controllers, and Components

- **25. Understanding AngularJS Scopes** — What a scope represents; The root scope; Scope properties and methods; Parent and child scopes; Scope inheritance; Scope isolation; Scope lifetime and destruction

- **26. Scope Inheritance and Data Access** — Reading inherited properties; Writing to inherited properties; Primitive values and object references; Shadowing inherited properties; Nested controller behavior; Avoiding scope-related bugs

- **27. Controllers** — The role of a controller; Registering controllers; Injecting dependencies into controllers; Managing view-specific state; Defining controller methods; Sharing reusable logic through services; Avoiding overly large controllers

- **28. Controller Scope with $scope** — Exposing data through $scope; Defining functions on $scope; Listening to scope events; $watch() and its purpose; Cleaning up scope listeners; Limitations of scope-heavy designs

- **29. The controllerAs Pattern** — Understanding controller aliases; Using this in controllers; Exposing data through controller instances; Controller aliases in templates; Nested controller aliases; Comparing controllerAs and $scope

- **30. AngularJS Components** — What an AngularJS component is; Registering components using .component(); Component configuration objects; Component templates; Component controllers; Using $ctrl in component templates; Component lifecycle hooks; Organizing applications around components

- **31. Component Bindings** — One-way input bindings using <; Two-way bindings using = in applicable legacy designs; Callback bindings using &; String attribute bindings using @; Optional bindings; Passing objects and arrays to components; Component communication patterns; Designing clear component interfaces

- **32. Component Lifecycle and Reusability** — $onInit(); $onChanges(); $doCheck(); $postLink(); $onDestroy(); Managing component resources; Lifecycle-aware initialization and cleanup; Components as route templates

### Module 6: AngularJS Directives

- **33. Introduction to Directives** — What a directive does; Built-in versus custom directives; Directive naming conventions; Element, attribute, class, and comment directives; The restrict option; Directive composition and reuse

- **34. Common Built-In Directives** — ng-app; ng-init and why application logic generally belongs elsewhere; ng-bind; ng-bind-template; ng-click; ng-dblclick; ng-mouseover and related events; ng-class; ng-style; ng-attr-*

- **35. Structural Directives** — ng-if; ng-repeat; ng-switch and related directives; ng-include; ng-view; ng-transclude; Element creation and removal; Scope behavior of structural directives

- **36. Attribute and Behavior Directives** — ng-disabled; ng-readonly; ng-required; ng-checked; ng-selected; ng-href; ng-src; ng-model; ng-model-options

- **37. Creating Custom Directives** — Registering a directive with .directive(); Directive definition objects; Directive templates and template URLs; The scope option; Isolated scope; Attribute observation with $observe(); Linking functions; Configuring directive priority

- **38. Directive Scope and Bindings** — Shared scope; Child scope; Isolated scope; @, =, and & bindings; Optional isolated-scope bindings; Passing callbacks to directives; Directive communication; Avoiding unintended scope conflicts

- **39. Directive Compilation and Linking** — The $compile service; The compile function; The pre link function; The post link function; Controller requirements; Parent and ancestor controller access; Directive priority and terminal behavior; When compilation and linking are necessary

- **40. Advanced Directive Design** — Reusable form-control directives; Integrating directives with ngModel; Implementing parsers and formatters; Implementing custom validators; Controlling DOM event listeners; Managing event listener cleanup; Avoiding unnecessary direct DOM manipulation; When a component is preferable to a directive

### Module 7: Filters and Data Formatting

- **41. Introduction to Filters** — What a filter does; Filter syntax in templates; Filter arguments; Chaining filters; Filters in JavaScript through $filter; Appropriate separation of formatting and business logic

- **42. Built-In Filters** — uppercase; lowercase; currency; number; date; json; limitTo; orderBy; filter for collection filtering

- **43. Custom Filters** — Registering a custom filter; Writing a filter transformation function; Accepting filter arguments; Handling null and undefined inputs; Creating reusable display filters; Testing custom filters; Avoiding expensive computations in frequently evaluated filters

- **44. Collection Filtering and Sorting** — Searchable lists; Filtering by object properties; Case-sensitive and case-insensitive matching; Sorting by a property; Reverse sort order; Multiple sorting criteria; Search, sort, and pagination patterns; Performance considerations for large collections

### Module 8: Forms, Input Controls, and Validation

- **45. Introduction to AngularJS Forms** — The role of forms in AngularJS; The form and ngForm directives; Form and field names; ng-model and form controls; Nested forms and their limitations; Form state and control state

- **46. Text and Number Inputs** — Text input fields; Password inputs; Email inputs; Number inputs; URL inputs; Telephone inputs; Date and time inputs; Checkboxes and radio buttons; Select menus and textareas

- **47. Understanding ngModel** — Binding an input to a model; Model and view values; Formatting user-entered data; Parsing view values; $viewValue and $modelValue; $setViewValue() and $render(); ngModelOptions; Debouncing model updates

- **48. Form Validation Fundamentals** — Built-in required validation; Minimum and maximum length; Minimum and maximum numeric values; Pattern validation; Email and number validity; Form validity and field validity; The $error object; Displaying field-specific validation messages

- **49. Form Interaction States** — $pristine and $dirty; $touched and $untouched; $valid and $invalid; $submitted; Resetting forms; Controlling submission buttons; Styling inputs according to validation states; Preventing duplicate submissions

- **50. Custom Form Validation** — Creating custom validators; Using $validators; Using $asyncValidators; Cross-field validation; Password confirmation validation; Remote validation; Reusable validation logic; Handling asynchronous validation failures

- **51. Form Submission and Data Handling** — Handling submission with ng-submit; Collecting form data; Preparing submission payloads; Showing loading states; Displaying server-side validation errors; Handling successful submission; Clearing forms after submission; Protecting against accidental duplicate requests

### Module 9: Dependency Injection and Reusable Logic

- **52. Introduction to Dependency Injection** — What dependency injection means; Why dependency injection matters; Injectors and injectable components; Dependency registration; Resolving dependencies; Dependency injection and testability

- **53. AngularJS Dependency Injection Syntax** — Implicit annotation; Inline array annotation; The $inject property; Minification and dependency names; Strict dependency injection mode; Diagnosing unknown provider errors

- **54. AngularJS Services** — What an AngularJS service is; Using built-in services; Sharing logic across controllers; Service instances and application lifetime; Separating business logic from view logic; Reusable application utilities

- **55. Creating Services with .service()** — Registering a service constructor; Injecting dependencies into a service; Defining service methods; Storing shared application state; Organizing service responsibilities; Testing service constructors

- **56. Creating Services with .factory()** — Registering a factory; Returning objects from a factory; Returning functions and utilities; Factory closures and private state; Comparing .factory() and .service(); Choosing an appropriate registration method

- **57. Providers, Values, and Constants** — Understanding providers; Creating custom providers; Configuring providers; Using .value(); Using .constant(); Configuring reusable dependencies; Differences between constants, values, factories, services, and providers

- **58. Advanced Dependency Injection Patterns** — Injecting dependencies into directives; Injecting dependencies into filters; Injecting dependencies into configuration blocks; Injecting dependencies into run blocks; Avoiding circular dependencies; Designing services with minimal coupling; Handling initialization dependencies

### Module 10: HTTP, REST APIs, and Data Integration

- **59. Introduction to HTTP in AngularJS** — HTTP request and response fundamentals; Request methods; Status codes; Request and response headers; JSON request and response bodies; Same-origin rules and CORS basics

- **60. The $http Service** — Making GET requests; Making POST requests; Making PUT and PATCH requests; Making DELETE requests; Configuring request headers; Setting request parameters; Handling responses; Handling request errors

- **61. Promises and Asynchronous Operations** — Introduction to asynchronous programming; Promises in JavaScript; The $q service; Resolving and rejecting promises; Promise chaining; Coordinating multiple requests; Handling asynchronous errors; Avoiding unnecessary nested callbacks

- **62. Data Services and Repository Patterns** — Moving HTTP logic out of controllers; Centralized API services; Separating API logic from UI logic; Creating reusable CRUD methods; Transforming API responses; Handling empty and missing responses; Centralizing error handling; Designing mockable data-access layers

- **63. The $resource Service** — Introduction to ngResource; Adding the ngResource module; Defining REST resource objects; Query and get operations; Create, update, and delete operations; Resource parameters and URL configuration; Comparing $resource and $http; Limitations and maintenance of legacy integrations

- **64. Loading States, Caching, and Error Feedback** — Tracking request progress; Loading indicators; Empty-state messages; Retry behavior; Request cancellation where supported; Using $cacheFactory; Avoiding duplicate requests; Informing users about recoverable failures

### Module 11: Routing and Single-Page Applications

- **65. Introduction to Single-Page Applications** — What an SPA is; Client-side versus server-side navigation; URL management; Route-based views; Browser history; Deep linking

- **66. AngularJS Routing with ngRoute** — Installing or including angular-route; Declaring the ngRoute dependency; Configuring $routeProvider; Defining routes with .when(); Displaying route templates through ng-view; Defining a fallback route; Route template URLs; Route configuration errors

- **67. Route Parameters and Navigation** — Path parameters; Query parameters; $routeParams; $location; Hash-based navigation; HTML5 mode and URL configuration; Browser back and forward navigation; Handling invalid routes

- **68. Advanced Route Configuration** — Route-specific controllers; Component-based routes; Route resolves; Loading data before displaying a route; Handling rejected route resolves; Route change events; Route reloads; Route-specific page titles

- **69. Route Protection and Navigation UX** — Authentication state and route access; Redirecting unauthenticated users; Client-side authorization checks; Preserving the intended destination; Route loading indicators; Unsaved form-change warnings; Access control must also be enforced by the server

### Module 12: Events, Timing, and Framework Internals

- **70. AngularJS Event Handling** — DOM events and AngularJS events; Handling click and input events; Broadcasting scope events; Emitting events upward; Listening with $on(); Removing event listeners; Designing event-driven communication; Avoiding excessive use of global scope events

- **71. The Digest Cycle** — What the digest cycle does; Watchers and expressions; $digest(); $apply(); $eval() and $evalAsync(); $applyAsync(); Interaction with browser events; Diagnosing updates that do not appear

- **72. Watchers and Change Detection** — Registering a watcher with $watch(); Collection watching with $watchCollection(); Deep equality watching; Watch expressions and listener functions; Watcher deregistration; Watchers and performance; Avoiding side effects within watchers

- **73. Timers and Scheduling** — The $timeout service; Cancelling pending timeouts; The $interval service; Cancelling intervals; Differences from native timers; Scheduling callbacks within the framework lifecycle; Cleanup during scope destruction

- **74. Understanding Compilation and Rendering** — The AngularJS compilation process; Template compilation; Directive linking; Interpolation watchers; DOM updates; Scope creation and teardown; Common rendering performance bottlenecks

### Module 13: Animation, Accessibility, and DOM Integration

- **75. Animations with ngAnimate** — Installing and configuring ngAnimate; Animation hooks on AngularJS directives; CSS transitions; CSS keyframe animations; JavaScript-based animations; Enter and leave animations; Animation performance; Respecting reduced-motion preferences

- **76. DOM Manipulation** — AngularJS and the browser DOM; The angular.element() API; Integrating external JavaScript widgets; Directive-based DOM integration; Avoiding conflicting DOM ownership; Event listener management; Cleanup when DOM elements are removed

- **77. Accessibility with ngAria** — What web accessibility means; The ngAria module; ARIA attributes and directives; Accessible interactive controls; Keyboard navigation; Labels and accessible form errors; Focus management during navigation; Screen-reader testing and manual verification

- **78. Touch and Mobile Browser Support** — The ngTouch module; Touch events and gestures; Swipe-related features; Mobile form usability; Responsive interface patterns; Testing on touch-capable devices; Legacy dependency considerations

### Module 14: External Modules, Cookies, and HTML Sanitization

- **79. Managing Third-Party Modules** — Finding and evaluating AngularJS modules; Declaring external dependencies; Dependency version management; Compatibility with AngularJS 1.x; Checking package maintenance status; Replacing abandoned dependencies; Auditing third-party code

- **80. Cookies with ngCookies** — Introduction to the ngCookies module; Reading cookies with $cookies; Setting and removing cookies; Cookie options and expiration; Cookie size and storage limitations; Secure cookie configuration; Avoiding storage of sensitive application secrets

- **81. HTML Sanitization with ngSanitize** — Introduction to the ngSanitize module; Sanitizing untrusted HTML; Understanding the $sanitize service; Using the linky filter; Safe versus unsafe HTML rendering; Understanding $sce and trust contexts; Why trusting arbitrary user-supplied HTML is dangerous

- **82. Template Loading and Inclusion** — Using ng-include; Loading templates from URLs; Template URL organization; Template caching concepts; Handling missing templates; Template reuse and maintainability; Avoiding unsafe dynamic template construction

### Module 15: Testing and Quality Assurance

- **83. Introduction to AngularJS Testing** — Why automated testing matters; Unit, integration, and end-to-end tests; Testable application architecture; Mocking dependencies; Deterministic tests; Testing legacy code safely

- **84. JavaScript Testing Fundamentals** — Assertions and test expectations; Test suites and test cases; Setup and teardown hooks; Testing asynchronous behavior; Test doubles, stubs, and spies; Organizing test files

- **85. Unit Testing with AngularJS Mocks** — The ngMock module; Loading modules into tests; Using module() and inject() in the test environment; Injecting services into tests; Understanding $httpBackend; Flushing mocked HTTP requests; Testing $timeout and $interval; Isolating dependencies between tests

- **86. Testing Controllers and Components** — Testing controller behavior; Testing controller-as patterns; Testing component initialization; Testing component inputs and outputs; Testing lifecycle behavior; Testing event handlers; Verifying error handling; Testing boundary conditions

- **87. Testing Services, Filters, and Directives** — Service unit tests; Factory tests; Custom filter tests; Directive compilation in tests; Testing directive bindings; Form validation tests; Testing asynchronous services; Testing cleanup and resource management

- **88. End-to-End Testing** — Browser-driven testing concepts; Planning user journeys; Testing navigation; Testing form submission; Testing API-driven workflows; Handling asynchronous page updates; Isolating test data; Maintaining legacy end-to-end test suites

- **89. Testing Strategy and Coverage** — Unit-test coverage; Integration testing boundaries; Regression testing; Smoke tests; Testing application errors; Continuous integration concepts; Reducing flaky tests; Interpreting coverage reports

### Module 16: Debugging and Troubleshooting

- **90. Browser Developer Tools** — Using the browser console; Inspecting HTML and CSS; Debugging JavaScript; Using breakpoints; Inspecting network requests; Inspecting local storage and cookies; Diagnosing loading and caching issues

- **91. Common AngularJS Errors** — Unknown provider errors; Missing module errors; Controller registration errors; Undefined values in templates; Incorrect dependency injection annotations; Circular dependencies; Compilation errors; Non-assignable binding errors

- **92. Data Binding and Scope Problems** — Bindings that fail to update; Incorrect scope inheritance; Incorrect controller aliases; Digest-cycle conflicts; Incorrect watcher behavior; Asynchronous updates outside AngularJS; Incorrect component bindings

- **93. Network and Routing Problems** — Diagnosing failed HTTP requests; Understanding API status codes; Diagnosing CORS issues; Missing templates; Incorrect route definitions; URL and history configuration; Server fallback configuration for SPA routes

- **94. Systematic Troubleshooting** — Reproducing a bug consistently; Isolating the smallest failing example; Reading AngularJS error documentation; Inspecting dependency versions; Writing a regression test; Documenting root causes and resolutions

### Module 17: Security and Privacy

- **95. AngularJS Security Fundamentals** — Client-side versus server-side security; Understanding the application threat model; Untrusted inputs and output contexts; Defense in depth; Legacy dependency risk; Security maintenance limitations after framework end of support

- **96. Cross-Site Scripting (XSS)** — What XSS is; Safe text interpolation; Handling HTML supplied by users; Understanding sanitization; Safe template design; Reviewing $sce usage; Avoiding arbitrary trust declarations; Testing output encoding and sanitization

- **97. Cross-Site Request Forgery and Authentication** — What CSRF is; Cookie-based authentication risks; CSRF tokens and server-side validation; Session expiration; Authentication state in the frontend; Redirect and route-guard limitations; Why frontend checks cannot replace backend authorization

- **98. HTTP and Browser Security** — HTTPS requirements; Secure handling of authentication data; Security-related HTTP headers; Content Security Policy concepts; CORS configuration fundamentals; Cookie security attributes; Handling confidential information in errors and logs

- **99. Secure Application Maintenance** — Dependency inventory; Reviewing known vulnerabilities; Removing unused packages; Avoiding unsupported security assumptions; Protecting user-submitted data; Security regression testing; Establishing a migration or retirement plan

### Module 18: Performance and Optimization

- **100. AngularJS Performance Fundamentals** — Rendering and digest-cycle costs; Watcher count; Large lists and repeated elements; Excessive template expressions; Unnecessary DOM manipulation; Measuring before optimizing

- **101. Optimizing Data Binding** — One-time bindings; Reducing unnecessary watchers; Avoiding complex template expressions; Choosing between $watch() and $watchCollection(); Avoiding expensive filter computations; Using stable collection identities; Cleaning up watchers and listeners

- **102. Optimizing API Requests** — Eliminating duplicate requests; Caching read-only data; Debouncing search requests; Reducing unnecessary response payloads; Handling concurrent requests; Avoiding sequential requests where dependencies do not require them; Measuring API latency

- **103. Optimizing Templates and Assets** — Reusing component templates; Template caching; Minifying production JavaScript and CSS; Managing browser caching; Reducing initial asset payloads; Optimizing image delivery; Understanding source maps in production builds

- **104. Profiling and Performance Testing** — Browser performance tools; Measuring rendering and interaction latency; Identifying slow JavaScript operations; Profiling repeated list rendering; Detecting memory leaks; Establishing performance baselines; Verifying improvements with repeatable measurements

### Module 19: Application Architecture and Code Quality

- **105. Structuring a Maintainable AngularJS Application** — Feature-based organization; Separation of concerns; Controllers versus components; Services for shared logic; Shared UI components; Avoiding duplicated business logic; Establishing clear module boundaries

- **106. Component-Based Architecture** — Breaking pages into components; Defining component responsibilities; Designing one-way input flows; Communicating through callback bindings; Managing shared application state; Building reusable interface patterns; Preparing component boundaries for migration

- **107. Code Quality and Maintainability** — Naming conventions; Consistent file organization; Avoiding large controllers; Avoiding tightly coupled services; Documenting public interfaces; Linting legacy JavaScript; Refactoring duplicated code; Maintaining a consistent style guide

- **108. Error Handling and Logging** — Centralized error-handling concepts; HTTP failure handling; The $exceptionHandler service; Logging application errors; User-friendly error messages; Avoiding sensitive information in logs; Distinguishing recoverable and unrecoverable errors

- **109. State Management Patterns** — Local component state; Shared service state; Route-level data loading; Synchronizing state with URLs; Managing cached server data; Avoiding hidden state dependencies; Documenting ownership of shared state

### Module 20: Build Tools, Deployment, and Production Maintenance

- **110. Managing Project Dependencies** — Understanding package manifests; Working with npm in legacy projects; Pinning dependency versions; Lockfiles and repeatable installation; Recognizing deprecated packages; Evaluating dependency updates; Keeping development and production dependencies separate

- **111. Development and Build Workflows** — Static development servers; JavaScript linting; Automated tests in a build pipeline; Asset bundling concepts; JavaScript and CSS minification; Environment-specific configuration; Build artifact verification

- **112. Deploying an AngularJS Application** — Serving the built application; Configuring static hosting; Configuring SPA route fallback; Handling asset paths; HTTPS configuration; Environment variables and public configuration; Checking production network requests; Smoke testing a deployed release

- **113. Production Monitoring and Reliability** — Client-side error monitoring; Logging and diagnostics; Tracking failed API calls; Monitoring application performance; Managing browser compatibility issues; Release and rollback planning; Incident documentation

- **114. Maintaining Existing AngularJS Applications** — Auditing the current codebase; Inventorying routes and features; Identifying third-party dependencies; Prioritizing defects and security risks; Establishing regression tests; Documenting undocumented behavior; Managing technical debt; Deciding whether to maintain, migrate, or retire the application

### Module 21: Legacy Modules and Specialized APIs

- **115. The Core ng Module** — Core directives; Core services; Core filters; Global framework APIs; Discovering functionality in API documentation

- **116. Additional Official AngularJS Modules** — ngRoute; ngAnimate; ngAria; ngCookies; ngMessages; ngResource; ngSanitize; ngTouch; ngMock

- **117. The $parse and $interpolate Services** — Understanding $parse; Evaluating supported AngularJS expressions; Using $interpolate; Interpolation delimiters and expressions; Appropriate use in custom directives; Security considerations when handling expressions

- **118. The $compile Service** — Compilation of DOM templates; Compiling directive-bearing content; Linking compiled content to a scope; Managing compiled elements; Handling linked-element cleanup; Risks of arbitrary dynamic template compilation

- **119. Caching and Utility Services** — $cacheFactory; $log; $window; $document; $location; $anchorScroll; $filter; Appropriate abstraction through application services

- **120. Legacy Ecosystem Evaluation** — Assessing compatibility before adopting a package; Evaluating community-maintained extensions; Recognizing discontinued libraries; Replacing obsolete UI dependencies; Managing AngularJS Material legacy dependencies; Documenting unsupported features; Reducing dependence on unmaintained components

### Module 22: Migration and Modernization

- **121. Introduction to AngularJS Migration** — Why legacy applications need modernization; Maintenance versus migration; Identifying migration constraints; Assessing application complexity; Establishing a baseline of features and tests; Defining measurable migration goals

- **122. Preparing an AngularJS Application for Migration** — Refactoring controllers into components; Separating templates from business logic; Moving reusable logic into services; Reducing direct DOM manipulation; Removing unnecessary scope inheritance; Improving dependency injection annotations; Adding tests around critical behavior

- **123. Component-Based Refactoring** — Replacing controller-heavy views with components; Defining clear component inputs and outputs; Using lifecycle hooks consistently; Isolating feature boundaries; Reducing implicit global state; Preparing services for reuse; Building migration-friendly interfaces

- **124. Migration Strategies** — Incremental modernization; Rewriting an entire application; Coexisting legacy and modern application sections; Route-by-route migration planning; Shared API contracts; Data consistency across migrated features; Rollback and release strategies

- **125. AngularJS and Modern Angular Concepts** — Structural differences between the frameworks; AngularJS controllers and modern Angular components; AngularJS services and modern dependency injection; AngularJS templates and modern template syntax; Differences in forms and validation; Differences in routing; Differences in testing and build tooling

- **126. Migration Planning and Completion** — Mapping legacy features to replacement features; Estimating migration effort; Tracking feature parity; Testing migrated workflows; Accessibility and performance regression checks; Removing obsolete libraries; Establishing end-of-life criteria for legacy code

### Module 23: Real-World Application Patterns

- **127. Dashboard Applications** — Dashboard component structure; Reusable metric cards; Filtering and sorting datasets; API-driven dashboard data; Loading, error, and empty states; Large data collection performance

- **128. CRUD Applications** — Listing records; Viewing record details; Creating records; Editing existing records; Deleting records safely; Client-side and server-side validation; Error recovery and confirmation dialogs

- **129. Authentication-Aware Interfaces** — Login form structure; Displaying authentication state; Handling session expiration; Redirecting after login; Hiding or showing navigation according to user permissions; Enforcing permissions on the server

- **130. Data-Heavy Interfaces** — Searchable tables; Multi-field filters; Pagination; Sorting; Query-parameter synchronization; Caching and data refresh; Accessible tables and controls

- **131. Reusable UI Libraries** — Component catalogs; Shared form controls; Consistent validation messages; Reusable loading and error states; Component documentation; Compatibility and regression tests

### Module 24: Exercises, Professional Practices, and Reference Skills

- **132. Practical JavaScript Refreshers** — Objects and arrays; Array transformation methods; Closures and scope; Callbacks and promises; JSON processing; HTTP requests; Browser event handling

- **133. Reading and Understanding Existing Code** — Tracing application bootstrap; Identifying module dependencies; Following controller-to-service calls; Tracing template data bindings; Locating route configurations; Understanding directive behavior; Documenting an unknown codebase

- **134. Problem-Solving and Debugging Challenges** — Fixing a broken binding; Correcting a dependency injection error; Debugging a failed API request; Resolving a routing issue; Fixing form validation; Reducing excessive watchers; Finding and fixing a memory leak

- **135. Documentation and Teamwork** — Reading API reference pages; Writing setup instructions; Documenting service interfaces; Version control and meaningful commits; Reviewing changes; Writing bug reports; Maintaining migration notes

- **136. Course Review and Readiness Assessment** — Core terminology assessment; Data binding and directives assessment; Services and dependency injection assessment; Forms and routing assessment; HTTP integration assessment; Testing and security assessment; Performance and maintainability assessment; Final practical project review

## Section C: Practical exercises

1. **First AngularJS Page:** Create an application that displays a heading, a paragraph, and a dynamic value.

2. **Profile Card:** Display a person's name, role, and contact details through data binding.

3. **Interactive Counter:** Use buttons to increase and decrease a counter.

4. **Product List:** Display an array of products using ng-repeat.

5. **Searchable List:** Add a search field to filter a collection.

6. **Conditional Messages:** Show different messages using ng-if and ng-switch.

7. **Price Formatter:** Apply currency, number, and date filters to sample data.

8. **Contact Form:** Bind form fields using ng-model.

9. **Validation Practice:** Add required, email, length, and pattern validation.

10. **Custom Filter:** Create a custom filter for formatting a status value.

11. **Student Management:** Use controllers and services to manage student records.

12. **Reusable Profile Component:** Create a component with input bindings and callback bindings.

13. **Custom Validation:** Implement a validator that compares two related form fields.

14. **REST API Integration:** Fetch a list of records using $http.

15. **CRUD Service:** Implement create, read, update, and delete methods through a reusable service.

16. **Multi-Page SPA:** Configure a home page, listing page, details page, and not-found route.

17. **Route Data Loading:** Load record details through route resolves.

18. **Request Error Handling:** Display loading, success, empty, and failure states.

19. **Automated Unit Tests:** Test a custom service and filter using AngularJS mocks.

20. **Reusable Form Control:** Create a directive or component for a repeated form input pattern.

21. **Directive Engineering:** Implement a reusable directive with isolated scope and cleanup logic.

22. **Digest Cycle Investigation:** Identify why a UI update fails and correct the framework integration.

23. **Performance Audit:** Measure and reduce unnecessary watchers in a large list.

24. **Centralized Error Handling:** Standardize errors returned from an API service.

25. **Security Review:** Audit a sample application's HTML rendering, routing, and authentication assumptions.

26. **Test Automation:** Create unit tests for components, directives, forms, and asynchronous services.

27. **Legacy Dependency Audit:** Identify unmaintained packages and propose replacements.

28. **Migration Preparation:** Refactor a controller-heavy page into reusable components and services.

29. **Production Deployment:** Deploy an SPA and verify deep links, static assets, error handling, and HTTPS.

30. **Codebase Audit:** Document the architecture, risks, dependencies, tests, and recommended next steps for an

## Section D: Projects

1. **Personal Portfolio Dashboard:** Build an interactive profile and portfolio page with data binding, skills, project cards, category filtering, conditional content, formatting and responsive presentation.

2. **Student Record Manager:** Display and manage student records with listing, add/edit forms, validation, search, sorting, deletion confirmation and empty states.

3. **Expense Summary Calculator:** Record sample expenses, categorize entries, calculate totals, filter by category and format amounts/dates.

4. **Product Catalogue:** Create product listing and detail views backed by a mock API, including search, sorting, filtering, routes, pagination, loading and error states.

5. **Task Management Application:** Build a multi-view task manager with create/edit, priority/status, search, filters, validated forms, details routes, service-based state and tests.

6. **API-Driven Admin Dashboard:** Build an API-backed dashboard with summary cards, searchable tables, CRUD operations, pagination, failure handling and permission-aware UI behavior.

7. **Custom AngularJS Component Library:** Create reusable inputs, buttons, validation helpers and confirmation components with documented contracts, consistent states and tests.

8. **Legacy Application Performance Audit:** Measure and improve an existing app through dependency inventory, watcher/render investigation, large-list optimization, API review, leak checks and regressions.

9. **AngularJS Legacy Modernization Prototype:** Prepare a small legacy application for incremental replacement with architecture notes, components, service/API boundaries, tests, dependency risks, migration and rollback plans.

10. **Multi-Role Inventory and Order Management Application:** Build a maintainable multi-view inventory/order SPA using a mock API with customer/order records, search, filtering, sorting, pagination, reusable components, validation, tests, accessibility, performance, security and a modernization roadmap.

## Section E: Advanced and specialized topics

Cross-linked into the corresponding core/advanced lessons: custom directive compilation/linking; advanced `ngModel`; `$parse`, `$interpolate`, `$compile`, and `$q`; configurable providers; component lifecycle and communication; route resolves and rejection handling; digest-cycle diagnostics and watcher optimization; mocked HTTP/asynchronous testing; asynchronous custom validation; runtime error monitoring; `ngAnimate`; `ngAria`; `ngCookies`; `ngMessages`; `ngResource`; `ngSanitize`; `ngTouch`; legacy AngularJS Material/third-party UI components; historical build systems/test runners; historical package-manager configuration. Legacy UI libraries/build systems are marked optional and need separate compatibility review.

## Section F: Learning roadmap

1. **Web fundamentals:** Modules 1–2; milestone: a local page loads the legacy library and displays a dynamic value.
2. **Core framework:** Modules 3–8; milestone: a student manager with reusable components and validated forms.
3. **Application architecture:** Modules 9–12; milestone: a multi-view CRUD application with mock/API data and loading/error states.
4. **Professional frontend development:** Modules 13–19; milestone: tests plus a security, accessibility, performance and architecture review.
5. **Production maintenance:** Modules 20–21; milestone: documented dependencies, build/deploy steps, monitoring and operations.
6. **Modernization:** Module 22 and one project from Module 23, then the capstone; milestone: a risk-reviewed migration plan with feature-parity and rollback checks.

## PDF topics corrected, excluded or qualified

- **No numbered core curriculum topics were omitted.** The 136 numbered topic headings and their extracted subtopic headings are represented in ordered lesson files.
- The module titles and topic order are preserved from the PDF; source Section C contains 30 practical exercises, Section D contains 10 projects, and Section E specialist topics are cross-linked above.
- The PDF’s status wording was not changed: end-of-support is explicitly stated and treated as a maintenance constraint, not a reason to recommend new AngularJS applications.
- Examples are newly authored short teaching examples, not copied tutorial passages. Each is marked for static inspection; CodeLeaf currently does not provide an AngularJS-specific sandbox.
- The exam file is a blueprint only. No assessment was administered and no certificate is issued by this patch. All course content remains draft.

## Source references

- [AngularJS API Reference (1.8.4 documentation snapshot)](https://docs.angularjs.org/api) — AngularJS project documentation; checked 2026-10-15. Supports: core ng module, services, directives, filters, global APIs.

- [AngularJS Developer Guide](https://docs.angularjs.org/guide) — AngularJS project documentation; checked 2026-10-15. Supports: application setup, modules, data binding, dependency injection, routing, testing.

- [Understanding Components](https://docs.angularjs.org/guide/component) — AngularJS project documentation; checked 2026-10-15. Supports: component registration, bindings, lifecycle hooks, component architecture.

- [AngularJS Security Guide](https://docs.angularjs.org/guide/security) — AngularJS project documentation; checked 2026-10-15. Supports: HTML sanitization, template injection, XSS, trusted values.

- [Unit Testing](https://docs.angularjs.org/guide/unit-testing) — AngularJS project documentation; checked 2026-10-15. Supports: Jasmine-style unit testing, angular-mocks, HTTP mocking.

- [ngRoute API Reference](https://docs.angularjs.org/api/ngRoute) — AngularJS project documentation; checked 2026-10-15. Supports: $routeProvider, ngView, $routeParams, route resolves.

- [$http Service API Reference](https://docs.angularjs.org/api/ng/service/$http) — AngularJS project documentation; checked 2026-10-15. Supports: HTTP requests, promises, response handling.

- [AngularJS end-of-support notice](https://docs.angularjs.org/) — AngularJS project documentation; checked 2026-10-15. Supports: official end-of-support status, distinction from modern Angular.

- [Angular documentation (modern Angular)](https://angular.dev/) — Angular documentation team; checked 2026-10-15. Supports: comparison with modern Angular, migration target research.

- [MDN: HTTP overview](https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview) — MDN Web Docs; checked 2026-10-15. Supports: HTTP request/response fundamentals, status codes, headers.
