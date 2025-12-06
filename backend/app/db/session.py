"""
Database session management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Build connection string for SQL Server with Windows Authentication
connection_string = (
    f"mssql+pyodbc://{settings.DB_HOST}/{settings.DB_NAME}"
    f"?driver=ODBC+Driver+17+for+SQL+Server"
    f"&Trusted_Connection=yes"
)

logger.info(f"Database connection: {settings.DB_HOST}/{settings.DB_NAME}")

# Create engine
engine = create_engine(
    connection_string,
    echo=False,  # Set to True for SQL query logging
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """
    Dependency for getting database session

    Usage in FastAPI endpoints:
        @router.get("/items")
        def get_items(db: Session = Depends(get_db)):
            items = db.query(Item).all()
            return items
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
