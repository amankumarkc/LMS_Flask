from flask import Flask, render_template, redirect, request, make_response, jsonify, Response, flash, url_for
from config import db
from models import Book, Member, Transaction
from peewee import IntegrityError, DoesNotExist
from weasyprint import HTML
from datetime import datetime, timedelta, date
from books_api import fetch_books, save_books_to_db
import csv
from io import StringIO

app = Flask(__name__)

@app.route('/')
def home():
    return render_template("home.html")

# View Books Page
@app.route('/books')
def books():
    all_books = Book.select()  # Fetch all books from DB
    return render_template("books.html", books=all_books)

# Add(Import) Book Page
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

#  Download Books CSV
@app.route('/download-books-csv', methods=['GET'])
def download_books_csv():
    books = Book.select()  # Fetch all books from the database

    # Create an in-memory file object
    output = StringIO()
    writer = csv.writer(output)

    # Write CSV header
    writer.writerow(["Book ID", "Title", "Author", "Language", "Publisher", "Stock"])

    # Write book data
    for book in books:
        writer.writerow([book.id, book.title, book.author, book.language, book.publisher, book.stock])

    # Move the cursor to the beginning of the file
    output.seek(0)

    # Create response with CSV content
    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=library_books.csv"
    
    return response


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

# Create Member Page
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

# Download Members CSV
@app.route('/download-members-csv', methods=['GET'])
def download_members_csv():
    members = Member.select()  # Fetch all members from the database

    # Create an in-memory file object
    output = StringIO()
    writer = csv.writer(output)

    # Write CSV header
    writer.writerow(["Member ID", "First Name", "Last Name", "Gender", "DOB", "Email", "Phone", "Address"])

    # Write member data
    for member in members:
        writer.writerow([
            member.member_id, member.first_name, member.last_name, 
            member.gender, member.dob, member.email, 
            member.phone, f"{member.locality}, {member.city}, {member.state}, {member.pincode}"
        ])

    # Move the cursor to the beginning of the file
    output.seek(0)

    # Create response with CSV content
    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=library_members.csv"
    
    return response


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
        member.card_status = request.form.get("card_status", member.card_status)
        member.card_expiry = request.form.get("card_expiry", member.card_expiry)
        member.outstanding_debt = request.form.get("outstanding_debt", member.outstanding_debt)

        # Regenerate Member ID if Name, Gender, or Phone changes
        new_member_id = (member.first_name[0] + member.last_name[0] + member.gender[0] + member.phone[-2:]).upper()
        if member.member_id != new_member_id:
            member.member_id = new_member_id  # Update in database
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

# View Member Card
@app.route("/view-card/<int:member_id>")
def view_card(member_id):
    member = Member.get_or_none(Member.id == member_id)
    if not member:
        return "Member Not Found", 404
    return render_template("view-card.html", member=member)

# Library Card PDF View in Browser
@app.route("/download/<int:member_id>")
def download_pdf(member_id):
    member = Member.get_or_none(Member.id == member_id)
    if not member:
        return "Member Not Found", 404

    html = HTML(string=render_template("print/library-card.html", member=member))
    pdf_content = html.write_pdf()

    response = Response(pdf_content, content_type="application/pdf")
    response.headers["Content-Disposition"] = f"inline; filename=Library_Card_{member.member_id}.pdf"  # ✅ Open in browser

    return response

# Create Transaction Page
@app.route('/create-transaction', methods=['GET', 'POST'])
def create_transaction():
    if request.method == 'GET':
        # Serialize members data
        members_data = [
            {
                'id': member.id,
                'first_name': member.first_name,
                'last_name': member.last_name,
                'member_id': member.member_id,
                'outstanding_debt': float(member.outstanding_debt)
            }
            for member in Member.select()
        ]

        # Serialize books data
        books_data = [
            {
                'id': book.id,
                'title': book.title,
                'author': book.author,
                'stock': book.stock
            }
            for book in Book.select().where(Book.stock > 0)
        ]

        # Serialize transactions data
        transactions_data = [
            {
                'id': trans.id,
                'member_id': trans.member.id,
                'book_id': trans.book.id,
                'issue_date': trans.issue_date.strftime('%Y-%m-%d'),
                'due_date': trans.due_date.strftime('%Y-%m-%d'),
                'status': trans.status
            }
            for trans in Transaction.select().where(Transaction.status == 'issued')
        ]

        return render_template(
            "create-transaction.html",
            members=members_data,
            books=books_data,
            transactions=transactions_data,
            today=date.today().strftime('%Y-%m-%d')
        )

    elif request.method == 'POST':
        try:
            status = request.form['status']
            member_id = request.form['member']
            book_id = request.form['book']
            member = Member.get_by_id(member_id)
            book = Book.get_by_id(book_id)

            if status == 'issued':
                # Check outstanding debt
                current_outstanding = member.outstanding_debt + 40  # Adding new rent
                if current_outstanding > 500:
                    return jsonify({
                        "success": False,
                        "message": "Cannot issue book. Outstanding debt would exceed ₹500"
                    }), 400

                # Create transaction
                transaction = Transaction.create(
                    member=member,
                    book=book,
                    issue_date=date.today(),
                    due_date=date.today() + timedelta(days=14),
                    status='issued',
                    rent_fee=40
                )

                # Update book stock and member debt
                book.stock -= 1
                book.save()
                member.outstanding_debt = current_outstanding
                member.save()

                return jsonify({
                    "success": True,
                    "message": f"Book '{book.title}' successfully issued to {member.first_name} {member.last_name}"
                }), 201

            elif status == 'returned':
                # Invoice ID and Mode of Payment are mandatory
                mode_of_payment = request.form.get('mode_of_payment')
                invoice_id = request.form.get('invoice_id')
                
                if not mode_of_payment or not invoice_id:
                    return jsonify({
                        "success": False,
                        "message": "Invoice ID and Mode of Payment are required to return a book."
                    }), 400

                # Get the original transaction
                transaction = Transaction.get(
                    (Transaction.member == member) & 
                    (Transaction.book == book) & 
                    (Transaction.status == 'issued')
                )
                
                return_date = datetime.strptime(request.form['return_date'], '%Y-%m-%d').date()
                late_days = max(0, (return_date - transaction.due_date).days)
                late_fine = late_days * 5
                rent_fee = 40  # Rent fee is fixed
                total_deduction = rent_fee + late_fine

                # Update transaction
                transaction.return_date = return_date
                transaction.late_days = late_days
                transaction.fine = late_fine
                transaction.status = 'returned'
                transaction.mode_of_payment = mode_of_payment
                transaction.invoice_id = invoice_id
                transaction.save()

                # Update book stock
                book.stock += 1
                book.save()

                # Update member debt (Ensuring it doesn't go negative)
                member.outstanding_debt = max(0, member.outstanding_debt - total_deduction)
                member.save()

                return jsonify({
                    "success": True,
                    "message": f"Book '{book.title}' successfully returned by {member.first_name} {member.last_name}"
                }), 200

        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"An error occurred: {str(e)}"
            }), 500

    return jsonify({"success": False, "message": "Invalid request"}), 400