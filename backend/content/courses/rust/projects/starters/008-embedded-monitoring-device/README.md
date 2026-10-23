# Embedded Monitoring Device

## Purpose
Build a monitoring application for a supported microcontroller or emulated target.

## Start here
1. Confirm the input, output, and invalid-input cases.
2. Add tests before growing the implementation.
3. Keep external effects behind explicit boundaries.

## Verification
Run `cargo run`, then add tests and run `cargo test`. Before review, also run `cargo fmt --check` and `cargo clippy --all-targets --all-features -- -D warnings` where supported. Record toolchain and dependency versions.
