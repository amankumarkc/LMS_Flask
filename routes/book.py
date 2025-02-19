import csv
from io import StringIO
from peewee import IntegrityError
from models import Book, Transaction
from books_api import fetch_books, save_books_to_db
from flask import Blueprint, redirect, render_template, request, jsonify, Response, url_for
from typing import List, Dict, Any, Union, Optional

bp = Blueprint('book', __name__, url_prefix='/book')

# Serialize a book instance to dictionary.
def serialize_book(book: Book) -> Dict[str, Any]:

    return {
        'id': book.id,
        'title': book.title,
        'author': book.author,
        'isbn': book.isbn,
        'publisher': book.publisher,
        'stock': book.stock,
        'num_pages': book.num_pages,
        'publication_date': book.publication_date,
        'language': book.language,
        'mrp': float(book.mrp)
    }

# Get book by ID with error handling.
def get_book_by_id(book_id: int) -> Optional[Book]:
    
    return Book.get_or_none(Book.id == book_id)


# List all books.
@bp.route('/list')
def books():

    all_books = Book.select()
    return render_template("books.html", books=all_books)


# Handle book API integration.
@bp.route('/api', methods=["GET", "POST"])
def index():

    if request.method == "POST":
        form_data = {
            'title': request.form.get("title", ""),
            'authors': request.form.get("authors", ""),
            'isbn': request.form.get("isbn", ""),
            'publisher': request.form.get("publisher", ""),
            'num_pages': request.form.get("num_pages", ""),
            'required_books': int(request.form.get("required_books", 20))
        }

        books = fetch_books(**form_data)
        if books:
            save_books_to_db(books)

        return render_template("books_api.html", books=books)   

    return render_template("books_api.html", books=[])


# Generate and download books CSV.
@bp.route('/download-csv', methods=['GET'])
def download_books_csv():

    books = Book.select()
    headers = ["Book ID", "Title", "Author", "Language", "Publisher", "Stock"]
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)

    for book in books:
        writer.writerow([
            book.id,
            book.title,
            book.author,
            book.language,
            book.publisher,
            book.stock
        ])

    output.seek(0)
    response = Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=library_books.csv"}
    )
    
    return response


# Create a new book.
@bp.route('/create', methods=['GET', 'POST'])
def create_book():

    if request.method == 'POST':
        try:
            book_data = {
                'title': request.form.get('title'),
                'author': request.form.get('author'),
                'isbn': request.form.get('isbn'),
                'publisher': request.form.get('publisher'),
                'stock': int(request.form.get('stock', 5)),
                'num_pages': int(request.form.get('num_pages', '0')),
                'publication_date': int(request.form.get('publication_date')),
                'language': request.form.get('language', 'English'),
                'mrp': float(request.form.get('mrp', '0.0'))
            }

            book = Book.create(**book_data)
            return jsonify({
                "success": True,
                "message": f"Book '{book.title}' successfully created!",
                "book": serialize_book(book)
            }), 201

        except IntegrityError:
            return jsonify({
                "success": False,
                "message": "Error: A book with this ISBN already exists."
            }), 400
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"An error occurred: {str(e)}"
            }), 500

    return render_template("create-book.html")


# Edit an existing book.
@bp.route('/edit/<int:book_id>', methods=['GET', 'POST'])
def edit_books(book_id: int):

    book = get_book_by_id(book_id)
    if not book:
        return jsonify({
            "success": False,
            "message": "Book not found"
        }), 404

    if request.method == 'POST':
        try:
            book.stock = int(request.form.get("stock", book.stock))
            book.mrp = float(request.form.get("mrp", book.mrp))
            book.num_pages = int(request.form.get("num_pages", book.num_pages))
            book.save()

            return redirect(url_for('book.books'))
        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"Error updating book: {str(e)}"
            }), 500

    return render_template("edit-books.html", book=book)

# Delete a single book.
@bp.route('/delete/<int:book_id>', methods=['DELETE'])
def delete_book(book_id: int):

    book = get_book_by_id(book_id)
    if not book:
        return jsonify({
            "success": False,
            "message": "Book not found"
        }), 404

    if Transaction.select().where(Transaction.book == book).exists():
        return jsonify({
            "success": False,
            "message": "This book can't be deleted as it is linked to a transaction."
        }), 400

    try:
        book.delete_instance()
        return jsonify({
            "success": True,
            "message": f"Book '{book.title}' has been successfully deleted!"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error deleting book: {str(e)}"
        }), 500


# Delete multiple books at once.
@bp.route('/delete-bulk', methods=['POST'])
def bulk_delete_books():
    data = request.get_json()
    book_ids = data.get("book_ids", [])

    if not book_ids:
        return jsonify({
            "success": False,
            "message": "No books selected!"
        }), 400

    deleted_books = []
    failed_books = []

    try:
        for book_id in book_ids:
            book = Book.get_or_none(Book.id == book_id)  # Ensure book retrieval

            if book:
                if Transaction.select().where(Transaction.book == book).exists():
                    failed_books.append({"title": book.title, "stock": book.stock})  # JSON format
                else:
                    deleted_books.append({"title": book.title, "stock": book.stock})
                    book.delete_instance()

        return jsonify({
            "success": True,
            "deleted_books": deleted_books,
            "failed_books": failed_books
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error during bulk delete: {str(e)}"
        }), 500
