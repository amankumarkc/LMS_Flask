from config.config import db

try:
    db.connect()
    print("Database connected successfully!")
    db.close()
except Exception as e:
    print(f"Database connection failed: {e}")
