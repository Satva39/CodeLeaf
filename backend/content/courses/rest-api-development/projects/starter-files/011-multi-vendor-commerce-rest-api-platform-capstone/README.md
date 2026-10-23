# Multi-Vendor Commerce REST API Platform — Capstone

## Goal
Design and implement a production-oriented commerce API where customers browse products, suppliers manage inventory, and orders follow a controlled lifecycle.

## Required features
- Customer and supplier identity, profiles, and access control
- Products, categories, variants, inventory, search, and pagination
- Server-side cart and order totals with transaction-safe inventory checks
- Payment sandbox/mock integration, signed webhook verification, and duplicate-event protection
- Tenant-aware authorization, OpenAPI contracts, automated tests, observability, and recovery documentation

## Suggested build order
1. Write the resource map and endpoint inventory.
2. Document each request, response, and failure outcome.
3. Implement validation, authentication/authorization, and persistence.
4. Test normal, invalid, unauthorized, duplicate, and dependency-failure requests.
5. Run the relevant checklist in the course before submitting.

## Safety and execution
Use synthetic records and a local development database. Do not use production credentials, real customer data, or live payment endpoints. The CodeLeaf API does not execute arbitrary submitted code; use a separately isolated local runner if your implementation needs one.
