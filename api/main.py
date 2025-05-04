from fastapi import FastAPI, HTTPException, Depends, status
from typing import List, Optional
import mysql.connector
from mysql.connector import Error
from pydantic import BaseModel, EmailStr, Field
from datetime import date, timedelta
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="Library Management API",
    description="A simple CRUD API for managing a library system",
    version="1.0.0"
)

# Database connection configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "library_api")
}

# Function to get database connection
def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")

# Pydantic models for data validation
class MemberBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    membership_status: str = "Active"

class MemberCreate(MemberBase):
    pass

class Member(MemberBase):
    member_id: int

    class Config:
        orm_mode = True

class BookBase(BaseModel):
    isbn: str
    title: str
    author: str
    genre: Optional[str] = None
    available_copies: int = 0
    total_copies: int = 0

class BookCreate(BookBase):
    pass

class Book(BookBase):
    book_id: int

    class Config:
        orm_mode = True

class LoanBase(BaseModel):
    book_id: int
    member_id: int
    due_date: Optional[date] = None
    status: str = "Borrowed"

class LoanCreate(LoanBase):
    pass

class Loan(LoanBase):
    loan_id: int
    loan_date: date
    return_date: Optional[date] = None

    class Config:
        orm_mode = True

# Member Routes
@app.post("/members/", response_model=Member, status_code=status.HTTP_201_CREATED)
def create_member(member: MemberCreate):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        query = """
        INSERT INTO members (first_name, last_name, email, phone_number, membership_status)
        VALUES (%s, %s, %s, %s, %s)
        """
        values = (
            member.first_name,
            member.last_name,
            member.email,
            member.phone_number,
            member.membership_status
        )
        
        cursor.execute(query, values)
        conn.commit()
        
        # Get the ID of the newly inserted member
        member_id = cursor.lastrowid
        
        # Create the response
        created_member = {
            "member_id": member_id,
            **member.dict()
        }
        
        return created_member
    except Error as e:
        conn.rollback()
        if "Duplicate entry" in str(e) and "email" in str(e):
            raise HTTPException(status_code=400, detail="Email already registered")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/members/", response_model=List[Member])
def get_all_members():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        query = "SELECT * FROM members"
        cursor.execute(query)
        members = cursor.fetchall()
        return members
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/members/{member_id}", response_model=Member)
def get_member(member_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        query = "SELECT * FROM members WHERE member_id = %s"
        cursor.execute(query, (member_id,))
        member = cursor.fetchone()
        
        if member is None:
            raise HTTPException(status_code=404, detail="Member not found")
        
        return member
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.put("/members/{member_id}", response_model=Member)
def update_member(member_id: int, member: MemberBase):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check if member exists
        cursor.execute("SELECT * FROM members WHERE member_id = %s", (member_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Member not found")
        
        query = """
        UPDATE members
        SET first_name = %s, last_name = %s, email = %s, phone_number = %s, membership_status = %s
        WHERE member_id = %s
        """
        values = (
            member.first_name,
            member.last_name,
            member.email,
            member.phone_number,
            member.membership_status,
            member_id
        )
        
        cursor.execute(query, values)
        conn.commit()
        
        # Return updated member
        cursor.execute("SELECT * FROM members WHERE member_id = %s", (member_id,))
        updated_member = cursor.fetchone()
        return updated_member
    except Error as e:
        conn.rollback()
        if "Duplicate entry" in str(e) and "email" in str(e):
            raise HTTPException(status_code=400, detail="Email already registered")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.delete("/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_member(member_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if member has active loans
        cursor.execute("SELECT * FROM loans WHERE member_id = %s AND status != 'Returned'", (member_id,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Cannot delete member with active loans")
        
        # Check if member exists
        cursor.execute("SELECT * FROM members WHERE member_id = %s", (member_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Member not found")
        
        # Delete member
        cursor.execute("DELETE FROM members WHERE member_id = %s", (member_id,))
        conn.commit()
        
        return None
    except Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

# Book Routes
@app.post("/books/", response_model=Book, status_code=status.HTTP_201_CREATED)
def create_book(book: BookCreate):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        query = """
        INSERT INTO books (isbn, title, author, genre, available_copies, total_copies)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (
            book.isbn,
            book.title,
            book.author,
            book.genre,
            book.available_copies,
            book.total_copies
        )
        
        cursor.execute(query, values)
        conn.commit()
        
        # Get the ID of the newly inserted book
        book_id = cursor.lastrowid
        
        # Create the response
        created_book = {
            "book_id": book_id,
            **book.dict()
        }
        
        return created_book
    except Error as e:
        conn.rollback()
        if "Duplicate entry" in str(e) and "isbn" in str(e):
            raise HTTPException(status_code=400, detail="ISBN already exists")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/books/", response_model=List[Book])
def get_all_books():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        query = "SELECT * FROM books"
        cursor.execute(query)
        books = cursor.fetchall()
        return books
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/books/{book_id}", response_model=Book)
def get_book(book_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        query = "SELECT * FROM books WHERE book_id = %s"
        cursor.execute(query, (book_id,))
        book = cursor.fetchone()
        
        if book is None:
            raise HTTPException(status_code=404, detail="Book not found")
        
        return book
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.put("/books/{book_id}", response_model=Book)
def update_book(book_id: int, book: BookBase):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check if book exists
        cursor.execute("SELECT * FROM books WHERE book_id = %s", (book_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Book not found")
        
        query = """
        UPDATE books
        SET isbn = %s, title = %s, author = %s, genre = %s, available_copies = %s, total_copies = %s
        WHERE book_id = %s
        """
        values = (
            book.isbn,
            book.title,
            book.author,
            book.genre,
            book.available_copies,
            book.total_copies,
            book_id
        )
        
        cursor.execute(query, values)
        conn.commit()
        
        # Return updated book
        cursor.execute("SELECT * FROM books WHERE book_id = %s", (book_id,))
        updated_book = cursor.fetchone()
        return updated_book
    except Error as e:
        conn.rollback()
        if "Duplicate entry" in str(e) and "isbn" in str(e):
            raise HTTPException(status_code=400, detail="ISBN already exists")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if book has active loans
        cursor.execute("SELECT * FROM loans WHERE book_id = %s AND status != 'Returned'", (book_id,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Cannot delete book with active loans")
        
        # Check if book exists
        cursor.execute("SELECT * FROM books WHERE book_id = %s", (book_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Book not found")
        
        # Delete book
        cursor.execute("DELETE FROM books WHERE book_id = %s", (book_id,))
        conn.commit()
        
        return None
    except Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

# Loan Routes
@app.post
from fastapi import FastAPI, HTTPException, Depends, status
from typing import List, Optional
import mysql.connector
from mysql.connector import Error
from pydantic import BaseModel, EmailStr, Field
from datetime import date, timedelta
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI(
    title="Library Management API",
    description="A simple CRUD API for managing a library system",
    version="1.0.0"
)

# Database connection configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "library_api")
}

# Function to get database connection
def get_db_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")

# Pydantic models for data validation
class MemberBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: Optional[str] = None
    membership_status: str = "Active"

class MemberCreate(MemberBase):
    pass

class Member(MemberBase):
    member_id: int

    class Config:
        orm_mode = True

class BookBase(BaseModel):
    isbn: str
    title: str
    author: str
    genre: Optional[str] = None
    available_copies: int = 0
    total_copies: int = 0

class BookCreate(BookBase):
    pass

class Book(BookBase):
    book_id: int

    class Config:
        orm_mode = True

class LoanBase(BaseModel):
    book_id: int
    member_id: int
    due_date: Optional[date] = None
    status: str = "Borrowed"

class LoanCreate(LoanBase):
    pass

class Loan(LoanBase):
    loan_id: int
    loan_date: date
    return_date: Optional[date] = None

    class Config:
        orm_mode = True

# Member Routes
@app.post("/loans/", response_model=Loan, status_code=status.HTTP_201_CREATED)
def create_loan(loan: LoanCreate):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check if book exists and is available
        cursor.execute("SELECT * FROM books WHERE book_id = %s", (loan.book_id,))
        book = cursor.fetchone()
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        if book["available_copies"] <= 0:
            raise HTTPException(status_code=400, detail="Book not available for loan")
        
        # Check if member exists
        cursor.execute("SELECT * FROM members WHERE member_id = %s", (loan.member_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Member not found")
        
        # Set default due date if not provided (14 days from today)
        if loan.due_date is None:
            due_date = date.today() + timedelta(days=14)
        else:
            due_date = loan.due_date
        
        # Create loan
        query = """
        INSERT INTO loans (book_id, member_id, loan_date, due_date, status)
        VALUES (%s, %s, CURDATE(), %s, %s)
        """
        values = (
            loan.book_id,
            loan.member_id,
            due_date,
            loan.status
        )
        
        cursor.execute(query, values)
        
        # Update book availability
        cursor.execute("""
        UPDATE books 
        SET available_copies = available_copies - 1 
        WHERE book_id = %s
        """, (loan.book_id,))
        
        conn.commit()
        
        # Get the created loan
        loan_id = cursor.lastrowid
        cursor.execute("SELECT * FROM loans WHERE loan_id = %s", (loan_id,))
        created_loan = cursor.fetchone()
        
        return created_loan
    except Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/loans/", response_model=List[Loan])
def get_all_loans():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        query = "SELECT * FROM loans"
        cursor.execute(query)
        loans = cursor.fetchall()
        return loans
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/loans/{loan_id}", response_model=Loan)
def get_loan(loan_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        query = "SELECT * FROM loans WHERE loan_id = %s"
        cursor.execute(query, (loan_id,))
        loan = cursor.fetchone()
        
        if loan is None:
            raise HTTPException(status_code=404, detail="Loan not found")
        
        return loan
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.put("/loans/{loan_id}/return", response_model=Loan)
def return_book(loan_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check if loan exists
        cursor.execute("SELECT * FROM loans WHERE loan_id = %s", (loan_id,))
        loan = cursor.fetchone()
        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")
        
        # Check if book is already returned
        if loan["status"] == "Returned":
            raise HTTPException(status_code=400, detail="Book already returned")
        
        # Update loan status
        cursor.execute("""
        UPDATE loans
        SET status = 'Returned', return_date = CURDATE()
        WHERE loan_id = %s
        """, (loan_id,))
        
        # Update book availability
        cursor.execute("""
        UPDATE books 
        SET available_copies = available_copies + 1 
        WHERE book_id = %s
        """, (loan["book_id"],))
        
        conn.commit()
        
        # Get updated loan
        cursor.execute("SELECT * FROM loans WHERE loan_id = %s", (loan_id,))
        updated_loan = cursor.fetchone()
        
        return updated_loan
    except Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.delete("/loans/{loan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_loan(loan_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check if loan exists
        cursor.execute("SELECT * FROM loans WHERE loan_id = %s", (loan_id,))
        loan = cursor.fetchone()
        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")
        
        # If the loan status is "Borrowed", update book availability before deletion
        if loan["status"] == "Borrowed":
            cursor.execute("""
            UPDATE books 
            SET available_copies = available_copies + 1 
            WHERE book_id = %s
            """, (loan["book_id"],))
        
        # Delete the loan
        cursor.execute("DELETE FROM loans WHERE loan_id = %s", (loan_id,))
        conn.commit()
        
        return None
    except Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

# Search Routes
@app.get("/search/books", response_model=List[Book])
def search_books(
    title: Optional[str] = None,
    author: Optional[str] = None,
    genre: Optional[str] = None,
    available_only: bool = False
):
    if not any([title, author, genre]):
        raise HTTPException(status_code=400, detail="At least one search parameter is required")
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        query = "SELECT * FROM books WHERE 1=1"
        params = []
        
        if title:
            query += " AND title LIKE %s"
            params.append(f"%{title}%")
        
        if author:
            query += " AND author LIKE %s"
            params.append(f"%{author}%")
        
        if genre:
            query += " AND genre LIKE %s"
            params.append(f"%{genre}%")
        
        if available_only:
            query += " AND available_copies > 0"
        
        cursor.execute(query, params)
        books = cursor.fetchall()
        return books
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/members/{member_id}/loans", response_model=List[Loan])
def get_member_loans(member_id: int, active_only: bool = False):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check if member exists
        cursor.execute("SELECT * FROM members WHERE member_id = %s", (member_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Member not found")
        
        query = "SELECT * FROM loans WHERE member_id = %s"
        params = [member_id]
        
        if active_only:
            query += " AND status != 'Returned'"
        
        cursor.execute(query, params)
        loans = cursor.fetchall()
        return loans
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/books/{book_id}/loans", response_model=List[Loan])
def get_book_loans(book_id: int, active_only: bool = False):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check if book exists
        cursor.execute("SELECT * FROM books WHERE book_id = %s", (book_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Book not found")
        
        query = "SELECT * FROM loans WHERE book_id = %s"
        params = [book_id]
        
        if active_only:
            query += " AND status != 'Returned'"
        
        cursor.execute(query, params)
        loans = cursor.fetchall()
        return loans
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)("/members/", response_model=Member, status_code=status.HTTP_201_CREATED)
def create_member(member: MemberCreate):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        query = """
        INSERT INTO members (first_name, last_name, email, phone_number, membership_status)
        VALUES (%s, %s, %s, %s, %s)
        """
        values = (
            member.first_name,
            member.last_name,
            member.email,
            member.phone_number,
            member.membership_status
        )
        
        cursor.execute(query, values)
        conn.commit()
        
        # Get the ID of the newly inserted member
        member_id = cursor.lastrowid
        
        # Create the response
        created_member = {
            "member_id": member_id,
            **member.dict()
        }
        
        return created_member
    except Error as e:
        conn.rollback()
        if "Duplicate entry" in str(e) and "email" in str(e):
            raise HTTPException(status_code=400, detail="Email already registered")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/members/", response_model=List[Member])
def get_all_members():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        query = "SELECT * FROM members"
        cursor.execute(query)
        members = cursor.fetchall()
        return members
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/members/{member_id}", response_model=Member)
def get_member(member_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        query = "SELECT * FROM members WHERE member_id = %s"
        cursor.execute(query, (member_id,))
        member = cursor.fetchone()
        
        if member is None:
            raise HTTPException(status_code=404, detail="Member not found")
        
        return member
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.put("/members/{member_id}", response_model=Member)
def update_member(member_id: int, member: MemberBase):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check if member exists
        cursor.execute("SELECT * FROM members WHERE member_id = %s", (member_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Member not found")
        
        query = """
        UPDATE members
        SET first_name = %s, last_name = %s, email = %s, phone_number = %s, membership_status = %s
        WHERE member_id = %s
        """
        values = (
            member.first_name,
            member.last_name,
            member.email,
            member.phone_number,
            member.membership_status,
            member_id
        )
        
        cursor.execute(query, values)
        conn.commit()
        
        # Return updated member
        cursor.execute("SELECT * FROM members WHERE member_id = %s", (member_id,))
        updated_member = cursor.fetchone()
        return updated_member
    except Error as e:
        conn.rollback()
        if "Duplicate entry" in str(e) and "email" in str(e):
            raise HTTPException(status_code=400, detail="Email already registered")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.delete("/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_member(member_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if member has active loans
        cursor.execute("SELECT * FROM loans WHERE member_id = %s AND status != 'Returned'", (member_id,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Cannot delete member with active loans")
        
        # Check if member exists
        cursor.execute("SELECT * FROM members WHERE member_id = %s", (member_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Member not found")
        
        # Delete member
        cursor.execute("DELETE FROM members WHERE member_id = %s", (member_id,))
        conn.commit()
        
        return None
    except Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

# Book Routes
@app.post("/books/", response_model=Book, status_code=status.HTTP_201_CREATED)
def create_book(book: BookCreate):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        query = """
        INSERT INTO books (isbn, title, author, genre, available_copies, total_copies)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (
            book.isbn,
            book.title,
            book.author,
            book.genre,
            book.available_copies,
            book.total_copies
        )
        
        cursor.execute(query, values)
        conn.commit()
        
        # Get the ID of the newly inserted book
        book_id = cursor.lastrowid
        
        # Create the response
        created_book = {
            "book_id": book_id,
            **book.dict()
        }
        
        return created_book
    except Error as e:
        conn.rollback()
        if "Duplicate entry" in str(e) and "isbn" in str(e):
            raise HTTPException(status_code=400, detail="ISBN already exists")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/books/", response_model=List[Book])
def get_all_books():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        query = "SELECT * FROM books"
        cursor.execute(query)
        books = cursor.fetchall()
        return books
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.get("/books/{book_id}", response_model=Book)
def get_book(book_id: int):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        query = "SELECT * FROM books WHERE book_id = %s"
        cursor.execute(query, (book_id,))
        book = cursor.fetchone()
        
        if book is None:
            raise HTTPException(status_code=404, detail="Book not found")
        
        return book
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.put("/books/{book_id}", response_model=Book)
def update_book(book_id: int, book: BookBase):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check if book exists
        cursor.execute("SELECT * FROM books WHERE book_id = %s", (book_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Book not found")
        
        query = """
        UPDATE books
        SET isbn = %s, title = %s, author = %s, genre = %s, available_copies = %s, total_copies = %s
        WHERE book_id = %s
        """
        values = (
            book.isbn,
            book.title,
            book.author,
            book.genre,
            book.available_copies,
            book.total_copies,
            book_id
        )
        
        cursor.execute(query, values)
        conn.commit()
        
        # Return updated book
        cursor.execute("SELECT * FROM books WHERE book_id = %s", (book_id,))
        updated_book = cursor.fetchone()
        return updated_book
    except Error as e:
        conn.rollback()
        if "Duplicate entry" in str(e) and "isbn" in str(e):
            raise HTTPException(status_code=400, detail="ISBN already exists")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

@app.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Check if book has active loans
        cursor.execute("SELECT * FROM loans WHERE book_id = %s AND status != 'Returned'", (book_id,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Cannot delete book with active loans")
        
        # Check if book exists
        cursor.execute("SELECT * FROM books WHERE book_id = %s", (book_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Book not found")
        
        # Delete book
        cursor.execute("DELETE FROM books WHERE book_id = %s", (book_id,))
        conn.commit()
        
        return None
    except Error as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        cursor.close()
        conn.close()

# Loan Routes
@app.post