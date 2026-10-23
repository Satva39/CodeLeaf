-- Original CodeLeaf practice fixture. Safe to run in a disposable database.
PRAGMA foreign_keys = ON;
CREATE TABLE authors (author_id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
CREATE TABLE books (book_id INTEGER PRIMARY KEY, title TEXT NOT NULL, published_year INTEGER CHECK (published_year BETWEEN 1450 AND 2100));
CREATE TABLE book_authors (book_id INTEGER NOT NULL REFERENCES books(book_id) ON DELETE CASCADE, author_id INTEGER NOT NULL REFERENCES authors(author_id) ON DELETE CASCADE, PRIMARY KEY (book_id, author_id));
INSERT INTO authors(name) VALUES ('A. Rivera'), ('K. Patel');
INSERT INTO books(title, published_year) VALUES ('Small Data Systems', 2022), ('Query Patterns', 2024);
INSERT INTO book_authors(book_id,author_id) VALUES (1,1), (2,2);
SELECT b.title, a.name FROM books AS b JOIN book_authors AS ba USING(book_id) JOIN authors AS a USING(author_id) ORDER BY b.title;
