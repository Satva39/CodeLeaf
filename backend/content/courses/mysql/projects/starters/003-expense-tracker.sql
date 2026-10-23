-- Expense tracker starter; use DECIMAL for money.
CREATE TABLE categories (category_id BIGINT PRIMARY KEY, category_name VARCHAR(80) NOT NULL UNIQUE);
CREATE TABLE transactions (transaction_id BIGINT PRIMARY KEY, category_id BIGINT NOT NULL, amount DECIMAL(12,2) NOT NULL, occurred_on DATE NOT NULL, note VARCHAR(255), FOREIGN KEY (category_id) REFERENCES categories(category_id));
-- TODO: seed synthetic transactions and write a monthly report.
