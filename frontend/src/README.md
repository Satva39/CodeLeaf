# Frontend source map

- `App.jsx`: route table only; add or change URL routes here.
- `components/layout/Header.jsx`: top navigation, brand, search and theme toggle.
- `components/layout/Footer.jsx`: shared footer.
- `components/common.jsx`: reusable cards, headings, page shell, bookmark button and empty states.
- `pages/`: one file per page/route. Keep page-specific state and markup here.
- `data.js`: catalog roadmap, category groupings, lesson navigation groups and plans.
- `data/lessonContent.js`: current sample lesson payloads. Replace with manifest/API-backed content when the course importer is added.
- `lib/demoState.js`: local demo state and shared formatting/API URL helper.
- `styles.css`: CSS import entry point only.
- `styles/`: base tokens, navigation/layout, homepage, page components, responsive rules, account styles and readability overrides.

## Adding a new page
1. Create `pages/YourPage.jsx` and export it as default.
2. Add its route in `App.jsx`.
3. Put reusable components in `components/common.jsx` only when they are shared by multiple pages.
4. Add page-specific CSS to `styles/pages.css`; responsive adjustments belong in `styles/responsive.css`.


## Adding some more new features
1. Created some features like: having seperated Reference, Projects and Praticies for all the courses.