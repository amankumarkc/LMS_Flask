from models import db  # Ensure db is your Postgres database instance

def drop_all_tables():
    with db.atomic():
        db.execute_sql("DROP SCHEMA public CASCADE;")
        db.execute_sql("CREATE SCHEMA public;")
        print("All tables deleted successfully!")

drop_all_tables()
