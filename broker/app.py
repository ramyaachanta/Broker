import random
import re
otp_store = {}
import smtplib
from email.mime.text import MIMEText
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash


from urllib.parse import quote_plus
app = Flask(__name__)
CORS(app)

app.secret_key = "supersecretkey"


password = quote_plus("Cse@40668")  # Encode special characters
app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://postgres:{password}@localhost:5432/broker_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    ip = db.Column(db.String(100), nullable=False)
    port = db.Column(db.Integer, nullable=False)

    def __init__(self, name, ip, port):
        self.name = name
        self.ip = ip
        self.port = port
    
import smtplib
from email.mime.text import MIMEText

def send_otp_email(recipient_email, otp):
    # ✅ This is the broker's Gmail (used to send OTP to providers)
    sender_email = "bhagyaputturu2000@gmail.com"           # Replace with your broker Gmail
    app_password = "kgty rnzp fniw kgyc"           # Replace with your Gmail App Password

    subject = "Your OTP Code - Service Broker"
    body = f"""
    Hello,

    Your One-Time Password (OTP) is: {otp}

    Please enter this OTP to verify your identity and continue with your request.
    This OTP is valid for a single use and should not be shared with anyone.

    Regards,  
    Service Broker Team
    """

    # Create the email message
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = recipient_email

    try:
        # Setup SMTP connection and send the email
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()

        print(f"✅ OTP email sent to {recipient_email}")
    except Exception as e:
        print(f"❌ Failed to send OTP email to {recipient_email}:", e)




@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    user = ProviderUser.query.filter_by(username=username).first()
    if user and user.check_password(password):
        session["user"] = username
        return jsonify({"success": True, "message": "Login Successful"})

    return jsonify({"success": False, "message": "Invalid credentials"}), 401

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"success": False, "message": "Username and password required"}), 400
    
    if not is_valid_email(username):
        return jsonify({"success": False, "message": "Invalid email address"}), 400

    if ProviderUser.query.filter_by(username=username).first():
        return jsonify({"success": False, "message": "Username already exists"}), 409

    new_user = ProviderUser(username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"success": True, "message": "Registration successful"})

@app.route("/get_current_user")
def get_current_user():
    if "user" in session:
        return jsonify({"logged_in": True, "username": session["user"]})
    return jsonify({"logged_in": False})


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("home"))

    services = Service.query.all()
    return render_template("dashboard.html", services=services, username=session["user"])


@app.route("/add_service", methods=["POST"])
def add_service():
    if "user" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    username = session["user"]  # 🧠 Get logged-in user automatically
    data = request.json

    service_name = data.get("service_name")
    service_ip = data.get("service_ip")
    service_port = data.get("service_port")
    password = data.get("password")
    otp = data.get("otp")

    provider = ProviderUser.query.filter_by(username=username).first()
    if not provider or not provider.check_password(password):
        return jsonify({"success": False, "message": "Invalid provider credentials"}), 401

    expected_otp = otp_store.get(username)
    if otp != expected_otp:
        return jsonify({"success": False, "message": "Invalid or missing OTP"}), 401
    del otp_store[username]

    existing_service = Service.query.filter_by(name=service_name).first()
    if existing_service:
        return jsonify({"success": False, "message": "Service already exists"})

    new_service = Service(name=service_name, ip=service_ip, port=service_port)
    db.session.add(new_service)
    db.session.commit()

    return jsonify({"success": True, "message": f"Service '{service_name}' added successfully!"})

@app.route("/get_service", methods=["POST"])
def get_service():
    data = request.json
    service_name = data.get("service_name")

    if not service_name:
        return jsonify({"success": False, "message": "Missing service name"}), 400

    service = Service.query.filter_by(name=service_name).first()
    if not service:
        return jsonify({"success": False, "message": "Service not found"}), 404

    return jsonify({
        "success": True,
        "service_name": service.name,
        "service_ip": service.ip,
        "service_port": service.port,
        "service_url": f"http://{service.ip}:{service.port}"
    })


@app.route("/get_services", methods=["GET"])
def get_services():
    services = Service.query.all()
    service_names = [service.name for service in services]
    return jsonify({"success": True, "services": service_names})

@app.route("/remove_service", methods=["POST"])
def remove_service():
    if "user" not in session:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    username = session["user"]
    data = request.json

    service_name = data.get("service_name")
    password = data.get("password")
    otp = data.get("otp")

    provider = ProviderUser.query.filter_by(username=username).first()
    if not provider or not provider.check_password(password):
        return jsonify({"success": False, "message": "Invalid provider credentials"}), 401

    expected_otp = otp_store.get(username)
    if otp != expected_otp:
        return jsonify({"success": False, "message": "Invalid or missing OTP"}), 401
    del otp_store[username]

    service = Service.query.filter_by(name=service_name).first()
    if not service:
        return jsonify({"success": False, "message": "Service not found"})

    db.session.delete(service)
    db.session.commit()

    return jsonify({"success": True, "message": f"Service '{service_name}' removed successfully!"})


@app.route("/request_otp", methods=["POST"])
def request_otp():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    provider = ProviderUser.query.filter_by(username=username).first()
    if not provider or not provider.check_password(password):
        return jsonify({"success": False, "message": "Invalid credentials"}), 401

    otp = str(random.randint(100000, 999999))
    otp_store[username] = otp

    send_otp_email(username, otp)
    return jsonify({"success": True, "message": "OTP sent successfully"})


class ProviderUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

# Just run this twwo lines firsst time to create table in DB and comment later
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)