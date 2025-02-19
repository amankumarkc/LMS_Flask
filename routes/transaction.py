import csv
from weasyprint import HTML
from models import Transaction, Member, Book
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, request, jsonify, Response, make_response
from io import StringIO
from books_api import generate_arn
import json

bp = Blueprint('transaction', __name__, url_prefix='/transaction')
CONFIG_FILE = "rent.json"
@bp.route('/list')
def transactions():
    all_transactions = Transaction.select().join(Member).switch(Transaction).join(Book)
    
    for transaction in all_transactions:
        if transaction.invoice_id is None:
            arn = generate_arn(transaction)
            if arn:
                transaction.invoice_id = arn
                transaction.save()
    
    return render_template("transactions.html", transactions=all_transactions)

@bp.route('/download-csv', methods=['GET'])
def download_transactions_csv():
    transactions = Transaction.select().join(Member).switch(Transaction).join(Book)

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Transaction ID", "Member Name", "Book Title", "Issue Date", "Due Date", "Status"])

    for transaction in transactions:
        writer.writerow([
            transaction.id, 
            f"{transaction.member.first_name} {transaction.member.last_name}", 
            transaction.book.title,
            transaction.issue_date,
            transaction.due_date,
            transaction.status
        ])

    output.seek(0)
    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=library_transactions.csv"

    return response

@bp.route('/create', methods=['GET', 'POST'])
def create_transaction():
    if request.method == 'GET':
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

        books_data = [
            {
                'id': book.id,
                'title': book.title,
                'author': book.author,
                'stock': book.stock
            }
            for book in Book.select().where(Book.stock > 0)
        ]

        return render_template(
            "create-transaction.html",
            members=members_data,
            books=books_data,
            today=date.today().strftime('%Y-%m-%d')
        )

    elif request.method == 'POST':
        try:
            member_id = request.form['member']
            book_id = request.form['book']
            issue_date = datetime.strptime(request.form['issue_date'], '%Y-%m-%d').date()
            due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d').date()
            
            member = Member.get_by_id(member_id)
            book = Book.get_by_id(book_id)

            # Check outstanding debt
            current_outstanding = member.outstanding_debt + 40  # Adding new rent
            if current_outstanding > 500:
                return jsonify({
                    "success": False,
                    "message": "Cannot issue book. Outstanding debt would exceed ₹500"
                }), 400

            # Validate due date is at least 14 days after issue date
            min_due_date = issue_date + timedelta(days=14)
            if due_date < min_due_date:
                return jsonify({
                    "success": False,
                    "message": "Due date must be at least 14 days after issue date"
                }), 400

            # Create transaction
            transaction = Transaction.create(
                member=member,
                book=book,
                issue_date=issue_date,
                due_date=due_date,
                status='issued',
                rent_fee=get_rent()
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

        except Exception as e:
            return jsonify({
                "success": False,
                "message": f"An error occurred: {str(e)}"
            }), 500

@bp.route("/download-pdf/<int:id>")
def download_transaction_pdf(id):
    try:
        transaction = Transaction.get_by_id(id)
        html_content = render_template("print/transaction-receipt.html", transaction=transaction)
        pdf = HTML(string=html_content).write_pdf()
        
        response = make_response(pdf)
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Content-Disposition"] = f"inline; filename=receipt_{id}.pdf"

        return response
    except Transaction.DoesNotExist:
        return "Transaction not found", 404

@bp.route('/delete/<int:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    try:
        transaction = Transaction.get_or_none(Transaction.id == transaction_id)
        if transaction:
            transaction.delete_instance()
            return jsonify({'success': True, 'message': 'Transaction deleted successfully'}), 200
        else:
            return jsonify({'success': False, 'error': 'Transaction not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/delete-bulk', methods=['POST'])
def delete_transactions():
    try:
        data = request.get_json()
        transaction_ids = data.get('transaction_ids', [])

        if not transaction_ids:
            return jsonify({'success': False, 'error': 'No transaction IDs provided'}), 400

        deleted_count = Transaction.delete().where(Transaction.id.in_(transaction_ids)).execute()
        return jsonify({'success': True, 'deleted': deleted_count}), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/return/<int:transaction_id>', methods=['POST'])
def return_transaction(transaction_id):
    transaction = Transaction.get_or_none(Transaction.id == transaction_id)

    if not transaction or transaction.status != 'issued':
        return jsonify({"success": False, "error": "Transaction not found or already returned"}), 400

    data = request.json
    if not data:
        return jsonify({"success": False, "error": "Invalid data"}), 400

    transaction.return_date = data.get("return_date")
    transaction.fine = data.get("fine", 0)
    transaction.status = "returned"
    transaction.save()

    # Update the book stock
    book = transaction.book
    book.stock += 1
    book.save()
    
    # Reduce the member's outstanding debt by the rent fee amount
    member = transaction.member
    if member:
        member.outstanding_debt = max(0, member.outstanding_debt - transaction.rent_fee)
        member.save()
    
    return jsonify({"success": True, "invoice_id": transaction.invoice_id})


def get_rent():
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
    return config.get("rent_amount", 40)  # Default to 40