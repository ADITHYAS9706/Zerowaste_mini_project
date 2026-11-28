
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv(".env", override=True)

connection_url = URL.create(
    drivername="postgresql+psycopg",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME", "postgres"),
    query={"sslmode": "require"},
)

engine = create_engine(connection_url)

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print("Database test result:", result.scalar())
        print("DATABASE CONNECTION SUCCESSFUL")

except Exception as error:
    print("DATABASE CONNECTION FAILED")
    print(type(error).__name__)
    print(str(error))

finally:
    engine.dispose()
