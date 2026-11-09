from flask import Flask, request
from flask_cors import CORS
import rag
import llm
import agent
import traceback
import io

try:
    import pypdf
except ImportError:
    pypdf = None

def extract_text_from_pdf(stream) -> str:
    if pypdf is None:
        raise RuntimeError("pypdf is not installed. Please install pypdf to process PDF files.")
    reader = pypdf.PdfReader(stream)
    pages_text = []
    for page in reader.pages:
        t = page.extract_text()
        if t and t.strip():
            pages_text.append(t.strip())
    return "\n\n".join(pages_text)

app = Flask(__name__)
CORS(app)

@app.get("/health")
def health():
    return {"status":"ok"}

@app.get("/resume/status")
def resume_status():
    try:
        count = rag.collection.count()
        return {"indexed": count > 0, "chunk_count": count, "available": True}
    except Exception as e:
        return {"indexed": False, "chunk_count": 0, "available": False, "error": str(e)}

@app.post("/resume/upload")
def resume_upload():
    if "file" not in request.files:
        return {"error": "file field is required in multipart/form-data"}, 400
    file = request.files["file"]
    if not file or file.filename == "":
        return {"error": "no file selected"}, 400

    filename = file.filename.lower()
    try:
        if filename.endswith(".pdf"):
            text = extract_text_from_pdf(file.stream)
        elif filename.endswith(".txt"):
            text = file.read().decode("utf-8", errors="ignore")
        else:
            return {"error": "Only .pdf and .txt files are supported"}, 400

        if not text.strip():
            return {
                "error": "Could not extract readable text from PDF. The file may be a scanned image without selectable text."
            }, 400

        count = rag.index_resume(text)
        return {
            "chunks_indexed": count,
            "filename": file.filename,
            "char_count": len(text)
        }, 201
    except Exception as e:
        traceback.print_exc()
        return {"error": f"Failed to process file: {str(e)}"}, 500

@app.post("/resume/index")
def resume_index():
    if "file" in request.files:
        return resume_upload()
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    if not text:
        return {"error": "file or text is required"}, 400
    return {"chunks_indexed": rag.index_resume(text)}, 201

@app.post("/search")
def search():
    data = request.get_json(silent=True) or {}
    query = data.get("query", "").strip()
    if not query:
        return {"error":"query is required"}, 400
    return {"results":rag.search(query)}

@app.post("/jd/analyze")
def analyze_id():
    data = request.get_json(silent=True) or {}
    jd_text = data.get("text","").strip()
    if not jd_text:
        return {"error":"text is required"}, 400
    try:
        analysis = llm.analyze_jd(jd_text)
        return{"analysis":analysis}
    except Exception as e:
        return {"error":str(e)}, 500
@app.post("/match")
def match_resume():
    data=request.get_json(silent = True) or {}
    jd_text = data.get("text","").strip()
    if not jd_text: return {"error":"text required"}, 400

    try:
        jd_analysis = llm.analyze_jd(jd_text)
        skills = jd_analysis.get("required_skills",[])
        chunk_dict={}
        for skill in skills:
            for res in rag.search(skill, k = 2):
                chunk_dict[res["id"]] = {"id":res["id"],"text":res["text"]}
        match_results = llm.evaluate_match(skills, list(chunk_dict.values()))
        return  {"jd_analysis":jd_analysis,"match":match_results}
    except Exception as e:
        return {"error":str(e)},500

@app.post("/tailor")
def tailor_resume():
    data = request.get_json(silent=True) or {}
    jd_text = data.get("text", "").strip()
    if not jd_text: return {"error": "text required"}, 400

    try:
        # 1. Broad retrieval using JD skills & keywords
        jd_analysis = llm.analyze_jd(jd_text)

        keywords = jd_analysis.get("keywords") or []
        skills = jd_analysis.get("required_skills") or []
        query = " ".join(keywords + skills)

        if not query.strip():
            query = "machine learning artificial intelligence"

        retrieved = rag.search(query, k=5)
        chunks = [{"id": r["id"], "text": r["text"]} for r in retrieved]
        valid_ids = {c["id"] for c in chunks}

        # 2. Generate bullets
        tailor_results = llm.generate_bullets(jd_text, chunks)

        bullets = tailor_results.get("bullets") or []
        valid_bullets = [b for b in bullets if b.get("source_chunk_id") in valid_ids]

        return {
            "bullets": valid_bullets,
            "discarded_hallucinations": len(bullets) - len(valid_bullets)
        }
    except Exception as e:
        return {"error": str(e)}, 500

@app.post("/agent/run")
def trigger_agent():
    data = request.get_json(silent=True) or {}
    jd_text = data.get("text", "").strip()
    if not jd_text:
        return {"error":"text required"}, 400

    try :
        result = agent.run_agent(jd_text)
        result.pop("jd_text", None)
        return{"copilot_results":result}
    except Exception as e:
        traceback.print_exc()
        return {"error":str(e)}, 500
