import json
import time
import re
import ollama
from pydantic import BaseModel, ValidationError
from typing import Optional

class JDAnalysis(BaseModel):
    title: str
    seniority: str
    required_skills: list[str]
    nice_to_have: list[str]
    keywords: list[str]

class SkillMatch(BaseModel):
    skill: str
    status: str
    source_chunk_id: Optional[str]
    reasoning: str

class MatchResponse(BaseModel):
    score: int
    matches: list[SkillMatch]

class TailoredBullet(BaseModel):
    bullet: str
    source_chunk_id: str

class TailorResponse(BaseModel):
    bullets: list[TailoredBullet]

class PrepResponse(BaseModel):
    questions: list[str]

def analyze_jd(jd_text: str, retries=2) -> dict:
    prompt = f"""Analyze the following job description. Return ONLY valid JSON matching this exact structure:
    {{
        "title": "Extracted Job Title",
        "seniority": "Entry/Mid/Senior/Lead",
        "required_skills": ["skill1", "skill2"],
        "nice_to_have": ["skill3"],
        "keywords": ["keyword1"]
    }}
    Job Description:
    {jd_text}
    """
    for attempt in range(retries):
        try:
            response = ollama.chat(
                model='llama3.2',
                messages=[{'role': 'user', 'content': prompt}],
                format='json'
            )
            raw_text = response['message']['content'].strip()
            data = json.loads(raw_text)
            validated = JDAnalysis(**data)
            return validated.model_dump()
        except (json.JSONDecodeError, ValidationError) as e:
            if attempt == retries - 1:
                raise Exception(f"LLM failed to return valid schema: {e}")
            time.sleep(1)

def evaluate_match(skills: list[str], chunks: list[dict], retries=2) -> dict:
    prompt = f"""Evaluate if the candidate possesses the following required skills based ONLY on the provided resume chunks.
    For each skill, label as 'covered', 'partial', or 'missing'.
    If covered or partial, you MUST provide the exact 'source_chunk_id' from the chunks.
    Calculate a matching score from 0-100 based on coverage.
    Return ONLY valid JSON matching this structure: {{"score": 85, "matches": [{{"skill": "str", "status": "str", "source_chunk_id": "str", "reasoning": "str"}}]}}

    Required Skills: {skills}
    Resume Chunks: {json.dumps(chunks)}
    """
    for attempt in range(retries):
        try:
            response = ollama.chat(
                model='llama3.2',
                messages=[{'role': 'user', 'content': prompt}],
                format='json'
            )
            raw_text = response['message']['content'].strip()
            return MatchResponse(**json.loads(raw_text)).model_dump()
        except Exception as e:
            if attempt == retries - 1: raise Exception(f"Match Failed: {e}")
            time.sleep(1)

def generate_bullets(jd_text: str, chunks: list[dict], retries=2) -> dict:
    prompt = f"""Draft 3 tailored resume bullet points for this job description using ONLY the provided resume chunks.
    Each bullet MUST cite the exact 'source_chunk_id' it was derived from. Do not invent information.
    Return ONLY valid JSON matching this structure: {{"bullets": [{{"bullet": "str", "source_chunk_id": "str"}}]}}

    Job Description: {jd_text}
    Resume Chunks: {json.dumps(chunks)}
    """
    for attempt in range(retries):
        try:
            response = ollama.chat(
                model='llama3.2',
                messages=[{'role': 'user', 'content': prompt}],
                format='json'
            )
            raw_text = response['message']['content'].strip()
            return TailorResponse(**json.loads(raw_text)).model_dump()
        except Exception as e:
            if attempt == retries - 1: raise Exception(f"Tailor failed: {e}")
            time.sleep(1)

def generate_prep_questions(skills: list[str], retries=2) -> list[str]:
    skills_str = ", ".join(skills) if skills else "general software engineering"
    prompt = f"""Generate exactly 3 focused, technical interview questions to test a candidate on these skills: {skills_str}.
Return ONLY valid JSON matching this exact structure:
{{
    "questions": [
        "First question here?",
        "Second question here?",
        "Third question here?"
    ]
}}
Do NOT include any conversational filler, introductory sentences, assessment criteria, bullet points, or notes. Return ONLY the JSON object.
"""
    for attempt in range(retries):
        try:
            response = ollama.chat(
                model='llama3.2',
                messages=[{'role': 'user', 'content': prompt}],
                format='json'
            )
            raw_text = response['message']['content'].strip()
            data = json.loads(raw_text)
            validated = PrepResponse(**data)
            cleaned = []
            for q in validated.questions:
                if isinstance(q, str):
                    q_clean = re.sub(r'^(?:Question\s*\d*[:.-]?|\d+[\.\)])\s*', '', q.strip())
                    if q_clean and len(q_clean) > 10:
                        cleaned.append(q_clean)
            if cleaned:
                return cleaned[:3]
        except Exception as e:
            if attempt == retries - 1:
                print(f"Prep generation warning: {e}")
            time.sleep(1)
    return []
