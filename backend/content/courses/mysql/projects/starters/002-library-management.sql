-- Library Management starter.
CREATE TABLE books (book_id BIGINT PRIMARY KEY, isbn VARCHAR(20) UNIQUE, title VARCHAR(200) NOT NULL);
CREATE TABLE members (member_id BIGINT PRIMARY KEY, full_name VARCHAR(120) NOT NULL, email VARCHAR(255) NOT NULL UNIQUE);
CREATE TABLE loans (loan_id BIGINT PRIMARY KEY, book_id BIGINT NOT NULL, member_id BIGINT NOT NULL, loaned_on DATE NOT NULL, returned_on DATE, FOREIGN KEY (book_id) REFERENCES books(book_id), FOREIGN KEY (member_id) REFERENCES members(member_id));
-- TODO: add sample data, overdue queries, constraints and loan-history tests.
