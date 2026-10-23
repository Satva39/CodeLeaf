-- Inventory / order processing starter.
CREATE TABLE inventory (product_id BIGINT PRIMARY KEY, sku VARCHAR(80) NOT NULL UNIQUE, quantity INT NOT NULL CHECK (quantity >= 0));
CREATE TABLE orders (order_id BIGINT PRIMARY KEY, customer_id BIGINT NOT NULL, status VARCHAR(30) NOT NULL, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE order_items (order_id BIGINT NOT NULL, product_id BIGINT NOT NULL, quantity INT NOT NULL CHECK (quantity > 0), unit_price DECIMAL(12,2) NOT NULL, PRIMARY KEY (order_id, product_id), FOREIGN KEY (order_id) REFERENCES orders(order_id), FOREIGN KEY (product_id) REFERENCES inventory(product_id));
-- TODO: implement transaction-safe reservation, idempotency, concurrency tests and reports.
