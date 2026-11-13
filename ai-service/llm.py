
import json
import os
import re
import time

from groq import Groq
from pydantic import BaseModel, ValidationError
from typing import Optional


# Groq configuration
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

MODEL = os.environ.get(
    "GROQ_MODEL",
    "llama-3.3-70b-versatile"
)


# Response schemas
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


# Shared Groq JSON generation function
def generate_json(prompt: str) -> dict:
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "Return only valid JSON. Do not include Markdown."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
        max_completion_tokens=2500
    )

    content = response.choices[0].message.content
    return json.loads(content)


def run_with_retries(prompt: str, retries: int = 2) -> dict:
    last_error = None

    for attempt in range(retries):
        try:
            return generate_json(prompt)
        except Exception as error:
            last_error = error
            if attempt < retries - 1:
                time.sleep(2)

    raise Exception(f"Groq generation failed: {last_error}")


def analyze_jd(jd_text: str, retries=2) -> dict:
    prompt = f"""
Analyze the following job description.

Return JSON with this exact structure:
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

    data = run_with_retries(prompt, retries)
    return JDAnalysis(**data).model_dump()



def evaluate_match(
    skills: list[str],
    chunks: list[dict],
    retries=2
) -> dict:

    prompt = f"""
Evaluate the candidate's skills using ONLY the supplied resume evidence.

For EVERY required skill, return exactly one assessment.

Use these statuses:
- covered: Explicitly demonstrated in the resume.
- partial: Related experience or indirect evidence exists.
- missing: No supporting evidence exists.

Rules:
1. Never assume a skill merely because another related skill is present.
2. Do not invent experience, certifications or projects.
3. Every covered or partial assessment must cite an exact source_chunk_id.
4. Use null for source_chunk_id when status is missing.
5. Assess skills individually.

Return JSON in this format:
{{
    "matches": [
        {{
            "skill": "Python",
            "status": "covered",
            "source_chunk_id": "chunk - 0",
            "reasoning": "Python is explicitly listed in technical skills."
        }}
    ]
}}

Required Skills:
{json.dumps(skills)}

Complete Resume Chunks:
{json.dumps(chunks)}
"""

    data = run_with_retries(prompt, retries)

    valid_chunk_ids = {
        chunk["id"] for chunk in chunks
    }

    raw_matches = data.get("matches", [])

    match_lookup = {
        str(item.get("skill", "")).strip().lower(): item
        for item in raw_matches
        if isinstance(item, dict)
    }

    validated_matches = []

    for skill in skills:
        item = match_lookup.get(skill.strip().lower(), {})

        status = str(item.get("status", "missing")).lower()
        source_id = item.get("source_chunk_id")
        reasoning = item.get("reasoning", "No supporting evidence found.")

        if status not in ["covered", "partial", "missing"]:
            status = "missing"

        if status in ["covered", "partial"]:
            if source_id not in valid_chunk_ids:
                status = "missing"
                source_id = None
                reasoning = "No valid resume evidence citation was provided."
        else:
            source_id = None

        validated_matches.append({
            "skill": skill,
            "status": status,
            "source_chunk_id": source_id,
            "reasoning": reasoning
        })

    points = {
        "covered": 1.0,
        "partial": 0.5,
        "missing": 0.0
    }

    total_points = sum(
        points[item["status"]]
        for item in validated_matches
    )

    score = round(
        (total_points / len(skills)) * 100
    ) if skills else 0

    return {
        "score": score,
        "matches": validated_matches
    }

def generate_bullets(
    jd_text: str,
    chunks: list[dict],
    retries=2
) -> dict:
    prompt = f"""
Draft 3 tailored resume bullet points for this job description
using ONLY the provided resume chunks.

Each bullet must cite the exact source_chunk_id.
Do not invent candidate experience or skills.

Return JSON:
{{
    "bullets": [
        {{
            "bullet": "Example achievement",
            "source_chunk_id": "chunk - 0"
        }}
    ]
}}

Job Description:
{jd_text}

Resume Chunks:
{json.dumps(chunks)}
"""

    data = run_with_retries(prompt, retries)
    return TailorResponse(**data).model_dump()


def generate_prep_questions(
    skills: list[str],
    retries=2
) -> list[str]:
    skills_str = (
        ", ".join(skills)
        if skills
        else "general software engineering"
    )

    prompt = f"""
Generate exactly 3 focused technical interview questions
to test a candidate on these skills:

{skills_str}

Return JSON:
{{
    "questions": [
        "First question?",
        "Second question?",
        "Third question?"
    ]
}}

Do not include introductions, explanations, or assessment criteria.
"""

    try:
        data = run_with_retries(prompt, retries)
        validated = PrepResponse(**data)

        cleaned = [
            re.sub(
                r"^(?:Question\s*\d*[:.-]?|\d+[\.\)])\s*",
                "",
                q.strip()
            )
            for q in validated.questions
            if isinstance(q, str)
        ]

        return [q for q in cleaned if len(q) > 10][:3]

    except Exception as error:
        print(f"Interview question generation failed: {error}")
        return []
