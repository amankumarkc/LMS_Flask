from peewee import PostgresqlDatabase
import os
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


# Load DATABASE_URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Parse DATABASE_URL
    parsed_url = urlparse(DATABASE_URL)

    DATABASE = {
        'name': parsed_url.path[1:],  # Extract database name (remove leading '/')
        'user': parsed_url.username,
        'password': parsed_url.password,
        'host': parsed_url.hostname,
        'port': parsed_url.port
    }
else:
    # Fallback to local development database
    DATABASE = {
        'name': 'lmsdb',
        'user': 'librarian',
        'password': 'root',
        'host': 'localhost',
        'port': 5432
    }

# Initialize the Peewee database
db = PostgresqlDatabase(
    DATABASE['name'], 
    user=DATABASE['user'], 
    password=DATABASE['password'], 
    host=DATABASE['host'], 
    port=DATABASE['port']
)
