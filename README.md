# CodeLeaf Home Category Filter Redesign

This incremental patch replaces the long, multi-row category button list with one compact category filter control. It preserves the existing `category` state and `courses` filter logic, provides a matching-course count, and adds a Clear filter control when a category is selected.

## Apply

1. Back up `frontend/src/pages/HomePage.jsx` and `frontend/src/styles/home.css`.
2. Extract this ZIP into your `E:\Code_Leaf` project root, preserving the `frontend/scripts` path.
3. In PowerShell at `E:\Code_Leaf`, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\Apply-CodeLeaf-CategoryFilterRedesign.ps1 -ProjectRoot "E:\Code_Leaf"
cd E:\Code_Leaf\frontend
node scripts\test-home-category-tabs-css.mjs
npm run build
```

The patch script is idempotent. It removes the previous `CODELEAF_CATEGORY_TABS_POLISH` override if present, replaces the old wrapping category list, and refreshes its own marked CSS block. It does not modify subscription, payment, backend, or course-filter logic.
