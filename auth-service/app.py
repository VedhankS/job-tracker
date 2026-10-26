import os
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()
jwt = JWTManager()

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(120), unique = True, nullable = False)
    password_hash = db.Column(db.String(256),nullable=False)

def create_app(test_config = None):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL","sqlite:///users.db")
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY","dev-secret-key-change-in-prod")
    if test_config:
        app.config.update(test_config)
    db.init_app(app)
    jwt.init_app(app)

    with app.app_context():
        db.create_all()
    @app.get("/health")
    def health():
        return {"status":"ok"}
    @app.post("/register")
    def register():
        data = request.get_json(silent = True) or {}
        email = data.get("email")
        password = data.get("password")
        if not email or not password:
            return{"error":"email and password are required"}, 400
        if User.query.filter_by(email = email).first():
            return {"error":"email already registered"}, 409
        user = User(
            email = email,
            password_hash = generate_password_hash(password),
        )
        db.session.add(user)
        db.session.commit()
        return {"id":user.id,"email":user.email},201
    @app.post("/login")
    def login():
        data = request.get_json(silent = True) or {}
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return {"error" :"email and password are required"}, 400
        user = User.query.filter_by(email = email).first()
        if not user or not check_password_hash(user.password_hash,password):
            return{"error":"User Not registered or invalid credentials"}, 401
        token = create_access_token(identity = str(user.id))
        return {"access_token":token},200
    return app
