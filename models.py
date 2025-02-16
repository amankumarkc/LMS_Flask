from peewee import *
from config import db
from datetime import date, timedelta

class BaseModel(Model):
    class Meta:
        database = db

class Book(BaseModel):
    title = CharField()
    author = CharField()
    isbn = CharField(unique=True)
    publisher = CharField()
    stock = IntegerField(default=5)
    num_pages = IntegerField()
    publication_date = IntegerField()
    language = CharField(default='English')  # e.g., English, Hindi, French
    mrp = FloatField()  # Maximum Retail Price
    times_issued = IntegerField(default=0)  # Number of times issued

class Member(BaseModel):
    first_name = CharField()
    last_name = CharField()
    member_id = CharField(unique=True)  # Auto-generated
    email = CharField(unique=True)
    phone = CharField()

    # Bifurcated Address Fields
    locality = TextField()
    city = CharField()
    state = CharField()
    pincode = CharField()

    dob = DateField()
    age = IntegerField()  # Auto-calculated
    gender = CharField(choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    outstanding_debt = FloatField(default=0.0)
    last_active = DateField(null=True)  # Updates when book is issued/returned
    card_status = CharField(choices=[('Active', 'Active'), ('Inactive', 'Inactive'), ('Suspended', 'Suspended')])
    card_expiry = DateField(null=True)  # Auto-generated based on joining date

class Transaction(BaseModel):
    member = ForeignKeyField(Member, backref='transactions')
    book = ForeignKeyField(Book, backref='transactions')
    issue_date = DateField(default=date.today)  # Default to today
    due_date = DateField()
    return_date = DateField(null=True)
    rent_fee = FloatField(default=0)
    fine = FloatField(default=0)  # Fine logic handled in backend
    status = CharField(choices=[('issued', 'Issued'), ('returned', 'Returned')])
    late_days = IntegerField(default=0)  # Number of late days (calculated)
    mode_of_payment = CharField(choices=[('cash', 'Cash'), ('online', 'Online')], null=True)
    invoice_id = CharField(null=True, unique=True)  # For fine tracking

# Connect and create tables
db.connect()
db.create_tables([Book, Member, Transaction])
