# CodeLeaf Phase 5 — Isolated code runner threat model

## Scope and trust boundaries

The main FastAPI service validates authenticated requests, enforces per-account quotas, and proxies to a separately deployed runner control plane. It must never execute submitted source code or accept caller-provided shell commands, container image names, runtime paths, or Docker arguments. The runner control plane should run on a dedicated disposable host or dedicated VM that is separate from the main API, database, and all credential-bearing workloads.

The runner executes only the `python` and `javascript` adapters. It accepts bounded source and standard input, and binds the runtime to an immutable SHA-256 image reference selected from server-side configuration. It does not mount the host filesystem or application source into the job container. It disables networking, drops Linux capabilities, runs as a non-root UID, uses a read-only root filesystem, a small no-exec `/tmp`, no-new-privileges, PID/memory/CPU caps, a bounded output stream, per-job timeouts, and container removal on completion/cancellation/failure.

## Threats and controls

- **Command/image injection:** Fixed argument arrays and server-side language/image allowlists; no `shell=True` or learner-selected command/image.
- **Host/container breakout:** Docker provides an isolation boundary, not a proof of safety. Use a patched kernel and daemon, a dedicated runner host, non-root service account, AppArmor/SELinux or an equivalent mandatory access policy, and consider a stronger sandbox (gVisor/Firecracker) before untrusted public production use.
- **Network exfiltration / SSRF:** Job containers use `--network=none` and receive no host mounts or service credentials. The control-plane host itself must have restrictive outbound access; do not use it for other workloads.
- **Denial of service:** Per-owner concurrency and per-minute quotas, service-wide semaphore, timeout, memory/CPU/PID caps, input/output caps, in-memory queue limits and regular host monitoring. The in-memory job store resets on restart and is an MVP limitation, not a durable queue.
- **Cross-account job reads/cancels:** The API checks the owning user in PostgreSQL; the runner checks its service token plus `X-CodeLeaf-User` and compares the job owner before returning/cancelling it.
- **Secret leakage:** Submitted source is not persisted in the runner job record or logs. Return bounded stdout/stderr and generic infrastructure errors; never log tokens or source. Avoid enabling verbose HTTP/client logs that include request bodies.
- **Unpatched runtime dependencies:** Runtime images must be scanned, patched, and pinned to immutable digests. The runner fails closed when a runtime image is absent or is not an immutable SHA-256 reference.

## Local setup and deployment

The `docker-compose.runner.yml` is for local testing only. Configure a random `RUNNER_SERVICE_TOKEN` (at least 32 characters) shared between the main backend and the runner, and immutable runtime image IDs/digests. Pull chosen runtime tags, inspect the resulting image IDs, then pass those immutable IDs to the runner; production deployment should use verified registry digests and image scanning. Do not expose the runner port publicly; restrict access to the main API service over a private network or authenticated service mesh.

The runner Compose example mounts the Docker socket, which effectively grants powerful control over the host daemon. This is acceptable only on the isolated development runner host described above. Do not run the control plane on the main application host or on a host containing production secrets. Docker socket access is not an acceptable tenant-isolation boundary by itself.

## What is and is not verified

The included tests validate input limits, immutable image references, ownership checks, and that generated Docker commands include required isolation/resource flags. They do not establish that arbitrary code is safe, that the host kernel cannot be escaped, that an actual Docker daemon enforces all flags, or that the service is production-ready. Before public production use, run the runner on an isolated machine and perform controlled end-to-end timeout, memory/PID limit, network-block, output-limit, cancellation and cleanup tests against the exact deployment images and runtime configuration. Keep the runner disabled until this validation is complete.
