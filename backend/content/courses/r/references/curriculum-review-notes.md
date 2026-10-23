# R Language curriculum coverage and review notes

Reviewed on: 2026-10-17

## Source files and coverage

- Primary syllabus: `R(1).pdf` (62 pages). All pages were rendered for visual inspection; the PDF is predominantly textual curriculum and tables. Page 1 contains course overview/audience/prerequisites/outcomes; Section B spans pages 2–52 and contains the continuous numbered curriculum; Sections C–G provide exercises, projects, specialist topics, learning path and the pre-publication coverage checklist.
- The parsed Section B contains 23 module headings and the continuous numbered lesson sequence 1–247. Every main lesson title is retained as an independent lesson JSON file; every detected decimal-numbered subtopic is stored in the corresponding lesson’s `subtopics` and coverage ledger.
- Section C contains 40 practical exercises. The generated exercise filenames correspond to the listed exercise briefs in order.
- Section D contains nine projects and one integrated capstone. Each is present as a separate project JSON file with a draft rubric and a separate repository-only reference outline.
- Sections E–G are retained as recommendations/coverage notes below. Specialist material is represented as optional Module 22 and the relevant advanced/professional modules rather than being forced into the beginner path.

## Corrected, qualified or deferred material

1. **Execution claims:** all code examples use `static-validation` because the current CodeLeaf playground only previews HTML/CSS/JavaScript and this patch does not add an isolated R runtime. Code examples and expected output must be run in a supported R environment before publication.
2. **Current technical behavior:** official references point to R’s release manuals and current project/package documentation (checked on the date above). Package names/APIs and deployment behavior can change; course maintainers should verify the documented version and execute relevant examples just before release.
3. **Statistical claims:** examples with statistical or predictive methods are instructional sketches. Interpretation must be checked against design, assumptions, uncertainty, leakage, held-out performance and domain context. The code alone is not evidence of a valid research conclusion.
4. **Exercise grading:** current backend graders support `choice`, `exact_text` and `contains_all`. Practical R submissions use only a draft `contains_all` token check, which is not execution or semantic validation. Exercises therefore remain draft and should not be published with automatic rewards until the grader is replaced by a secure isolated runner or appropriate human assessment.
5. **Certificates / exams:** `exam-blueprint.json` specifies an assessment blueprint and per-lesson knowledge checks; it does not claim the repository implements a distinct randomized high-stakes exam or certificate issuing/verification engine.

## PDF Section E — advanced and optional specializations

- Advanced R internals: evaluation, environments, promises, memory management and metaprogramming (Modules 21 and 22).
- Package engineering: namespaces, S3/S4, tests, package checks and release workflows (Modules 19–20).
- Statistical research: experimental design, Bayesian inference, survival analysis and simulation (Modules 14, 22).
- Machine learning: pipelines, ensembles, feature selection, validation and interpretability (Module 15 and optional Module 22).
- Time series: ARIMA, decomposition, seasonality and forecast evaluation (Module 22).
- Bioinformatics: Bioconductor, genomic data, biological annotations and reproducible pipelines (Module 22).
- Geospatial: `sf`, spatial joins, rasters, coordinate systems and mapping (Module 22).
- Database analytics: DBI, database-specific drivers, query optimization and large-data workflows (Modules 16, 21–22).
- Interactive analytics: Shiny modules, reactive state, accessibility, caching and deployment (Modules 18 and 23).
- High-performance R: profiling, `data.table`, parallel processing, Rcpp and memory optimization (Module 21).
- Research publishing: Quarto books, reusable reports, citations and automated publishing (Module 17).
- Production operations: CI, containers, scheduled jobs, monitoring, recovery and environments (Modules 19 and 23).

## PDF Section F — suggested learning path

1. **Stage 1:** Modules 1–7, programming foundations.
2. **Stage 2:** Modules 8–11, functional programming, text, files and data manipulation.
3. **Stage 3:** Modules 12–14, visualization, EDA and statistical foundations.
4. **Stage 4:** Modules 15–16, modeling and external data.
5. **Stage 5:** Modules 17–18, reproducible reporting then Shiny.
6. **Stage 6:** Modules 19–21, engineering quality, packages and advanced internals.
7. **Stage 7:** Modules 22–23, chosen specialization and professional/production practice.
8. **Stage 8:** complete the capstone or a well-scoped specialist project with tests, decisions, limitations and result provenance.

## Full ordered Section B syllabus

### Module 1: Introduction to R

1. Introduction to R Language
   - What Is R?
   - R as a Programming Language and Statistical Computing Environment
   - History and Evolution of R
   - Relationship Between R and the S Language
   - R's Open-Source Development Model
2. Why R Is Used
   - Statistical Computing
   - Data Analysis and Data Science
   - Data Visualization
   - Scientific Research and Reproducible Analysis
   - Automation and Application Development
3. Applications of R in Different Industries
   - Business Analytics and Finance
   - Healthcare and Clinical Research
   - Biology and Bioinformatics
   - Economics and Social Sciences
   - Marketing and Customer Analytics
   - Environmental and Geospatial Analysis
4. Advantages, Limitations, and Alternatives
   - Advantages of R
   - Limitations of R
   - R Compared with Python
   - R Compared with Excel and Statistical Software
   - Choosing R for a Project
5. Prerequisites for Learning R
   - Basic Computer Skills
   - Mathematical Foundations
   - Basic Statistical Concepts
   - Understanding Files and Folders
   - Programming Prerequisites and Common Misconceptions
6. Installing R
   - Downloading R from the Official R Project
   - Installing R on Windows
   - Installing R on macOS
   - Installing R on Linux
   - Verifying the Installation
   - Understanding R Versions and Updates
7. Setting Up the R Development Environment
   - Working in the R Console
   - Installing and Using RStudio
   - Using Other Editors and Development Environments
   - Understanding Scripts, Console, Environment, and Files Panels
   - Configuring the Working Directory
   - Keyboard Shortcuts and Productivity Features
8. Your First R Program
   - Executing an Expression
   - Printing Text and Results
   - Performing a Calculation
   - Saving and Running an R Script
   - Understanding Output and Errors
   - Building a Small First Program

### Module 2: R Syntax and Fundamental Rules

9. Understanding R Syntax
   - Expressions and Statements
   - Commands and Function Calls
   - Case Sensitivity
   - Whitespace and Indentation
   - Single-Line and Multiline Expressions
10. Comments in R
   - Single-Line Comments
   - Writing Useful Code Comments
   - Commenting Out Code During Debugging
   - Documentation Comments and Their Limitations
11. Variables and Assignment
   - Creating Variables
   - The Assignment Operator <-
   - Assignment Using =
   - Assignment with ->
   - Updating Existing Variables
   - Naming and Overwriting Objects
12. Naming Rules and Reserved Words
   - Valid Object Names
   - Invalid Names and Special Characters
   - Reserved Words
   - Naming Conventions
   - Avoiding Confusing or Conflicting Names
13. Using the R Console
   - Interactive Execution
   - Evaluating Expressions
   - Reusing Previous Commands
   - Understanding Printed Results
   - Recovering from Incomplete Expressions
14. Basic Input and Output
   - Displaying Values with print()
   - Displaying Formatted Messages
   - Reading User Input
   - Formatting Console Output
   - Distinguishing Returned Values from Printed Output
15. Getting Help in R
   - Using ?function_name
   - Using help() and help.search()
   - Reading Function Documentation
   - Understanding Arguments and Return Values
   - Finding Examples and Related Functions
   - Using Package Documentation and Vignettes
16. How R Executes Code
   - Parsing and Evaluating Expressions
   - Order of Evaluation
   - The Global Environment
   - Object Creation and Removal
   - Understanding the Execution Lifecycle

### Module 3: Data Types, Values, and Basic Objects

17. Introduction to Data Types
   - What Is a Data Type?
   - Atomic Data Types
   - Storage Modes and Classes
   - Checking Types with typeof() and class()
   - Understanding Type Conversion
18. Numeric Data
   - Integer Values
   - Double-Precision Numeric Values
   - Creating Integers
   - Decimal Numbers
   - Floating-Point Precision
   - Numeric Overflow and Special Values
19. Character Data
   - Character Values
   - Single and Double Quotes
   - Creating and Combining Strings
   - Escape Sequences
   - Empty Strings
   - Missing and Nonmissing Character Values
20. Logical Data
   - TRUE and FALSE
   - Logical Expressions
   - Logical Coercion
   - The Three-Valued Logic of NA
   - Logical Results in Data Analysis
21. Complex Numbers
   - Representing Complex Numbers
   - Real and Imaginary Components
   - Arithmetic with Complex Numbers
   - Common Complex-Number Functions
22. Special Values in R
   - NULL
   - NA
   - NaN
   - Inf and -Inf
   - Testing Special Values
   - Differences Between Missing, Empty, and Undefined Values
23. Type Conversion and Coercion
   - Implicit Coercion
   - Explicit Conversion with as.*() Functions
   - Numeric-to-Character Conversion
   - Character-to-Numeric Conversion
   - Logical-to-Numeric Conversion
   - Common Coercion Errors
24. Checking and Inspecting Objects
   - typeof()
   - class()
   - str()
   - length()
   - is.*() Functions
   - attributes()
25. Object Attributes
   - Names
   - Dimensions
   - Class Attributes
   - Custom Attributes
   - How Attributes Affect Object Behavior
26. Missing-Value Handling
   - Detecting Missing Values with is.na()
   - Removing or Filtering Missing Values
   - Missing Values in Comparisons
   - Missing Values in Mathematical Operations
   - Avoiding Accidental Data Loss
27. Working with Basic Expressions
   - Creating Expressions
   - Evaluating Expressions
   - Understanding the Difference Between Values and Expressions
   - Inspecting Expression Results
   - Practical Expression Exercises

### Module 4: Operators, Vectors, and Vectorized Computing

28. Arithmetic Operators
   - Addition and Subtraction
   - Multiplication and Division
   - Exponentiation
   - Integer Division and Remainder
   - Operator Precedence
   - Parentheses and Nested Calculations
29. Comparison Operators
   - Equal and Not Equal
   - Greater Than and Less Than
   - Inclusive Comparisons
   - Comparing Numbers and Strings
   - Handling Comparisons Involving Missing Values
30. Logical Operators
   - Element-Wise AND with &
   - Element-Wise OR with |
   - Negation with !
   - Short-Circuit && and ||
   - Logical Precedence
   - Logical Conditions with NA
31. Other Important Operators
   - The Sequence Operator :
   - The Membership Operator %in%
   - The Special-Function Operator %...%
   - The Pipe Operator |>
   - The Help Operator ?
   - Namespace Operators :: and :::
32. Understanding Vectors
   - What Is a Vector?
   - Creating Vectors with c()
   - Atomic Vectors
   - Vector Length
   - Vector Naming
   - Empty and Missing-Value Vectors
33. Generating Sequences and Repeated Values
   - Using :
   - Generating Sequences with seq()
   - Repeating Values with rep()
   - Creating Numeric Ranges
   - Sequences with Fixed Lengths
   - Common Sequence-Generation Mistakes
34. Vectorized Operations
   - Arithmetic on Vectors
   - Comparisons Across Vectors
   - Element-Wise Logical Operations
   - Applying Functions to Whole Vectors
   - Advantages of Vectorized Computation
   - Understanding Recycling Rules
35. Indexing and Subsetting Vectors
   - Positive Integer Indexing
   - Negative Indexing
   - Logical Indexing
   - Character Indexing by Name
   - Using which()
   - Combining Multiple Conditions
36. Modifying Vectors
   - Updating Existing Elements
   - Appending and Combining Values
   - Removing Elements
   - Replacing Values Using Logical Conditions
   - Renaming Elements
   - Copy-on-Modify Behavior at an Introductory Level
37. Sorting and Ranking
   - sort()
   - order()
   - rank()
   - Sorting in Ascending and Descending Order
   - Sorting with Missing Values
   - Sorting Data with Tie Values
38. Vector Statistics and Transformations
   - sum() and prod()
   - min() , max() , and range()
   - mean() and median()
   - sd() and var()
   - cumsum() and cumprod()
   - diff() , pmin() , and pmax()

### Module 5: Data Structures in R

39. Matrices
   - Introduction to Matrices
   - Creating Matrices with matrix()
   - Rows, Columns, and Dimensions
   - Row and Column Names
   - Matrix Indexing
   - Matrix Arithmetic and Multiplication
40. Arrays
   - Introduction to Arrays
   - Creating Multidimensional Arrays
   - Dimensions and Dimension Names
   - Array Indexing
   - Array Arithmetic
   - Practical Scientific Applications
41. Lists
   - Introduction to Lists
   - Creating Lists
   - Storing Different Types of Objects
   - Accessing List Elements with [] , [[]] , and $
   - Nested Lists
   - Modifying and Combining Lists
42. Data Frames
   - Introduction to Data Frames
   - Creating Data Frames
   - Rows and Columns
   - Accessing Columns and Rows
   - Adding, Updating, and Removing Columns
   - Combining Data Frames
   - Inspecting Data Frames with head() , tail() , and str()
43. Tibbles
   - What Is a Tibble?
   - Creating Tibbles
   - Tibbles Compared with Base Data Frames
   - Printing and Inspecting Tibbles
   - Column Types and Recycling Behavior
   - When to Use Tibbles
44. Factors and Categorical Data
   - What Is a Factor?
   - Creating Factors with factor()
   - Levels and Labels
   - Ordered Factors
   - Modifying Factor Levels
   - Using forcats for Factor Manipulation
45. Dates and Times
   - Working with Date
   - Date-Time Objects with POSIXct and POSIXlt
   - Parsing Date Strings
   - Formatting Dates and Times
   - Time Zones and Daylight-Saving Considerations
   - Date Arithmetic
   - Working with difftime
46. Raw Vectors
   - Creating Raw Vectors
   - Converting Values to Raw Data
   - Working with Bytes
   - Raw Data and Binary Processing
47. Object Classes and Structured Objects
   - Understanding Classes
   - Attributes and Class-Based Behavior
   - Built-in Object Classes
   - Inspecting Objects
   - Creating Simple Custom Classes
48. Choosing the Right Data Structure
   - Vector vs. List
   - Matrix vs. Data Frame
   - Data Frame vs. Tibble
   - Factors vs. Character Vectors
   - Dates vs. Character Strings
   - Choosing Structures for Real-World Data
49. Data Structure Conversion and Reshaping
   - Converting Between Vectors and Lists
   - Converting Matrices and Data Frames
   - Combining and Splitting Objects
   - Binding Rows and Columns
   - Reshaping Data Structures
   - Preserving Types During Conversion

### Module 6: Conditions, Loops, and Control Flow

50. Conditional Statements
   - Introduction to if
   - The if...else Structure
   - Nested Conditions
   - Conditions with Multiple Logical Expressions
   - Returning Values from Conditional Expressions
51. Vectorized Conditional Selection
   - ifelse()
   - if_else() from dplyr
   - Choosing Between Scalar and Vectorized Conditions
   - Handling Missing Conditions
   - Avoiding Type and Recycling Surprises
52. Switch Statements
   - Using switch()
   - Numeric Selection
   - Character Selection
   - Default Cases
   - When to Use switch() vs. if...else
53. The for Loop
   - Loop Fundamentals
   - Iterating Over Sequences
   - Iterating Over Vectors
   - Iterating Over Lists
   - Nested Loops
   - Preallocating Results
54. The while Loop
   - Loop Conditions
   - Updating Conditions
   - Preventing Infinite Loops
   - Practical Iterative Algorithms
55. The repeat Loop
   - Introduction to repeat
   - Using break
   - Building Controlled Repetition
   - Comparing repeat , for , and while
56. Loop Control
   - break
   - next
   - Skipping Iterations
   - Exiting Nested Loops
   - Avoiding Unnecessary Control Complexity
57. Program Logic and Decision Design
   - Boolean Conditions
   - Compound Conditions
   - Boundary Conditions
   - Guard Clauses
   - Handling Empty and Missing Inputs
58. Vectorization vs. Loops
   - R's Vectorized Model
   - Replacing Simple Loops with Vectorized Operations
   - When Explicit Loops Are Appropriate
   - Measuring Performance Rather Than Guessing
59. Writing Reusable Control-Flow Patterns
   - Validation Before Processing
   - Processing Collections
   - Accumulating Results
   - Early Returns and Exit Conditions
   - Implementing Simple Algorithms
60. Control-Flow Exercises
   - Number Classification
   - Grade Calculation
   - Summation and Counting Problems
   - Pattern and Sequence Problems
   - Data Filtering Challenges

### Module 7: Functions and Reusable Programming

61. Introduction to Functions
   - What Is a Function?
   - Built-in Functions
   - User-Defined Functions
   - Function Calls and Arguments
   - Return Values
62. Creating Functions
   - Function Syntax
   - Function Bodies
   - Formal Arguments
   - Calling Functions
   - Returning Results with return()
   - Implicit Return Values
63. Function Arguments
   - Positional Arguments
   - Named Arguments
   - Default Argument Values
   - Required and Optional Inputs
   - Argument Matching Rules
   - The Ellipsis ...
64. Local and Global Variables
   - Function Environments
   - Local Variables
   - Global Variables
   - Variable Shadowing
   - Why Unnecessary Global Modification Is Risky
65. Scope and Environments
   - Lexical Scoping
   - Environment Chains
   - Enclosing and Parent Environments
   - environment() and parent.env()
   - Closures and Captured Variables
   - Practical Scope-Related Bugs
66. Functions as First-Class Objects
   - Assigning Functions to Variables
   - Passing Functions as Arguments
   - Returning Functions
   - Anonymous Functions
   - Function Composition
67. Anonymous Functions and Formula Shorthand
   - Anonymous Functions with function()
   - Shorthand Anonymous Functions with \(x)
   - Formula-Based Function Shortcuts in Relevant APIs
   - Choosing Clear Function Syntax
68. Recursive Functions
   - Understanding Recursion
   - Base Cases
   - Recursive Calls
   - Recursive Data Processing
   - Limitations of Deep Recursion
69. Closures
   - What Is a Closure?
   - Functions That Remember Their Environment
   - Factory Functions
   - Stateful Functions
   - Use Cases and Testing Considerations
70. Writing Robust Functions
   - Input Validation
   - Type and Length Checks
   - Handling Empty Inputs
   - Avoiding Hidden Side Effects
   - Writing Predictable Return Values
   - Documenting Assumptions
71. Function Composition and Pipelines
   - Combining Functions
   - The Base Pipe |>
   - The First-Argument Placeholder _
   - Named Intermediate Results
   - Improving Readability with Pipelines
72. Function Documentation
   - Naming Functions Clearly
   - Documenting Arguments
   - Explaining Return Values
   - Documenting Errors and Side Effects
   - Examples and Usage Notes
73. Building a Small Function Library
   - Organizing Related Functions
   - Avoiding Repeated Logic
   - Creating Helper Functions
   - Writing Function-Level Tests
   - Refactoring Script Code into Reusable Functions

### Module 8: Apply Functions and Functional Programming

74. Introduction to Functional Programming in R
   - Functions as Values
   - Stateless Transformations
   - Side Effects
   - Functional Programming Principles
   - Benefits and Trade-Offs
75. The apply() Family
   - apply() for Matrix Operations
   - lapply() for Lists and Vectors
   - sapply() and Simplification
   - vapply() and Return-Type Guarantees
   - tapply() for Grouped Application
   - mapply() for Multiple Inputs
76. Map, Filter, and Reduce
   - Mapping Functions Across Collections
   - Filtering Values
   - Reducing Results
   - Purrr's map() Functions
   - keep() , discard() , and reduce()
77. Working with purrr
   - map() and Typed Variants
   - Iterating Over Multiple Inputs
   - map2() and pmap()
   - walk() for Side Effects
   - Safe Mapping and Error Handling
   - Anonymous Functions Within Mappers
78. Splitting and Grouped Processing
   - split()
   - by()
   - aggregate()
   - Processing Groups with dplyr
   - Combining Group-Wise Results
79. Anonymous Iteration and Repetition
   - replicate()
   - lapply() vs. Explicit Loops
   - Repeated Simulations
   - Repeating Work with Controlled Inputs
80. Functional Programming with the Tidyverse
   - Pipelines and Functional Composition
   - Mapping over Data and Model Collections
   - Nesting and Unnesting Data
   - Grouped Model Workflows
   - Managing Multiple Analytical Outputs
81. Functional Programming Best Practices
   - Choosing the Correct Apply Function
   - Avoiding Accidental Simplification
   - Type-Safe Result Construction
   - Readability vs. Cleverness
   - Testing Functional Workflows
82. Functional Programming Challenges
   - Batch File Processing
   - Summaries Across Datasets
   - Repeated Model Fitting
   - Parallel-Friendly Function Design
   - Building a Reusable Data Transformation Pipeline

### Module 9: Strings, Regular Expressions, and Text Processing

83. String Fundamentals
   - Creating and Combining Strings
   - String Length
   - Substring Extraction
   - String Replacement
   - Splitting Strings
   - Case Conversion and Whitespace Handling
84. Base R String Functions
   - paste() and paste0()
   - nchar()
   - substr() and substring()
   - strsplit()
   - sub() and gsub()
   - trimws()
85. Text Manipulation with stringr
   - String Detection
   - String Extraction
   - String Replacement
   - String Splitting
   - String Joining
   - Consistent String Handling Across Vectors
86. Regular Expressions
   - Regex Fundamentals
   - Literal Characters and Metacharacters
   - Character Classes
   - Anchors and Word Boundaries
   - Quantifiers and Alternation
   - Capture Groups
   - Lookarounds Where Supported
   - Escaping and Regex Debugging
87. Extracting Structured Information from Text
   - Parsing Identifiers
   - Extracting Dates from Text
   - Cleaning Imported Text
   - Handling Repeated Delimiters
   - Validating Text Formats
88. Text Encoding and Internationalization
   - Character Encodings
   - UTF-8
   - Non-English Characters
   - Unicode and Text Comparison
   - Encoding Problems During File Import
89. Date and Time Manipulation with lubridate
   - Parsing Dates and Times
   - Extracting Year, Month, and Day
   - Durations, Periods, and Intervals
   - Time Zones
   - Date Sequences
   - Calendar-Based Calculations
90. Specialized Text Analysis
   - Word Counts and Tokenization
   - Working with Text Corpora
   - Document-Term Matrices
   - Text Cleaning and Normalization
   - Introductory Sentiment and Topic Analysis
91. Parsing and Structured Text
   - Reading Plain-Text Files
   - Parsing Delimited Records
   - JSON and Nested Data
   - XML Structure
   - Handling Malformed Records
92. Text Processing Validation and Testing
   - Testing String Functions
   - Testing Edge Cases
   - Handling Missing Text
   - Regex Performance and Readability
   - Building a Text-Cleaning Utility
93. Text Processing Practical Applications
   - Cleaning Survey Responses
   - Extracting Information from Logs
   - Standardizing Product Names
   - Detecting Invalid Input Formats
   - Preparing Text for Analysis

### Module 10: Working with Files, Directories, and External Data

94. Working with Files and Directories
   - Understanding File Paths
   - Relative and Absolute Paths
   - Working Directories
   - Creating and Listing Directories
   - Checking File Existence
   - File Metadata and Permissions
95. Reading and Writing Text Files
   - readLines() and writeLines()
   - readChar() and writeChar()
   - read.table() and write.table()
   - Text Connections
   - Handling Line Endings and Encoding
96. Working with CSV and Delimited Files
   - read.csv() and write.csv()
   - Reading Tab-Delimited Files
   - Custom Delimiters
   - Column Names and Column Types
   - Handling Missing Values
   - Importing Large Delimited Files
97. Importing Spreadsheet Data
   - Reading Excel Files with readxl
   - Selecting Sheets and Ranges
   - Handling Spreadsheet Headers
   - Working with Dates and Mixed Types
   - Writing Excel Files Using Suitable Packages
98. Saving and Loading R Objects
   - save() and load()
   - saveRDS() and readRDS()
   - .RData and .rds Formats
   - Serialization Concepts
   - Choosing Reusable Storage Formats
99. Importing Statistical Software Formats
   - SPSS Data
   - Stata Data
   - SAS Data
   - Variable Labels and Metadata
   - Preserving Categorical Variables
100. JSON, XML, and Other Data Formats
   - Reading and Writing JSON
   - Nested JSON Structures
   - XML Documents and Nodes
   - Working with Parquet and Columnar Formats
   - Choosing Formats Based on Data Size and Usage
101. Data Export and Report Outputs
   - Exporting Cleaned Data
   - Writing Tables and Summaries
   - Exporting Charts
   - Saving Statistical Models
   - Creating Automated Output Folders
102. Import Validation and Data Quality
   - Detecting Incorrect Column Types
   - Verifying Row Counts
   - Checking Required Columns
   - Detecting Duplicate Records
   - Validating Data Ranges
   - Logging Data-Import Warnings
103. Automated File Processing
   - Listing Matching Files
   - Processing Files in Batches
   - Combining Monthly or Daily Data
   - Managing Output Filenames
   - Safe File Overwrites and Backups
   - Building Repeatable Import Pipelines
104. File and Data Pipeline Troubleshooting
   - Working-Directory Errors
   - Incorrect Delimiters
   - Missing or Unexpected Columns
   - Encoding and Locale Problems
   - Inconsistent Schemas Across Files
   - Handling Corrupt or Incomplete Inputs

### Module 11: Data Cleaning and Manipulation

105. Introduction to Data Wrangling
   - What Is Data Wrangling?
   - Tidy Data Principles
   - Raw, Clean, and Analysis-Ready Data
   - Data Cleaning Workflow
   - Documenting Transformation Decisions
106. Selecting and Filtering Data
   - Selecting Columns
   - Filtering Rows
   - Selecting with Logical Conditions
   - Renaming Columns
   - Excluding Unneeded Variables
   - Selecting by Column Names and Types
107. Transforming Columns
   - Creating New Variables
   - Modifying Existing Variables
   - mutate() and Related Functions
   - Conditional Column Creation
   - Type Conversion and Standardization
   - Removing Temporary Columns
108. Sorting and Ranking Data
   - Sorting by One Column
   - Sorting by Multiple Columns
   - Ascending and Descending Order
   - Top-N and Bottom-N Records
   - Handling Ties and Missing Values
109. Grouping and Summarization
   - group_by()
   - summarise()
   - Group-Wise Counts
   - Multiple Summary Measures
   - Grouped Mutations
   - Grouping and Regrouping Data
110. Combining Datasets
   - Row Binding
   - Column Binding
   - Inner Joins
   - Left, Right, and Full Joins
   - Semi-Joins and Anti-Joins
   - Join Keys and Relationship Validation
   - Resolving Duplicate Column Names
111. Reshaping Data
   - Wide and Long Formats
   - pivot_longer()
   - pivot_wider()
   - Splitting Columns into Variables
   - Combining Multiple Variables
   - Handling Repeated Measurements
112. Handling Missing Data
   - Identifying Missing Values
   - Counting Missing Values
   - Removing Incomplete Records
   - Imputing Missing Values
   - Distinguishing Structural and Accidental Missingness
   - Assessing the Effect of Missing Data Decisions
113. Duplicates, Inconsistencies, and Outliers
   - Detecting Duplicate Records
   - Removing Exact Duplicates
   - Detecting Inconsistent Categories
   - Standardizing Units and Labels
   - Investigating Outliers
   - Keeping an Audit Trail of Cleaning Operations
114. Working with Categorical and Date Data
   - Reordering Factor Levels
   - Combining Rare Categories
   - Parsing and Standardizing Dates
   - Extracting Calendar Components
   - Creating Date-Based Groups
   - Handling Invalid Dates
115. Data Manipulation with the Tidyverse
   - Introduction to dplyr
   - Introduction to tidyr
   - The Native Pipe Operator |>
   - The Tidyverse Pipe Workflow
   - Column Selection Helpers
   - Understanding Evaluation Within Data-Masking Functions
116. Data Transformation Quality Assurance
   - Checking Row Counts Before and After Transformations
   - Verifying Uniqueness of Keys
   - Checking Join Results
   - Validating Business Rules
   - Writing Reusable Cleaning Functions
   - Designing an End-to-End Cleaning Pipeline

### Module 12: Data Visualization and Graphics

117. Introduction to Data Visualization
   - Purpose of Data Visualization
   - Choosing the Right Chart
   - Variables and Measurement Scales
   - Visual Encoding
   - Common Visualization Mistakes
118. Base R Graphics
   - Introduction to the Base Graphics System
   - plot()
   - hist()
   - barplot()
   - boxplot()
   - pairs() and Scatterplot Matrices
119. Customizing Base R Charts
   - Titles and Axis Labels
   - Colors and Point Symbols
   - Lines and Line Types
   - Axis Ranges and Tick Marks
   - Legends
   - Multiple Plots and Layouts
120. Introduction to ggplot2
   - Grammar of Graphics
   - The ggplot() Function
   - Aesthetic Mappings
   - Geometric Layers
   - Statistics and Position Adjustments
   - Plot Objects and Layered Construction
121. Common Charts with ggplot2
   - Scatterplots
   - Line Charts
   - Bar Charts
   - Histograms and Density Plots
   - Boxplots and Violin Plots
   - Frequency and Proportion Charts
122. Advanced ggplot2 Customization
   - Scales and Legends
   - Themes and Theme Elements
   - Labels and Annotations
   - Faceting
   - Coordinate Systems
   - Statistical Transformations
   - Custom Geometries and Extensions
123. Visualizing Complex and Multidimensional Data
   - Bubble Charts
   - Heatmaps
   - Correlation Plots
   - Pairwise Relationship Plots
   - Small Multiples
   - Visualizing High-Dimensional Patterns
124. Time-Based and Geospatial Visualizations
   - Time-Series Charts
   - Seasonal and Calendar Plots
   - Mapping Points and Regions
   - Choropleth Maps
   - Spatial Layers and Coordinate Systems
125. Statistical and Model Visualizations
   - Distribution Comparisons
   - Regression Lines and Confidence Bands
   - Residual Plots
   - Diagnostic Charts
   - Model Performance Visualization
   - Uncertainty Visualization
126. Interactive Visualization
   - Hover and Tooltip Concepts
   - Plotly for Interactive Charts
   - Linking Charts and Tables
   - Interactive Filtering
   - Performance Considerations for Large Visualizations
127. Exporting and Publishing Graphics
   - Exporting PNG and JPEG Images
   - Exporting PDF and Vector Graphics
   - Controlling Size and Resolution
   - Fonts and Rendering Considerations
   - Consistent Styling Across Reports
   - Preparing Graphics for Publications
128. Visualization Quality and Accessibility
   - Choosing Accessible Color Palettes
   - Avoiding Color-Only Communication
   - Clear Labels and Legends
   - Appropriate Scales and Baselines
   - Showing Uncertainty Honestly
   - Designing for Screen and Print

### Module 13: Exploratory Data Analysis and Descriptive Statistics

129. Introduction to Exploratory Data Analysis
   - Purpose of EDA
   - Questions to Ask Before Modeling
   - Understanding the Dataset Structure
   - Univariate and Multivariate Exploration
   - Iterative Analysis and Documentation
130. Descriptive Statistics
   - Mean
   - Median
   - Mode and Frequency
   - Minimum, Maximum, and Range
   - Variance and Standard Deviation
   - Quartiles and Percentiles
131. Frequency Distributions
   - Counts and Proportions
   - Frequency Tables
   - Grouped Frequencies
   - Cumulative Frequency
   - Distribution Summaries
132. Understanding Distributions
   - Shape and Symmetry
   - Skewness
   - Heavy and Light Tails
   - Outliers and Extreme Values
   - Comparing Distributions
   - Distribution-Based Assumptions
133. Relationships Between Variables
   - Covariance
   - Pearson Correlation
   - Spearman and Kendall Correlation
   - Cross-Tabulation
   - Association Between Categorical Variables
   - Correlation vs. Causation
134. Data Quality Exploration
   - Missingness Profiles
   - Duplicate and Unique Values
   - Invalid Ranges
   - Unexpected Categories
   - Cross-Variable Consistency
   - Data Quality Summary Reports
135. Grouped and Comparative Analysis
   - Group-Wise Summary Statistics
   - Comparing Categories
   - Comparing Time Periods
   - Aggregations and Weighted Summaries
   - Sample Size and Group Imbalance
136. EDA with Base R and Tidyverse
   - Summary Functions
   - Grouped Summaries with dplyr
   - Visual Exploration with ggplot2
   - Profiling Data Frames
   - Automating Exploratory Summaries
137. Sampling and Representativeness
   - Population and Sample
   - Random Sampling
   - Stratified Sampling Concepts
   - Sampling Bias
   - Nonresponse and Selection Bias
   - Evaluating Whether Data Can Support a Conclusion
138. Outlier Detection and Robust Summaries
   - Interquartile Range
   - Standard-Score Methods
   - Robust Measures of Location and Spread
   - Univariate and Multivariate Outliers
   - Investigating Rather Than Automatically Deleting Outliers
139. Exploratory Analysis Report
   - Defining Analytical Questions
   - Producing Summary Tables
   - Creating a Visualization Set
   - Recording Data Limitations
   - Writing Evidence-Based Findings

### Module 14: Probability, Statistical Inference, and Experiments

140. Probability Fundamentals
   - Events and Sample Spaces
   - Probability Rules
   - Conditional Probability
   - Independence
   - Bayes' Theorem
   - Probability Calculations in R
141. Probability Distributions in R
   - Density Functions: d*
   - Distribution Functions: p*
   - Quantile Functions: q*
   - Random Generation Functions: r*
   - Binomial and Poisson Distributions
   - Normal, Uniform, and Exponential Distributions
142. Random Sampling and Simulation
   - Random Number Generation
   - Setting a Random Seed
   - Sampling with and Without Replacement
   - Monte Carlo Estimation
   - Simulation-Based Probability
   - Reproducible Random Experiments
143. Sampling Distributions
   - Sampling Variability
   - Standard Error
   - Central Limit Theorem
   - Bootstrap Sampling
   - Understanding the Distribution of an Estimator
144. Statistical Estimation
   - Point Estimates
   - Estimator Bias
   - Consistency and Precision
   - Confidence Intervals
   - Interpretation of Statistical Uncertainty
145. Hypothesis Testing
   - Null and Alternative Hypotheses
   - Test Statistics
   - P-Values
   - Significance Levels
   - Type I and Type II Errors
   - Statistical Significance vs. Practical Importance
146. Common Statistical Tests
   - One-Sample and Two-Sample t-Tests
   - Paired t-Tests
   - Proportion Tests
   - Chi-Square Tests
   - Nonparametric Tests
   - Choosing Tests Based on Study Design and Assumptions
147. Analysis of Variance
   - Introduction to ANOVA
   - One-Way ANOVA
   - Factorial ANOVA Concepts
   - Multiple Comparisons
   - Assumption Checking
   - Effect Sizes and Interpretation
148. Experimental Design
   - Treatments and Control Groups
   - Randomization
   - Replication and Blocking
   - Confounding Variables
   - Power and Sample Size Concepts
   - Design Limitations and Ethical Data Collection
149. Correlation and Statistical Relationships
   - Testing Correlation
   - Confidence Intervals for Associations
   - Partial Correlation Concepts
   - Confounding and Spurious Relationships
   - Interpreting Association in Context
150. Resampling Methods
   - Bootstrap Confidence Intervals
   - Permutation Tests
   - Cross-Validation as a Resampling Method
   - Simulation-Based Inference
   - Computational Cost of Resampling
151. Statistical Analysis Reporting
   - Reporting Test Statistics
   - Reporting Confidence Intervals
   - Reporting Effect Sizes
   - Reporting Assumptions and Limitations
   - Avoiding P-Hacking and Selective Reporting
   - Reproducible Statistical Results

### Module 15: Regression, Statistical Modeling, and Machine Learning

152. Introduction to Statistical Modeling
   - What Is a Model?
   - Response and Predictor Variables
   - Model Assumptions
   - Training and Evaluation Data
   - Explanation vs. Prediction
   - Model Generalization and Overfitting
153. R Modeling Fundamentals
   - Formula Notation
   - Fitting Models with lm()
   - Fitting Models with glm()
   - Model Objects
   - Using summary() and coef()
   - Predictions with predict()
154. Simple Linear Regression
   - The Linear Regression Model
   - Least-Squares Estimation
   - Interpreting Coefficients
   - Predictions and Fitted Values
   - Residuals and Error
   - Assessing Model Fit
155. Multiple Linear Regression
   - Multiple Predictors
   - Categorical Predictors
   - Interaction Terms
   - Polynomial Terms
   - Multicollinearity
   - Coefficient Interpretation and Limitations
156. Regression Diagnostics
   - Residual Diagnostics
   - Linearity
   - Constant Variance
   - Residual Normality and Its Role
   - Influential Observations
   - Remedies and Alternative Models
157. Generalized Linear Models
   - Link Functions
   - Binomial Models
   - Logistic Regression
   - Poisson Regression
   - Overdispersion
   - Interpreting Predictions and Effects
158. Model Comparison and Selection
   - Nested-Model Comparisons
   - Information Criteria
   - Adjusted R2
   - Cross-Validation
   - Model Complexity and Generalization
   - Avoiding Data Leakage
159. Classification Fundamentals
   - Classification Problems
   - Logistic Classification
   - Decision Trees
   - Random Forests
   - Support Vector Machines
   - Naive Bayes
   - Model Selection for Classification
160. Regression-Based Prediction
   - Predicting Continuous Outcomes
   - Feature Selection
   - Regularization Concepts
   - Ridge Regression
   - Lasso Regression
   - Comparing Predictive Performance
161. Clustering and Unsupervised Learning
   - Unsupervised Learning Concepts
   - K-Means Clustering
   - Hierarchical Clustering
   - Distance Metrics
   - Choosing the Number of Clusters
   - Evaluating Cluster Structure
162. Dimensionality Reduction
   - Principal Component Analysis
   - Scaling Before PCA
   - Interpreting Principal Components
   - Dimension Reduction for Visualization
   - Limitations of Reduced Representations
163. Machine-Learning Evaluation
   - Train, Validation, and Test Sets
   - Confusion Matrices
   - Accuracy, Precision, Recall, and F1
   - ROC Curves and AUC
   - Regression Metrics
   - Class Imbalance
   - Calibration and Threshold Selection
164. Model Workflows and Tuning
   - Preprocessing Pipelines
   - Feature Engineering
   - Resampling and Cross-Validation
   - Hyperparameter Tuning
   - Automated Workflows with tidymodels
   - Reproducible Model Comparisons
165. Model Interpretation, Fairness, and Deployment
   - Interpreting Predictors
   - Variable Importance
   - Model Explainability Concepts
   - Bias and Fairness Assessment
   - Limitations of Predictive Systems
   - Saving Models and Reusing Predictions

### Module 16: Databases, APIs, and External Integrations

166. Introduction to Database Access in R
   - Relational Database Fundamentals
   - Why Connect R to a Database?
   - Database Drivers
   - Credentials and Connection Strings
   - Connection Management
167. Connecting to Databases with DBI
   - The DBI Interface
   - Establishing and Closing Connections
   - Sending Queries
   - Fetching Results
   - Metadata and Table Discovery
   - Handling Connection Errors
168. SQL Integration
   - Executing SQL Queries
   - Reading Database Tables into R
   - Parameterized Queries
   - Writing Results Back to Databases
   - Transaction Management
   - Avoiding SQL Injection
169. Working with Different Database Systems
   - SQLite with RSQLite
   - PostgreSQL with RPostgres
   - MySQL and MariaDB Connectivity
   - ODBC Connections
   - Choosing a Backend
   - Database Compatibility and Portability
170. Connecting to Web APIs
   - HTTP Fundamentals
   - REST API Concepts
   - GET and POST Requests
   - Headers and Query Parameters
   - JSON Responses
   - Pagination
   - Authentication and API Tokens
   - Rate Limits and Error Responses
171. Web Data Collection
   - Downloading Public Datasets
   - Importing Remote Files
   - HTML Parsing Basics
   - Responsible Web Scraping
   - Request Throttling and Site Policies
   - Data Provenance and Collection Records
172. Integrating R with Other Systems
   - Calling Command-Line Programs
   - Running R Scripts from the Terminal
   - Interoperability with Python Using reticulate
   - Calling Compiled Code
   - Using R Within Larger Applications
   - Handling External Dependencies and Failures

### Module 17: Reproducible Research, Reports, and Documentation

173. Introduction to Reproducible Analysis
   - Reproducibility and Repeatability
   - Separating Data, Code, and Outputs
   - Recording Analytical Decisions
   - Deterministic and Stochastic Workflows
   - Reproducibility Limitations
174. Quarto Fundamentals
   - What Is Quarto?
   - Creating a Quarto Document
   - Markdown Basics
   - YAML Front Matter
   - Executable R Code Blocks
   - Rendering Documents
175. R Markdown and Document Workflows
   - R Markdown Fundamentals
   - Code Chunks and Chunk Options
   - Parameters and Dynamic Documents
   - Tables and Figures
   - When to Maintain Existing R Markdown Projects
   - Understanding the Relationship Between Quarto and R Markdown
176. Creating Professional Reports
   - HTML Reports
   - PDF Reports
   - Word Documents
   - Report Templates
   - Tables with Appropriate Formatting
   - Cross-References and Captions
177. Presentation and Book Publishing
   - Presentations with Quarto
   - Quarto Websites
   - Multi-Page Documentation
   - Books and Structured Tutorials
   - Navigation and Table of Contents
   - Publishing Reproducible Learning Materials
178. Automated Analytical Reporting
   - Parameterized Reports
   - Scheduled Report Generation
   - Report Generation for Multiple Datasets
   - Handling Failed Rendering
   - Validating Report Outputs
   - Automating Distribution of Results
179. Data Storytelling and Technical Communication
   - Identifying the Audience
   - Presenting Findings in Context
   - Writing Clear Statistical Conclusions
   - Integrating Charts and Tables
   - Distinguishing Results from Interpretation
   - Communicating Uncertainty
180. Reproducibility and Project Environments
   - Project-Based Workflows
   - Recording Package Dependencies
   - Managing Environments with renv
   - Lockfiles and Project Restoration
   - Fixed Seeds and Reproducible Simulations
   - Handling Data and Software Version Changes
181. Publishing and Sharing Analytical Work
   - Organizing Source Files
   - Publishing Rendered Reports
   - Sharing Data and Code Responsibly
   - Redacting Sensitive Information
   - Documenting How to Reproduce Results

### Module 18: Interactive Application Development with Shiny

182. Introduction to Shiny
   - What Is Shiny?
   - Applications of Interactive R Apps
   - Installing Shiny
   - The Structure of a Shiny Application
   - Running and Stopping an App
183. Shiny Application Structure
   - The ui Object
   - The server Function
   - The shinyApp() Function
   - The app.R File
   - Organizing Larger Applications
184. Building User Interfaces
   - Page Layouts
   - Sidebar Layouts
   - Input Controls
   - Output Containers
   - Tabs and Navigation
   - Layout and Component Reuse
185. Collecting User Input
   - Text Inputs
   - Numeric Inputs
   - Select Menus
   - Checkbox and Radio Inputs
   - Sliders and Date Inputs
   - Action Buttons
   - Validating User Input
186. Reactive Programming
   - Reactivity Fundamentals
   - Reactive Expressions
   - Render Functions
   - Observers
   - req() and validate()
   - Understanding Reactive Dependencies
187. Rendering Outputs
   - Text Outputs
   - Tables and Data Frames
   - Static Plots
   - Interactive Charts
   - Downloadable Files
   - Dynamic UI Outputs
188. Reactive State and Events
   - Input-to-Output Dependencies
   - Event-Driven Reactivity
   - reactiveVal() and reactiveValues()
   - observeEvent() and Related Patterns
   - Preventing Unnecessary Recalculation
   - Managing Reset and Update Actions
189. Styling Shiny Applications
   - Themes with bslib
   - Layout and Spacing
   - Custom CSS
   - Responsive Design
   - Accessible Input Labels
   - Consistent User Experience
190. Modular Shiny Applications
   - Why Modules Are Needed
   - Module UI and Server Functions
   - Namespaces
   - Reusable Components
   - Organizing Modules Across Files
191. Advanced Shiny Features
   - Dynamic UI
   - File Uploads and Downloads
   - Asynchronous Operations
   - Long-Running Calculations
   - Caching
   - Progress Indicators
192. Shiny Security and Data Protection
   - Input Validation
   - Authentication and Authorization Concepts
   - Handling Uploaded Files Safely
   - Protecting Credentials and Secrets
   - Avoiding Exposure of Private Data
   - Understanding Session Isolation
193. Shiny Testing and Debugging
   - Debugging Reactive Graphs
   - Testing Server Logic
   - Testing UI Interactions
   - Measuring Response Time
   - Diagnosing Memory and State Problems
194. Shiny Deployment
   - Local Deployment and Testing
   - Posit Connect and Other Hosting Options
   - Containerized Deployment Concepts
   - Environment and Dependency Management
   - Logs and Operational Monitoring
   - Updating Deployed Applications
195. Building Production-Ready Shiny Apps
   - Application Architecture
   - User Feedback and Error Messages
   - Load and Performance Testing
   - Accessibility and Usability
   - Deployment Checklists
   - Maintenance and Version Updates

### Module 19: Debugging, Testing, and Software Quality

196. Understanding Errors and Warnings
   - Syntax Errors
   - Runtime Errors
   - Warnings and Messages
   - Reading Error Messages
   - Reproducing Errors Reliably
197. Debugging R Programs
   - Using print() for Diagnosis
   - Using browser()
   - debug() and Related Tools
   - Stepping Through Execution
   - Inspecting the Call Stack
   - Using Debugging Features in an IDE
198. Error Handling
   - try()
   - tryCatch()
   - withCallingHandlers()
   - Raising Errors with stop()
   - Warnings with warning()
   - Defining Condition Classes
199. Assertions and Input Validation
   - Validating Arguments
   - Checking Data Shapes and Types
   - Enforcing Business Rules
   - Assertions and Preconditions
   - Designing Clear Failure Messages
200. Testing Fundamentals
   - What Is Software Testing?
   - Unit Testing
   - Integration Testing
   - Regression Testing
   - Test Fixtures and Test Data
   - Choosing What to Test
201. Testing with testthat
   - Creating Test Files
   - Writing Expectations
   - Testing Expected Errors and Warnings
   - Running Test Suites
   - Organizing Tests
   - Reading Test Results
202. Advanced Testing Strategies
   - Edge-Case Testing
   - Property-Based Testing Concepts
   - Snapshot Testing
   - Testing Randomized Functions
   - Testing Numerical Tolerances
   - Mocking External Dependencies
203. Code Quality and Style
   - Consistent Naming
   - Readable Indentation
   - Small, Focused Functions
   - Avoiding Duplicate Logic
   - Refactoring
   - Automated Style and Lint Checks
204. Static Analysis and Code Review
   - Understanding Code Linting
   - Identifying Suspicious Expressions
   - Reviewing Dependencies
   - Conducting Peer Reviews
   - Improving Code Based on Review Feedback
205. Logging and Diagnostics
   - Console Messages vs. Structured Logging
   - Recording Execution Events
   - Logging Failures
   - Debugging Batch Jobs
   - Managing Log Files
   - Avoiding Sensitive Data in Logs
206. Version Control with Git
   - Introduction to Git
   - Tracking R Scripts
   - Commits and Branches
   - Resolving Merge Conflicts
   - Collaborative Development
   - Managing Data, Secrets, and Generated Files in Repositories
207. Continuous Integration
   - Automated Test Execution
   - Repeated Build and Check Workflows
   - Automated Package Checks
   - Environment Setup in CI
   - Reviewing Build Failures
   - Dependency Updates and Validation
208. Professional Project Organization
   - Organizing Source Code and Data
   - Separating Configuration from Logic
   - Creating a Project README
   - Documenting Setup and Execution
   - Data and Output Folder Conventions
   - Establishing a Maintenance Workflow

### Module 20: R Packages and Package Development

209. Understanding R Packages
   - What Is an R Package?
   - Package vs. Script
   - Package Functions and Data
   - Package Namespaces
   - Package Dependencies
   - CRAN, Bioconductor, and Other Repositories
210. Installing and Managing Packages
   - install.packages()
   - library() and require()
   - Using package::function
   - Updating and Removing Packages
   - Understanding Package Libraries
   - Dependency Conflicts
211. Creating a Package
   - Package Directory Structure
   - Creating Packages with usethis
   - The DESCRIPTION File
   - The NAMESPACE File
   - The R/ Source Directory
   - Data and Supporting Files
212. Documenting Packages with roxygen2
   - Function Documentation
   - Documentation Tags
   - Generating Help Files
   - Documenting Arguments and Return Values
   - Documenting Package Datasets
   - Vignettes and Tutorials
213. Package Testing and Development Workflow
   - Creating Package Tests
   - devtools::test()
   - Development Builds
   - R CMD check
   - Understanding Check Results
   - Automated Package Validation
214. Namespaces and Dependency Design
   - Importing Functions
   - Exporting Public Functions
   - Internal Functions
   - Declaring Package Dependencies
   - Avoiding Unnecessary Dependencies
   - Designing Stable APIs
215. Package Data and Examples
   - Included Example Datasets
   - External Data Files
   - Reproducible Package Examples
   - Executable Documentation
   - Example Runtime Considerations
216. Publishing and Maintaining Packages
   - Preparing Release Metadata
   - License Selection and Compatibility
   - CRAN Submission Concepts
   - Package Versioning
   - Managing Issues and Contributions
   - Release Notes and Deprecation
217. Advanced Package Development
   - S3 Methods in Packages
   - S4 Classes and Methods
   - Exported Generics and Method Registration
   - Compiled Code Integration
   - System Requirements
   - Cross-Platform Compatibility
218. Package Security and Sustainability
   - Dependency Risk
   - Licensing and Attribution
   - Handling Credentials
   - Reproducible Builds
   - Long-Term Maintenance
   - Supporting Users and Contributors
219. Contributing to Existing R Packages
   - Reading an Unfamiliar Codebase
   - Understanding Issues and Feature Requests
   - Writing Minimal Reproductions
   - Preparing Focused Changes
   - Submitting Pull Requests
   - Communicating Technical Decisions
220. Building a Complete R Package
   - Planning a Reusable Utility
   - Implementing Public Functions
   - Documenting the API
   - Testing Valid and Invalid Inputs
   - Running Package Checks
   - Preparing a Release

### Module 21: Advanced R Programming and Performance

221. Advanced Object Semantics
   - Copy-on-Modify
   - Object Identity and Sharing
   - Attributes and Class Dispatch
   - Object Size and Memory
   - Understanding Unexpected Mutation
222. Environments and Evaluation
   - Environment Objects
   - Lexical Environments
   - Variable Lookup
   - Promise Objects and Delayed Evaluation
   - Lazy Evaluation of Function Arguments
   - Evaluation Environments
223. Nonstandard Evaluation and Metaprogramming
   - Language Objects and Expressions
   - Quoting and Evaluating Expressions
   - substitute() and eval()
   - Quasiquotation Concepts
   - Data Masking
   - Tidy Evaluation and rlang
   - Safe Design of Programmable Interfaces
224. Object-Oriented Programming in R
   - Overview of R's Object Systems
   - S3 Classes
   - S3 Generic Functions
   - S3 Methods and Dispatch
   - S4 Classes and Validity
   - S4 Generic Functions and Methods
   - Reference Classes and Their Context
   - R6 Classes and Reference Semantics
225. Advanced Function Design
   - Higher-Order Functions
   - Function Factories
   - Closures and Mutable State
   - Replacement Functions
   - Custom Operators
   - Designing Composable APIs
226. Memory Management
   - R Objects and Memory Allocation
   - Garbage Collection
   - gc()
   - Large Object Handling
   - Memory-Intensive Transformations
   - Practical Memory Profiling
227. Profiling and Benchmarking
   - Measuring Runtime
   - system.time()
   - Benchmarking Alternatives
   - Sampling-Based Profiling
   - Using Rprof() and Profiling Tools
   - Identifying Actual Bottlenecks
228. Performance Optimization
   - Vectorization
   - Avoiding Unnecessary Copies
   - Preallocation
   - Efficient Data Structures
   - Reducing Repeated Computation
   - Caching Expensive Results
   - Benchmark-Driven Optimization
229. Parallel and Distributed Computing
   - Concepts of Parallel Computation
   - Base R Parallel Capabilities
   - Parallel Apply Patterns
   - Reproducible Randomness in Parallel Jobs
   - Worker and Process Management
   - Failure Handling and Resource Limits
   - Distributed Data Processing Concepts
230. Compiled-Code Integration
   - When R-Level Code Is Insufficient
   - Calling C and C++ from R
   - Rcpp Fundamentals
   - Interoperability and Data Conversion
   - Compilation and Platform Compatibility
   - Native Interface Safety and Maintenance

### Module 22: Specialized R Domains

231. Time-Series Analysis
   - Time-Series Objects and Indexing
   - Trend and Seasonality
   - Decomposition
   - Autocorrelation and Partial Autocorrelation
   - AR, MA, ARMA, and ARIMA Models
   - Forecasting and Forecast Evaluation
   - Advanced Time-Series Workflows
232. Bayesian Statistics
   - Bayesian Inference
   - Prior and Posterior Distributions
   - Credible Intervals
   - Markov Chain Monte Carlo Concepts
   - Model Diagnostics
   - Bayesian Workflow and Reporting
233. Survival Analysis
   - Time-to-Event Data
   - Censoring
   - Kaplan–Meier Estimation
   - Log-Rank Tests
   - Cox Proportional Hazards Models
   - Survival Model Diagnostics
234. Bioinformatics with R
   - Biological Data Formats
   - Genomic Data Concepts
   - Bioconductor Packages
   - Sequence and Expression Data
   - Annotation and Metadata
   - High-Throughput Experimental Analysis
   - Reproducible Bioinformatics Pipelines
235. Geospatial Analysis
   - Spatial Data Concepts
   - Vector and Raster Data
   - Coordinate Reference Systems
   - Spatial Data with sf
   - Raster Processing
   - Spatial Joins and Aggregation
   - Geographic Visualization
   - Spatial Analysis Limitations
236. Econometrics and Financial Analysis
   - Economic Data Structures
   - Regression-Based Econometrics
   - Panel Data Concepts
   - Causal Inference Methods
   - Financial Returns and Risk Measures
   - Volatility Modeling Concepts
   - Financial Data Visualization
237. Text Mining and Natural Language Processing
   - Corpus Construction
   - Tokenization
   - Stop Words and Text Normalization
   - Document-Term Matrices
   - Text Classification
   - Topic Modeling
   - Evaluating Text Models
238. Advanced Machine Learning
   - Gradient Boosting
   - Model Ensembles
   - Neural Network Concepts
   - Deep Learning Ecosystem Overview
   - Tuning Complex Models
   - Interpretability and Error Analysis
   - Training and Deployment Considerations
239. High-Performance and Large-Scale Data
   - Efficient Data Structures
   - data.table
   - Lazy Data Processing Concepts
   - Arrow and Columnar Data
   - Database-Pushed Computation
   - Spark Integration Concepts
   - Memory and Compute Trade-Offs
240. Advanced Graphics and Interactive Analytics
   - Specialized Statistical Graphics
   - Interactive Dashboards
   - Dynamic Filtering and Cross-Selection
   - Advanced Layouts and Annotations
   - Communicating Complex Models
   - Performance and Accessibility

### Module 23: Security, Deployment, and Professional Practice

241. Security Fundamentals for R Projects
   - Managing Secrets and API Tokens
   - Protecting Database Credentials
   - Safe File and Network Operations
   - Validating External Inputs
   - Handling Untrusted Serialized Data
   - Dependency and Supply-Chain Awareness
242. Data Privacy and Responsible Analysis
   - Personal and Sensitive Data
   - Anonymization Limitations
   - Minimizing Unnecessary Data Collection
   - Access Control
   - Responsible Data Sharing
   - Ethical Interpretation of Results
243. R in Automation and Production
   - Running Scripts Noninteractively
   - Using Rscript
   - Command-Line Arguments
   - Scheduled Jobs
   - Exit Codes and Failure Signals
   - Logging and Monitoring
244. Deployment and Infrastructure
   - Server Execution Concepts
   - Environment Variables
   - Dependency Installation During Deployment
   - Docker Concepts for R Applications
   - Deployment of Reports and Applications
   - Environment-Specific Configuration
245. Maintaining Production R Workflows
   - Dependency Updates
   - Data Schema Changes
   - Monitoring Failures
   - Reproducible Recovery
   - Backups and Retention
   - Versioned Releases and Rollbacks
246. Professional Documentation and Collaboration
   - README Files
   - Function and Package Documentation
   - Data Dictionaries
   - Reproducible Setup Instructions
   - Team Coding Conventions
   - Collaborative Reviews and Issue Tracking
247. Professional R Project Workflow
   - Clarifying the Analytical Objective
   - Inspecting and Validating Input Data
   - Planning the Analysis
   - Building Modular Functions
   - Testing and Reviewing Results
   - Reporting and Delivering Outputs
   - Maintaining the Project Over Time

## Review exit criteria before publication

- Execute all base-R examples in a current R release and update output where console formatting varies.
- Test package-specific examples with documented package versions; keep network, database and deployment examples isolated and credential-safe.
- Peer-review all statistical explanations, assumptions, uncertainty statements and model-evaluation guidance.
- Review exercise and project rubrics; do not enable auto-grading with token matching as a correctness guarantee.
- Verify accessibility of SVG labels/captions and the rendered learner experience on desktop/mobile.
- Import into a non-production database, inspect preview behavior and run the project’s backend/frontend checks before publishing.
