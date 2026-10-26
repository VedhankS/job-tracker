import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required,get_jwt_identity

db = SQLAlchemy()
jwt = JWTManager()

class Job(db.Model):
    id = db.Column(db.Integer,primary_key = True)
    user_id = db.Column(db.Integer,nullable=False)
    company = db.Column(db.String(100), nullable = False)
    role = db.Column(db.String(100), nullable = False)
    status = db.Column(db.String(30), nullable = False, default = "applied")

    def to_dict(self):
        return {
            "id":self.id,
            "user_id":self.user_id,
            "company":self.company,
            "role":self.role,
            "status":self.status,
        }
def create_app(test_config = None):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL","sqlite:///jobs.db")
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY","dev-secret-key-change-in-prod")
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    jwt.init_app(app)

    with app.app_context():
        db.create_all()

    @app.errorhandler(404)
    def not_found(e):
        return {"error":"Not Found"},404

    @app.get("/health")
    def health():
        return {"status":"ok"}

    @app.get("/jobs")
    @jwt_required()
    def list_jobs():
        current_user_id = int(get_jwt_identity())
        jobs = Job.query.filter_by(user_id=current_user_id).all()
        return jsonify([j.to_dict() for j in jobs])

    @app.post("/jobs")
    @jwt_required()
    def create_job():
        current_user_id=int(get_jwt_identity())
        data = request.get_json(silent = True) or {}
        if not data.get("company") or not data.get("role"):
            return {"error":"Company and role are required"}, 400
        job = Job(
            user_id = current_user_id,
            company = data["company"],
            role = data["role"],
            status = data.get("status","applied"),
        )
        db.session.add(job)
        db.session.commit()
        return job.to_dict(),201

    @app.get("/jobs/<int:job_id>")
    @jwt_required()
    def get_job(job_id):
        current_user_id = int(get_jwt_identity())
        job = Job.query.filter_by(id = job_id, user_id = current_user_id).first_or_404()
        return job.to_dict()

    @app.put("/jobs/<int:job_id>")
    @jwt_required()
    def update_job(job_id):
        current_user_id=int(get_jwt_identity())
        job = Job.query.filter_by(id=job_id,user_id=current_user_id).first_or_404()
        data = request.get_json(silent = True) or {}
        job.company = data.get("company", job.company)
        job.role = data.get("role", job.role)
        job.status = data.get("status", job.status)
        db.session.commit()
        return job.to_dict()

    @app.delete("/jobs/<int:job_id>")
    @jwt_required()
    def delete_job(job_id):
        current_user_id = int(get_jwt_identity())
        job = Job.query.filter_by(id=job_id,user_id=current_user_id).first_or_404()
        db.session.delete(job)
        db.session.commit()
        return "", 204

    return app
