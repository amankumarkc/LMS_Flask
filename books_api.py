import requests

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
