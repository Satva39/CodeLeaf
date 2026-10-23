# SQL practice dataset

Recommended engine: PostgreSQL 15+; use PostgreSQL 18 if available. Create a **dedicated disposable** database named `codeleaf_sql_lab`, then run `postgresql-lab-setup.sql` inside that database.

The setup script drops and recreates only the course's practice tables in the currently connected database. Verify `current_database()` and `current_user` first; never run it against production or data you need to keep. The tables and rows are synthetic.

In `psql`, for example:

```powershell
createdb -U postgres codeleaf_sql_lab
psql -U postgres -d codeleaf_sql_lab -f ./datasets/postgresql-lab-setup.sql
```

Adapt the path to the course directory on your machine. A GUI SQL client can also open and run the file after you select the disposable database. Some examples require optional extensions (notably PostGIS) or are explicitly marked as `psql` client commands; they are not expected to work unchanged in every engine.

The included data supports students/subjects, employees/departments, customers, categories/products, orders/order items/payments, accounts, JSON events and small temporal-history examples. A destructive reset is intentionally kept in this standalone lab script only.
