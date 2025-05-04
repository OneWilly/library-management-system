-- Library Management System Database
-- Created by William Oneka

-- Drop database if exists
DROP DATABASE IF EXISTS library_management;

-- Create database
CREATE DATABASE library_management;
USE library_management;

-- Create Members table
CREATE TABLE members (
    member_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone_number VARCHAR(15),
    address VARCHAR(255),
    date_of_birth DATE,
    membership_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    membership_status ENUM('Active', 'Expired', 'Suspended') DEFAULT 'Active',
    CONSTRAINT chk_email CHECK (email LIKE '%@%.%')
);

-- Create Books table
CREATE TABLE books (
    book_id INT AUTO_INCREMENT PRIMARY KEY,
    isbn VARCHAR(20) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    author VARCHAR(100) NOT NULL,
    publisher VARCHAR(100),
    publication_year INT,
    genre VARCHAR(50),
    language VARCHAR(30) DEFAULT 'English',
    page_count INT,
    available_copies INT NOT NULL DEFAULT 0,
    total_copies INT NOT NULL DEFAULT 0,
    date_added DATE DEFAULT (CURRENT_DATE),
    CONSTRAINT chk_publication_year CHECK (publication_year IS NULL OR (publication_year > 0 AND publication_year <= YEAR(CURRENT_DATE))),
    CONSTRAINT chk_copies CHECK (available_copies <= total_copies)
);

-- Create Staff table
CREATE TABLE staff (
    staff_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone_number VARCHAR(15),
    position VARCHAR(50) NOT NULL,
    hire_date DATE NOT NULL,
    salary DECIMAL(10, 2),
    CONSTRAINT chk_staff_email CHECK (email LIKE '%@%.%')
);

-- Create Categories table
CREATE TABLE categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

-- Create Book_Categories table (Many-to-Many relationship)
CREATE TABLE book_categories (
    book_id INT,
    category_id INT,
    PRIMARY KEY (book_id, category_id),
    FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE CASCADE
);

-- Create Loans table
CREATE TABLE loans (
    loan_id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    member_id INT NOT NULL,
    staff_id INT NOT NULL,
    loan_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    due_date DATE NOT NULL,
    return_date DATE,
    status ENUM('Borrowed', 'Returned', 'Overdue', 'Lost') DEFAULT 'Borrowed',
    FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE RESTRICT,
    FOREIGN KEY (member_id) REFERENCES members(member_id) ON DELETE RESTRICT,
    FOREIGN KEY (staff_id) REFERENCES staff(staff_id) ON DELETE RESTRICT,
    CONSTRAINT chk_dates CHECK (
        due_date >= loan_date AND 
        (return_date IS NULL OR return_date >= loan_date)
    )
);

-- Create Fines table
CREATE TABLE fines (
    fine_id INT AUTO_INCREMENT PRIMARY KEY,
    loan_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    issue_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    payment_date DATE,
    status ENUM('Pending', 'Paid', 'Waived') DEFAULT 'Pending',
    FOREIGN KEY (loan_id) REFERENCES loans(loan_id) ON DELETE CASCADE,
    CONSTRAINT chk_amount CHECK (amount > 0),
    CONSTRAINT chk_payment_date CHECK (payment_date IS NULL OR payment_date >= issue_date)
);

-- Create Reservations table
CREATE TABLE reservations (
    reservation_id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    member_id INT NOT NULL,
    reservation_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    expiry_date DATE NOT NULL,
    status ENUM('Active', 'Fulfilled', 'Cancelled', 'Expired') DEFAULT 'Active',
    FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
    FOREIGN KEY (member_id) REFERENCES members(member_id) ON DELETE CASCADE,
    CONSTRAINT chk_reservation_dates CHECK (expiry_date > reservation_date)
);

-- Create a trigger to update available_copies when book is borrowed
DELIMITER //
CREATE TRIGGER after_loan_insert
AFTER INSERT ON loans
FOR EACH ROW
BEGIN
    IF NEW.status = 'Borrowed' THEN
        UPDATE books SET available_copies = available_copies - 1
        WHERE book_id = NEW.book_id AND available_copies > 0;
    END IF;
END//

-- Create a trigger to update available_copies when book is returned
CREATE TRIGGER after_loan_update
AFTER UPDATE ON loans
FOR EACH ROW
BEGIN
    IF NEW.status = 'Returned' AND OLD.status != 'Returned' THEN
        UPDATE books SET available_copies = available_copies + 1
        WHERE book_id = NEW.book_id;
    END IF;
END//

-- Create a trigger to check if a reservation can be fulfilled after a book return
CREATE TRIGGER check_reservations_after_return
AFTER UPDATE ON loans
FOR EACH ROW
BEGIN
    DECLARE reservation_exists INT;
    
    IF NEW.status = 'Returned' AND OLD.status != 'Returned' THEN
        -- Check if there's an active reservation for this book
        SELECT COUNT(*) INTO reservation_exists
        FROM reservations
        WHERE book_id = NEW.book_id AND status = 'Active'
        ORDER BY reservation_date ASC
        LIMIT 1;
        
        -- If there's a reservation, update its status
        IF reservation_exists > 0 THEN
            UPDATE reservations
            SET status = 'Fulfilled'
            WHERE book_id = NEW.book_id AND status = 'Active'
            ORDER BY reservation_date ASC
            LIMIT 1;
        END IF;
    END IF;
END//
DELIMITER ;

-- Insert sample data for Members
INSERT INTO members (first_name, last_name, email, phone_number, address, date_of_birth, membership_date)
VALUES 
    ('John', 'Doe', 'john.doe@example.com', '+1-555-123-4567', '123 Main St, Anytown', '1985-04-15', '2023-01-10'),
    ('Jane', 'Smith', 'jane.smith@example.com', '+1-555-987-6543', '456 Oak Ave, Somewhere', '1990-08-22', '2023-02-15'),
    ('Michael', 'Johnson', 'michael.j@example.com', '+1-555-456-7890', '789 Pine Rd, Elsewhere', '1978-12-03', '2023-03-05'),
    ('Sarah', 'Williams', 'sarah.w@example.com', '+1-555-246-8135', '321 Elm St, Nowhere', '1995-06-17', '2023-04-20'),
    ('David', 'Brown', 'david.b@example.com', '+1-555-369-8520', '654 Maple Dr, Anyplace', '1982-11-30', '2023-05-12');

-- Insert sample data for Books
INSERT INTO books (isbn, title, author, publisher, publication_year, genre, language, page_count, available_copies, total_copies)
VALUES 
    ('9780061120084', 'To Kill a Mockingbird', 'Harper Lee', 'HarperCollins', 1960, 'Fiction', 'English', 336, 3, 5),
    ('9780141439518', 'Pride and Prejudice', 'Jane Austen', 'Penguin Classics', 1813, 'Romance', 'English', 432, 2, 3),
    ('9780451524935', '1984', 'George Orwell', 'Signet Classics', 1949, 'Dystopian', 'English', 328, 4, 4),
    ('9780743273565', 'The Great Gatsby', 'F. Scott Fitzgerald', 'Scribner', 1925, 'Fiction', 'English', 180, 1, 2),
    ('9780316769174', 'The Catcher in the Rye', 'J.D. Salinger', 'Little, Brown and Company', 1951, 'Coming-of-age', 'English', 277, 2, 3),
    ('9780679783268', 'Crime and Punishment', 'Fyodor Dostoevsky', 'Vintage Classics', 1866, 'Psychological Fiction', 'English', 671, 1, 1),
    ('9780547928227', 'The Hobbit', 'J.R.R. Tolkien', 'Houghton Mifflin Harcourt', 1937, 'Fantasy', 'English', 366, 0, 2),
    ('9781451673319', 'Fahrenheit 451', 'Ray Bradbury', 'Simon & Schuster', 1953, 'Dystopian', 'English', 249, 3, 3);

-- Insert sample data for Staff
INSERT INTO staff (first_name, last_name, email, phone_number, position, hire_date, salary)
VALUES 
    ('Robert', 'Johnson', 'robert.j@library.org', '+1-555-111-2222', 'Head Librarian', '2018-06-15', 65000.00),
    ('Emily', 'Davis', 'emily.d@library.org', '+1-555-222-3333', 'Assistant Librarian', '2020-03-10', 52000.00),
    ('Thomas', 'Wilson', 'thomas.w@library.org', '+1-555-333-4444', 'IT Specialist', '2021-09-20', 58000.00),
    ('Amanda', 'Taylor', 'amanda.t@library.org', '+1-555-444-5555', 'Circulation Clerk', '2022-01-05', 42000.00);

-- Insert sample data for Categories
INSERT INTO categories (name, description)
VALUES 
    ('Fiction', 'Literary works created from the imagination'),
    ('Non-fiction', 'Informational and factual writing'),
    ('Biography', 'An account of someone\'s life written by someone else'),
    ('Science Fiction', 'Fiction based on imagined future scientific or technological advances'),
    ('Mystery', 'Fiction dealing with the solution of a crime or puzzle'),
    ('Romance', 'Fiction that focuses on the romantic relationship between characters'),
    ('History', 'Non-fiction about past events'),
    ('Self-Help', 'Books aimed at helping readers solve personal problems');

-- Insert sample data for Book_Categories
INSERT INTO book_categories (book_id, category_id)
VALUES 
    (1, 1), -- To Kill a Mockingbird - Fiction
    (2, 1), -- Pride and Prejudice - Fiction
    (2, 6), -- Pride and Prejudice - Romance
    (3, 1), -- 1984 - Fiction
    (3, 4), -- 1984 - Science Fiction
    (4, 1), -- The Great Gatsby - Fiction
    (5, 1), -- The Catcher in the Rye - Fiction
    (6, 1), -- Crime and Punishment - Fiction
    (6, 5), -- Crime and Punishment - Mystery
    (7, 1), -- The Hobbit - Fiction
    (7, 4), -- The Hobbit - Science Fiction
    (8, 1), -- Fahrenheit 451 - Fiction
    (8, 4); -- Fahrenheit 451 - Science Fiction

-- Insert sample data for Loans
INSERT INTO loans (book_id, member_id, staff_id, loan_date, due_date, return_date, status)
VALUES 
    (1, 1, 2, '2023-06-01', '2023-06-15', '2023-06-14', 'Returned'),
    (2, 2, 2, '2023-06-05', '2023-06-19', '2023-06-18', 'Returned'),
    (3, 3, 4, '2023-06-10', '2023-06-24', NULL, 'Borrowed'),
    (4, 4, 4, '2023-06-15', '2023-06-29', '2023-07-05', 'Returned'),
    (5, 5, 2, '2023-06-20', '2023-07-04', NULL, 'Borrowed'),
    (7, 1, 4, '2023-06-25', '2023-07-09', NULL, 'Overdue'),
    (1, 3, 2, '2023-07-01', '2023-07-15', NULL, 'Borrowed');

-- Insert sample data for Fines
INSERT INTO fines (loan_id, amount, issue_date, payment_date, status)
VALUES 
    (4, 3.50, '2023-07-05', '2023-07-10', 'Paid'),
    (6, 7.00, '2023-07-10', NULL, 'Pending');

-- Insert sample data for Reservations
INSERT INTO reservations (book_id, member_id, reservation_date, expiry_date, status)
VALUES 
    (7, 2, '2023-07-05', '2023-07-19', 'Active'),
    (3, 1, '2023-07-10', '2023-07-24', 'Active'),
    (6, 4, '2023-07-15', '2023-07-29', 'Cancelled');