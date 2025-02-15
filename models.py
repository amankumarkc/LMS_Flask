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

    # def save(self, *args, **kwargs):
    #     # Ensure ISBN is exactly 13 digits
    #     if not (self.isbn.isdigit() and len(self.isbn) == 13):
    #         raise ValueError("ISBN must be exactly 13 digits")
        
    #     super().save(*args, **kwargs)


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

    # def save(self, *args, **kwargs):
    #     # Auto-calculate age
    #     today = date.today()
    #     self.age = today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))

    #     # Generate member_id with first_name, last_name, dob and gender (e.g., "AMM10" for Aman (Male) born in October)
    #     self.member_id = f"{self.first_name[0].upper()}{self.last_name[0].upper()}{self.gender[0].upper()}{str(self.dob.month).zfill(2)}"\
        
    #     super().save(*args, **kwargs)


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

    # def save(self, *args, **kwargs):
    #     # Automatically set due_date to 14 days from issue_date if not provided
    #     if not self.due_date:
    #         self.due_date = self.issue_date + timedelta(days=14)

    #     # Auto-calculate late_days if book is returned
    #     if self.return_date:
    #         self.late_days = max((self.return_date - self.due_date).days, 0)

    #     super().save(*args, **kwargs)


# Connect and create tables
db.connect()
db.create_tables([Book, Member, Transaction])
