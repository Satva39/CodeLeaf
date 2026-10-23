# SciPy curriculum review notes

## Source inspection

The entire supplied `SciPy.pdf` was text-extracted and rendered for visual inspection (40 pages). Section B provides 136 numbered topics across 20 modules; Section C lists 28 practical exercises; Section D lists 11 numbered project briefs plus the capstone (12 total); Section E adds 10 optional specialist topics; Sections F and G describe the path and quality checks. The PDF's project thumbnails/illustrative visuals on pages 30–33 and its tables/roadmap visuals around pages 36–39 were also inspected in the rendered pages; the numbered curriculum remains the primary source for lesson names and subtopic wording.

## Preserved from the PDF

- All 136 numbered lesson titles and the subtopic lines extracted from Section B.
- All 28 named practical exercises, mapped to relevant lesson IDs.
- All 11 numbered project briefs and the separate capstone, including objectives and principal features.
- All 10 Section E specialist-topic groups, preserved in `advanced-specialist-topics.md`.
- The seven-stage learning path and prerequisite map in `learning-roadmap.md`.

## Technical clarifications and treatment decisions

1. **Version assumptions:** the curriculum is written against the official SciPy 1.18.0 manual surfaced on 2026-10-17. The available local runtime is SciPy 1.17.0; this is reported explicitly instead of claiming examples were executed against 1.18.0. Recheck the target Python/NumPy combinations and release notes before publication.
2. **Legacy Fourier API:** the PDF correctly identifies `scipy.fftpack` as legacy; this course points new Fourier examples to `scipy.fft` and retains `fftpack` for migration awareness only.
3. **Legacy interpolation:** the PDF marks `interp1d` as legacy material. New interpolation examples use current alternatives such as `CubicSpline` and `PchipInterpolator`; `interp1d` is not used as the recommended path.
4. **Differentiation:** `scipy.differentiate` is included directly, with `derivative`, `jacobian`, and `hessian`, consistent with the modern documentation.
5. **Optional specialist material:** advanced topics, source builds, low-level BLAS/LAPACK, spatial rotations, high-dimensional interpolation, meta-analysis, and API migration are not omitted; they are explicitly preserved as optional material rather than forced into the 136 numbered core lessons.
6. **Additional metadata:** estimated workload (100 hours), exercise-to-lesson mapping, project rubrics, and the 30-question suggested final assessment distribution are CodeLeaf editorial recommendations, not values asserted by the PDF. They remain draft.
7. **Code execution:** the existing platform content mode displays code and can provide static/concept grading; a browser page is not a secure general-purpose Python executor. The examples are marked `static-validation`. Do not enable arbitrary code execution through the production FastAPI process.
8. **Security and gamification:** this patch includes no API keys, secrets, production credentials, or XP overrides. Exercise/lesson completion rewards remain governed by platform-wide backend logic.

## Review status

All course content files are marked `draft`. JSON/schema and asset-reference validation is performed before packaging. A draft passing local validation is not a claim that all 136 examples were executed on SciPy 1.18.0 or that course material has received human subject-matter approval.
