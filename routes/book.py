import csv
from io import StringIO
from peewee import IntegrityError
from models import Book, Transaction
from books_api import fetch_books, save_books_to_db
from flask import Blueprint, redirect, render_template, request, jsonify, Response

bp = Blueprint('book', __name__, url_prefix='/book')

@bp.route('/list')
def books():
    all_books = Book.select()
    return render_template("books.html", books=all_books)

@bp.route('/api', methods=["GET", "POST"])
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
            save_books_to_db(books)

        return render_template("books_api.html", books=books)   

    return render_template("books_api.html", books=[])

@bp.route('/download-csv', methods=['GET'])
def download_books_csv():
    books = Book.select()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Book ID", "Title", "Author", "Language", "Publisher", "Stock"])

    for book in books:
        writer.writerow([book.id, book.title, book.author, book.language, book.publisher, book.stock])

    output.seek(0)
    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=library_books.csv"
    
    return response

@bp.route('/create', methods=['GET', 'POST'])
def create_book():
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            author = request.form.get('author')
            isbn = request.form.get('isbn')
            publisher = request.form.get('publisher')
            stock = int(request.form.get('stock', 5))
            num_pages = int(request.form.get('num_pages', '0'))
            publication_date = int(request.form.get('publication_date'))
            language = request.form.get('language', 'English')
            mrp = float(request.form.get('mrp', '0.0'))

            book = Book.create(
                title=title,
                author=author,
                isbn=isbn,
                publisher=publisher,
                stock=stock,
                num_pages=num_pages,
                publication_date=publication_date,
                language=language,
                mrp=mrp
            )
            book.save()
            return jsonify({"message": f"Book '{book.title}' successfully created!"}), 201

        except IntegrityError:
            return jsonify({"message": "Error: A book with this ISBN already exists."}), 400
        except Exception as e:
            return jsonify({"message": f"An error occurred: {str(e)}"}), 500

    return render_template("create-book.html")

@bp.route('/edit/<int:book_id>', methods=['GET', 'POST'])
def edit_books(book_id):
    book = Book.get_or_none(Book.id == book_id)
    if not book:
        return "Book not found", 404

    if request.method == 'POST':
        book.stock = int(request.form.get("stock", book.stock))
        book.mrp = float(request.form.get("mrp", book.mrp))
        book.num_pages = int(request.form.get("num_pages", book.num_pages))
        book.save()

        return redirect("/book/list")

    return render_template("edit-books.html", book=book)

@bp.route('/delete/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    book = Book.get_or_none(Book.id == book_id)
    if not book:
        return jsonify({"message": "Book not found"}), 404

    if Transaction.select().where(Transaction.book == book).exists():
        return jsonify({"message": "This book can't be deleted as it is linked to a transaction."}), 400

    book.delete_instance()
    return jsonify({"message": f"Book '{book.title}' has been successfully deleted!"})

@bp.route('/delete-bulk', methods=['POST'])
def bulk_delete_books():
    data = request.get_json()
    book_ids = data.get("book_ids", [])

    if not book_ids:
        return jsonify({"message": "No books selected!"}), 400

    deleted_books = []
    failed_books = []
    for book_id in book_ids:
        book = Book.get_or_none(Book.id == book_id)
        if book:
            if Transaction.select().where(Transaction.book == book).exists():
                failed_books.append(f"'{book.title}' (Stock: {book.stock})")
            else:
                deleted_books.append(f"'{book.title}' ({book.stock} stock)")
                book.delete_instance()

    if not deleted_books:
        return jsonify({"message": "No valid books found to delete!"}), 404

    if failed_books:
        return jsonify({
            "message": f"Some books could not be deleted as they are referenced in transactions: {', '.join(failed_books)}"
        }), 400

    return jsonify({"message": f"Deleted books: {', '.join(deleted_books)}"}), 200