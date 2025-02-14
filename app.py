from flask import Flask, render_template, redirect, request, make_response, jsonify
from config import db
from models import Book, Member, Transaction
from weasyprint import HTML
from books_api import fetch_books, save_books_to_db

app = Flask(__name__)

@app.route('/')
def home():
    return "home page"

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