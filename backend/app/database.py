
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# Locate backend folder
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(BASE_DIR / ".env")

# Read database credentials
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "postgres")

# Validate credentials
if not all([DB_USER, DB_PASSWORD, DB_HOST]):
    raise ValueError("Missing database credentials in .env")

# Safely construct PostgreSQL URL
database_url = URL.create(
    drivername="postgresql+psycopg",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME,
    query={"sslmode": "require"}
)

# Create database engine
engine = create_engine(
    database_url,
    pool_pre_ping=True
)

# Test connection
def test_connection():
    try:
        with engine.connect() as connection:
            result = connection.execute(
                text("SELECT version()")
            )

            print("Successfully connected to Supabase!")
            print(result.scalar())

    except Exception as error:
        print("Database connection failed:")
        print(error)


if __name__ == "__main__":
    test_connection()
