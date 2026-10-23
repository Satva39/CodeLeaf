-- Production-ready e-commerce schema skeleton; test locally before adapting.
CREATE TABLE customers (customer_id BIGINT PRIMARY KEY, email VARCHAR(255) NOT NULL UNIQUE, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE products (product_id BIGINT PRIMARY KEY, sku VARCHAR(80) NOT NULL UNIQUE, title VARCHAR(200) NOT NULL, active BOOLEAN NOT NULL DEFAULT TRUE);
CREATE TABLE product_variants (variant_id BIGINT PRIMARY KEY, product_id BIGINT NOT NULL, variant_code VARCHAR(80) NOT NULL UNIQUE, FOREIGN KEY (product_id) REFERENCES products(product_id));
CREATE TABLE orders (order_id BIGINT PRIMARY KEY, customer_id BIGINT NOT NULL, status VARCHAR(30) NOT NULL, created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (customer_id) REFERENCES customers(customer_id));
CREATE TABLE order_items (order_id BIGINT NOT NULL, variant_id BIGINT NOT NULL, quantity INT NOT NULL CHECK (quantity > 0), unit_price DECIMAL(12,2) NOT NULL, PRIMARY KEY (order_id, variant_id), FOREIGN KEY (order_id) REFERENCES orders(order_id), FOREIGN KEY (variant_id) REFERENCES product_variants(variant_id));
-- TODO: add suppliers, carts, inventory and payment state; design transaction boundaries and migration/restore procedures.
