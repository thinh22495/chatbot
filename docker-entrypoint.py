import subprocess
import time
import psycopg2
from psycopg2 import OperationalError
import os

def wait_for_db():
    """Wait for database to be ready"""
    retries = 5
    while retries > 0:
        try:
            conn = psycopg2.connect(
                dbname=os.getenv("POSTGRES_DB"),
                user=os.getenv("POSTGRES_USER"),
                password=os.getenv("POSTGRES_PASSWORD"),
                host=os.getenv("POSTGRES_SERVER"),
                port=os.getenv("POSTGRES_PORT", "5432")
            )
            conn.close()
            return True
        except OperationalError:
            retries -= 1
            time.sleep(2)
    return False

def run_migrations():
    """Run database migrations"""
    result = subprocess.run(["alembic", "upgrade", "head"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Migration failed: {result.stderr}")
        return False
    return True

if __name__ == "__main__":
    print("Waiting for database...")
    if not wait_for_db():
        print("Database connection failed")
        exit(1)

    print("Running migrations...")
    if not run_migrations():
        print("Migration failed")
        exit(1)

    print("Starting application...")
    subprocess.run(["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"])