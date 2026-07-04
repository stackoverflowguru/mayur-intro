from flask import Flask, render_template_string, request
import re

app = Flask(__name__)

required_skills = [
    "python",
    "numpy",
    "pandas",
    "sql",
    "machine learning",
    "data analysis",
    "excel",
    "communication"
]

resume_sections = {
    "education": r"\beducation\b",
    "experience": r"\bexperience\b",
    "projects": r"\bprojects\b|\bproject\b",
    "skills": r"\bskills\b|\bskill\b",
    "certifications": r"\bcertifications\b|\bcertificate\b",
    "summary": r"\bsummary\b|\bobjective\b"
}

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Resume Analyzer</title>
    <style>
        :root {
            font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            color-scheme: dark;
            color: #e2e8f0;
            background: #090b14;
        }
        body {
            margin: 0;
            min-height: 100vh;
            background: radial-gradient(circle at top, rgba(56, 189, 248, 0.12), transparent 18%),
                        linear-gradient(180deg, #020617 0%, #090b14 100%);
            color: #e2e8f0;
        }
        .container {
            max-width: 960px;
            margin: 0 auto;
            padding: 2rem 1.5rem 3rem;
        }
        .card {
            background: rgba(15, 23, 42, 0.92);
            border: 1px solid rgba(148, 163, 184, 0.18);
            border-radius: 28px;
            padding: 1.75rem;
            backdrop-filter: blur(18px);
            box-shadow: 0 24px 56px rgba(0, 0, 0, 0.28);
        }
        h1, h2 {
            margin: 0 0 1rem;
            font-weight: 700;
        }
        p {
            margin: 0 0 1rem;
            color: #94a3b8;
            line-height: 1.75;
        }
        textarea {
            width: 100%;
            min-height: 220px;
            padding: 1rem;
            border-radius: 18px;
            border: 1px solid rgba(148, 163, 184, 0.16);
            background: rgba(15, 23, 42, 0.9);
            color: #e2e8f0;
            resize: vertical;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
            font-size: 0.98rem;
        }
        button {
            border: none;
            border-radius: 16px;
            padding: 0.95rem 1.5rem;
            background: linear-gradient(135deg, #38bdf8, #6366f1);
            color: white;
            cursor: pointer;
            font-size: 1rem;
            font-weight: 600;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        button:hover {
            transform: translateY(-1px);
            box-shadow: 0 16px 32px rgba(56, 189, 248, 0.28);
        }
        .result {
            margin-top: 1.75rem;
            display: grid;
            gap: 1rem;
        }
        .result-summary,
        .result-skill-list,
        .result-section {
            background: rgba(15, 23, 42, 0.95);
            border: 1px solid rgba(148, 163, 184, 0.14);
            border-radius: 22px;
            padding: 1.35rem;
        }
        .badges {
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            margin-top: 0.75rem;
        }
        .badge {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.65rem 0.9rem;
            border-radius: 999px;
            background: rgba(56, 189, 248, 0.12);
            color: #cbd5e1;
            border: 1px solid rgba(56, 189, 248, 0.22);
            font-size: 0.95rem;
            font-weight: 600;
        }
        .skill-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 0.85rem;
        }
        .skill-box {
            padding: 0.85rem 1rem;
            border-radius: 18px;
            border: 1px solid rgba(148, 163, 184, 0.14);
            background: rgba(15, 23, 42, 0.98);
        }
        .skill-box.match {
            border-color: #22c55e;
            background: rgba(34, 197, 94, 0.08);
        }
        .skill-box.no-match {
            border-color: #ef4444;
            background: rgba(239, 68, 68, 0.1);
        }
        .recommendation {
            margin-top: 0.5rem;
            padding: 1rem;
            border-radius: 18px;
            background: rgba(63, 63, 70, 0.9);
            color: #f8fafc;
        }
        .status-pill {
            display: inline-flex;
            align-items: center;
            padding: 0.45rem 0.75rem;
            border-radius: 999px;
            font-weight: 700;
        }
        .status-pill.good { background: #16a34a; }
        .status-pill.okay { background: #f59e0b; }
        .status-pill.needs { background: #dc2626; }
        @media (max-width: 720px) {
            .container { padding: 1.25rem; }
            .hero { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h1>Resume Analyzer</h1>
            <p>Paste resume text below and get a quick skill match score, missing skills, and section coverage feedback.</p>
            <form method="post">
                <textarea name="resume_text" placeholder="Paste your resume text here...">{{ resume_text }}</textarea>
                <button type="submit">Analyze Resume</button>
            </form>
        </div>

        {% if result %}
            <div class="result">
                <div class="result-summary card">
                    <h2>Summary</h2>
                    <p><strong>Score:</strong> {{ result.percentage }}%</p>
                    <p><strong>Matched:</strong> {{ result.matched }} / {{ result.total }} required skills</p>
                    <p><strong>Experience detected:</strong> {{ result.experience_years }} years</p>
                    <div class="badges">
                        {% for section in result.sections %}
                            <span class="badge">{{ section }}</span>
                        {% endfor %}
                    </div>
                    <div class="recommendation">
                        <strong>Recommendation:</strong> {{ result.recommendation }}
                    </div>
                </div>

                <div class="result-section card">
                    <h2>Skill Match</h2>
                    <div class="skill-grid">
                        {% for skill in result.skills %}
                            <div class="skill-box {{ 'match' if skill[1] else 'no-match' }}">
                                {{ skill[0] }}
                            </div>
                        {% endfor %}
                    </div>
                </div>

                <div class="result-section card">
                    <h2>Missing Skills</h2>
                    {% if result.missing_skills %}
                        <div class="badges">
                            {% for missing in result.missing_skills %}
                                <span class="badge">{{ missing }}</span>
                            {% endfor %}
                        </div>
                    {% else %}
                        <p>Excellent! All required skills are present in the resume.</p>
                    {% endif %}
                </div>
            </div>
        {% endif %}
    </div>
</body>
</html>
"""


def analyze_resume(text: str):
    normalized = text.lower()
    skill_status = []

    for skill in required_skills:
        found = bool(re.search(r"\b" + re.escape(skill) + r"\b", normalized))
        skill_status.append((skill.title(), found))

    matched = sum(1 for _, matched in skill_status if matched)
    total = len(required_skills)
    percentage = round((matched / total) * 100, 2) if total else 0.0

    missing_skills = [skill for skill, matched in skill_status if not matched]
    experience_years = extract_experience_years(normalized)
    sections = [name.title() for name, pattern in resume_sections.items() if re.search(pattern, normalized)]

    recommendation = generate_recommendation(percentage, sections)

    return {
        "skills": skill_status,
        "matched": matched,
        "total": total,
        "percentage": percentage,
        "missing_skills": missing_skills,
        "experience_years": experience_years,
        "sections": sections or ["No section headings found"],
        "recommendation": recommendation,
    }


def extract_experience_years(text: str) -> int:
    matches = re.findall(r"(\d+)\s*(?:\+|\-|to|\s)?\s*(?:years|yrs|year)", text)
    years = [int(value) for value in matches if value.isdigit()]
    return max(years) if years else 0


def generate_recommendation(score: float, sections: list[str]) -> str:
    if score >= 80:
        base = "Your resume already matches the required skill set strongly."
        detail = "Focus on clear project and experience descriptions to keep it strong."
    elif score >= 60:
        base = "Good skill coverage, but there is room to improve."
        detail = "Add any missing technical terms and stronger section headings."
    elif score >= 40:
        base = "Your resume has some key skills, but it needs more polish."
        detail = "Include more examples of relevant tools and projects."
    else:
        base = "The resume is missing several required skills."
        detail = "Highlight technical experience and update the skills section."

    if "Skills" not in sections:
        detail += " Make sure the resume includes a dedicated Skills section."

    return f"{base} {detail}"


@app.route("/", methods=["GET", "POST"])
def index():
    resume_text = ""
    result = None

    if request.method == "POST":
        resume_text = request.form.get("resume_text", "")
        result = analyze_resume(resume_text)

    return render_template_string(PAGE_TEMPLATE, resume_text=resume_text, result=result)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)