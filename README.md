# library-management-system
A MySQL database and FastAPI CRUD application for library management
# Library Management System

A complete database management system with a CRUD API built using MySQL and FastAPI.

## Project Description

This project implements a comprehensive Library Management System that allows librarians to manage books, members, and loans. The system consists of two main components:

1. **MySQL Database**: A relational database schema with properly defined constraints and relationships.
2. **FastAPI CRUD API**: A RESTful API that interfaces with the database, allowing for complete management of the library system.

## Entity Relationship Diagram (ERD)

![Library Management System ERD](https://drive.google.com/uc?export=view&id=10yjt66c9Vg1QM1eHGFEkOkZiG8K8tvhT)

## Features

### Database (Question 1)
- Well-structured relational database with proper constraints (PK, FK, NOT NULL, UNIQUE)
- Multiple types of relationships (1-to-many, many-to-many)
- Triggers for automated updates when books are borrowed or returned
- Sample data for testing

### API (Question 2)
- Complete CRUD operations for members, books, and loans
- Data validation using Pydantic models
- Error handling and proper HTTP status codes
- Search functionality for books and loans
- Business logic for book loans and returns

## Setup Instructions

### Database Setup

1. Install MySQL Server if you haven't already
2. Run the SQL script to create and populate the database:

```bash
mysql -u root -p < library_management_system.sql
```

For the API's simplified database:

```bash
mysql -u root -p < api_database.sql
```

### API Setup

1. Clone this repository
2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the requirements:

```bash
pip install -r requirements.txt
```

4. Copy the `.env.example` file to `.env` and update with your database credentials:

```bash
cp .env.example .env
```

5. Run the API:

```bash
python main.py
```

The API will be available at http://localhost:8000

## API Documentation

Once the API is running, you can access the automatically generated Swagger documentation at:

http://localhost:8000/docs

This documentation provides an interactive interface where you can test all the API endpoints.

## API Endpoints

### Members
- `GET /members/` - Get all members
- `POST /members/` - Create a new member
- `GET /members/{member_id}` - Get a specific member
- `PUT /members/{member_id}` - Update a member
- `DELETE /members/{member_id}` - Delete a member
- `GET /members/{member_id}/loans` - Get a member's loans

### Books
- `GET /books/` - Get all books
- `POST /books/` - Add a new book
- `GET /books/{book_id}` - Get a specific book
- `PUT /books/{book_id}` - Update a book
- `DELETE /books/{book_id}` - Delete a book
- `GET /books/{book_id}/loans` - Get a book's loan history
- `GET /search/books` - Search for books

### Loans
- `GET /loans/` - Get all loans
- `POST /loans/` - Create a new loan
- `GET /loans/{loan_id}` - Get a specific loan
- `PUT /loans/{loan_id}/return` - Return a book
- `DELETE /loans/{loan_id}` - Delete a loan

## Technologies Used

- **MySQL**: For the relational database
- **Python**: Programming language
- **FastAPI**: Web framework for building the API
- **Pydantic**: Data validation
- **MySQL Connector/Python**: Database connector

## License

MIT

## Author

William Oneka