-- HR database starter.
CREATE TABLE departments (department_id BIGINT PRIMARY KEY, department_name VARCHAR(120) NOT NULL UNIQUE);
CREATE TABLE employees (employee_id BIGINT PRIMARY KEY, department_id BIGINT NOT NULL, manager_id BIGINT NULL, full_name VARCHAR(120) NOT NULL, hired_on DATE NOT NULL, FOREIGN KEY (department_id) REFERENCES departments(department_id), FOREIGN KEY (manager_id) REFERENCES employees(employee_id));
-- TODO: add hierarchy queries, access roles and historical reporting.
