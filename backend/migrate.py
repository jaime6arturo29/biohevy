import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
database_url = os.environ.get("DATABASE_URL")
engine = create_engine(database_url)

try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN clerk_id VARCHAR UNIQUE;"))
        conn.commit()
        print("Column clerk_id added.")
except Exception as e:
    print(f"Error (maybe column exists?): {e}")
