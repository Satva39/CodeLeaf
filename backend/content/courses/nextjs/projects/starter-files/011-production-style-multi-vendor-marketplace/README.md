# Production-Style Multi-Vendor Marketplace — starter files

## Goal
Build a marketplace where customers browse products, place orders, and manage purchases, while vendors manage inventory and authorized administrators oversee the platform.

## Setup
Create a separate JavaScript Next.js project with `npx create-next-app@latest my-app --js --app`, then copy the files from this folder into it. The starter folder is deliberately small; add the features described in the project brief in milestones.

## Required checkpoints
- [ ] Separate customer/vendor/admin experiences
- [ ] dynamic product routes, search, sorting, filtering, and pagination
- [ ] database-backed inventory, profiles, and order management
- [ ] validated forms and server-side mutations
- [ ] test-mode payment integration with verified payment events
- [ ] order processing, upload validation, and external API integrations
- [ ] SEO metadata, image optimization, loading and error states
- [ ] authentication, permission, business-rule, and end-to-end tests
- [ ] production deployment, environment management, monitoring, architecture documentation

## Verification
Run the applicable lint and test scripts and `npm run build`. Use synthetic data and test-mode credentials. Test direct route loads, invalid input, empty state, failures, and permission boundaries. Do not commit environment secrets.
