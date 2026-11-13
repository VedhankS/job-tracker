
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
Evaluate whether the candidate possesses the following skills
based ONLY on the provided resume chunks.

For each skill, use status: covered, partial, or missing.

If covered or partial, provide the exact source_chunk_id.
Do not invent evidence.

Return JSON:
{{
    "score": 85,
    "matches": [
        {{
            "skill": "Python",
            "status": "covered",
            "source_chunk_id": "chunk - 0",
            "reasoning": "Evidence from the resume"
        }}
    ]
}}

Required Skills:
{json.dumps(skills)}

Resume Chunks:
{json.dumps(chunks)}
"""

    data = run_with_retries(prompt, retries)
    return MatchResponse(**data).model_dump()


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
