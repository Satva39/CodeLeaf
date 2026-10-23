# Redis curriculum review notes

Reviewed on 2026-10-20 against the 47-page `Redis.pdf` and current official Redis documentation. The syllabus is preserved as 24 modules and 202 ordered lesson titles, including advanced/specialist topics. The attached PDF is the course scope source; official docs below are used to check version-sensitive details and command guidance.

## Corrections and compatibility notes

1. **Redis Arrays** — The PDF lists `ARSET`, `ARGET`, `ARRANGE`, and `ARRTRIM` but does not put a minimum version next to the lesson. Current official command documentation identifies Arrays with Redis Open Source 8.8.0 or later; check provider/service compatibility before using the feature. Arrays are explicitly optional/specialist in this course rather than a baseline assumption for all Redis 8 deployments.
2. **Vector sets** — Vector sets are a Redis Open Source 8.0 feature in current documentation. Command support continues to evolve, so examples are capability-gated and must be checked against the deployment.
3. **Legacy sorted-set command** — `ZRANGEBYSCORE` is deprecated since Redis 6.2; use `ZRANGE ... BYSCORE` for new code, while understanding legacy examples.
4. **Legacy list-moving command** — `RPOPLPUSH` is deprecated since Redis 6.2; prefer `LMOVE RIGHT LEFT` where its semantics meet the need.
5. **Transactions** — `MULTI`/`EXEC` serialize a group of queued commands but do not provide automatic relational-database-style rollback for runtime command errors. Design explicit validation/error handling.
6. **Durability and replication** — In-memory state is not the same as durability. RDB, AOF and no-persistence configurations have different data-loss/recovery trade-offs; replication is asynchronous and should not be treated as a guarantee of zero data loss. Test the selected recovery policy.
7. **Pub/Sub vs Streams** — Pub/Sub is best-effort broadcast to subscribers that are online; Streams provide stored entries, consumer groups, acknowledgements and pending-entry recovery. They solve different delivery problems.
8. **Hosted services** — Managed Redis offerings may gate modules/data types, commands, topology controls, permissions, or configuration features. Every specialised lesson says to verify support rather than treating Redis Open Source and every hosted SKU as identical.

## Visuals and execution boundary

The module and lesson SVGs are original CodeLeaf vector diagrams, 1200×675 (16:9), designed as input → reason → verify learning models. Code blocks are marked `static-validation`; CodeLeaf renders them as reference material and does not execute Redis commands. Python client snippets require a separately configured local/test Redis endpoint. Project starters are local-only, use a `REDIS_URL` environment variable, and are not deployed or executed during course generation.

## Editorial status

Everything remains **draft**. Although there are 3 question prompts per lesson, token-based practice smoke checks, 10 project briefs, and starter files, these are not a substitute for Redis-backed integration tests and human review. Protected answer/solution files are intended to remain repository-side under the existing API rules. Review each command output, current version compatibility, assessment quality, and provider-specific claims before publication.

## Official documentation

- Redis data types: https://redis.io/docs/latest/develop/data-types/
- Redis command reference: https://redis.io/docs/latest/commands/
- Redis Arrays (`ARSET`): https://redis.io/docs/latest/commands/arset/
- Redis vector sets: https://redis.io/docs/latest/develop/data-types/vector-sets/
- Redis Time Series: https://redis.io/docs/latest/develop/data-types/timeseries/
- Redis probabilistic data structures: https://redis.io/docs/latest/develop/data-types/probabilistic/
- Redis transactions: https://redis.io/docs/latest/develop/interact/transactions/
- Redis Functions: https://redis.io/docs/latest/develop/interact/programmability/functions-intro/
- Redis clients: https://redis.io/docs/latest/connect/clients/
- redis-py connection guide: https://redis.io/docs/latest/develop/clients/redis-py/connect/
- Redis persistence: https://redis.io/docs/latest/management/persistence/
- Redis security and ACLs: https://redis.io/docs/latest/operate/oss_and_stack/management/security/ and https://redis.io/docs/latest/operate/oss_and_stack/management/security/acl/
- Redis Sentinel: https://redis.io/docs/latest/operate/oss_and_stack/management/sentinel/
- Redis Cluster: https://redis.io/docs/latest/management/scaling/
- Redis memory and latency optimisation: https://redis.io/docs/latest/management/optimization/memory-optimization/ and https://redis.io/docs/latest/management/optimization/latency/
- `RPOPLPUSH`: https://redis.io/docs/latest/commands/rpoplpush/
- `ZRANGEBYSCORE`: https://redis.io/docs/latest/commands/zrangebyscore/
