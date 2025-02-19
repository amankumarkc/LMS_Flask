from flask import Flask, render_template, jsonify, request
from routes import book, member, transaction
import json
import os

CONFIG_FILE = "rent.json"


app = Flask(__name__)

# Register blueprints
app.register_blueprint(book.bp)
app.register_blueprint(member.bp)
app.register_blueprint(transaction.bp)

@app.route('/')
def home():
    return render_template("home.html")

 
@app.route('/update-rent', methods=['POST'])
def update_rent():
    try:
        # Get the new rent amount from the form data
        new_rent = int(request.form['rent_amount'])

        # Read the existing configuration from the JSON file
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)

        # Update the rent amount in the config
        config["rent_amount"] = new_rent

        # Write the updated configuration back to the JSON file
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)

        return jsonify({"success": True, "message": f"Rent updated to ₹{new_rent}"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500



@app.route('/settings', methods=['GET'])
def settings():
    try:
        # Read the current rent from the config file
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)

        # Get the current rent amount, default to 40 if not set
        current_rent = config.get("rent_amount", 40)

        return render_template('settings.html', current_rent=current_rent)

    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500



if __name__ == '__main__':
    app.run(debug=True)