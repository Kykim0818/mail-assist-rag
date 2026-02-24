import aiosqlite
from pathlib import Path
from backend.config import settings


async def get_db_path() -> Path:
    """Get database path and ensure parent directory exists."""
    db_path = Path(settings.DB_PATH)
    if not db_path.is_absolute():
        db_path = Path(__file__).resolve().parent.parent / db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


async def init_db() -> None:
    """Initialize database with tables and seed initial categories."""
    db_path = await get_db_path()
    
    async with aiosqlite.connect(str(db_path)) as db:
        db.row_factory = aiosqlite.Row
        
        # Create emails table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT,
                subject TEXT,
                body TEXT NOT NULL,
                summary TEXT,
                category TEXT DEFAULT '미분류',
                date_extracted TEXT,
                status TEXT DEFAULT 'completed',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create categories table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create index on category
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_emails_category ON emails(category)
        """)
        
        # Seed initial categories
        categories = ['미분류', 'HR/인사', '프로젝트', '일정', '공지사항']
        for category in categories:
            await db.execute(
                "INSERT OR IGNORE INTO categories (name) VALUES (?)",
                (category,)
            )
        
        await db.commit()


async def insert_email(email_data: dict) -> int:
    """Insert a new email and return the new row id."""
    db_path = await get_db_path()
    
    async with aiosqlite.connect(str(db_path)) as db:
        db.row_factory = aiosqlite.Row
        
        cursor = await db.execute(
            """
            INSERT INTO emails (sender, subject, body, summary, category, date_extracted, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                email_data.get('sender'),
                email_data.get('subject'),
                email_data.get('body'),
                email_data.get('summary'),
                email_data.get('category', '미분류'),
                email_data.get('date_extracted'),
                email_data.get('status', 'completed')
            )
        )
        await db.commit()
        return cursor.lastrowid


async def get_emails(category: str | None = None, limit: int = 50, offset: int = 0) -> list[dict]:
    """Get emails with optional category filter, ordered by created_at DESC."""
    db_path = await get_db_path()
    
    async with aiosqlite.connect(str(db_path)) as db:
        db.row_factory = aiosqlite.Row
        
        if category:
            cursor = await db.execute(
                """
                SELECT * FROM emails
                WHERE category = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (category, limit, offset)
            )
        else:
            cursor = await db.execute(
                """
                SELECT * FROM emails
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset)
            )
        
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_email_by_id(email_id: int) -> dict | None:
    """Get an email by id."""
    db_path = await get_db_path()
    
    async with aiosqlite.connect(str(db_path)) as db:
        db.row_factory = aiosqlite.Row
        
        cursor = await db.execute(
            "SELECT * FROM emails WHERE id = ?",
            (email_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_email_category(email_id: int, category: str) -> None:
    """Update the category of an email."""
    db_path = await get_db_path()
    
    async with aiosqlite.connect(str(db_path)) as db:
        await db.execute(
            "UPDATE emails SET category = ? WHERE id = ?",
            (category, email_id)
        )
        await db.commit()


async def get_categories() -> list[dict]:
    """Get all categories."""
    db_path = await get_db_path()
    
    async with aiosqlite.connect(str(db_path)) as db:
        db.row_factory = aiosqlite.Row
        
        cursor = await db.execute(
            "SELECT id, name, description FROM categories ORDER BY name"
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def add_category(name: str, description: str | None = None) -> int:
    """Add a new category and return the new row id."""
    db_path = await get_db_path()
    
    async with aiosqlite.connect(str(db_path)) as db:
        cursor = await db.execute(
            "INSERT INTO categories (name, description) VALUES (?, ?)",
            (name, description)
        )
        await db.commit()
        return cursor.lastrowid


async def update_category(category_id: int, name: str) -> None:
    """Update a category name."""
    db_path = await get_db_path()
    
    async with aiosqlite.connect(str(db_path)) as db:
        await db.execute(
            "UPDATE categories SET name = ? WHERE id = ?",
            (name, category_id)
        )
        await db.commit()


async def delete_category(category_id: int) -> None:
    """Delete a category and reassign its emails to '미분류'."""
    db_path = await get_db_path()
    
    async with aiosqlite.connect(str(db_path)) as db:
        # First, get the category name
        cursor = await db.execute(
            "SELECT name FROM categories WHERE id = ?",
            (category_id,)
        )
        row = await cursor.fetchone()
        
        if row:
            category_name = row[0]
            # Update emails with this category to '미분류'
            await db.execute(
                "UPDATE emails SET category = '미분류' WHERE category = ?",
                (category_name,)
            )
            # Delete the category
            await db.execute(
                "DELETE FROM categories WHERE id = ?",
                (category_id,)
            )
            await db.commit()
