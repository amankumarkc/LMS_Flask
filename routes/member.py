import csv
from weasyprint import HTML
from models import Member
from io import StringIO
from peewee import IntegrityError
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, Response, redirect

bp = Blueprint('member', __name__, url_prefix='/member')

@bp.route('/list')
def members():
    all_members = Member.select()
    return render_template("members.html", members=all_members)

@bp.route('/create', methods=['GET', 'POST'])
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
            
            dob_date = datetime.strptime(dob, "%Y-%m-%d")
            today = datetime.today()
            age = today.year - dob_date.year - ((today.month, today.day) < (dob_date.month, dob_date.day))
            
            member_id = (first_name[0].upper() + 
                         last_name[0].upper() + 
                         gender[0].upper() + 
                         phone[-2:])
            
            card_status = "Active"
            card_expiry = today + timedelta(days=730)

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

@bp.route('/download-csv', methods=['GET'])
def download_members_csv():
    members = Member.select()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Member ID", "First Name", "Last Name", "Gender", "DOB", "Email", "Phone", "Address"])

    for member in members:
        writer.writerow([
            member.member_id, member.first_name, member.last_name, 
            member.gender, member.dob, member.email, 
            member.phone, f"{member.locality}, {member.city}, {member.state}, {member.pincode}"
        ])

    output.seek(0)
    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=library_members.csv"
    
    return response

@bp.route('/edit/<int:member_id>', methods=['GET', 'POST'])
def edit_member(member_id):
    member = Member.get_or_none(Member.id == member_id)
    if not member:
        return "Member not found", 404

    if request.method == 'POST':
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

        new_member_id = (member.first_name[0] + member.last_name[0] + member.gender[0] + member.phone[-2:]).upper()
        if member.member_id != new_member_id:
            member.member_id = new_member_id
        member.save()

        return redirect('/member/list')

    return render_template("edit-member.html", member=member)

@bp.route("/delete/<int:member_id>", methods=["DELETE"])
def delete_member(member_id):
    try:
        member = Member.get_or_none(Member.id == member_id)

        if not member:
            return jsonify({"error": "Member not found"}), 404
        
        if member.outstanding_debt > 0:
            return jsonify({"error": f"Cannot delete {member.first_name} {member.last_name}. Outstanding debt: ₹{member.outstanding_debt}"}), 400

        member.delete_instance()
        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/delete-bulk', methods=['POST'])
def bulk_delete_members():
    data = request.get_json()
    member_ids = data.get("member_ids", [])

    if not member_ids:
        return jsonify({"message": "No members selected!"}), 400

    deletable_members = []
    blocked_members = []

    for member_id in member_ids:
        member = Member.get_or_none(Member.id == member_id)
        if member:
            if member.outstanding_debt > 0:
                blocked_members.append(f"{member.first_name} {member.last_name} (₹{member.outstanding_debt})")
            else:
                deletable_members.append(member)

    if deletable_members:
        for member in deletable_members:
            member.delete_instance()

    if blocked_members:
        return jsonify({
            "success": False,
            "blocked_members": blocked_members,
            "deleted_count": len(deletable_members)
        }), 400

    return jsonify({"success": True, "message": f"Deleted {len(deletable_members)} members."}), 200

@bp.route("/view-card/<int:member_id>")
def view_card(member_id):
    member = Member.get_or_none(Member.id == member_id)
    if not member:
        return "Member Not Found", 404
    return render_template("view-card.html", member=member)

@bp.route("/download-pdf/<int:member_id>")
def download_pdf(member_id):
    member = Member.get_or_none(Member.id == member_id)
    if not member:
        return "Member Not Found", 404

    html = HTML(string=render_template("print/library-card.html", member=member))
    pdf_content = html.write_pdf()

    response = Response(pdf_content, content_type="application/pdf")
    response.headers["Content-Disposition"] = f"inline; filename=Library_Card_{member.member_id}.pdf"

    return response