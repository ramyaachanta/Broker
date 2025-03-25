from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS


from urllib.parse import quote_plus
app = Flask(__name__)
CORS(app)

app.secret_key = "supersecretkey"


password = quote_plus("Nithya@123")  # Encode special characters
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

with app.app_context():
    db.create_all()

# --------- DUMMY LOGIN ---------
DUMMY_USERNAME = "admin"
DUMMY_PASSWORD = "password123"

# --------- ROUTES ---------

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if username == DUMMY_USERNAME and password == DUMMY_PASSWORD:
        session["user"] = username
        return jsonify({"success": True, "message": "Login Successful"})
    return jsonify({"success": False, "message": "Invalid credentials"})

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("home"))

    services = Service.query.all()
    return render_template("dashboard.html", services=services)

@app.route("/add_service", methods=["POST"])
def add_service():
    # if "user" not in session:
    #     return jsonify({"success": False, "message": "Unauthorized"})

    data = request.json
    service_name = data.get("service_name")
    service_ip = data.get("service_ip")
    service_port = data.get("service_port")

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
        return jsonify({"success": False, "message": "Unauthorized"})

    data = request.json
    service_name = data.get("service_name")

    service = Service.query.filter_by(name=service_name).first()
    if not service:
        return jsonify({"success": False, "message": "Service not found"})

    db.session.delete(service)
    db.session.commit()

    return jsonify({"success": True, "message": f"Service '{service_name}' removed successfully!"})

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)