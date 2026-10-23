-- Illustrative schema only; adapt identity and data types to the target database.
CREATE TABLE Student (
    StudentID INTEGER NOT NULL PRIMARY KEY,
    DisplayName VARCHAR(80) NOT NULL
);

-- Use only synthetic local test records. Add provider-specific identity and constraints deliberately.
