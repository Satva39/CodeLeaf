# SciPy advanced and specialist topics

This optional reference preserves Section E of the supplied 40-page SciPy curriculum PDF. It extends the 136 numbered core lessons; it is not a claim that every item is necessary for a beginner course. All topics remain draft until checked against the exact supported SciPy version.

## 1. Advanced numerical linear algebra
- Matrix functions, including matrix exponentials and logarithms.
- Generalized eigenvalue problems and advanced decompositions.
- Specialized factorizations for structured matrices.
- Iterative eigenvalue calculations with sparse operators.
- Conditioning, stability, and numerical error analysis.
- Low-level BLAS and LAPACK concepts behind linear-algebra performance.

## 2. Advanced numerical optimization
- Large-scale nonlinear optimization.
- Advanced constrained optimization.
- Mixed-integer linear programming.
- Robust least-squares modeling.
- Optimization under noisy objective evaluations.
- Sensitivity and parameter identifiability.
- Comparative evaluation of optimization algorithms.

## 3. Advanced statistical methods
- Custom probability distributions and advanced random-variable APIs.
- Power analysis and experimental design.
- Bootstrap and permutation methods for custom statistics.
- Multiple-hypothesis corrections.
- Contingency tables, association measures, and meta-analysis foundations.
- Statistical assumptions, model diagnostics, and interpretation.

## 4. Advanced spatial computation
- Rigid-body transformations through `scipy.spatial.transform`.
- Rotation representations and composition.
- Interpolation in higher-dimensional scientific spaces.
- Large point-cloud indexing.
- Computational-geometry edge cases.
- Graph optimization and sparse graph algorithms.

## 5. Advanced differential equations and integration
- Solver selection for stiff systems.
- Error control and adaptive integration.
- Event-driven physical simulations.
- Boundary-value problems with unknown parameters.
- Difficult integrands and convergence diagnostics.
- Conservation laws and independent solution validation.

## 6. Specialized signal processing
- Filter realization and numerical stability.
- High-order filters using second-order sections.
- Transfer-function and state-space analysis.
- Advanced spectral estimation and time-frequency analysis.
- Sample-rate conversion and aliasing control.

## 7. Advanced image processing
- Morphological operations on multidimensional data.
- Distance transforms and geometric measurements.
- Image-registration foundations.
- Interpolation effects on transformed images.
- Segmentation validation.
- Memory-efficient batch processing.

## 8. SciPy internals and performance engineering
- How compiled numerical routines interact with Python.
- Array-memory and data-conversion costs.
- Benchmarking numerical algorithms and profiling repeated calculations.
- Threading and numerical-library performance.
- Debugging numerical differences across environments.

## 9. Building SciPy from source
- Purpose of source builds and build dependencies.
- Development environment setup.
- Running tests against a source checkout.
- Building documentation.
- Contributing code and reproducing upstream issues.

## 10. Legacy APIs and migration
- Older Fourier routines under `scipy.fftpack`; use `scipy.fft` for new workflows when appropriate.
- Legacy interpolation interfaces; identify supported alternatives such as `CubicSpline` and `PchipInterpolator` before choosing an interface for new work.
- Deprecated functions encountered in older tutorials.
- Release-note and warning-based migration workflows.
- Version compatibility and regression testing.

## Treatment

These topics are cross-linked conceptually to lessons in linear algebra (28–36, 91–95), integration and differential equations (37–47), interpolation (48–53), optimization (54–64), signals (65–76), statistics (77–90), spatial algorithms (96–101), image processing (102–108), and professional practice (125–132). A future specialist course may split them into separate lessons after scope and execution environments are decided.
