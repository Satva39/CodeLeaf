-- Student Management Database starter; use only in a disposable schema.
CREATE TABLE students (student_id BIGINT PRIMARY KEY, full_name VARCHAR(120) NOT NULL, email VARCHAR(255) NOT NULL UNIQUE);
CREATE TABLE teachers (teacher_id BIGINT PRIMARY KEY, full_name VARCHAR(120) NOT NULL);
CREATE TABLE subjects (subject_id BIGINT PRIMARY KEY, subject_name VARCHAR(120) NOT NULL UNIQUE, teacher_id BIGINT, FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id));
CREATE TABLE enrollments (student_id BIGINT NOT NULL, subject_id BIGINT NOT NULL, enrolled_on DATE NOT NULL, grade DECIMAL(5,2), PRIMARY KEY (student_id, subject_id), FOREIGN KEY (student_id) REFERENCES students(student_id), FOREIGN KEY (subject_id) REFERENCES subjects(subject_id));
-- TODO: add synthetic seed rows, grade summaries, negative tests and teardown notes.
