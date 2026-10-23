# TaskFlow — Task Management API and CLI

**Status:** Draft starter scaffold. It is not a complete solution.

## Objective
Build a task management system consisting of an HTTP API and a separate Dart command-line client.

## Requirements from the course brief
- [ ] CRUD tasks with IDs, titles, descriptions, statuses, and due dates
- [ ] Consistent validation and errors
- [ ] Status/date filtering, search, and pagination
- [ ] Repository abstraction and storage adapter
- [ ] HTTP CLI client
- [ ] Bounded async operations and error handling
- [ ] Unit/integration tests, API documentation, reproducible dependencies, automated analysis
- [ ] Build/release preparation and security documentation

## Run locally

1. Install the stable Dart SDK and verify `dart --version`.
2. From this directory run `dart pub get`, `dart format .`, `dart analyze .`, and `dart run bin/main.dart`.
3. Add unit/integration tests that exercise normal, invalid, and boundary inputs. Run `dart test` after adding the `test` dev dependency.
4. Record the SDK version and target platform used for verification.

CodeLeaf does not execute arbitrary submitted Dart code in the API process. Use a local SDK or a separately isolated runner.
