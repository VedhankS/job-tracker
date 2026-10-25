from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Job(db.Model):
    id = db.Column(db.Integer,primary_key = True)
    company = db.Column(db.String(100), nullable = False)
    role = db.Column(db.String(100), nullable = False)
    status = db.Column(db.String(30), nullable = False, default = "applied")

    def to_dict(self):
        return {
            "id":self.id,
            "company":self.company,
            "role":self.role,
            "status":self.status,
        }
def create_app(test_config = None):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///jobs.db"
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    with app.app_context():
        db.create_all()

    @app.errorhandler(404)
    def not_found(e):
        return {"error":"Not Found"},404
    @app.get("/health")
    def health():
        return {"status":"ok"}

    @app.get("/jobs")
    def list_jobs():
        jobs = Job.query.all()
        return jsonify([j.to_dict() for j in jobs])
    @app.post("/jobs")
    def create_job():
        data = request.get_json(silent = True) or {}
        if not data.get("company") or not data.get("role"):
            return {"error":"Company and role are required"}, 400
        job = Job(
            company = data["company"],
            role = data["role"],
            status = data.get("status","applied"),
        )
        db.session.add(job)
        db.session.commit()
        return job.to_dict(),201

    @app.get("/jobs/<int:job_id>")
    def get_job(job_id):
        job = db.get_or_404(Job, job_id)
        return job.to_dict()
    @app.put("/jobs/<int:job_id>")
    def update_job(job_id):
        job = db.get_or_404(Job,job_id)
        data = request.get_json(silent = True) or {}
        job.company = data.get("company", job.company)
        job.role = data.get("role", job.role)
        job.status = data.get("status", job.status)
        db.session.commit()
        return job.to_dict()
    @app.delete("/jobs/<int:job_id>")
    def delete_job(job_id):
        job = db.get_or_404(Job, job_id)
        db.session.delete(job)
        db.session.commit()
        return "", 204
    return app
