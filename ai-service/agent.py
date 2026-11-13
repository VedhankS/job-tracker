import llm
import rag
import re
from typing import TypedDict
from langgraph.graph import StateGraph, END

class GraphState(TypedDict):
    jd_text: str
    analysis: dict
    match_data: dict
    tailored_bullets: list
    prep_questions: list

def get_skills_safely(analysis_dict: dict) -> list:
    if not analysis_dict:
        return []
    # Fallback to catch LLM key hallucinations
    return analysis_dict.get("required_skills") or analysis_dict.get("skills") or []

def analyze_node(state: GraphState):
    print("Agent: Analyzing JD...")
    return {"analysis": llm.analyze_jd(state.get("jd_text", ""))}

def match_node(state: GraphState):
    print("Agent: Matching Skills against Resume...")

    skills = get_skills_safely(state.get("analysis", {}))

    if not skills:
        return {
            "match_data": {
                "score": 0,
                "matches": []
            }
        }
    chunks = rag.get_all_chunks()

    if not chunks:
        return {
            "match_data": {
                "score": 0,
                "matches": [
                    {
                        "skill": skill,
                        "status": "missing",
                        "source_chunk_id": None,
                        "reasoning": "No resume chunks found. Please upload and index your resume."
                    }
                    for skill in skills
                ]
            }
        }

    # Evaluate each required skill against the complete resume
    match_data = llm.evaluate_match(skills, chunks)

    return {"match_data": match_data}

def tailor_node(state: GraphState):
    print("Agent: Tailoring Bullets...")
    skills = get_skills_safely(state.get("analysis", {}))
    query = " ".join(skills) if skills else "machine learning"

    retrieved = rag.search(query, k=5)
    chunks = [{"id": r["id"], "text": r["text"]} for r in retrieved]
    if not chunks:
        return {"tailored_bullets": []}

    valid_ids = {c["id"] for c in chunks}

    # Safe extraction of bullets
    tailor_results = llm.generate_bullets(state.get("jd_text", ""), chunks) or {}
    raw_bullets = tailor_results.get("bullets") or []

    valid_bullets = [b for b in raw_bullets if isinstance(b, dict) and b.get("source_chunk_id") in valid_ids]
    return {"tailored_bullets": valid_bullets}

def extract_questions_from_raw_text(text: str) -> list[str]:
    lines = text.split('\n')
    questions = []
    current_q = []
    in_criteria = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        lower = stripped.lower()
        if lower.startswith('here are') or lower.startswith('note:'):
            continue
        if 'assessment criteria' in lower:
            in_criteria = True
            continue
        if re.match(r'^(?:\d+[\.\)]|\*\*\d+[\.\)]|\*\*Question\s*\d*|\d+\.\s*\*?\*?Question)', stripped, re.IGNORECASE):
            in_criteria = False
            if current_q:
                questions.append(' '.join(current_q).strip())
                current_q = []
            clean = re.sub(r'^(?:\d+[\.\)]\s*\*?\*?Question\s*[:.-]?\s*\*?\*?|\d+[\.\)]|\*\*Question\s*[:.-]?\s*\*?\*?)\s*', '', stripped, flags=re.IGNORECASE)
            current_q.append(clean)
        elif not in_criteria and current_q:
            if not stripped.startswith('*') and not stripped.startswith('-'):
                current_q.append(stripped)

    if current_q:
        questions.append(' '.join(current_q).strip())
    return [q for q in questions if len(q) > 10][:3]


def prep_node(state: GraphState):
    print("Agent: Generating Interview Questions...")

    match_data = state.get("match_data") or {}
    matches = match_data.get("matches") or []

    missing = [
        m.get("skill")
        for m in matches
        if isinstance(m, dict)
        and m.get("status") == "missing"
        and m.get("skill")
    ]

    questions = llm.generate_prep_questions(missing)

    return {"prep_questions": questions}


workflow = StateGraph(GraphState)
workflow.add_node("analyze", analyze_node)
workflow.add_node("match", match_node)
workflow.add_node("tailor", tailor_node)
workflow.add_node("prep", prep_node)

workflow.set_entry_point("analyze")
workflow.add_edge("analyze", "match")
workflow.add_edge("match", "tailor")
workflow.add_edge("tailor", "prep")
workflow.add_edge("prep", END)

agent_app = workflow.compile()

def run_agent(jd_text: str):
    return agent_app.invoke({"jd_text": jd_text})
