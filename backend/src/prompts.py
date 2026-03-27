from __future__ import annotations


def get_skill_extraction_prompt(text: str, mode: str) -> str:
    """
    mode:
      - "resume": extract candidate skills (no proficiency/years in output)
      - "jd": extract required skills (no required_level/importance in output)
    """
    if mode not in {"resume", "jd"}:
        raise ValueError("mode must be 'resume' or 'jd'")

    if mode == "resume":
        return f"""You are an expert HR skill analyzer.

Extract ALL technical and professional skills from the text below.

For each skill extract:
- skill_name

Rules:
- Do not hallucinate.
- Normalize skill names (e.g., "Python Programming" -> "Python").
- You MAY infer certain professional skills ONLY when there are strong, explicit signals in the resume.
  - Add an inferred skill only if you can point to a concrete indicator in the text (link, activity, achievement, role, keyword).
  - Do NOT infer based on generic job titles alone.
  - Examples of allowed inference signals:
    - If LeetCode / Codeforces / "DSA" / "data structures" / "competitive programming" / "math olympiad" is mentioned -> include "Problem Solving".
    - If "debate" / "public speaking" / "toastmasters" is mentioned -> include "Communication".
    - If "team lead" / "captain" / "club secretary" / "organized event" is mentioned -> include "Leadership".
    - If "hackathon" / "built X in 24/48 hours" -> include "Rapid Prototyping".
    - If "internship" / "project collaboration" / "cross-functional" -> include "Collaboration".
- Return ONLY valid JSON.

Output Format:
{{
  "skills": [
    {{
      "skill_name": "Python",
    }}
  ]
}}

Text:
{text}
"""

    # mode == "jd"
    return f"""You are an expert job requirement analyzer.

Extract ALL required skills from the job description.

For each skill extract:
- skill_name

Rules:
- Extract only explicitly required skills.
- Ignore soft skills unless clearly stated.
- Normalize skill names.
- Return ONLY valid JSON.

Output Format:
{{
  "skills": [
    {{
      "skill_name": "Python",
    }}
  ]
}}

Text:
{text}
"""

