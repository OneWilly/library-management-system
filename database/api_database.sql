-- Library Management API Database (Simplified Version)
-- Created by William Oneka

DROP DATABASE IF EXISTS library_api;
CREATE DATABASE library_api;
USE library_api;

-- Create Members table
CREATE TABLE members (
    member_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone_number VARCHAR(15),
    membership_status ENUM('Active', 'Expired', 'Suspended') DEFAULT 'Active',
    CONSTRAINT chk_email CHECK (email LIKE '%@%.%')
);

-- Create Books table
CREATE TABLE books (
    book_id INT AUTO_INCREMENT PRIMARY KEY,
    isbn VARCHAR(20) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(100) NOT NULL,
    genre VARCHAR(50),
    available_copies INT NOT NULL DEFAULT 0,
    total_copies INT NOT NULL DEFAULT 0,
    CONSTRAINT chk_copies CHECK (available_copies <= total_copies)
);

-- Create Loans table
CREATE TABLE loans (
    loan_id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    member_id INT NOT NULL,
    loan_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    due_date DATE NOT NULL,
    return_date DATE,
    status ENUM('Borrowed', 'Returned', 'Overdue', 'Lost') DEFAULT 'Borrowed',
    FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE RESTRICT,
    FOREIGN KEY (member_id) REFERENCES members(member_id) ON DELETE RESTRICT,
    CONSTRAINT chk_dates CHECK (
        due_date >= loan_date AND 
        (return_date IS NULL OR return_date >= loan_date)
    )
);

-- Insert sample data for Members
INSERT INTO members (first_name, last_name, email, phone_number, membership_status)
VALUES 
    ('John', 'Doe', 'john.doe@example.com', '+1-555-123-4567', 'Active'),
    ('Jane', 'Smith', 'jane.smith@example.com', '+1-555-987-6543', 'Active'),
    ('Michael', 'Johnson', 'michael.j@example.com', '+1-555-456-7890', 'Active');

-- Insert sample data for Books
INSERT INTO books (isbn, title, author, genre, available_copies, total_copies)
VALUES 
    ('9780061120084', 'To Kill a Mockingbird', 'Harper Lee', 'Fiction', 3, 5),
    ('9780141439518', 'Pride and Prejudice', 'Jane Austen', 'Romance', 2, 3),
    ('9780451524935', '1984', 'George Orwell', 'Dystopian', 4, 4);

-- Insert sample data for Loans
INSERT INTO loans (book_id, member_id, loan_date, due_date, return_date, status)
VALUES 
    (1, 1, '2023-06-01', '2023-06-15', '2023-06-14', 'Returned'),
    (2, 2, '2023-06-05', '2023-06-19', NULL, 'Borrowed'),
    (3, 3, '2023-06-10', '2023-06-24', NULL, 'Borrowed');