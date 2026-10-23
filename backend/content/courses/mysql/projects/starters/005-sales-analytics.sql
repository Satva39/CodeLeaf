-- Sales analytics starter.
CREATE TABLE sales (sale_id BIGINT PRIMARY KEY, product_id BIGINT NOT NULL, sold_at DATETIME NOT NULL, quantity INT NOT NULL, unit_price DECIMAL(12,2) NOT NULL);
-- TODO: group by month/product, rank products with a window function, and compare EXPLAIN plans.
