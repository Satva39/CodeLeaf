# SciPy learning roadmap and prerequisite map

## Course baseline

- **Core sequence:** 20 modules and 136 numbered lesson topics from the supplied SciPy curriculum PDF.
- **Prerequisites:** basic Python and NumPy array reasoning. Calculus, probability, linear algebra, and ODEs are reviewed as needed.
- **Version policy:** official SciPy 1.18.0 manual checked 2026-10-17; local validation runtime is SciPy 1.17.0. Retest against the exact target version before publication.

## Stages

1. **Orientation and setup (Modules 1–3; lessons 1–20):** package purpose, environment, API documentation, NumPy arrays, dtype, precision, and error.
2. **Numerical foundations (Modules 4–5; lessons 21–36):** constants, special functions, finite-difference differentiation, linear systems, factorizations, eigenvalues, least squares, residuals.
3. **Core numerical methods (Modules 6–8; lessons 37–64):** quadrature, ODE initial/boundary-value problems, interpolation, root finding, optimization, curve fitting, convergence troubleshooting.
4. **Signal and statistical analysis (Modules 9–11; lessons 65–90):** FFTs, filters, resampling, probability distributions, tests, bootstrap/Monte Carlo methods, and reporting.
5. **Specialized scientific methods (Modules 12–17; lessons 91–120):** sparse arrays and solvers, spatial algorithms, image processing, clustering, scientific file I/O, and orthogonal distance regression.
6. **Professional workflow (Modules 18–19; lessons 121–132):** reusable functions, subpackage integration, performance, parallel-workload reasoning, numerical testing, debugging, reproducibility, security, and contribution.
7. **Capstone (Module 20; lessons 133–136):** define a numerical question, choose methods, build a reproducible structure, validate independently, and communicate trade-offs and limitations.

## Dependency map

| Topic area | Recommended prerequisites | Notes |
|---|---|---|
| Constants and special functions | Python imports, numerical types, basic algebra | Start with Module 4 after foundations. |
| Numerical differentiation | NumPy arrays and function evaluation | Step size and finite precision can interact. |
| Dense linear algebra | Arrays, matrices, basic linear algebra | Check residuals and conditioning; an inverse is rarely the first choice for solving Ax=b. |
| Integration and ODEs | Functions, calculus, initial/boundary conditions | Solver method and tolerance depend on stiffness, scale, and problem structure. |
| Interpolation | Arrays, coordinates, sampled data | Separate interpolation from extrapolation; choose shape-preserving methods when appropriate. |
| Optimization | Objective functions, derivatives, basic calculus | Local/global search and constraints are distinct considerations. |
| Fourier and signal processing | Arrays, periodicity, sampling, frequency | Sampling rate and window choices affect interpretation. |
| Statistics | Descriptive statistics, probability, sampling | Choose tests based on study design and assumptions, not the smallest p-value. |
| Sparse algorithms | Linear algebra and matrix structure | Sparse representation is beneficial only when the structure and operation justify it. |
| Spatial and clustering algorithms | Coordinates, geometry, distance metrics | Feature scaling and memory costs may matter. |
| Image processing | Multidimensional arrays and coordinate transforms | Track axes, interpolation, boundary mode, and dtype. |
| Scientific I/O | File paths, numeric types, data schemas | Validate metadata and round-trip saved data. |
| ODR | Regression fundamentals and model functions | Useful when uncertainty in independent variables matters. |
| Professional validation | Familiarity with at least two SciPy subpackages | Validate results independently and record versions and assumptions. |

## Flexible pathways

The curriculum is not strictly linear beyond prerequisites. A statistics learner may prioritize Modules 4, 11, 16, and 19; an engineering learner may prioritize Modules 5–8 and the advanced optimization/ODE extensions. Keep the base modules and prerequisites visible when learners choose a specialization.
