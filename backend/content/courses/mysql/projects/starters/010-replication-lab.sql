-- Replication lab worksheet. Configure only between isolated test instances.
SHOW REPLICA STATUS\G
SELECT @@GLOBAL.gtid_executed AS executed_gtids;
-- TODO: record topology, binary-log/GTID assumptions, lag, controlled failure and recovery proof.
