# Vue.js — Full Syllabus Map

Source: `Vue.pdf` (34 pages); all 20 modules and 152 numbered lesson headings were extracted from Section B and matched to separate JSON lesson files.

## Module 01: Introduction to Vue.js

1. **Introduction to Vue.js** (`vue-lesson-001`)
   - What Vue.js is
   - Vue as a JavaScript framework
   - Declarative rendering and reactive interfaces
   - Vue's component-based programming model
2. **Why Vue.js Is Used** (`vue-lesson-002`)
   - Problems Vue solves
   - Common use cases
   - Advantages and limitations
   - When Vue is a suitable choice
3. **Where Vue.js Is Used** (`vue-lesson-003`)
   - Interactive websites
   - Single-page applications
   - Dashboards and administration panels
   - Progressive enhancement of existing websites
   - Full-stack applications
4. **History and Evolution of Vue.js** (`vue-lesson-004`)
   - Origins and design goals
   - Major changes from Vue 2 to Vue 3
   - Vue's current architecture and ecosystem
   - Understanding legacy Vue projects
5. **Understanding the Vue Application Architecture** (`vue-lesson-005`)
   - Browser, DOM, and JavaScript
   - Components and the component tree
   - Reactive state and rendering
   - Vue's rendering and update cycle
6. **Prerequisites for Learning Vue** (`vue-lesson-006`)
   - HTML elements and forms
   - CSS selectors, layout, and responsive design
   - JavaScript variables, functions, objects, and arrays
   - ES modules, promises, and asynchronous JavaScript
7. **Vue Development Tools** (`vue-lesson-007`)
   - Code editors
   - Browser developer tools
   - Vue DevTools
   - Online Vue Playground
8. **Vue Installation and Environment Setup** (`vue-lesson-008`)
   - Installing Node.js and a package manager
   - Understanding npm packages and dependencies
   - Creating a project with create-vue
   - Starting the development server
   - Understanding the development server and browser preview

## Module 02: Vue Project Structure and Application Basics

9. **Exploring a Vue Project** (`vue-lesson-009`)
   - src , public , and project configuration
   - The main.js entry point
   - The root App.vue component
   - Assets and reusable components
   - Views, routes, and application entry points
10. **Vue Single-File Components** (`vue-lesson-010`)
   - Purpose of .vue files
   - The <template> block
   - The <script> block
   - The <style> block
   - How a Vue SFC is compiled
11. **Creating and Mounting a Vue Application** (`vue-lesson-011`)
   - Importing createApp
   - Creating the application instance
   - Mounting the application
   - Configuring application-level features
   - Multiple Vue applications on one page
12. **Development and Production Modes** (`vue-lesson-012`)
   - Running the development server
   - Hot Module Replacement
   - Creating a production build
   - Understanding generated assets
   - Inspecting build and runtime errors
13. **Vue Project Configuration** (`vue-lesson-013`)
   - Understanding package.json
   - Package scripts and dependencies
   - The Vite configuration file
   - Environment variables and configuration
   - Managing dependency versions

## Module 03: Vue Template Syntax

14. **Introduction to Vue Templates** (`vue-lesson-014`)
   - Template syntax and HTML compatibility
   - Template expressions
   - Data binding and declarative rendering
15. **Text Interpolation** (`vue-lesson-015`)
   - Double-curly-brace syntax
   - Rendering strings and numbers
   - Evaluating simple expressions
   - Handling missing and nullish values
16. **Attribute Binding with v-bind** (`vue-lesson-016`)
   - Binding HTML attributes
   - Shorthand binding with :
   - Boolean attributes
   - Binding multiple attributes
17. **Dynamic Class Binding** (`vue-lesson-017`)
   - Conditional classes
   - Object syntax
   - Array syntax
   - Combining static and dynamic classes
18. **Dynamic Style Binding** (`vue-lesson-018`)
   - Inline style objects
   - Array syntax for styles
   - Dynamic style properties
   - Combining static and reactive styles
19. **Event Binding with v-on** (`vue-lesson-019`)
   - Listening for DOM events
   - Shorthand syntax with @
   - Calling methods from event handlers
   - Passing event arguments
20. **Conditional Rendering** (`vue-lesson-020`)
   - v-if
   - v-else-if and v-else
   - Conditional rendering with <template>
   - Understanding when conditional elements are created
21. **List Rendering with v-for** (`vue-lesson-021`)
   - Iterating over arrays
   - Accessing indexes
   - Iterating over objects and numeric ranges
   - Rendering nested lists
22. **Keys and Efficient List Updates** (`vue-lesson-022`)
   - Purpose of the key attribute
   - Stable and unique keys
   - Keys when rendering components
   - Common list-rendering mistakes
23. **Built-in Directives and Template Rules** (`vue-lesson-023`)
   - Directive names and expressions
   - Directive arguments
   - Dynamic directive arguments
   - Directive modifiers
   - Template expression limitations

## Module 04: Directives and Rendering Patterns

24. **Understanding Vue Directives** (`vue-lesson-024`)
   - How directives work
   - Directive values and update behavior
   - Choosing between directives and components
25. **v-if Versus v-show** (`vue-lesson-025`)
   - Element creation and removal
   - CSS-based visibility
   - Performance considerations
   - Choosing the right directive
26. **Working with v-model** (`vue-lesson-026`)
   - Two-way binding
   - Input and textarea binding
   - Checkbox and radio binding
   - Select menus and option values
27. **Text and HTML Rendering Directives** (`vue-lesson-027`)
   - v-text
   - v-html
   - Differences between text and HTML rendering
   - Security considerations for HTML content
28. **Advanced Rendering Directives** (`vue-lesson-028`)
   - v-once
   - v-memo
   - When rendering optimizations are appropriate
   - Understanding the trade-offs of manual optimization
29. **Writing Custom Directives** (`vue-lesson-029`)
   - When a custom directive is useful
   - Directive lifecycle hooks
   - Accessing the associated DOM element
   - Passing directive values and arguments
   - Building reusable DOM behavior

## Module 05: Vue Reactivity System

30. **Introduction to Reactivity** (`vue-lesson-030`)
   - What reactive state means
   - Reactive dependencies
   - Triggering component updates
   - Understanding Vue's update batching
31. **The ref() API** (`vue-lesson-031`)
   - Creating reactive references
   - Reading and updating .value
   - Using refs in templates
   - Refs for primitive and object values
32. **The reactive() API** (`vue-lesson-032`)
   - Creating reactive objects
   - Nested reactive properties
   - Updating arrays and objects
   - Understanding proxy-based reactivity
33. **Choosing Between ref() and reactive()** (`vue-lesson-033`)
   - Differences in usage
   - Ref unwrapping
   - Replacing reactive object values
   - Common reactivity pitfalls
34. **Computed Properties** (`vue-lesson-034`)
   - Creating computed values
   - Getter behavior
   - Computed values and dependency tracking
   - Cached computation
   - Writable computed properties
35. **Watching Reactive State** (`vue-lesson-035`)
   - The watch() API
   - Watching refs, getters, and reactive objects
   - Watching multiple sources
   - Immediate and deep watching
   - Once-only watchers where supported
36. **Automatic Reactive Effects** (`vue-lesson-036`)
   - watchEffect()
   - watchPostEffect()
   - watchSyncEffect()
   - Explicit versus automatic dependency tracking
37. **Advanced Reactivity Utilities** (`vue-lesson-037`)
   - toRef() and toRefs()
   - unref() and toValue()
   - readonly() and shallow APIs
   - isRef() and isReactive()
   - markRaw() and toRaw()
38. **Reactivity Debugging and Best Practices** (`vue-lesson-038`)
   - Destructuring reactive objects safely
   - Debugging reactive dependencies
   - Avoiding unnecessary deep watchers
   - Preventing accidental state loss
   - Choosing an appropriate state representation

## Module 06: Events, Forms, and User Input

39. **Handling DOM Events** (`vue-lesson-039`)
   - Click, input, change, and submit events
   - Inline handlers and method handlers
   - Passing event objects
   - Event arguments and handler reuse
40. **Event Modifiers** (`vue-lesson-040`)
   - .stop and .prevent
   - .self and .once
   - Keyboard modifiers
   - Mouse and key modifiers
   - System modifier keys
41. **Form Inputs with Vue** (`vue-lesson-041`)
   - Text inputs and textareas
   - Checkboxes and radio groups
   - Select elements and multiple selection
   - Number and other specialized inputs
42. **v-model Modifiers** (`vue-lesson-042`)
   - .lazy
   - .number
   - .trim
   - Native input binding versus component binding
43. **Form Validation** (`vue-lesson-043`)
   - Required fields and constraints
   - Validating email, numbers, and text
   - Custom validation logic
   - Showing field-specific errors
   - Accessible error messages
44. **Form Submission and Data Processing** (`vue-lesson-044`)
   - Preventing unintended page reloads
   - Validating before submission
   - Transforming form values
   - Submission loading states
   - Handling server validation responses
45. **Building Reusable Form Logic** (`vue-lesson-045`)
   - Sharing validation functions
   - Resetting forms
   - Dirty and touched field states
   - Multi-step forms
   - File input handling

## Module 07: Component Fundamentals

46. **Introduction to Vue Components** (`vue-lesson-046`)
   - Why components are used
   - Component boundaries and responsibilities
   - Parent and child components
   - Component trees
47. **Creating and Using Components** (`vue-lesson-047`)
   - Defining an SFC component
   - Importing child components
   - Local component usage
   - Component naming conventions
   - Organizing component files
48. **Component Props** (`vue-lesson-048`)
   - Declaring props
   - Passing static and dynamic props
   - Required and optional props
   - Defaults and validation
   - Object and array props
49. **One-Way Data Flow** (`vue-lesson-049`)
   - Parent-to-child communication
   - Why children should not mutate props directly
   - Deriving local values from props
   - Keeping component APIs predictable
50. **Component Events** (`vue-lesson-050`)
   - Declaring emitted events
   - Emitting events from children
   - Passing event payloads
   - Validating emitted events
   - Listening in parent components
51. **Component Slots** (`vue-lesson-051`)
   - Default slots
   - Named slots
   - Scoped slots
   - Slot fallback content
   - Forwarding slots through components
52. **Component v-model** (`vue-lesson-052`)
   - Binding parent state to child components
   - The modelValue and update:modelValue convention
   - defineModel() where supported
   - Named models
   - Component model modifiers
53. **Fallthrough Attributes and Component APIs** (`vue-lesson-053`)
   - Attributes that are not declared as props
   - $attrs and attribute inheritance
   - Multiple root nodes
   - Controlling attribute inheritance
   - Exposing selected component methods
54. **Component Communication Patterns** (`vue-lesson-054`)
   - Props and emitted events
   - Shared state
   - Provide and inject
   - Avoiding tightly coupled components
   - Choosing communication patterns by use case

## Module 08: Component Architecture and Lifecycle

55. **Component Lifecycle** (`vue-lesson-055`)
   - Component creation and setup
   - Mounting and updating
   - Unmounting
   - Lifecycle order in parent and child components
56. **Lifecycle Hooks** (`vue-lesson-056`)
   - onBeforeMount() and onMounted()
   - onBeforeUpdate() and onUpdated()
   - onBeforeUnmount() and onUnmounted()
   - onErrorCaptured()
   - onRenderTracked() and onRenderTriggered()
57. **DOM Template Refs** (`vue-lesson-057`)
   - Referencing DOM elements
   - Accessing child component instances
   - Refs inside v-for
   - Conditional and asynchronous elements
58. **Working with the DOM After Updates** (`vue-lesson-058`)
   - Vue's asynchronous update cycle
   - nextTick()
   - Measuring elements
   - Managing focus
   - Cleaning up DOM-related side effects
59. **Error Handling in Components** (`vue-lesson-059`)
   - Handling synchronous errors
   - Handling asynchronous errors
   - Component error capture
   - Application-level error handlers
   - User-friendly error interfaces
60. **Designing Maintainable Components** (`vue-lesson-060`)
   - Single-responsibility components
   - Presentational versus data-oriented components
   - Reusable UI components
   - Component composition
   - Managing component complexity

## Module 09: Styling, Transitions, and Animations

61. **Styling Vue Components** (`vue-lesson-061`)
   - Global CSS
   - Component-level styling
   - Scoped styles
   - CSS Modules
   - Importing external stylesheets
62. **Advanced Vue Styling** (`vue-lesson-062`)
   - Dynamic style bindings
   - CSS custom properties and reactive values
   - Deep selectors
   - Slotted content styling
   - CSS organization and naming conventions
63. **The <Transition> Component** (`vue-lesson-063`)
   - Enter and leave transitions
   - Transition classes
   - Transition duration and timing
   - JavaScript transition hooks
64. **The <TransitionGroup> Component** (`vue-lesson-064`)
   - Animating list insertion and removal
   - Animating moved elements
   - List transition classes
   - Handling keyed lists
65. **State-Driven Animation and Motion Design** (`vue-lesson-065`)
   - CSS transitions and keyframes
   - Animating reactive state
   - Coordinating animations with component events
   - Reduced-motion preferences
   - Avoiding distracting or inaccessible motion

## Module 10: Reusable Logic with Composables

66. **Introduction to Composables** (`vue-lesson-066`)
   - What a composable is
   - Naming conventions such as useFeature
   - Extracting reusable logic
   - When to introduce a composable
67. **Building Custom Composables** (`vue-lesson-067`)
   - Returning refs and computed values
   - Accepting arguments and reactive inputs
   - Exposing functions and state
   - Sharing logic between components
68. **Common Composable Patterns** (`vue-lesson-068`)
   - Fetching and caching data
   - Window events and browser APIs
   - Timers and subscriptions
   - Form logic
   - Reusable filtering and sorting
69. **Composable Lifecycle and Side Effects** (`vue-lesson-069`)
   - Lifecycle hooks inside composables
   - Cleaning up event listeners
   - Watcher cleanup
   - Preventing stale asynchronous results
   - SSR-compatible composables
70. **Composables Versus Other Reuse Techniques** (`vue-lesson-070`)
   - Composables versus mixins
   - Composables versus utility functions
   - Composables versus components
   - Avoiding unnecessary shared abstractions

## Module 11: Vue Router and Application Navigation

71. **Introduction to Client-Side Routing** (`vue-lesson-071`)
   - What a router does
   - Single-page applications and browser history
   - Routes, views, and navigation
   - Choosing between routing and conditional rendering
72. **Installing and Configuring Vue Router** (`vue-lesson-072`)
   - Creating a router instance
   - Defining route records
   - Registering the router with Vue
   - Using <RouterLink> and <RouterView>
73. **Route Paths and Navigation** (`vue-lesson-073`)
   - Static routes
   - Named routes
   - Programmatic navigation
   - Redirects and aliases
   - Browser back and forward navigation
74. **Dynamic Routes and Route Parameters** (`vue-lesson-074`)
   - Route parameters
   - Reading route parameters
   - Query parameters
   - Optional and repeatable parameters
   - Watching route changes
75. **Nested Routes and Layouts** (`vue-lesson-075`)
   - Parent and child routes
   - Nested <RouterView> components
   - Shared layouts
   - Route organization by feature
76. **Navigation Guards** (`vue-lesson-076`)
   - Global guards
   - Per-route guards
   - In-component guards
   - Cancelling and redirecting navigation
   - Asynchronous guards and error handling
77. **Advanced Routing** (`vue-lesson-077`)
   - Lazy-loaded route components
   - Route metadata
   - Scroll behavior
   - Catch-all routes and 404 pages
   - Dynamic route registration
78. **Authentication and Route Access** (`vue-lesson-078`)
   - Public and private page patterns
   - Authentication state integration
   - Redirecting unauthenticated users
   - Role-aware user interface navigation
   - Why frontend route guards do not replace backend authorization
79. **Route Data and Loading States** (`vue-lesson-079`)
   - Fetching data for a route
   - Loading and error states
   - Handling parameter changes
   - Preventing stale responses
   - Deciding between route guards and component fetching

## Module 12: APIs, Asynchronous Operations, and Data Handling

80. **Asynchronous JavaScript in Vue** (`vue-lesson-080`)
   - Promises and async / await
   - Asynchronous work in event handlers
   - Error handling with try and catch
   - Coordinating multiple requests
81. **Connecting Vue to HTTP APIs** (`vue-lesson-081`)
   - Fetching data with the Fetch API
   - Understanding HTTP methods and status codes
   - Sending request headers and JSON bodies
   - Using an optional HTTP client library
   - Handling unsuccessful responses
82. **Designing an API Service Layer** (`vue-lesson-082`)
   - Separating requests from UI components
   - Organizing API service modules
   - Request and response transformation
   - Centralized error handling
   - Reusable API utilities
83. **Data Fetching in Components** (`vue-lesson-083`)
   - Loading, success, error, and empty states
   - Fetching data on mount
   - Reacting to parameter changes
   - Refresh and retry behavior
   - Avoiding duplicate requests
84. **Advanced Data Fetching** (`vue-lesson-084`)
   - Cancelling requests with AbortController
   - Handling race conditions
   - Debounced search
   - Pagination and infinite scrolling
   - Caching and stale-data policies
85. **Data Manipulation and Presentation** (`vue-lesson-085`)
   - Filtering and sorting
   - Search and computed results
   - Formatting dates and currency
   - Paginated data display
   - Separating server state from local UI state
86. **Browser APIs and Persistent Data** (`vue-lesson-086`)
   - Local storage
   - Session storage
   - URL state and query parameters
   - Network and online status
   - Storage limitations and privacy considerations
87. **Real-Time Data and File Transfers** (`vue-lesson-087`)
   - WebSocket integration
   - Receiving live updates
   - Uploading files
   - Downloading files
   - Connection recovery and cleanup
88. **Environment-Specific API Configuration** (`vue-lesson-088`)
   - Development and production API URLs
   - Vite environment variables
   - Client-exposed versus server-only configuration
   - Avoiding secrets in browser bundles
   - Managing API configuration across deployments

## Module 13: State Management with Pinia

89. **Understanding Application State** (`vue-lesson-089`)
   - Local component state
   - Lifted and shared state
   - Derived state
   - UI state versus server data
   - When a state-management library is useful
90. **Introduction to Pinia** (`vue-lesson-090`)
   - What Pinia does
   - Installing and registering Pinia
   - Defining a store
   - Accessing a store from components
91. **Store State** (`vue-lesson-091`)
   - Declaring state
   - Reading and updating state
   - Resetting state
   - Using reactive state in components
92. **Getters and Derived Store Data** (`vue-lesson-092`)
   - Defining getters
   - Computed store values
   - Getter parameters and caching considerations
   - Avoiding duplicated state
93. **Actions and Business Logic** (`vue-lesson-093`)
   - Synchronous actions
   - Asynchronous actions
   - Calling API services from stores
   - Loading and error states
   - Organizing actions by responsibility
94. **Structuring Larger Pinia Applications** (`vue-lesson-094`)
   - Multiple stores
   - Store composition
   - Store-to-store communication
   - Shared versus feature-specific state
   - Avoiding circular dependencies
95. **Pinia and Component Integration** (`vue-lesson-095`)
   - Using store values in templates
   - storeToRefs()
   - Updating state from components
   - Keeping component responsibilities clear
96. **Persisting and Debugging State** (`vue-lesson-096`)
   - Manual persistence
   - Persistence plugins
   - State inspection in Vue DevTools
   - State reset and debugging
   - Protecting sensitive user data
97. **Advanced Pinia Topics** (`vue-lesson-097`)
   - Store plugins
   - Store testing
   - Hot Module Replacement
   - SSR and per-request state
   - Store hydration
98. **Understanding Vuex and Legacy State Management** (`vue-lesson-098`)
   - Overview of Vuex
   - State, mutations, actions, and getters
   - Vuex modules
   - Understanding legacy codebases
   - Choosing Pinia for new Vue applications

## Module 14: Advanced Components and Rendering

99. **Dynamic Components** (`vue-lesson-099`)
   - The <component> element
   - Switching component types
   - Dynamic component props
   - Maintaining component identity
100. **Asynchronous Components** (`vue-lesson-100`)
   - defineAsyncComponent()
   - Lazy loading components
   - Loading and error components
   - Delay and timeout behavior
101. **Component Caching with <KeepAlive>** (`vue-lesson-101`)
   - Preserving component state
   - Include and exclude rules
   - Activation and deactivation hooks
   - Cache behavior and memory considerations
102. **Teleport and Advanced DOM Placement** (`vue-lesson-102`)
   - Understanding <Teleport>
   - Modals and overlays
   - Target elements
   - Disabled and deferred teleport behavior where supported
103. **Suspense and Asynchronous Component Coordination** (`vue-lesson-103`)
   - Understanding <Suspense>
   - Default and fallback content
   - Asynchronous dependencies
   - Error and loading-state design
   - Checking feature status and limitations before production use
104. **Provide and Inject** (`vue-lesson-104`)
   - provide() and inject()
   - Application-level dependency provision
   - Providing reactive values
   - Typed or symbolic injection keys
   - Designing dependency boundaries
105. **Render Functions and Virtual DOM** (`vue-lesson-105`)
   - What render functions are
   - The h() function
   - Creating VNodes
   - Rendering children and props
   - When render functions are preferable to templates
106. **JSX in Vue** (`vue-lesson-106`)
   - JSX fundamentals
   - Configuring JSX support
   - Rendering components using JSX
   - JSX and template syntax trade-offs
107. **Vue Plugins and Application Extensions** (`vue-lesson-107`)
   - What a Vue plugin is
   - Creating and installing plugins
   - Registering shared functionality
   - Adding application-level properties
   - Plugin configuration and documentation
108. **Advanced Component API Patterns** (`vue-lesson-108`)
   - Exposing component methods
   - Forwarding attributes and slots
   - Recursive components
   - Generic reusable UI patterns
   - Component API versioning and maintainability

## Module 15: TypeScript and Large-Scale Code Organization

109. **Introduction to TypeScript in Vue** (`vue-lesson-109`)
   - JavaScript versus TypeScript
   - Enabling TypeScript in a Vue project
   - Type inference
   - Interfaces, type aliases, and unions
110. **Typing Vue Component Props and Events** (`vue-lesson-110`)
   - Type-based defineProps()
   - Typed event declarations
   - Typed defaults
   - Component model typing
111. **Typed Reactivity and Composition API** (`vue-lesson-111`)
   - Typing refs and reactive objects
   - Typing computed values
   - Typing watchers
   - Typing template refs
112. **Typed Composables and Stores** (`vue-lesson-112`)
   - Designing reusable typed functions
   - Generic composables
   - Typed Pinia state and actions
   - Typed API responses
113. **Type Checking and Developer Tooling** (`vue-lesson-113`)
   - Vue language tooling
   - vue-tsc
   - Type-checking as part of CI
   - Resolving common SFC type errors
114. **Scaling a Vue Codebase** (`vue-lesson-114`)
   - Feature-based folder structures
   - Component, service, and store boundaries
   - Module naming and import conventions
   - Shared types and utilities
   - Avoiding circular dependencies

## Module 16: Testing and Quality Assurance

115. **Introduction to Vue Testing** (`vue-lesson-115`)
   - Why automated testing matters
   - Types of tests
   - Test planning and coverage
   - Choosing the appropriate test level
116. **Unit Testing with Vitest** (`vue-lesson-116`)
   - Installing and configuring Vitest
   - Writing test cases
   - Assertions and matchers
   - Testing pure functions
   - Testing edge cases
117. **Testing Vue Components** (`vue-lesson-117`)
   - Installing Vue Test Utils
   - Mounting components
   - Inspecting rendered output
   - Testing props and emitted events
   - Testing slots and component models
118. **Testing User Interactions** (`vue-lesson-118`)
   - Triggering DOM events
   - Testing forms and validation
   - Testing conditional rendering
   - Testing loading and error states
119. **Testing Composables and Reactivity** (`vue-lesson-119`)
   - Testing returned reactive values
   - Testing watchers and asynchronous effects
   - Cleaning up mounted instances
   - Testing browser-dependent behavior
120. **Testing Router and Pinia** (`vue-lesson-120`)
   - Mocking or configuring router instances
   - Testing navigation behavior
   - Creating isolated Pinia instances
   - Testing store actions and getters
121. **Mocking Dependencies and API Calls** (`vue-lesson-121`)
   - Mock functions and modules
   - Mocking network responses
   - Testing failures and retries
   - Avoiding brittle test assumptions
122. **End-to-End Testing** (`vue-lesson-122`)
   - Introduction to browser-driven testing
   - Testing complete user journeys
   - Choosing tools such as Cypress or Playwright
   - Test data and backend integration
   - Reliable test environments
123. **Quality Gates and Continuous Integration** (`vue-lesson-123`)
   - Running tests automatically
   - Linting and formatting checks
   - Type checks where applicable
   - Test coverage reports
   - Preventing regressions before deployment

## Module 17: Accessibility, Security, and User Experience

124. **Accessibility Fundamentals in Vue** (`vue-lesson-124`)
   - Semantic HTML
   - Accessible names and labels
   - Keyboard navigation
   - Focus management
   - Accessible interactive controls
125. **Accessible Forms and Dynamic Interfaces** (`vue-lesson-125`)
   - Labeling form fields
   - Communicating validation errors
   - Announcing important status changes
   - Managing focus after navigation and dialogs
   - Testing with assistive technologies
126. **Responsive and Inclusive UI Design** (`vue-lesson-126`)
   - Responsive CSS with Vue components
   - Accessible menus and dialogs
   - Reduced-motion preferences
   - Usable loading, empty, and error states
   - Localization and internationalization fundamentals
127. **Vue Application Security** (`vue-lesson-127`)
   - Rendering untrusted content safely
   - Understanding cross-site scripting (XSS)
   - Safe use of v-html
   - Why untrusted strings must not become Vue templates
   - Handling untrusted URLs and dynamic attributes
128. **Frontend Authentication and Security Boundaries** (`vue-lesson-128`)
   - Authentication state in the UI
   - Secure communication with backend APIs
   - Session and token handling considerations
   - Cross-site request forgery coordination with the backend
   - Why frontend checks cannot enforce authorization by themselves
129. **Dependency and Configuration Security** (`vue-lesson-129`)
   - Keeping dependencies updated
   - Reviewing third-party packages
   - Managing public and private configuration
   - Preventing secret exposure in client bundles
   - Production error and data handling

## Module 18: Performance and Optimization

130. **Understanding Vue Performance** (`vue-lesson-130`)
   - Initial loading and rendering costs
   - Component rendering and reactive updates
   - Network, bundle, and DOM performance
   - Establishing performance baselines
131. **Reactive and Rendering Optimization** (`vue-lesson-131`)
   - Avoiding unnecessary reactive state
   - Using computed properties effectively
   - Keeping component boundaries appropriate
   - Avoiding unnecessary watchers
   - Handling large lists efficiently
132. **Page Loading and Bundle Optimization** (`vue-lesson-132`)
   - Route-level code splitting
   - Lazy-loaded components
   - Tree shaking
   - Asset optimization
   - Understanding bundle analysis
133. **Profiling and Measuring Performance** (`vue-lesson-133`)
   - Vue DevTools profiling
   - Browser performance tools
   - Measuring rendering behavior
   - Identifying slow interactions
   - Core Web Vitals fundamentals
134. **Advanced Performance Techniques** (`vue-lesson-134`)
   - Virtual scrolling
   - Large reactive data structures
   - Reducing unnecessary DOM work
   - Caching and request optimization
   - Avoiding premature optimization

## Module 19: Server-Side Rendering, Nuxt, and Deployment

135. **Vue Rendering Architectures** (`vue-lesson-135`)
   - Client-side rendering (CSR)
   - Server-side rendering (SSR)
   - Static-site generation (SSG)
   - Hydration
   - Selecting an architecture for an application
136. **Vue Server-Side Rendering Fundamentals** (`vue-lesson-136`)
   - Server-rendering Vue components
   - Server and client execution environments
   - Hydrating rendered HTML
   - Managing server and client entry points
   - SSR limitations and trade-offs
137. **SSR Data and State Management** (`vue-lesson-137`)
   - Loading data during rendering
   - Serializing and hydrating application state
   - Preventing cross-request state pollution
   - Server-only and browser-only APIs
   - Error handling and loading behavior
138. **SSR Troubleshooting and Security** (`vue-lesson-138`)
   - Hydration mismatches
   - Browser-specific assumptions
   - Time-dependent and nondeterministic rendering
   - Server-side performance
   - SSR security considerations
139. **Introduction to Nuxt** (`vue-lesson-139`)
   - What Nuxt adds to Vue
   - Nuxt project structure
   - Pages, layouts, and routing conventions
   - Auto-imports and framework conventions
   - When to use Vue with Vite versus Nuxt
140. **Building Applications with Nuxt** (`vue-lesson-140`)
   - Data fetching conventions
   - Middleware and navigation
   - Server routes and API endpoints
   - Runtime configuration
   - Error pages and application layouts
141. **Static Generation and Rendering Strategies** (`vue-lesson-141`)
   - Pre-rendered pages
   - Hybrid rendering concepts
   - Content-oriented websites
   - SEO and metadata
   - Choosing rendering strategies by route
142. **Building for Production** (`vue-lesson-142`)
   - Running a production build
   - Inspecting production output
   - Handling runtime configuration
   - Configuring asset paths
   - Testing the production build locally
143. **Deploying Vue Applications** (`vue-lesson-143`)
   - Static hosting
   - Deploying to a cloud or hosting platform
   - SPA history fallback configuration
   - Cache headers and asset versioning
   - HTTPS and domain configuration
144. **CI/CD and Release Management** (`vue-lesson-144`)
   - Version control and release branches
   - Automated builds and tests
   - Preview deployments
   - Environment promotion
   - Rollbacks and release verification
145. **Monitoring and Production Maintenance** (`vue-lesson-145`)
   - Runtime error logging
   - Frontend monitoring
   - Performance monitoring
   - Handling broken API dependencies
   - Maintenance and dependency updates

## Module 20: Professional Practices, Legacy Projects, and Further Learning

146. **Code Quality and Maintainability** (`vue-lesson-146`)
   - Consistent naming conventions
   - Formatting and linting
   - Refactoring without changing behavior
   - Avoiding duplicated logic
   - Writing maintainable Vue code
147. **Collaboration and Version Control** (`vue-lesson-147`)
   - Git fundamentals for Vue projects
   - Branches and pull requests
   - Code review practices
   - Conflict resolution
   - Working with shared component libraries
148. **Documentation and Technical Communication** (`vue-lesson-148`)
   - Documenting component APIs
   - Recording project setup steps
   - Documenting environment configuration
   - Writing useful error reports
   - Maintaining architecture notes
149. **Vue 2 and Vue 3 Migration** (`vue-lesson-149`)
   - Identifying Vue 2 applications
   - Major migration considerations
   - Options API compatibility
   - Updating dependencies and tooling
   - Testing behavior after migration
150. **Legacy Tooling and Ecosystem** (`vue-lesson-150`)
   - Vue CLI and its maintenance status
   - Migrating older projects to Vite
   - Understanding Vuex codebases
   - Updating outdated patterns
   - Evaluating third-party Vue libraries
151. **Building Reusable UI Systems** (`vue-lesson-151`)
   - Shared components and design tokens
   - Component documentation
   - Theming and customization
   - Packaging reusable components
   - Versioning shared UI libraries
152. **Contributing to the Vue Ecosystem** (`vue-lesson-152`)
   - Reading official documentation effectively
   - Understanding issue reports
   - Creating minimal bug reproductions
   - Contributing to open-source projects
   - Following framework changes responsibly

