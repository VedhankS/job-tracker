import os
import json
import requests
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity
from sqlalchemy import inspect, text

db = SQLAlchemy()
jwt = JWTManager()

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    company = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="applied")
    job_description = db.Column(db.Text, nullable=True)
    match_score = db.Column(db.Integer, nullable=True)
    tailored_bullets = db.Column(db.JSON, nullable=True)
    prep_questions = db.Column(db.JSON, nullable=True)
    skills = db.Column(db.JSON, nullable=True)

    def to_dict(self):
        def _parse_json(val):
            if val is None:
                return []
            if isinstance(val, (list, dict)):
                return val
            if isinstance(val, str):
                try:
                    return json.loads(val)
                except Exception:
                    return [val]
            return val

        return {
            "id": self.id,
            "user_id": self.user_id,
            "company": self.company,
            "role": self.role,
            "status": self.status,
            "job_description": self.job_description,
            "match_score": self.match_score,
            "tailored_bullets": _parse_json(self.tailored_bullets),
            "prep_questions": _parse_json(self.prep_questions),
            "skills": _parse_json(self.skills),
        }

def create_app(test_config=None):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///jobs.db")
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-secret-key-change-in-prod")
    app.config["AI_SERVICE_URL"] = os.environ.get("AI_SERVICE_URL", "http://ai-service:5002")

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    jwt.init_app(app)

    with app.app_context():
        db.create_all()
        # Ensure schema migrations for existing tables
        try:
            inspector = inspect(db.engine)
            if "job" in inspector.get_table_names():
                existing_cols = [c["name"] for c in inspector.get_columns("job")]
                is_pg = "postgres" in app.config.get("SQLALCHEMY_DATABASE_URI", "")
                json_type = "JSON" if is_pg else "TEXT"
                new_columns = [
                    ("job_description", "TEXT"),
                    ("match_score", "INTEGER"),
                    ("tailored_bullets", json_type),
                    ("prep_questions", json_type),
                    ("skills", json_type),
                ]
                for col_name, col_type in new_columns:
                    if col_name not in existing_cols:
                        db.session.execute(text(f"ALTER TABLE job ADD COLUMN {col_name} {col_type}"))
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.warning(f"Database schema update check warning: {e}")

    @app.errorhandler(404)
    def not_found(e):
        return {"error": "Not Found"}, 404

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/jobs")
    @jwt_required()
    def list_jobs():
        current_user_id = int(get_jwt_identity())
        jobs = Job.query.filter_by(user_id=current_user_id).all()
        return jsonify([j.to_dict() for j in jobs])

    @app.post("/jobs")
    @jwt_required()
    def create_job():
        current_user_id = int(get_jwt_identity())
        data = request.get_json(silent=True) or {}
        if not data.get("company") or not data.get("role"):
            return {"error": "Company and role are required"}, 400
        job = Job(
            user_id=current_user_id,
            company=data["company"],
            role=data["role"],
            status=data.get("status", "applied"),
            job_description=data.get("job_description"),
            match_score=data.get("match_score"),
            tailored_bullets=data.get("tailored_bullets"),
            prep_questions=data.get("prep_questions"),
            skills=data.get("skills"),
        )
        db.session.add(job)
        db.session.commit()
        return job.to_dict(), 201

    @app.get("/jobs/<int:job_id>")
    @jwt_required()
    def get_job(job_id):
        current_user_id = int(get_jwt_identity())
        job = Job.query.filter_by(id=job_id, user_id=current_user_id).first_or_404()
        return job.to_dict()

    @app.put("/jobs/<int:job_id>")
    @jwt_required()
    def update_job(job_id):
        current_user_id = int(get_jwt_identity())
        job = Job.query.filter_by(id=job_id, user_id=current_user_id).first_or_404()
        data = request.get_json(silent=True) or {}

        if "company" in data:
            job.company = data["company"]
        if "role" in data:
            job.role = data["role"]
        if "status" in data:
            job.status = data["status"]
        if "job_description" in data:
            job.job_description = data["job_description"]
        if "match_score" in data:
            job.match_score = data["match_score"]
        if "tailored_bullets" in data:
            job.tailored_bullets = data["tailored_bullets"]
        if "prep_questions" in data:
            job.prep_questions = data["prep_questions"]
        if "skills" in data:
            job.skills = data["skills"]

        db.session.commit()
        return job.to_dict()

    @app.delete("/jobs/<int:job_id>")
    @jwt_required()
    def delete_job(job_id):
        current_user_id = int(get_jwt_identity())
        job = Job.query.filter_by(id=job_id, user_id=current_user_id).first_or_404()
        db.session.delete(job)
        db.session.commit()
        return "", 204

    @app.post("/jobs/<int:job_id>/copilot")
    @jwt_required()
    def run_job_copilot(job_id):
        current_user_id = int(get_jwt_identity())
        job = Job.query.filter_by(id=job_id, user_id=current_user_id).first_or_404()
        data = request.get_json(silent=True) or {}

        jd_text = (data.get("text") or job.job_description or "").strip()
        if not jd_text:
            return {"error": "Job description text is required"}, 400

        ai_url = app.config.get("AI_SERVICE_URL", "http://ai-service:5002").rstrip("/")
        try:
            resp = requests.post(
                f"{ai_url}/agent/run",
                json={"text": jd_text},
                timeout=180
            )
            if resp.status_code != 200:
                return {"error": f"AI service error: {resp.text}"}, resp.status_code

            data_resp = resp.json()
            copilot_results = data_resp.get("copilot_results", {})

            # Update job record with AI insights
            job.job_description = jd_text
            if "match_data" in copilot_results and isinstance(copilot_results["match_data"], dict):
                job.match_score = copilot_results["match_data"].get("score")
            if "tailored_bullets" in copilot_results:
                raw_b = copilot_results["tailored_bullets"]
                job.tailored_bullets = [
                    b["bullet"] if isinstance(b, dict) and "bullet" in b else str(b)
                    for b in raw_b
                ]
            if "prep_questions" in copilot_results:
                job.prep_questions = copilot_results["prep_questions"]
            if "analysis" in copilot_results and isinstance(copilot_results["analysis"], dict):
                job.skills = copilot_results["analysis"].get("required_skills", [])

            db.session.commit()
            return {
                "job": job.to_dict(),
                "copilot_results": copilot_results
            }, 200
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to connect to AI service: {str(e)}"}, 503

    @app.post("/resume/upload")
    @jwt_required()
    def proxy_resume_upload():
        if "file" not in request.files:
            return {"error": "file field is required in multipart/form-data"}, 400
        file = request.files["file"]
        if file.filename == "":
            return {"error": "No file selected"}, 400

        ai_url = app.config.get("AI_SERVICE_URL", "http://ai-service:5002").rstrip("/")
        try:
            files = {"file": (file.filename, file.stream.read(), file.mimetype or "application/pdf")}
            resp = requests.post(f"{ai_url}/resume/upload", files=files, timeout=60)
            return resp.json(), resp.status_code
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to connect to AI service: {str(e)}"}, 503

    @app.post("/resume/index")
    @jwt_required()
    def proxy_resume_index():
        if "file" in request.files:
            return proxy_resume_upload()

        data = request.get_json(silent=True) or {}
        text_content = data.get("text", "").strip()
        if not text_content:
            return {"error": "file or text is required"}, 400

        ai_url = app.config.get("AI_SERVICE_URL", "http://ai-service:5002").rstrip("/")
        try:
            resp = requests.post(f"{ai_url}/resume/index", json={"text": text_content}, timeout=60)
            return resp.json(), resp.status_code
        except requests.exceptions.RequestException as e:
            return {"error": f"Failed to connect to AI service: {str(e)}"}, 503

    @app.get("/resume/status")
    @jwt_required()
    def proxy_resume_status():
        ai_url = app.config.get("AI_SERVICE_URL", "http://ai-service:5002").rstrip("/")
        try:
            resp = requests.get(f"{ai_url}/resume/status", timeout=10)
            return resp.json(), resp.status_code
        except requests.exceptions.RequestException:
            return {"indexed": False, "chunk_count": 0, "available": False}, 200

    return app
