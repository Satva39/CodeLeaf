# React curriculum index

> Source: `React.pdf`, Sections A–G. Lesson titles and subtopics follow the source syllabus; lesson details are expanded in individual JSON files. All content is draft until reviewed.

## Course overview

- **Audience:** HTML/CSS/JavaScript learners, JavaScript programmers, and frontend developers.
- **Prerequisites:** HTML structure/forms, CSS layout/responsive basics, and JavaScript fundamentals/modules/async.
- **Estimated workload:** 130 hours (source PDF estimate: 100–160 hours).
- **Outcome:** a production-ready React project, following the supplied curriculum scope.
- **Documentation baseline:** React 19.3 (official release notes dated 2026-09-09); current CodeLeaf frontend dependencies remain React/React DOM 18.3.1.

## Learning roadmap

### Phase 1: Foundations

Know React’s role, refresh JavaScript, and build a first component with JSX.

Introduction to React, Web Development and JavaScript Prerequisites, React Environment and Project Setup, JSX and JavaScript Expressions

### Phase 2: Components and Interactivity

Build reusable interactive UI and beginner projects.

React Components, Props, Composition, and Component Communication, Rendering, Lists, and Conditional UI, Events and User Interaction, State Management Fundamentals, Forms and User Input

### Phase 3: Hooks and State Architecture

Reuse logic and keep local/shared state predictable.

React Hooks, Effects, External Systems, and Asynchronous Behavior, Refs, the DOM, and Imperative Interactions, Context, Reducers, and Application State Architecture

### Phase 4: Real Applications

Add routing, APIs, modern form flows, styling, and accessibility.

Routing and Navigation, Working with APIs and Remote Data, Modern React Actions, Concurrency, and Form APIs, Styling, Assets, and UI Composition, Accessibility and Usability

### Phase 5: Reliability and Performance

Test, debug, profile, and maintain the codebase.

Testing React Applications, Debugging and Error Handling, Performance Optimization, React Architecture and Code Quality

### Phase 6: Advanced React

Choose rendering/server architectures safely and understand trust boundaries.

Rendering Architectures — SPA, SSR, SSG, and Streaming, React Server Components and Server Functions, React Security and Privacy

### Phase 7: Professional Readiness

Deploy, maintain, review, and present a capstone project.

Deployment, Build Optimization, and CI/CD, Ecosystem, Legacy React, and Collaboration, Professional React Engineering and Portfolio Readiness

## Complete ordered syllabus

### Module 1: Introduction to React

Difficulty: not specified · Track: core

1. **Introduction to React**
   - What React is
   - The purpose of a user-interface library
   - React's place in modern web development
2. **What Is React?**
   - React as a JavaScript library
   - Declarative user interfaces
   - Component-based development
   - React and React DOM
3. **Understanding React's UI Model**
   - User interfaces as a tree of components
   - Data flowing through components
   - UI updates resulting from data changes
   - Declarative versus imperative UI development
4. **History and Evolution of React**
   - Early React development
   - Introduction of components and JSX
   - Class components and lifecycle methods
   - The introduction of Hooks
   - Modern React and its evolving architecture
5. **Where Is React Used?**
   - Interactive websites
   - Single-page applications
   - Business dashboards
   - E-commerce storefronts
   - Content-driven websites
   - Web applications with complex state
6. **Advantages and Limitations of React**
   - Component reuse
   - Ecosystem and flexibility
   - Rendering and performance considerations
   - Learning complexity
   - Reliance on additional libraries and architecture choices
7. **React Versus Other UI Approaches**
   - React versus direct DOM manipulation
   - React versus template-based rendering
   - React versus other component frameworks
   - Choosing a suitable approach for a project
8. **React Learning Roadmap**
   - Required JavaScript concepts
   - Recommended learning sequence
   - Documentation and reference material
   - Practical exercises and project progression

### Module 2: Web Development and JavaScript Prerequisites

Difficulty: not specified · Track: core

9. **HTML Fundamentals for React**
   - Elements and attributes
   - Document structure
   - Semantic HTML
   - Forms and native controls
10. **CSS Fundamentals for React**
   - Selectors and the cascade
   - Box model
   - Flexbox and Grid
   - Responsive layouts
   - CSS class naming
11. **JavaScript Variables and Data Types**
   - let and const
   - Strings and numbers
   - Booleans and null
   - undefined
   - Type conversion
12. **JavaScript Operators and Expressions**
   - Arithmetic operators
   - Comparison operators
   - Logical operators
   - Ternary expressions
   - Nullish coalescing
   - Optional chaining
13. **JavaScript Control Flow**
   - if and else
   - switch
   - Loops and iteration
   - break and continue
   - Choosing appropriate control structures
14. **JavaScript Functions**
   - Function declarations
   - Function expressions
   - Arrow functions
   - Parameters and return values
   - Default parameters
   - Function scope
15. **JavaScript Objects and Arrays**
   - Object properties
   - Array indexing
   - Array iteration
   - Destructuring
   - Object and array copying
16. **Modern JavaScript Array Methods**
   - map()
   - filter()
   - find()
   - some() and every()
   - reduce()
   - Method chaining
17. **JavaScript Modules**
   - import and export
   - Named exports
   - Default exports
   - Module organization
   - Importing third-party packages
18. **JavaScript Asynchronous Programming**
   - Synchronous versus asynchronous operations
   - Promises
   - async and await
   - Error handling with try and catch
   - Asynchronous data fetching
19. **JavaScript Concepts Used Frequently in React**
   - Closures
   - Reference equality
   - Immutable updates
   - Callback functions
   - Pure functions
   - Event objects

### Module 3: React Environment and Project Setup

Difficulty: not specified · Track: core

20. **React Development Tools**
   - Code editors
   - Browser developer tools
   - React Developer Tools
   - Terminal and command-line basics
21. **Installing and Configuring Node.js**
   - Node.js and npm
   - Checking installed versions
   - npm package management
   - Understanding project dependencies
22. **Creating Your First React Project**
   - Understanding available project starters
   - Starting a project with Vite
   - Installing dependencies
   - Running the development server
23. **Understanding a React Project Structure**
   - src/ and public/
   - Application entry points
   - Component files
   - Stylesheets
   - Package configuration
24. **Understanding package.json**
   - Project metadata
   - Dependencies
   - Development dependencies
   - npm scripts
   - Version requirements
25. **Running and Building a React Application**
   - Development mode
   - Production builds
   - Previewing a build
   - Build output and generated files
26. **Understanding JSX Tooling**
   - JSX transformation
   - JavaScript modules
   - Development server behavior
   - Build tooling and browser compatibility
27. **Your First React Component**
   - Creating a component
   - Rendering text and HTML-like markup
   - Exporting a component
   - Importing it into the main application
28. **Mounting React into the Browser**
   - The root DOM element
   - createRoot()
   - root.render()
   - The role of React DOM
29. **React Developer Tools**
   - Inspecting the component tree
   - Examining props and state
   - Identifying unnecessary re-renders
   - Using the browser console effectively
30. **Adding React to an Existing Website**
   - Understanding incremental adoption
   - Loading React into a selected page region
   - Isolating React-managed UI
   - Integrating with existing frontend code
31. **Choosing a Project Architecture**
   - Build-tool-based single-page applications
   - Framework-based applications
   - Existing-project integration
   - Selecting a setup based on rendering and deployment needs

### Module 4: JSX and JavaScript Expressions

Difficulty: not specified · Track: core

32. **Introduction to JSX**
   - What JSX represents
   - JSX and JavaScript
   - Why JSX is useful
   - JSX transformation
33. **Writing JSX Expressions**
   - Curly braces
   - Displaying variables
   - Arithmetic expressions
   - Function calls in render expressions
34. **JSX Syntax Rules**
   - Returning a single parent expression
   - Closing tags
   - Nesting elements
   - JavaScript expressions versus statements
35. **JSX Attributes**
   - className
   - htmlFor
   - Boolean attributes
   - JavaScript expressions as attribute values
36. **Displaying Dynamic Content**
   - Variable values
   - Object properties
   - Array-derived content
   - Conditional text
   - Formatting values before rendering
37. **JSX Fragments**
   - Fragment
   - The shorthand fragment syntax
   - Grouping elements without extra DOM nodes
   - Keys on fragments in collections
38. **Conditional Rendering in JSX**
   - if statements outside JSX
   - Ternary expressions
   - Logical &&
   - Early returns
   - Selecting appropriate conditional patterns
39. **Rendering Lists in JSX**
   - Mapping arrays to elements
   - Structuring collection data
   - Rendering empty collections
   - Maintaining predictable list output
40. **Handling Styling in JSX**
   - className
   - Inline style objects
   - Dynamic class names
   - Conditional styling
41. **Common JSX Errors**
   - Missing closing tags
   - Invalid expression placement
   - Incorrect attribute naming
   - Returning adjacent elements
   - Incorrectly using objects as rendered children
   - Understanding compile-time errors
42. **JSX Best Practices**
   - Readable expressions
   - Extracting complex calculations
   - Keeping markup understandable
   - Separating data transformation from presentation

### Module 5: React Components

Difficulty: not specified · Track: core

43. **Introduction to Components**
   - Component responsibilities
   - Reusable UI sections
   - Components as building blocks
   - Identifying useful component boundaries
44. **Creating Function Components**
   - Function component syntax
   - Returning JSX
   - Naming components
   - Exporting and importing components
45. **Component Naming and Organization**
   - PascalCase naming
   - File naming conventions
   - Grouping related files
   - Separating components by responsibility
46. **Nesting Components**
   - Parent and child components
   - Component trees
   - Rendering child components
   - Understanding component relationships
47. **Rendering Components**
   - Rendering components as JSX elements
   - Rendering multiple instances
   - Reusing a component with different data
   - Understanding component output
48. **Component Identity**
   - Component type and identity
   - How React matches components between renders
   - Preserving component state
   - When a component is recreated
49. **Separating Components by Responsibility**
   - Presentation components
   - Components that manage interaction
   - Page-level components
   - Extracting repeated UI
50. **Pure Components and Render Purity**
   - Pure rendering logic
   - Avoiding mutations during render
   - Avoiding side effects during render
   - Why purity helps React optimize updates
51. **Component Lifecycle Concepts**
   - Mounting
   - Updating
   - Unmounting
   - Lifecycle concepts in function components
   - How modern Hooks relate to lifecycle behavior
52. **Class Components: Understanding Legacy React**
   - Class component structure
   - render()
   - Class state and setState()
   - Lifecycle methods
   - Existing projects that still use classes
53. **When to Split or Combine Components**
   - Avoiding oversized components
   - Avoiding excessive fragmentation
   - Defining reusable UI boundaries
   - Balancing readability and abstraction

### Module 6: Props, Composition, and Component Communication

Difficulty: not specified · Track: core

54. **Introduction to Props**
   - What props are
   - Passing values to components
   - Reading props
   - Reusing components with different props
55. **Passing Different Types of Props**
   - Strings and numbers
   - Booleans
   - Arrays and objects
   - Functions
   - JSX elements
56. **Destructuring Props**
   - Parameter destructuring
   - Default values
   - Renaming properties
   - Handling optional props
57. **The Special children Prop**
   - Passing nested JSX
   - Rendering children
   - Building reusable containers
   - Composing page layouts
58. **Component Composition**
   - Building larger components from smaller ones
   - Wrapper components
   - Layout composition
   - Slot-like APIs using props
59. **Passing Callback Functions Through Props**
   - Event callbacks
   - Passing arguments to callbacks
   - Parent-controlled interactions
   - Avoiding accidental immediate function execution
60. **Lifting State Up**
   - Identifying shared state
   - Moving state to a common parent
   - Sharing values with siblings
   - Coordinating related component behavior
61. **One-Way Data Flow**
   - Parent-to-child data
   - Child-to-parent event notifications
   - Predictable ownership of state
   - Avoiding conflicting sources of truth
62. **Props Versus State**
   - Immutable inputs
   - Component-owned data
   - Choosing the correct location for data
   - Avoiding redundant state
63. **Reusable Component API Design**
   - Clear prop names
   - Sensible defaults
   - Flexible component interfaces
   - Handling optional configuration
   - Avoiding unnecessarily complicated props

### Module 7: Rendering, Lists, and Conditional UI

Difficulty: not specified · Track: core

64. **Understanding the React Render Cycle**
   - Triggering a render
   - Calling component functions
   - Calculating the next UI
   - Committing changes to the DOM
65. **State, Render, and Commit**
   - Render phase
   - Commit phase
   - Browser-visible updates
   - Why rendering does not mean every DOM node is recreated
66. **Conditional UI Patterns**
   - Showing and hiding elements
   - Loading placeholders
   - Empty states
   - Error messages
   - Access-dependent UI
67. **Rendering Arrays of Data**
   - Mapping API data
   - Building cards and tables
   - Combining data transformations with rendering
   - Handling missing or empty data
68. **Understanding React Keys**
   - Why keys matter
   - Keys in lists
   - Stable identifiers
   - Why array positions can be problematic as keys
69. **Keys and Component State**
   - How keys influence component identity
   - State preservation between renders
   - Resetting component state with a different key
   - Avoiding unnecessary remounting
70. **Filtering and Sorting Rendered Data**
   - Search filtering
   - Category filtering
   - Sorting by properties
   - Combining filters
   - Computing derived lists
71. **Rendering Nested Data**
   - Nested arrays
   - Parent-child records
   - Grouped collections
   - Tree-shaped data
72. **Handling Empty, Missing, and Null Data**
   - Empty arrays
   - Missing object properties
   - Optional values
   - Safe rendering patterns
   - User-friendly empty states
73. **Rendering Different UI States**
   - Initial state
   - Loading state
   - Success state
   - Empty state
   - Failure state
74. **Understanding Reconciliation**
   - Comparing element types and keys
   - Reusing component instances
   - Updating existing DOM nodes
   - Replacing subtrees when identity changes
75. **Common Rendering Mistakes**
   - Missing keys
   - Unstable keys
   - Mutating arrays
   - Returning invalid children
   - Unintentionally resetting component state

### Module 8: Events and User Interaction

Difficulty: not specified · Track: core

76. **Introduction to React Events**
   - Event handlers
   - React event props
   - User interactions
   - Connecting buttons and controls to functions
77. **Handling Mouse and Pointer Events**
   - Clicks
   - Pointer interactions
   - Event targets
   - Choosing accessible interaction elements
78. **Handling Keyboard Events**
   - Key presses
   - Keyboard navigation
   - Escape and Enter behavior
   - Avoiding unnecessary custom keyboard handling
79. **Handling Form-Related Events**
   - Change events
   - Input events
   - Submit events
   - Preventing default browser behavior when necessary
80. **Passing Arguments to Event Handlers**
   - Inline callbacks
   - Capturing values in closures
   - Passing an identifier to a handler
   - Avoiding immediate invocation
81. **Understanding Event Objects**
   - Event properties
   - Target and current target
   - Default browser actions
   - Event propagation
82. **Event Propagation**
   - Bubbling
   - Stopping propagation when justified
   - Nested clickable elements
   - Choosing semantic HTML to avoid event conflicts
83. **Preventing Default Behavior**
   - Form submission
   - Link navigation
   - Default browser actions
   - Keeping custom behavior predictable
84. **Building Interactive Components**
   - Buttons and toggles
   - Dropdowns
   - Tabs
   - Modals
   - Menus and expandable sections

### Module 9: State Management Fundamentals

Difficulty: not specified · Track: core

85. **Introduction to State**
   - What state represents
   - Local UI data
   - State-driven rendering
   - Distinguishing state from regular variables
86. **Using useState**
   - Declaring state
   - Reading state values
   - State setter functions
   - Initial state values
87. **Updating State Correctly**
   - Replacing state values
   - Understanding scheduled updates
   - Avoiding direct mutations
   - Updating based on user interactions
88. **State as a Snapshot**
   - State values inside a render
   - Event handlers and captured values
   - Why updates do not immediately change the current variable
   - Avoiding stale assumptions
89. **Functional State Updates**
   - Updater functions
   - Updates based on previous state
   - Multiple updates in one event
   - Avoiding lost updates
90. **Updating Objects in State**
   - Copying existing objects
   - Changing nested properties
   - Preserving unrelated fields
   - Handling immutable object updates
91. **Updating Arrays in State**
   - Adding items
   - Removing items
   - Updating selected items
   - Reordering items
   - Avoiding mutating methods
92. **Managing Multiple State Variables**
   - Independent values
   - Related state
   - Splitting and combining state
   - Avoiding duplicated information
93. **Derived State**
   - Computing values from props and state
   - Calculating totals
   - Filtering displayed data
   - Avoiding unnecessary state variables
94. **Resetting State**
   - Reset buttons
   - Restoring initial values
   - Resetting forms
   - Using keys to reset an entire component subtree
95. **Preserving and Resetting State in the UI Tree**
   - Component position
   - Component type
   - Keys and identity
   - State preservation during conditional rendering
96. **Sharing State Across Components**
   - Lifting state
   - Prop drilling
   - Shared ownership
   - Identifying the nearest common parent
97. **State Structure Best Practices**
   - Avoiding contradictory states
   - Avoiding duplicated data
   - Keeping state minimal
   - Modeling UI states clearly
98. **Avoiding State Mutation Bugs**
   - Nested object mutation
   - Array mutation
   - Incorrect reference reuse
   - Recognizing unexpected render behavior
99. **Batching State Updates**
   - Multiple updates in one interaction
   - React's update batching
   - Functional updates
   - Avoiding assumptions about immediate rendering
100. **Debugging State Problems**
   - Inspecting current values
   - Tracing event handlers
   - Understanding stale closures
   - Reproducing state-related bugs

### Module 10: Forms and User Input

Difficulty: not specified · Track: core

101. **Introduction to Forms in React**
   - Native HTML forms
   - React-managed values
   - Handling form submission
   - Choosing an appropriate form architecture
102. **Controlled Components**
   - State-controlled input values
   - value and onChange
   - Controlling text fields
   - Synchronizing input and application state
103. **Uncontrolled Components**
   - Browser-managed input values
   - defaultValue
   - Reading values with refs
   - Choosing controlled or uncontrolled inputs
104. **Text and Multiline Inputs**
   - Text fields
   - Textareas
   - Search inputs
   - Updating form state
105. **Checkboxes and Radio Buttons**
   - Boolean input state
   - Radio groups
   - Selected values
   - Handling collections of selectable options
106. **Select Menus**
   - Selected options
   - Controlled select elements
   - Multiple selection
   - Dynamic options
107. **Number, Date, and Specialized Inputs**
   - Number fields
   - Date and time fields
   - Email and URL inputs
   - Input parsing and validation
108. **Handling Form Submission**
   - Submit handlers
   - Preventing page reloads
   - Reading form data
   - Submitting to an API
109. **Form Validation**
   - Required fields
   - Format validation
   - Range and length checks
   - Cross-field validation
   - Displaying field-specific errors
110. **Form Error Handling**
   - Server validation errors
   - Network failures
   - Invalid input
   - Error summaries
   - Correcting errors without losing user input
111. **Multi-Step Forms**
   - Step navigation
   - Retaining entered data
   - Step-level validation
   - Final submission
112. **Dynamic Forms**
   - Adding and removing fields
   - Repeating field groups
   - Conditional fields
   - Managing dynamic field identities
113. **File Inputs and Upload Interfaces**
   - Selecting files
   - File metadata
   - File size and type checks
   - Upload progress
   - Previewing permitted file formats
114. **Form Accessibility and Usability**
   - Labels
   - Instructions and descriptions
   - Validation feedback
   - Focus management
   - Keyboard navigation

### Module 11: React Hooks

Difficulty: not specified · Track: core

115. **Introduction to Hooks**
   - Why Hooks exist
   - Reusing stateful logic
   - Built-in versus custom Hooks
   - Hooks and function components
116. **Rules of Hooks**
   - Calling Hooks at the top level
   - Calling Hooks from React components or custom Hooks
   - Avoiding Hooks inside conditions and loops
   - Enforcing the rules with linting
117. **useState in Greater Depth**
   - Lazy initialization
   - Functional updates
   - Independent state values
   - State update patterns
118. **useEffect Fundamentals**
   - Synchronizing with external systems
   - Setting up an Effect
   - Dependency arrays
   - Cleanup functions
119. **useContext**
   - Reading Context
   - Accessing shared values
   - Provider-consumer relationships
   - When Context is appropriate
120. **useReducer**
   - Reducer functions
   - Initial state
   - Actions
   - Dispatching updates
   - Structuring complex state transitions
121. **useRef**
   - Persistent values between renders
   - Mutable references
   - Accessing DOM elements
   - Why changing a ref does not itself trigger a render
122. **useMemo**
   - Caching expensive calculations
   - Dependency management
   - Comparing calculated values
   - Knowing when memoization is unnecessary
123. **useCallback**
   - Caching function references
   - Passing callbacks to optimized children
   - Dependency management
   - Avoiding unnecessary memoization
124. **useTransition**
   - Marking updates as non-urgent
   - Pending transition states
   - Maintaining UI responsiveness
   - Combining transitions with asynchronous Actions
125. **useDeferredValue**
   - Deferring non-urgent values
   - Responsive search interfaces
   - Handling expensive rendering
   - Understanding what it does not guarantee
126. **useId**
   - Generating IDs for accessibility relationships
   - Connecting labels and controls
   - Stable IDs within a component tree
   - Avoiding its use for list keys
127. **useSyncExternalStore**
   - Subscribing to external stores
   - Reading external snapshots
   - Managing subscription cleanup
   - Integrating store-based libraries
128. **useImperativeHandle**
   - Customizing exposed refs
   - Limiting imperative interfaces
   - Interacting with non-React integrations
   - Understanding when declarative props are preferable
129. **Writing Custom Hooks**
   - Extracting shared logic
   - Naming conventions
   - Accepting parameters
   - Returning values and functions
   - Documenting Hook behavior
130. **Testing and Debugging Hooks**
   - Rules-of-Hooks errors
   - Testing stateful behavior through components
   - Dependency debugging
   - Reusing Hooks without duplicating state
   - React's official Hooks reference separates state, context, refs, Effects, and other categories. These
   - lessons should teach Hooks as individual tools with distinct responsibilities, not as a collection of
   - interchangeable utilities.
   - React

### Module 12: Effects, External Systems, and Asynchronous Behavior

Difficulty: not specified · Track: advanced

131. **Understanding Effects**
   - Why Effects exist
   - Synchronization with external systems
   - Effects versus event handlers
   - Effects versus derived data
132. **Effect Dependencies**
   - Reactive values
   - Dependency arrays
   - How dependency comparison works
   - Understanding why Effects rerun
133. **Effect Cleanup**
   - Cleaning up subscriptions
   - Clearing timers
   - Removing event listeners
   - Releasing resources
134. **Avoiding Unnecessary Effects**
   - Computing derived values during render
   - Handling events in event handlers
   - Resetting state without synchronization Effects
   - Recognizing unnecessary rendering cycles
135. **Connecting React to Browser APIs**
   - Browser event listeners
   - Timers
   - Online and offline state
   - Media-query subscriptions
   - Other external browser capabilities
136. **Integrating Non-React Libraries**
   - External widgets
   - Imperative UI libraries
   - Synchronizing external state
   - Cleanup and integration boundaries
137. **Data Fetching in Effects**
   - Initiating requests
   - Loading and error states
   - Updating displayed data
   - Managing request lifecycle
138. **Effect Race Conditions**
   - Requests completing out of order
   - Ignoring obsolete responses
   - Cleanup strategies
   - Abortable requests
139. **Effect Events and Non-Reactive Logic**
   - Understanding when logic should not resubscribe
   - The role of useEffectEvent
   - Separating Effect synchronization from event-like logic
   - Avoiding misuse of non-reactive logic
140. **Asynchronous Error Handling**
   - Promise rejections
   - API failures
   - Timeouts
   - Cancellation
   - Recovery and retry policies
141. **Synchronization Versus Initialization**
   - One-time initialization
   - Synchronizing after dependencies change
   - External-system consistency
   - Avoiding mount-only assumptions
142. **Common Effect Bugs**
   - Infinite loops
   - Missing dependencies
   - Stale closures
   - Duplicate subscriptions
   - Incorrect cleanup
143. **Effect Best Practices**
   - Keep Effects focused
   - Follow dependency rules
   - Prefer framework or data-layer fetching when appropriate
   - Keep external synchronization predictable
   - The official React guidance specifically recommends avoiding Effects for ordinary derived data and
   - event-driven actions when those tasks can be handled directly in render calculations or event
   - handlers.
   - React

### Module 13: Refs, the DOM, and Imperative Interactions

Difficulty: not specified · Track: core

144. **Accessing DOM Elements with Refs**
   - useRef
   - Attaching refs
   - Reading DOM properties
   - Null checks and element availability
145. **Managing Focus**
   - Focusing inputs
   - Returning focus after dialogs
   - Moving focus after form submission
   - Focus restoration
146. **Scrolling and Measuring Elements**
   - Scrolling to sections
   - Element measurements
   - Layout-dependent calculations
   - Timing considerations
147. **Handling Imperative Browser APIs**
   - DOM APIs
   - Media elements
   - Browser observers
   - Integrating third-party widgets
148. **Forwarding and Exposing Refs**
   - Ref ownership
   - forwardRef in applicable React versions and compatibility work
   - Ref props in modern React
   - Defining public ref interfaces
149. **Fragment Refs**
   - Ref support for Fragments
   - Working with grouped DOM content
   - Focus and visibility-related operations
   - Version requirements and appropriate use
150. **Managing Imperative Component APIs**
   - Exposed methods
   - useImperativeHandle
   - Narrow public interfaces
   - Preferring props for normal UI state
151. **Ref Best Practices**
   - Avoiding render-driving mutable state in refs
   - Avoiding unnecessary DOM mutation
   - Managing element lifecycle
   - Using refs only when appropriate

### Module 14: Context, Reducers, and Application State Architecture

Difficulty: not specified · Track: advanced

152. **Understanding React Context**
   - Creating Context
   - Providing values
   - Reading Context with useContext
   - Default values
153. **Designing Context Providers**
   - Provider placement
   - Provider composition
   - Shared application values
   - Separating unrelated contexts
154. **Avoiding Excessive Prop Drilling**
   - Identifying genuinely shared data
   - Context as an alternative
   - Component composition as an alternative
   - Balancing simplicity and flexibility
155. **Combining Context with Reducers**
   - Reducer-driven updates
   - Dispatch through Context
   - Centralized state transitions
   - Shared state across page sections
156. **Managing Complex State**
   - State transition models
   - Related data and invariants
   - Modeling mutually exclusive states
   - Keeping update logic testable
157. **State Management Architecture Choices**
   - Local component state
   - Lifted state
   - Context
   - Reducers
   - External state stores
158. **External State Libraries**
   - Why external stores exist
   - Store subscriptions
   - Zustand
   - Redux Toolkit
   - Choosing based on application requirements
159. **Server State Versus Client State**
   - Data fetched from APIs
   - Temporary UI state
   - Caching server responses
   - Invalidating stale data
   - Avoiding unnecessary duplication
160. **State Persistence**
   - Persisting preferences
   - Local and session storage
   - Restoring state
   - Handling schema changes and storage errors
161. **State Architecture Best Practices**
   - Single source of truth
   - Clear ownership
   - Predictable transitions
   - Avoiding unnecessary global state
   - Testing state logic independently

### Module 15: Routing and Navigation

Difficulty: not specified · Track: core

162. **Introduction to Client-Side Routing**
   - What routing solves
   - URL-based application state
   - Single-page navigation
   - Browser history
163. **Setting Up a Routing Library**
   - Installing a routing package
   - Configuring routes
   - Choosing a routing architecture
   - Understanding routing-library responsibilities
164. **Defining Routes**
   - Route paths
   - Page components
   - Default routes
   - Not-found pages
165. **Navigation Links**
   - Internal links
   - Navigation components
   - Active links
   - Avoiding unnecessary full-page reloads
166. **Dynamic Route Parameters**
   - Parameterized paths
   - Reading route parameters
   - Validating identifiers
   - Rendering resource-specific pages
167. **Nested Routes and Layouts**
   - Parent routes
   - Child routes
   - Layout components
   - Outlet-based rendering
   - Shared navigation and page structure
168. **Query Parameters**
   - Search parameters
   - Filters in URLs
   - Pagination parameters
   - Reading and updating query strings
169. **Programmatic Navigation**
   - Navigation after submission
   - Redirecting after an action
   - Back and forward navigation
   - Avoiding navigation loops
170. **Protected and Permission-Aware Routes**
   - Authentication state
   - UI-level access handling
   - Redirecting unauthenticated users
   - Why server-side authorization is still required
171. **Route-Based Loading and Error Handling**
   - Route-level loading
   - Missing resources
   - Route errors
   - Recoverable navigation failures
172. **Code Splitting by Route**
   - Lazy-loaded page components
   - Route-level bundles
   - Loading fallbacks
   - Avoiding oversized initial bundles
173. **Routing Architecture and Testing**
   - Route configuration
   - Deep links
   - Refreshing nested routes
   - Browser history testing
   - Handling unknown routes

### Module 16: Working with APIs and Remote Data

Difficulty: not specified · Track: advanced

174. **Understanding HTTP and APIs**
   - Requests and responses
   - HTTP methods
   - Headers
   - Status codes
   - JSON payloads
175. **Making Requests with fetch()**
   - GET requests
   - Request options
   - Parsing JSON
   - Understanding that HTTP error statuses need explicit handling
176. **Sending Data to an API**
   - POST requests
   - PUT and PATCH
   - DELETE requests
   - Request bodies
   - Content-type headers
177. **Loading Data into React**
   - Managing loaded data
   - Loading indicators
   - Error messages
   - Empty responses
   - Refreshing displayed results
178. **Building a Reusable API Layer**
   - Shared request functions
   - Base URLs
   - Centralized response parsing
   - Common error handling
   - Avoiding duplicate networking logic
179. **Environment Configuration for APIs**
   - Development and production endpoints
   - Environment variables
   - Public versus private configuration
   - Avoiding secrets in frontend bundles
180. **API Pagination**
   - Page-based pagination
   - Cursor-based pagination
   - Next and previous controls
   - Preserving filters while changing pages
181. **Search and Filtering with APIs**
   - Search requests
   - Query parameters
   - Debouncing input
   - Avoiding outdated responses
   - Displaying matching results
182. **Data Caching**
   - Cache keys
   - Cached responses
   - Freshness and staleness
   - Cache invalidation
   - Sharing cached data between components
183. **Data Fetching Libraries**
   - TanStack Query
   - SWR
   - Request deduplication
   - Background refetching
   - Choosing a data-fetching strategy
184. **Mutations and Server Updates**
   - Creating records
   - Updating records
   - Deleting records
   - Refreshing or invalidating cached data
   - Handling failed mutations
185. **Authentication and Session Integration**
   - Login and logout flows
   - Token and cookie concepts
   - Session expiration
   - Refreshing authenticated data
   - Respecting server-side authorization
186. **Real-Time Data and Subscriptions**
   - WebSockets
   - Server-sent events
   - Subscription setup and cleanup
   - Updating state from live events
187. **Uploading and Downloading Data**
   - Multipart form data
   - Progress indicators
   - File downloads
   - Retry and cancellation
   - Handling failed transfers
188. **API Reliability and Resilience**
   - Retries and backoff
   - Timeouts
   - Cancellation
   - Request race conditions
   - Error monitoring and graceful degradation

### Module 17: Modern React Actions, Concurrency, and Form APIs

Difficulty: not specified · Track: advanced

189. **Understanding Modern React Actions**
   - Asynchronous mutations
   - Pending state
   - Success and failure
   - Coordinating updates with React
190. **Function-Based Form Actions**
   - Passing functions to form action
   - Form submission using Actions
   - Form data handling
   - Uncontrolled form reset behavior
191. **useActionState**
   - Managing Action results
   - Tracking pending status
   - Validation responses
   - Reusing Action state in forms
192. **useFormStatus**
   - Reading the parent form's status
   - Pending submit buttons
   - Reusable form controls
   - Form-state-aware UI
193. **useOptimistic**
   - Displaying optimistic results
   - Applying temporary UI changes
   - Handling failure and rollback
   - Reconciling server responses
194. **requestFormReset**
   - Resetting form state through the React DOM API
   - Coordinating reset behavior with Actions
   - Choosing when a form should reset
195. **Understanding Transitions**
   - Urgent versus non-urgent updates
   - Transition scheduling
   - Pending transitions
   - Maintaining interaction responsiveness
196. **The React use API**
   - Reading supported resources
   - Reading Promises
   - Reading Context
   - Suspense integration
   - Resource caching requirements
197. **Suspense Boundaries**
   - Fallback UI
   - Suspended rendering
   - Boundary placement
   - Coordinating loading states
   - Avoiding unnecessarily broad fallbacks
198. **Error and Loading Boundaries for Async UI**
   - Separating loading from failure
   - Handling rejected resources
   - Error-boundary integration
   - Retry and recovery interfaces
199. **Activity-Based UI Rendering**
   - The <Activity /> component
   - Managing activities in a UI
   - Preserving or managing hidden UI state
   - Appropriate use cases and trade-offs
200. **View Transitions**
   - The <ViewTransition /> component
   - Animating UI changes
   - Entry, exit, movement, and resizing transitions
   - Coordinating transitions with updates
   - Accessibility and reduced-motion considerations
201. **Modern React Version Compatibility**
   - Checking API availability
   - Pinning compatible package versions
   - Reading release notes
   - Distinguishing stable features from experimental APIs
   - Migration planning
   - React 19 added Actions, useActionState , useOptimistic , function-based form Actions, and
   - useFormStatus . React 19.3 subsequently stabilized View Transitions and Fragment Refs. These
   - lessons should be version-labeled within the educational platform so students can distinguish
   - foundational React concepts from newer capabilities.

### Module 18: Styling, Assets, and UI Composition

Difficulty: not specified · Track: core

202. **Styling React Components**
   - Applying CSS classes
   - Component stylesheets
   - Global versus local styling
   - Organizing style files
203. **Conditional and Dynamic Styling**
   - Conditional class names
   - State-driven styling
   - Dynamic inline styles
   - Avoiding conflicting style conditions
204. **CSS Modules**
   - Scoped class names
   - Module imports
   - Component-specific styles
   - Combining modules with shared design tokens
205. **CSS-in-JS**
   - The concept of styling through JavaScript
   - Library-based styling
   - Dynamic style values
   - Runtime and build-time trade-offs
206. **Utility-First CSS Integration**
   - Utility-class workflows
   - Responsive variants
   - State variants
   - Organizing complex component styles
207. **Component Libraries and Design Systems**
   - UI library integration
   - Reusable design primitives
   - Theme configuration
   - Customization and consistency
208. **Managing Static Assets**
   - Image assets
   - SVG assets
   - Fonts
   - Asset imports
   - Public assets versus bundled assets
209. **Responsive Design**
   - Responsive layouts
   - Mobile-first styling
   - Responsive navigation
   - Flexible images and containers
   - Testing multiple viewport sizes
210. **Animation and Motion**
   - CSS transitions
   - CSS animations
   - Animation libraries
   - Motion preferences
   - React View Transitions where supported
211. **Designing Reusable Layouts**
   - Headers and footers
   - Navigation shells
   - Sidebars and content areas
   - Card layouts
   - Shared visual patterns

### Module 19: Accessibility and Usability

Difficulty: not specified · Track: core

212. **Introduction to Accessible React Interfaces**
   - Accessibility fundamentals
   - Semantic HTML
   - Inclusive interaction design
   - Accessibility as part of component design
213. **Semantic Elements**
   - Buttons versus clickable containers
   - Links versus buttons
   - Headings and landmarks
   - Native controls
214. **Accessible Forms**
   - Labels
   - Descriptions
   - Required fields
   - Error messages
   - Programmatic field relationships
215. **Keyboard Accessibility**
   - Keyboard-operable controls
   - Tab order
   - Focus indicators
   - Escape behavior
   - Avoiding keyboard traps
216. **Managing Focus in React**
   - Focus after navigation
   - Modal focus
   - Focus after submitting forms
   - Focus restoration
217. **Accessible Dialogs, Menus, and Tabs**
   - Roles and semantics
   - Focus handling
   - Keyboard interaction patterns
   - Dismissal behavior
218. **Screen Readers and Accessible Names**
   - Accessible labels
   - Alternative text
   - ARIA attributes
   - Announcements for dynamic content
219. **Dynamic UI and Live Regions**
   - Loading announcements
   - Form errors
   - Notifications
   - Asynchronous state changes
   - Avoiding unnecessary announcements
220. **Accessibility Testing**
   - Automated accessibility checks
   - Keyboard-only testing
   - Screen-reader testing
   - Contrast checks
   - Recognizing limitations of automated tools

### Module 20: Testing React Applications

Difficulty: not specified · Track: advanced

221. **Introduction to React Testing**
   - Purpose of tests
   - Unit, integration, and end-to-end tests
   - Test-driven workflows
   - What should and should not be mocked
222. **Setting Up a Testing Environment**
   - Choosing a test runner
   - Configuring Vitest or an equivalent runner
   - Test scripts
   - Environment configuration
223. **Testing Individual Components**
   - Rendering components
   - Checking visible text
   - Inspecting accessible elements
   - Testing different prop values
224. **React Testing Library**
   - User-centered testing
   - Queries based on accessible roles and labels
   - Avoiding implementation-detail tests
   - Understanding its guiding principles
225. **Simulating User Interactions**
   - Click interactions
   - Typing and input changes
   - Keyboard interactions
   - Form submission
   - Asynchronous user workflows
226. **Testing State Changes**
   - Initial state
   - Updated UI
   - Conditional rendering
   - Multiple consecutive interactions
227. **Testing Forms and Validation**
   - Required fields
   - Invalid input
   - Successful submission
   - Server validation errors
   - Loading and pending states
228. **Mocking API Requests**
   - Successful responses
   - Error responses
   - Delayed requests
   - Empty responses
   - Network failure scenarios
229. **Testing Custom Hooks**
   - Testing through component behavior
   - Extracting pure logic for direct testing
   - Managing asynchronous state
   - Avoiding tests tied to internal implementation
230. **Testing Routing**
   - Route rendering
   - Navigation
   - URL parameters
   - Not-found pages
   - Protected UI flows
231. **Testing Error Boundaries**
   - Rendering fallbacks
   - Recovery behavior
   - Unexpected rendering errors
   - Keeping tests isolated
232. **End-to-End Testing**
   - Browser-based tests
   - Playwright or equivalent tools
   - Login and checkout workflows
   - Realistic browser interactions
233. **Accessibility and Visual Regression Testing**
   - Automated accessibility checks
   - Visual snapshots
   - Responsive layout tests
   - Handling unstable snapshots
234. **Coverage, CI, and Test Maintenance**
   - Measuring coverage
   - Avoiding meaningless coverage targets
   - Running tests in CI
   - Debugging flaky tests
   - Maintaining a reliable test suite

### Module 21: Debugging and Error Handling

Difficulty: not specified · Track: core

235. **Reading React Error Messages**
   - Console warnings
   - Runtime exceptions
   - Rendering failures
   - Build-time errors
   - Finding the relevant component
236. **Debugging JSX and Component Errors**
   - Invalid children
   - Missing imports
   - Incorrect component exports
   - JSX syntax problems
237. **Debugging Hooks**
   - Rules-of-Hooks violations
   - Incorrect dependencies
   - Stale closures
   - Unexpected Effect execution
   - Hook-related lint warnings
238. **Debugging State Problems**
   - Incorrect updates
   - Mutated objects
   - Stale state assumptions
   - Unexpected state resets
   - Component identity problems
239. **Using React Developer Tools**
   - Component inspection
   - Props and state
   - Render profiling
   - Context inspection
   - Identifying component relationships
240. **Error Boundaries**
   - What they catch
   - Fallback interfaces
   - Recovery patterns
   - Error boundaries versus ordinary event errors
241. **Network and API Debugging**
   - Browser network tools
   - HTTP statuses
   - Request and response payloads
   - CORS errors
   - Authentication failures
242. **Debugging Development and Production Differences**
   - Development checks
   - Production builds
   - Environment variables
   - Build-time versus runtime failures
   - Reproducing production issues
243. **Logging and Error Monitoring**
   - Structured error reporting
   - Contextual information
   - Privacy-conscious logging
   - Monitoring unexpected failures
244. **Systematic Troubleshooting**
   - Reproducing the issue
   - Isolating the relevant component
   - Creating a minimal example
   - Testing one change at a time
   - Verifying the fix

### Module 22: Performance Optimization

Difficulty: not specified · Track: advanced

245. **Understanding React Performance**
   - Render frequency
   - Expensive computations
   - DOM updates
   - Network and bundle costs
   - User-perceived performance
246. **Measuring Before Optimizing**
   - Browser performance tools
   - React Profiler
   - Measuring component rendering
   - Identifying meaningful bottlenecks
247. **Understanding Re-Renders**
   - Parent renders
   - State changes
   - Context updates
   - Prop changes
   - Render versus DOM mutation
248. **Using React.memo**
   - Memoizing component rendering
   - Prop comparison
   - Stable versus new object references
   - When memoization helps
249. **Optimizing Expensive Calculations**
   - useMemo
   - Derived data
   - Algorithmic improvements
   - Avoiding unnecessary state updates
250. **Optimizing Callbacks and References**
   - useCallback
   - Stable function references
   - Reference equality
   - Avoiding unnecessary complexity
251. **React Compiler**
   - Automatic memoization
   - Compiler configuration
   - Compatibility and adoption
   - Compiler diagnostics
   - Evaluating actual performance improvements
252. **List Rendering Performance**
   - Large lists
   - Stable keys
   - Virtualization
   - Reducing unnecessary item rendering
   - Measuring scrolling performance
253. **Code Splitting**
   - Dynamic imports
   - lazy
   - Suspense fallbacks
   - Route-based loading
   - Reducing initial JavaScript
254. **Bundle Analysis**
   - Bundle size
   - Dependency analysis
   - Tree shaking
   - Duplicate dependencies
   - Removing unused code
255. **Scheduling and Responsive UI**
   - Transitions
   - Deferred values
   - Expensive search interfaces
   - Keeping urgent input responsive
256. **Server Rendering and Performance**
   - Initial HTML delivery
   - Streaming
   - Hydration costs
   - Static generation
   - Choosing an appropriate rendering strategy
257. **Performance Budgets and Verification**
   - Performance targets
   - Real-user measurements
   - Core Web Vitals
   - Regression monitoring
   - Verifying improvements with measurements
   - The React Compiler is a documented build-time optimization tool designed to handle many
   - memoization cases automatically. Learners should still understand profiling and manual memoization,
   - but should also understand when the compiler can reduce the need to write useMemo ,
   - useCallback , and React.memo explicitly.

### Module 23: React Architecture and Code Quality

Difficulty: not specified · Track: advanced

258. **Designing a Maintainable React Application**
   - Component boundaries
   - Feature organization
   - Separation of concerns
   - Keeping related logic together
259. **Organizing Files and Folders**
   - Feature-based structure
   - Shared components
   - Hooks and utility modules
   - Page and route organization
260. **Reusable UI Architecture**
   - Primitive components
   - Compound components
   - Composition patterns
   - Reusability versus premature abstraction
261. **Container and Presentation Responsibilities**
   - Data orchestration
   - Rendering responsibilities
   - Separation without excessive fragmentation
   - Testing boundaries
262. **Custom Hooks as Architectural Tools**
   - Reusing logic
   - Separating component behavior
   - Encapsulating subscriptions
   - Defining stable Hook interfaces
263. **Managing Application Configuration**
   - Environment-specific values
   - Feature configuration
   - Constants
   - Build-time versus runtime configuration
264. **Error and Loading State Architecture**
   - Shared loading patterns
   - Error boundaries
   - Page-level error handling
   - Reusable feedback components
265. **Design Systems and Component Contracts**
   - Shared design tokens
   - Consistent UI patterns
   - API stability
   - Component documentation
266. **JavaScript Quality Standards**
   - ESLint
   - React Hooks lint rules
   - Formatting
   - Naming conventions
   - Consistent code review standards
267. **Type Safety Options**
   - Documenting JavaScript props
   - PropTypes in existing projects
   - JSDoc
   - TypeScript as an optional extension
   - Checking package type support
268. **Refactoring React Applications**
   - Identifying duplication
   - Extracting components
   - Simplifying state
   - Reducing dependencies between components
   - Refactoring without breaking behavior
269. **Architectural Decision-Making**
   - Choosing local or global state
   - Choosing routing and data libraries
   - Evaluating framework requirements
   - Documenting trade-offs
   - Scaling an application incrementally

### Module 24: Rendering Architectures — SPA, SSR, SSG, and Streaming

Difficulty: not specified · Track: advanced

270. **Understanding React Rendering Architectures**
   - Client-side rendering
   - Server-side rendering
   - Static-site generation
   - Streaming server rendering
   - Hybrid rendering
271. **Single-Page Applications**
   - Client-side application bootstrap
   - Navigation without full reloads
   - SPA hosting requirements
   - Initial-loading trade-offs
272. **Server-Side Rendering**
   - Generating HTML on the server
   - Request-time rendering
   - Sending initial HTML
   - Server and browser responsibilities
273. **Hydration**
   - hydrateRoot()
   - Making server-rendered markup interactive
   - Matching initial server and client output
   - Diagnosing hydration mismatches
274. **Static Generation**
   - Generating pages ahead of time
   - Build-time data
   - Static hosting
   - Revalidation strategies provided by the chosen framework
275. **Streaming Server Rendering**
   - Streamed HTML
   - React DOM server APIs
   - Progressive rendering
   - Node.js streams and Web Streams
276. **Suspense in Server Rendering**
   - Suspense boundaries
   - Progressive delivery
   - Streaming fallbacks
   - Error handling during server rendering
277. **Hydration and Browser-Only APIs**
   - Avoiding server references to unavailable browser globals
   - Browser-dependent content
   - Consistent initial rendering
   - Handling browser-only functionality
278. **Server Rendering Data Requirements**
   - Loading data for initial output
   - Handling failures
   - Avoiding unnecessary duplicate requests
   - Framework-managed data loading
279. **Choosing a Rendering Strategy**
   - Application interactivity
   - Initial content delivery
   - SEO requirements
   - Hosting constraints
   - Team and maintenance costs
280. **React DOM Server APIs**
   - renderToString
   - Static rendering APIs
   - renderToPipeableStream
   - renderToReadableStream
   - Understanding framework-managed server rendering
281. **Common SSR Problems**
   - Hydration mismatches
   - Non-deterministic rendering
   - Browser-only dependencies
   - Incorrect data availability
   - Server rendering errors
282. **Rendering Architecture Performance**
   - Initial render
   - Streaming and progressive content
   - Hydration work
   - Caching
   - Measuring end-user impact
   - React's official server APIs distinguish Node.js stream rendering from Web Streams, and its
   - documentation notes that frameworks often manage these APIs on behalf of application developers.

### Module 25: React Server Components and Server Functions

Difficulty: not specified · Track: advanced

283. **Introduction to React Server Components**
   - What Server Components are
   - Server execution environments
   - Build-time versus request-time execution
   - How Server Components differ from SSR
284. **Server Components Versus Client Components**
   - Server-only execution
   - Interactive client components
   - Component tree boundaries
   - Deciding where interactivity is needed
285. **React Server Components in Frameworks**
   - Framework support
   - Bundler responsibilities
   - File conventions used by particular frameworks
   - Compatibility constraints
286. **Client Boundaries**
   - Client-entry components
   - Interactive UI
   - Serializable props
   - Avoiding unnecessarily large client boundaries
287. **Server-to-Client Data Flow**
   - Loading data on the server
   - Passing results to client components
   - Data serialization
   - Avoiding exposure of private server values
288. **Server Functions**
   - Server-executed functions
   - Client references to server functions
   - Asynchronous execution
   - Request-response behavior
289. **Server Function Actions**
   - Form Actions
   - Server mutations
   - Returned validation results
   - Integrating server operations with client UI
290. **Data Access in Server Components**
   - Server-only modules
   - Database access through supported framework patterns
   - Avoiding client-side exposure of credentials
   - Handling data-loading errors
291. **Security of Server Functions**
   - Authentication
   - Authorization
   - Input validation
   - Trust boundaries
   - Sensitive data handling
292. **Server Component Performance**
   - Minimizing unnecessary client JavaScript
   - Server-side data loading
   - Streaming integration
   - Caching considerations
   - Avoiding expensive serialized payloads
293. **Server Component Limitations and Trade-Offs**
   - Framework dependencies
   - Client interactivity boundaries
   - Server runtime constraints
   - Debugging across execution environments
   - Build and deployment complexity
294. **Framework-Specific Server Architecture**
   - Reading framework documentation
   - Understanding supported conventions
   - Version compatibility
   - Selecting architecture based on actual requirements
   - Server Components and Server Functions are important advanced topics, but their implementation
   - depends on the supporting framework or bundler. React's documentation distinguishes stable
   - component functionality from underlying infrastructure APIs that have different compatibility
   - guarantees.

### Module 26: React Security and Privacy

Difficulty: not specified · Track: advanced

295. **Introduction to Frontend Security**
   - Frontend versus backend security responsibilities
   - Trust boundaries
   - Client-side validation limitations
   - Secure application design
296. **Preventing Cross-Site Scripting**
   - Rendering untrusted text
   - Escaping and HTML interpretation
   - Avoiding unsafe HTML insertion
   - Reviewing third-party rendering libraries
297. **Handling Untrusted HTML**
   - dangerouslySetInnerHTML
   - Content sanitization
   - Trust assumptions
   - Trusted Types concepts
298. **Authentication and Authorization UI**
   - Login interfaces
   - Session expiration
   - Permission-aware rendering
   - Why hidden buttons do not enforce authorization
299. **Managing Sensitive Configuration**
   - Public environment variables
   - Server-only secrets
   - Build output inspection
   - Avoiding secrets in client-side code
300. **Secure API Communication**
   - HTTPS
   - Credential handling
   - Cookie and token considerations
   - Secure request practices
301. **Cross-Origin Resource Sharing**
   - Understanding CORS
   - Browser-enforced origin rules
   - Configuring requests with backend support
   - Diagnosing CORS failures
302. **Frontend Input Validation**
   - Data format validation
   - Length and range limits
   - User feedback
   - Server-side validation requirements
303. **Dependency Security**
   - Package auditing
   - Dependency updates
   - Lockfiles
   - Vulnerability response
   - Avoiding untrusted packages
304. **Privacy-Aware React Development**
   - Avoiding sensitive console logs
   - Minimizing collection of personal data
   - Secure error reporting
   - Protecting user input and uploaded data

### Module 27: Deployment, Build Optimization, and CI/CD

Difficulty: not specified · Track: advanced

305. **Preparing React for Production**
   - Production build
   - Build warnings
   - Dependency review
   - Environment configuration
   - Release readiness
306. **Understanding Build Artifacts**
   - Generated HTML
   - JavaScript bundles
   - CSS and assets
   - Source maps
   - Static file delivery
307. **Deploying a React SPA**
   - Static hosting
   - Build commands
   - Output directories
   - SPA route fallback configuration
   - Custom domains and HTTPS
308. **Deploying a React Framework Application**
   - Framework-specific builds
   - Runtime requirements
   - Static and dynamic routes
   - Server deployment constraints
   - Understanding platform support
309. **Environment Variables Across Deployments**
   - Development values
   - Preview values
   - Production configuration
   - Public versus private values
   - Rebuilding after build-time changes
310. **Production Routing and Deep Links**
   - Refreshing nested URLs
   - Server rewrites
   - Not-found behavior
   - Route-specific metadata
311. **Performance Before Deployment**
   - Build size
   - Asset optimization
   - Image delivery
   - Code splitting
   - Production profiling
312. **Continuous Integration**
   - Automated linting
   - Running unit tests
   - Building the application
   - Reproducible dependency installation
313. **Continuous Deployment**
   - Deployment previews
   - Release promotion
   - Environment separation
   - Rollback planning
   - Smoke testing
314. **Production Monitoring**
   - Runtime errors
   - Web performance metrics
   - Logging
   - User-visible failures
   - Monitoring configuration
315. **Maintaining Deployed Applications**
   - Version updates
   - Dependency upgrades
   - Incident response
   - Safe configuration changes
   - Recovery procedures

### Module 28: Ecosystem, Legacy React, and Collaboration

Difficulty: not specified · Track: legacy

316. **Exploring the React Ecosystem**
   - Routing libraries
   - Data-fetching libraries
   - State management
   - UI component libraries
   - Testing tools
317. **Selecting Third-Party Libraries**
   - Project requirements
   - Maintenance and support
   - Bundle size
   - Accessibility
   - Licensing and security considerations
318. **Working with Existing React Applications**
   - Understanding unfamiliar code
   - Inspecting dependencies
   - Identifying entry points
   - Tracing component hierarchies
319. **Legacy Class Component Maintenance**
   - Existing lifecycle methods
   - Class state
   - setState()
   - Error boundaries in class-based projects
   - Approaches to incremental modernization
320. **Legacy API and Tool Migration**
   - Deprecated tooling
   - Old package versions
   - Updating React DOM integration
   - Replacing obsolete setup instructions
   - Reading migration guides
321. **Migrating to Modern React Patterns**
   - Moving reusable logic into Hooks where appropriate
   - Simplifying lifecycle-driven logic
   - Adopting function components incrementally
   - Preserving application behavior
322. **Version Upgrades**
   - Reviewing release notes
   - Reading upgrade guides
   - Identifying breaking changes
   - Testing dependency compatibility
   - Planning safe upgrades
323. **Git and Collaborative Development**
   - Branches and commits
   - Pull requests
   - Code reviews
   - Resolving merge conflicts
   - Collaborating on component interfaces
324. **React Code Review**
   - Component clarity
   - State ownership
   - Effect correctness
   - Accessibility
   - Security and performance
325. **Documentation for React Projects**
   - Setup instructions
   - Component usage
   - Architecture decisions
   - API integration notes
   - Troubleshooting documentation
326. **Contributing to React Projects**
   - Understanding contribution guidelines
   - Issue investigation
   - Reproduction examples
   - Writing tests
   - Reviewing proposed changes

### Module 29: Professional React Engineering and Portfolio Readiness

Difficulty: not specified · Track: advanced

327. **React Application Requirements and Planning**
   - Defining functional requirements
   - Mapping UI states
   - Identifying reusable components
   - Planning data and API dependencies
328. **Translating Designs into Components**
   - Breaking interfaces into component trees
   - Identifying reusable patterns
   - Handling responsive designs
   - Coordinating design and implementation
329. **Building Reliable User Workflows**
   - Loading and success states
   - Empty and error states
   - Form validation
   - Retry and recovery paths
   - Preventing duplicate submissions where necessary
330. **Reviewing Production Readiness**
   - Functional completeness
   - Accessibility checks
   - Test coverage
   - Security review
   - Performance verification
331. **Maintaining a React Portfolio**
   - Selecting meaningful projects
   - Writing project documentation
   - Demonstrating architecture choices
   - Showing tests and deployments
   - Explaining trade-offs
332. **React Interview Preparation**
   - Components and props
   - State and Hooks
   - Rendering and reconciliation
   - Effects and dependencies
   - Performance and architecture questions
333. **Final React Engineering Assessment**
   - Design a component hierarchy
   - Build a data-driven interface
   - Integrate an API
   - Test important user workflows
   - Optimize measured performance
   - Deploy and document the final application

## Projects and assessments

- 30 standalone exercises with separate protected solution files.
- 10 project briefs with progressive milestones and 100-point rubrics.
- 333 lesson knowledge-check sets (3 questions each; 999 questions).
- One final assessment blueprint with 60 questions (1,059 questions total across lesson checks and final assessment).
- Advanced/server architecture topics are marked with framework/runtime assumptions in lesson content.

## Editorial notes

- Create React App is presented as legacy maintenance material, not the recommended new-project setup.
- React Server Components and Server Functions are scoped to compatible framework/runtime environments.
- No PDF screenshots or extraneous UI/branding artifacts are copied; the course uses original SVG learning diagrams.
- React 19.3-specific topics require a version-matched learning project; the CodeLeaf platform runtime was not upgraded by this content patch.
