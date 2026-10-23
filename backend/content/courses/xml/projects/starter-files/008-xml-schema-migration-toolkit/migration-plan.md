# Version migration plan
Map `catalog@version` to `catalog@schema-version`; map `product@id` to `product@sku`; map `name` to `display-name`; supply currency only from a documented rule or trusted source. Preserve the original file, validate the target schema, test missing/duplicate IDs, and define rollback.
