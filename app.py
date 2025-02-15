from flask import Flask, render_template, redirect, request, make_response, jsonify
from config import db
from models import Book, Member, Transaction
from peewee import IntegrityError
from weasyprint import HTML
from datetime import datetime, timedelta
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


# Display All Members
@app.route('/members')
def members():
    all_members = Member.select()  # Fetch all members from the database
    return render_template("members.html", members=all_members)

@app.route('/create-member', methods=['GET', 'POST'])
def create_member():
    if request.method == 'POST':
        try:
            first_name = request.form['first_name'].strip()
            last_name = request.form['last_name'].strip()
            email = request.form['email'].strip()
            phone = request.form['phone'].strip()
            locality = request.form['locality'].strip()
            city = request.form['city'].strip() or "Chandigarh"
            state = request.form['state'].strip() or "Chandigarh"
            pincode = request.form['pincode'].strip() or "160019"
            dob = request.form['dob']
            gender = request.form['gender']
            
            # Calculate Age
            dob_date = datetime.strptime(dob, "%Y-%m-%d")
            today = datetime.today()
            age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
            
            # Generate Member ID (e.g., "AKM83" for Aman Kumar, Male, Phone: 7634966583)
            member_id = (first_name[0].upper() + 
                         last_name[0].upper() + 
                         gender[0].upper() + 
                         phone[-2:])  # Last 2 digits of phone number
            
            # Default Values
            card_status = "Active"
            card_expiry = today + timedelta(days=730)  # 2 years from today

            # Insert into Database
            new_member = Member.create(
                first_name=first_name,
                last_name=last_name,
                member_id=member_id,
                email=email,
                phone=phone,
                locality=locality,
                city=city,
                state=state,
                pincode=pincode,
                dob=dob,
                age=age,
                gender=gender,
                outstanding_debt=0.0,
                last_active=None,
                card_status=card_status,
                card_expiry=card_expiry
            )

            return jsonify({"message": f"Member {first_name} {last_name} successfully created!", "member_id": member_id}), 201

        except IntegrityError:
            return jsonify({"message": "Error: Email or Member ID already exists!"}), 409
        except Exception as e:
            return jsonify({"message": f"An error occurred: {str(e)}"}), 500

    return render_template("create-member.html")

# Edit Member Page
@app.route('/edit-member/<int:member_id>', methods=['GET', 'POST'])
def edit_member(member_id):
    member = Member.get_or_none(Member.id == member_id)
    if not member:
        return "Member not found", 404

    if request.method == 'POST':
        # Update member details
        member.first_name = request.form.get("first_name", member.first_name)
        member.last_name = request.form.get("last_name", member.last_name)
        member.email = request.form.get("email", member.email)
        member.phone = request.form.get("phone", member.phone)
        member.locality = request.form.get("locality", member.locality)
        member.city = request.form.get("city", member.city)
        member.state = request.form.get("state", member.state)
        member.pincode = request.form.get("pincode", member.pincode)
        member.dob = request.form.get("dob", member.dob)
        member.gender = request.form.get("gender", member.gender)
        member.save()

        return redirect('/members')  # Redirect to members list

    return render_template("edit-member.html", member=member)

# Delete Single Member API
@app.route('/delete-member/<int:member_id>', methods=['DELETE'])
def delete_member(member_id):
    member = Member.get_or_none(Member.id == member_id)
    if member:
        member.delete_instance()
        return jsonify({
            "success": True,  # ✅ Added success field
            "message": f"Member '{member.first_name} {member.last_name}' has been successfully deleted!"
        }), 200
    return jsonify({"success": False, "error": "Member not found"}), 404


# Delete Bulk Members API
@app.route('/delete-members', methods=['POST'])
def bulk_delete_members():
    data = request.get_json()
    member_ids = data.get("member_ids", [])

    if not member_ids:
        return jsonify({"message": "No members selected!"}), 400

    deleted_members = []
    for member_id in member_ids:
        member = Member.get_or_none(Member.id == member_id)
        if member:
            deleted_members.append(f"{member.first_name} {member.last_name}")
            member.delete_instance()

    if not deleted_members:
        return jsonify({"message": "No valid members found to delete!"}), 404

    return jsonify({"message": f"Deleted members: {', '.join(deleted_members)}"}), 200

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


