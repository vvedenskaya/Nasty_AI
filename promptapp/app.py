import os 
from flask import Flask, request, jsonify, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message 
import sqlite3
import random
import string
from datetime import datetime,timedelta, timezone
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
import atexit


app = Flask(__name__)

instance_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
db_path = os.path.join(instance_dir, 'users.db')

if not os.path.exists(instance_dir):
    os.makedirs(instance_dir)

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenvb('MAIL_PASSWORD')
app.config['MAIL_USE_SSL'] = True

db = SQLAlchemy(app)
mail = Mail(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    confirmed = db.Column(db.Boolean, default=False)
    token = db.Column(db.String(120), unique=True, nullable=False)
    registered_on = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

def generate_token():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=20))


with app.app_context():
    try:
        db.create_all()
        print("Database and tables created")
        print(f"Database path: {db_path}")
    except Exception as e:
        print(f"Error creating database: {e}")


@app.route('/')
def index():
    return render_template('testerReg.html')

@app.route('/register', methods=['POST'])
def register():
    try:
        if request.is_json:
            data = request.get_json()
            name = data['name']
            email = data['email']
        else:
            name = request.form['name']
            email = request.form['email']

        print(f"Registering user: {name}, {email}")    

        if User.query.filter_by(email=email).first():
            return jsonify({"success": "false", "message": "Can't create new user. User with this email already exists"}), 400

        token = generate_token()
        new_user = User(name=name, email=email, confirmed=False, token=token)
        db.session.add(new_user)
        db.session.commit()

        print(f"User {name} registered successfully with ID {new_user.id} and token {new_user.token}")

        msg = Message('Confirm your registration', sender= app.config['MAIL_USERNAME'], recipients=[email])
        confirmation_url = url_for('confirm', id=new_user.id, token=token, _external=True)
        msg.body = f"Please click the link to confirm your registration: {confirmation_url}"
        mail.send(msg)
        
        print("Registration successful, confirmation email sent.")
        return jsonify({"success": "true", "message": "Check your email to finish registration"}), 200
    except Exception as e:
            print(f"Error during registration: {e}")
            return jsonify({"success": "false", "message": "An error occurred. Please try again later."}), 500
    

@app.route('/confirm', methods=['GET'])
def confirm():
    user_id = request.args.get('id')
    token = request.args.get('token')

    try:
        print(f"Confirming user with ID: {user_id} and token: {token}")
        user = db.session.get(User, user_id)
        print(f"User found: {user}")

        if user and user.token == token:
            user.confirmed = True
            db.session.commit()
            print(f"User {user_id} confirmed successfully")
            return render_template('emailConfirm.html')
        else:
            print(f"Invalid token or user not found for ID: {user_id} and token: {token}")
            return jsonify({"success": "false", "message": "Invalid token or user"}), 400
    except Exception as e:
        print(f"Error during confirmation: {e}")
        return jsonify({"success": "false", "message": "An error occured. Please try again later"}), 500


@app.route('/status', methods=['GET'])
def status():
    user_id = request.args.get('id')
    user = User.query.get(user_id)

    if user:
        return jsonify({"success": "true", "message": "User found", "user": {"name": user.name, "email": user.email, "confirmed": user.confirmed}})
    else:
        return jsonify({"success": "false", "message": "User not found"}), 404

@app.route('/verify', methods=['POST'])
def verify():
    data = request.get_json()
    user_id = data.get('id')
    token = data.get('token')

    user = User.query.get(user_id)

    if user and user.token == token:
        user.confirmed = True
        db.session.commit()
        return jsonify({"success": "true", "message": "User confirmed"}), 200
    else:
        return jsonify({"success": "false", "message": "Invalid token or user"}), 400
    
@app.route('/create_test_user')
def create_test_user():
    try:
        test_user = User(name="Test User", email="test@example.com", confirmed=False, token="testtoken")
        db.session.add(test_user)
        db.session.commit()
        return jsonify({"success": "true", "message": "Test user created successfully"}),200
    except Exception as e:
        return jsonify({"success": "false", "message": str(e)}), 500
    

def delete_unconfirmed_users():
    expiration_date = datetime.now(pytz.utc) - timedelta(weeks=1)
    unconfirmed_users = User.query.filter(User.confirmed == False, User.registered_on < expiration_date).all()
    
    for user in unconfirmed_users:
        db.session.delete(user)
    
    db.session.commit()

scheduler = BackgroundScheduler()
scheduler.add_job(func=delete_unconfirmed_users, trigger="interval", weeks=4)
scheduler.start()

atexit.register(lambda: scheduler.shutdown())


if __name__ == '__main__':
    app.run(debug=True)