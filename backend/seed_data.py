import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
import uuid
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

async def seed_books():
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Clear existing books
    await db.books.delete_many({})
    
    books = [
        {
            "id": str(uuid.uuid4()),
            "title": "Introduction to Algorithms",
            "author": "Thomas H. Cormen",
            "category": "Academic",
            "isbn": "978-0262033848",
            "description": "Comprehensive guide to algorithms and data structures",
            "total_copies": 5,
            "available_copies": 5,
            "image_url": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Clean Code",
            "author": "Robert C. Martin",
            "category": "Technology",
            "isbn": "978-0132350884",
            "description": "A handbook of agile software craftsmanship",
            "total_copies": 4,
            "available_copies": 4,
            "image_url": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "The Great Gatsby",
            "author": "F. Scott Fitzgerald",
            "category": "Fiction",
            "isbn": "978-0743273565",
            "description": "Classic American novel about the Jazz Age",
            "total_copies": 3,
            "available_copies": 3,
            "image_url": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Sapiens",
            "author": "Yuval Noah Harari",
            "category": "History",
            "isbn": "978-0062316110",
            "description": "A brief history of humankind",
            "total_copies": 6,
            "available_copies": 6,
            "image_url": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Artificial Intelligence: A Modern Approach",
            "author": "Stuart Russell",
            "category": "Science",
            "isbn": "978-0134610993",
            "description": "Comprehensive introduction to AI",
            "total_copies": 4,
            "available_copies": 4,
            "image_url": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Database System Concepts",
            "author": "Abraham Silberschatz",
            "category": "Reference",
            "isbn": "978-0073523323",
            "description": "Comprehensive database systems textbook",
            "total_copies": 3,
            "available_copies": 3,
            "image_url": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "To Kill a Mockingbird",
            "author": "Harper Lee",
            "category": "Fiction",
            "isbn": "978-0061120084",
            "description": "Classic novel about racial injustice",
            "total_copies": 4,
            "available_copies": 4,
            "image_url": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Thinking, Fast and Slow",
            "author": "Daniel Kahneman",
            "category": "Non-Fiction",
            "isbn": "978-0374533557",
            "description": "Exploration of the two systems that drive the way we think",
            "total_copies": 5,
            "available_copies": 5,
            "image_url": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Operating System Concepts",
            "author": "Abraham Silberschatz",
            "category": "Academic",
            "isbn": "978-1119320913",
            "description": "Fundamental concepts of operating systems",
            "total_copies": 4,
            "available_copies": 4,
            "image_url": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "Design Patterns",
            "author": "Erich Gamma",
            "category": "Technology",
            "isbn": "978-0201633610",
            "description": "Elements of reusable object-oriented software",
            "total_copies": 3,
            "available_copies": 3,
            "image_url": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "The Lean Startup",
            "author": "Eric Ries",
            "category": "Non-Fiction",
            "isbn": "978-0307887894",
            "description": "How today's entrepreneurs use continuous innovation",
            "total_copies": 4,
            "available_copies": 4,
            "image_url": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "title": "A Brief History of Time",
            "author": "Stephen Hawking",
            "category": "Science",
            "isbn": "978-0553380163",
            "description": "From the Big Bang to black holes",
            "total_copies": 5,
            "available_copies": 5,
            "image_url": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    await db.books.insert_many(books)
    print(f"✅ Successfully seeded {len(books)} books!")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_books())
