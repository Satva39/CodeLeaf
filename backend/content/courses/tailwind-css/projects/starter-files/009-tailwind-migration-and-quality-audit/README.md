# Tailwind Migration and Quality Audit — Starter

This starter uses plain HTML, CSS and JavaScript with Tailwind CSS v4 through the Vite plugin and Vite 7. No TypeScript is used. Use Node.js 20.19+ or 22.12+ for this Vite generation.

## Run locally (Windows PowerShell)

```powershell
npm install
npm run dev
```

Use the local URL printed by Vite. Confirm the installed Tailwind version before using v4-specific syntax in an existing project. Run `npm run build` after editing.

## Goal

Modernize a Tailwind v3 project in a branch while keeping existing screens usable and documenting decisions.

## Required features

- Dependency and integration migration
- Theme and source detection review
- Visual comparison before/after
- Accessibility, browser and regression audit

## Quality check

- Inspect narrow, medium and wide viewports.
- Use keyboard navigation and keep focus visible.
- Confirm the production CSS was generated.
- Add automated or human-reviewed tests where appropriate.
