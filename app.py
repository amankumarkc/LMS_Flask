from flask import Flask, render_template, redirect, request, make_response, jsonify
from config import db
from models import Book, Member, Transaction
from weasyprint import HTML
from books_api import fetch_books, save_books_to_db

app = Flask(__name__)

@app.route('/')
def home():
    return "home page"

# View Books Page
@app.route('/books')
def books():
    all_books = Book.select()  # Fetch all books from DB
    return render_template("books.html", books=all_books)

# Edit Book Page
@app.route('/edit-books/<int:book_id>', methods=['GET', 'POST'])
def edit_books(book_id):
    book = Book.get_or_none(Book.id == book_id)
    if not book:
        return "Book not found", 404

    if request.method == 'POST':
        # Update the book details
        book.stock = int(request.form.get("stock", book.stock))
        book.mrp = float(request.form.get("mrp", book.mrp))
        book.num_pages = int(request.form.get("num_pages", book.num_pages))
        book.save()

        return redirect("/books")  # Redirect back to books page

    return render_template("edit-books.html", book=book)

# Delete single Book API
@app.route('/delete-book/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    book = Book.get_or_none(Book.id == book_id)
    if not book:
        return jsonify({"message": "Book not found"}), 404

    book.delete_instance()
    return jsonify({"message": f"Book '{book.title}' has been successfully deleted!"})

# Delete bulk Book API
@app.route('/delete-books', methods=['POST'])
def bulk_delete_books():
    data = request.get_json()
    book_ids = data.get("book_ids", [])

    if not book_ids:
        return jsonify({"message": "No books selected!"}), 400

    deleted_books = []
    for book_id in book_ids:
        book = Book.get_or_none(Book.id == book_id)
        if book:
            deleted_books.append(f"'{book.title}' ({book.stock} stock)")
            book.delete_instance()

    if not deleted_books:
        return jsonify({"message": "No valid books found to delete!"}), 404

    return jsonify({"message": f"Deleted books: {', '.join(deleted_books)}"}), 200


@app.route('/members')
def members():
    return render_template("members.html")

@app.route('/create-member')
def create_member():
    return render_template("create-member.html")

@app.route('/create-transaction')
def create_transaction():
    return render_template("create-transaction.html")

@app.route("/books_api", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        title = request.form.get("title", "")
        authors = request.form.get("authors", "")
        isbn = request.form.get("isbn", "")
        publisher = request.form.get("publisher", "")
        num_pages = request.form.get("num_pages", "")
        required_books = int(request.form.get("required_books", 20))

        books = fetch_books(title, authors, isbn, publisher, num_pages, required_books)
        if books:
            save_books_to_db(books)  # Store books in DB

        return render_template("books_api.html", books=books)   
        

    return render_template("books_api.html", books=[])


