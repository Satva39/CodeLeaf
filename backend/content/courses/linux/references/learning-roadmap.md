# Linux learning roadmap

This roadmap follows Linux.pdf, Section F. Study destructive or state-changing topics in a disposable virtual machine, not on a production system.

## Phase 1 — Foundations
**Modules 1–6.** Understand distributions and architecture; prepare an installation or VM; navigate the terminal and filesystem; manage test files; search and transform text; consult documentation.

**Checkpoint:** identify the installed distribution and kernel, safely navigate a directory tree, compare two sample files, process text with a pipeline, and find the relevant manual page.

## Phase 2 — Core administration
**Modules 7–11.** Manage identities and permissions, package software, inspect processes and services, and learn storage structures.

**Checkpoint:** inspect a service and its logs, describe a permission decision, identify disk/mount state, and explain a safe update/rollback plan.

## Phase 3 — Networking and automation
**Modules 12–16.** Troubleshoot interfaces/routes/DNS/sockets, use SSH safely, learn Bash, automate repeatable tasks, and inspect logs/metrics.

**Checkpoint:** write a small script with validated inputs, connect to a practice VM after verifying its host key, and document one scheduled task or health check.

## Phase 4 — Production administration and security
**Modules 17–19.** Deploy services, harden access, and use evidence-first troubleshooting/recovery.

**Checkpoint:** deploy a test service, apply a least-privilege policy, review relevant logs, and recover from a planned fault in a disposable VM.

## Phase 5 — Advanced Linux
**Modules 20–23.** Explore kernel internals, performance, developer tooling, VMs, containers, namespaces, and resource controls.

**Checkpoint:** gather a baseline for a workload, identify a plausible bottleneck, and explain which boundaries containers do and do not isolate.

## Phase 6 — Professional practice
**Modules 24–27.** Operate cloud workloads, practise reliability and restore testing, understand desktop/specialized systems, and document maintainable changes.

**Checkpoint:** complete a capstone plan with repeatable provisioning, service verification, backup restoration evidence, and a recovery/runbook document.

## Suggested paths
- **Linux administration:** Modules 1–21, then 24 and 27; choose modules 22–23 or 25–26 as relevant.
- **Software development / DevOps:** Modules 1–8, 9–18, 22–24, then relevant advanced topics.
- **Security operations:** Modules 1–13, 16–21, and 24, emphasizing authorized lab systems and evidence handling.
- **Embedded systems:** Modules 1–6 and 19–20, followed by 26; C and computer architecture are useful prerequisites.

## Prerequisite map
| Topic | Useful prior concepts |
|---|---|
| Permissions and user administration | Terminal, paths, file metadata |
| Package management | CLI, repositories, trusted sources |
| Bash automation | Commands, quoting, streams, text processing, exit status |
| Storage administration | Devices, paths, permissions, recovery concepts |
| Networking | Addressing, routes, name resolution, sockets |
| SSH / remote administration | Users, permissions, networking, host-key verification |
| Security hardening | Identity, services, network exposure, logs |
| Performance work | Processes, memory, storage, monitoring |
| Kernel internals | OS fundamentals and computer architecture |
| Containers | Processes, permissions, networking, resource controls |
| Cloud automation | SSH, scripting, networking, services, version control |
| Capstone | Administration, security, monitoring, backups, deployment |
