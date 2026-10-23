# Git course curriculum review notes

## Source coverage

The supplied `Git.pdf` was reviewed as a 38-page PDF. Its Section B enumerates 216 lesson topics across 20 modules in a continuous 1–216 sequence; all were preserved in `course.json`, module files and separate lesson files. Section C lists 28 exercise ideas; those topics are mapped to relevant lessons. Section D lists six projects plus the professional team workflow capstone; all seven are represented. Sections E–G informed Core / Advanced / Optional Specialization / Professional labels, the suggested learning roadmap, prerequisites and the coverage audit.

## Technical notes and clarifications

- Prefer modern `git switch` and `git restore` for their focused branch/file-state operations; retain awareness of `git checkout` when maintaining older instructions or repositories.
- `git reset`, `git restore`, `git clean` and history rewriting can discard work or move refs. Examples use dry-run/read-only inspection first and require disposable practice repositories where state changes are demonstrated.
- `git revert` creates a new reversing commit; `git reset` moves the current branch/HEAD relationship and may change what is staged or checked out. They are not interchangeable.
- Fetch updates repository objects and remote-tracking refs but does not integrate into the current branch by itself. Pull fetches and then integrates according to configured behavior. Rejected pushes should be inspected rather than force-pushed immediately.
- `.gitignore` does not remove already tracked files or erase secrets from history. Exposed credentials should be revoked/rotated promptly; history cleanup and collaboration coordination are separate steps.
- A valid signature is not by itself proof that the identity is trusted. Verify signer identity against the team’s trust policy. Git LFS is a separate extension.
- The PDF calls out sparse-checkout implementation limitations. The current official documentation discusses sparse-checkout and sparse-index behavior separately and documents compatibility/known-bug considerations; this course treats limitations as version/tool/workflow-dependent instead of labeling every sparse-checkout workflow uniformly experimental.
- Hosting platform workflows (pull requests, merge requests, permissions, review approvals and branch protection) are not core Git commands. The lessons describe these as platform capabilities and refer to their official product documentation.
- The PDF does not prescribe an exact workload or specific installed Git version. This draft estimates 90 study/practice hours and references online official documentation checked on 2026-10-15; re-check the learner's `git --version` and provider docs before publication.

## Prerequisite roadmap

1. Modules 1–5: concepts, setup, repository model, working tree/index, commits and history.
2. Modules 6–10: recovery, branches, merge conflicts, remotes and team collaboration.
3. Modules 11–13: rebase, cherry-pick, release tags and advanced investigation.
4. Modules 14, 17–18: configuration, attributes, hooks, security and developer/hosting integrations.
5. Modules 15–16 and 19: internals, advanced repository features, maintenance and migration.
6. Module 20 plus practical exercises and the capstone: automation and professional workflow evidence.

## Publication and runner status

All course, module, lesson, exercise, project and assessment files are marked `draft`. All 216 lessons include a visual, command example, expected output, task, hints, common mistakes, recap, source links and a separate three-question knowledge-check file. The CodeLeaf app does not execute arbitrary Git commands inside FastAPI or the browser; commands should be run by a learner in a disposable local repository, and hands-on project work uses static checks plus human review. The exercise API has a fixed set of grading modes, so practical submissions use required-string smoke checks backed by explicit human-review criteria.

## Original content and assets

Course explanations, practice prompts and SVG diagrams are original CodeLeaf material based on the provided topic outline. The PDF supplies the subject coverage, not the complete lesson prose. Every visual in `assets/asset-manifest.json` is included as an SVG. No remote image URLs, externally copied illustrations or raster assets are required.
