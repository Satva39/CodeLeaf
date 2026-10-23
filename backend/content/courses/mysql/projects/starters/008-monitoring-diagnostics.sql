-- Use as a read-only local diagnostics worksheet.
SELECT VERSION() AS server_version;
SHOW GLOBAL STATUS LIKE 'Threads_connected';
SHOW FULL PROCESSLIST;
-- TODO: collect a bounded before/after sample and document required privileges and PII redaction.
