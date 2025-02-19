import requests
from models import Book
from config.config import db

API_URL = "https://frappe.io/api/method/frappe-library"

def fetch_books(title, authors, isbn, publisher, num_pages, required_books):
    fetched_books = []
    page = 1

    while len(fetched_books) < required_books:
        params = {
            "title": title,
            "authors": authors,
            "isbn": isbn,
            "publisher": publisher,
            "num_pages": num_pages
        }
        response = requests.get(API_URL, params=params)
        data = response.json().get("message", [])

        if not data:  # Stop if no more books are available
            break  

        fetched_books.extend(data)
        page += 1  

    return fetched_books[:required_books]  # Return exactly required_books

def save_books_to_db(books):
    """Save fetched books into the database, updating stock if the book already exists."""
    added_books = 0
    
    for book in books:
        title = book["title"]
        authors = book.get("authors", "Unknown")
        isbn = book.get("isbn", None)
        publisher = book.get("publisher", "N/A")
        num_pages = int(book.get("num_pages", 0))
        publication_date = int(book.get("publication_date", "2000").split("/")[-1])  # Extracting year
        language = book.get("language_code", "English")
        
        # Check if the book already exists based on ISBN
        existing_book = Book.get_or_none(Book.isbn == isbn)

        if existing_book:
            # Update stock count
            existing_book.stock += 1
            existing_book.save()
        else:
            # Create new book entry
            Book.create(
                title=title,
                author=authors,
                isbn=isbn,
                publisher=publisher,
                num_pages=num_pages,
                publication_date=publication_date,
                language=language,
                stock=1,  # Initial stock count
                mrp=0.0,  # Default value (you can update this)
                times_issued=0
            )
            added_books += 1
    
    return {"success": f"{added_books} new books added, existing books updated!"}

# External API Configuration
BASE_URL = "https://frappe.school"
ARN_API_ENDPOINT = "/api/method/generate-pro-einvoice-id"

def generate_arn(transaction):
    """Sends invoice details to the API to get an ARN number."""
    try:
        payload = {
            "customer_name": transaction.member.first_name,
            "invoice_id": transaction.id,
            "payable_amount": transaction.rent_fee
        }

        response = requests.post(f"{BASE_URL}{ARN_API_ENDPOINT}", json=payload)

        if response.status_code == 200:
            data = response.json()
            return data.get("arn", None)
        else:
            print(f"Failed to fetch ARN. Status Code: {response.status_code}, Response: {response.text}")
            return None
    except Exception as e:
        print(f"Error fetching ARN: {str(e)}")
        return None