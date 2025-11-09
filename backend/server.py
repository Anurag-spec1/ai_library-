from fastapi import FastAPI, APIRouter, HTTPException, Depends
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
SECRET_KEY = os.environ.get('JWT_SECRET', 'library-secret-key-change-in-production')
ALGORITHM = "HS256"
security = HTTPBearer()

# Create the main app
app = FastAPI()
api_router = APIRouter(prefix="/api")

# Models
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    name: str
    email: EmailStr
    role: str = "student"  # student or librarian
    borrowed_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserRegister(BaseModel):
    student_id: str
    name: str
    email: EmailStr
    password: str
    role: str = "student"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Book(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    author: str
    category: str
    isbn: str
    description: Optional[str] = None
    total_copies: int
    available_copies: int
    image_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BookCreate(BaseModel):
    title: str
    author: str
    category: str
    isbn: str
    description: Optional[str] = None
    total_copies: int
    image_url: Optional[str] = None

class Transaction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_name: str
    book_id: str
    book_title: str
    borrow_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    due_date: datetime
    return_date: Optional[datetime] = None
    fine: float = 0.0
    status: str = "borrowed"  # borrowed, returned, overdue

class BorrowRequest(BaseModel):
    book_id: str

class ReturnRequest(BaseModel):
    transaction_id: str

# Helper functions
def create_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

def calculate_fine(due_date: datetime, return_date: datetime) -> float:
    if return_date <= due_date:
        return 0.0
    overdue_days = (return_date - due_date).days
    return overdue_days * 2.0  # $2 per day

# Auth Routes
@api_router.post("/auth/register")
async def register(user_data: UserRegister):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = bcrypt.hashpw(user_data.password.encode('utf-8'), bcrypt.gensalt())
    
    # Create user
    user = User(
        student_id=user_data.student_id,
        name=user_data.name,
        email=user_data.email,
        role=user_data.role
    )
    
    doc = user.model_dump()
    doc['password'] = hashed_password.decode('utf-8')
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.users.insert_one(doc)
    
    token = create_token(user.id, user.email, user.role)
    return {"token": token, "user": user}

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not bcrypt.checkpw(credentials.password.encode('utf-8'), user['password'].encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user['id'], user['email'], user['role'])
    
    user_obj = {
        "id": user['id'],
        "student_id": user['student_id'],
        "name": user['name'],
        "email": user['email'],
        "role": user['role'],
        "borrowed_count": user.get('borrowed_count', 0)
    }
    
    return {"token": token, "user": user_obj}

# Book Routes
@api_router.get("/books", response_model=List[Book])
async def get_books(category: Optional[str] = None, search: Optional[str] = None):
    query = {}
    if category and category != "all":
        query["category"] = category
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"author": {"$regex": search, "$options": "i"}},
            {"isbn": {"$regex": search, "$options": "i"}}
        ]
    
    books = await db.books.find(query, {"_id": 0}).to_list(1000)
    for book in books:
        if isinstance(book['created_at'], str):
            book['created_at'] = datetime.fromisoformat(book['created_at'])
    return books

@api_router.get("/books/{book_id}", response_model=Book)
async def get_book(book_id: str):
    book = await db.books.find_one({"id": book_id}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if isinstance(book['created_at'], str):
        book['created_at'] = datetime.fromisoformat(book['created_at'])
    return book

@api_router.post("/books", response_model=Book)
async def create_book(book_data: BookCreate, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'librarian':
        raise HTTPException(status_code=403, detail="Only librarians can add books")
    
    book = Book(
        title=book_data.title,
        author=book_data.author,
        category=book_data.category,
        isbn=book_data.isbn,
        description=book_data.description,
        total_copies=book_data.total_copies,
        available_copies=book_data.total_copies,
        image_url=book_data.image_url
    )
    
    doc = book.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.books.insert_one(doc)
    return book

@api_router.delete("/books/{book_id}")
async def delete_book(book_id: str, current_user: dict = Depends(get_current_user)):
    if current_user['role'] != 'librarian':
        raise HTTPException(status_code=403, detail="Only librarians can delete books")
    
    result = await db.books.delete_one({"id": book_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"message": "Book deleted successfully"}

# Borrowing Routes
@api_router.post("/borrow")
async def borrow_book(request: BorrowRequest, current_user: dict = Depends(get_current_user)):
    # Get user
    user = await db.users.find_one({"id": current_user['user_id']})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check borrowing limit
    if user.get('borrowed_count', 0) >= 3:
        raise HTTPException(status_code=400, detail="Borrowing limit reached (max 3 books)")
    
    # Get book
    book = await db.books.find_one({"id": request.book_id})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    if book['available_copies'] <= 0:
        raise HTTPException(status_code=400, detail="Book not available")
    
    # Calculate due date (14 days for general, 7 for reference)
    loan_days = 7 if book['category'].lower() == 'reference' else 14
    due_date = datetime.now(timezone.utc) + timedelta(days=loan_days)
    
    # Create transaction
    transaction = Transaction(
        user_id=user['id'],
        user_name=user['name'],
        book_id=book['id'],
        book_title=book['title'],
        due_date=due_date
    )
    
    doc = transaction.model_dump()
    doc['borrow_date'] = doc['borrow_date'].isoformat()
    doc['due_date'] = doc['due_date'].isoformat()
    
    await db.transactions.insert_one(doc)
    
    # Update book availability
    await db.books.update_one(
        {"id": request.book_id},
        {"$inc": {"available_copies": -1}}
    )
    
    # Update user borrowed count
    await db.users.update_one(
        {"id": current_user['user_id']},
        {"$inc": {"borrowed_count": 1}}
    )
    
    return transaction

@api_router.post("/return")
async def return_book(request: ReturnRequest, current_user: dict = Depends(get_current_user)):
    # Get transaction
    transaction = await db.transactions.find_one({"id": request.transaction_id})
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if transaction['status'] != 'borrowed':
        raise HTTPException(status_code=400, detail="Book already returned")
    
    if transaction['user_id'] != current_user['user_id'] and current_user['role'] != 'librarian':
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Calculate fine
    return_date = datetime.now(timezone.utc)
    due_date = datetime.fromisoformat(transaction['due_date'])
    fine = calculate_fine(due_date, return_date)
    
    # Update transaction
    status = 'overdue' if fine > 0 else 'returned'
    await db.transactions.update_one(
        {"id": request.transaction_id},
        {
            "$set": {
                "return_date": return_date.isoformat(),
                "fine": fine,
                "status": status
            }
        }
    )
    
    # Update book availability
    await db.books.update_one(
        {"id": transaction['book_id']},
        {"$inc": {"available_copies": 1}}
    )
    
    # Update user borrowed count
    await db.users.update_one(
        {"id": transaction['user_id']},
        {"$inc": {"borrowed_count": -1}}
    )
    
    return {"message": "Book returned successfully", "fine": fine}

# Transaction Routes
@api_router.get("/transactions", response_model=List[Transaction])
async def get_transactions(current_user: dict = Depends(get_current_user)):
    query = {}
    if current_user['role'] != 'librarian':
        query['user_id'] = current_user['user_id']
    
    transactions = await db.transactions.find(query, {"_id": 0}).to_list(1000)
    for txn in transactions:
        if isinstance(txn['borrow_date'], str):
            txn['borrow_date'] = datetime.fromisoformat(txn['borrow_date'])
        if isinstance(txn['due_date'], str):
            txn['due_date'] = datetime.fromisoformat(txn['due_date'])
        if txn.get('return_date') and isinstance(txn['return_date'], str):
            txn['return_date'] = datetime.fromisoformat(txn['return_date'])
    return transactions

@api_router.get("/transactions/borrowed")
async def get_borrowed_books(current_user: dict = Depends(get_current_user)):
    transactions = await db.transactions.find(
        {"user_id": current_user['user_id'], "status": "borrowed"},
        {"_id": 0}
    ).to_list(1000)
    
    for txn in transactions:
        if isinstance(txn['borrow_date'], str):
            txn['borrow_date'] = datetime.fromisoformat(txn['borrow_date'])
        if isinstance(txn['due_date'], str):
            txn['due_date'] = datetime.fromisoformat(txn['due_date'])
    
    return transactions

# User Routes
@api_router.get("/users/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    user = await db.users.find_one({"id": current_user['user_id']}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@api_router.get("/stats")
async def get_stats():
    total_books = await db.books.count_documents({})
    total_users = await db.users.count_documents({"role": "student"})
    active_borrows = await db.transactions.count_documents({"status": "borrowed"})
    
    return {
        "total_books": total_books,
        "total_users": total_users,
        "active_borrows": active_borrows
    }

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()