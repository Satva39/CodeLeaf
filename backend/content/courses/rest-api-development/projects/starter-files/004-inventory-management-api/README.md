# Inventory Management API

## Goal
Build an API for products, stock quantities, and inventory changes.

## Required features
- Product and inventory resources
- Atomic stock adjustments and database constraints
- Filtering and low-stock queries
- Role permissions, audit history, and concurrency tests

## Suggested build order
1. Write the resource map and endpoint inventory.
2. Document each request, response, and failure outcome.
3. Implement validation, authentication/authorization, and persistence.
4. Test normal, invalid, unauthorized, duplicate, and dependency-failure requests.
5. Run the relevant checklist in the course before submitting.

## Safety and execution
Use synthetic records and a local development database. Do not use production credentials, real customer data, or live payment endpoints. The CodeLeaf API does not execute arbitrary submitted code; use a separately isolated local runner if your implementation needs one.
