from flask import Flask, render_template
from routes import book, member, transaction

app = Flask(__name__)

# Register blueprints
app.register_blueprint(book.bp)
app.register_blueprint(member.bp)
app.register_blueprint(transaction.bp)

@app.route('/')
def home():
    return render_template("home.html")

if __name__ == '__main__':
    app.run(debug=True)