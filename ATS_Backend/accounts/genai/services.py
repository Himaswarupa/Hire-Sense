from dotenv import load_dotenv
import os
import re
import json

load_dotenv()

from groq import Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


class AIResumeParser:
    @staticmethod
    def parse_to_json(resume_text):
        try:
            prompt = f"""
Extract resume into JSON:
- personal_info (name, email, phone)
- education
- experience
- skills

Return ONLY valid JSON.

Resume:
{resume_text[:3000]}
"""

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}]
            )

            text = response.choices[0].message.content or ""
            match = re.search(r'\{[\s\S]*\}', text)

            if match:
                return json.loads(match.group())

            return {"error": "Invalid JSON"}

        except Exception as e:
            return {"error": f"Parser failed: {str(e)}"}


class ATSEmbeddingMatcher:
    @staticmethod
    def calculate_match(resume_text, job_description):
        try:
            from sentence_transformers import SentenceTransformer
            from sklearn.metrics.pairwise import cosine_similarity

            model = SentenceTransformer('all-MiniLM-L6-v2')
            emb = model.encode([resume_text, job_description])

            score = cosine_similarity([emb[0]], [emb[1]])[0][0]

            prompt = f"""
Compare resume and job description.
List 3 missing skills clearly.

Resume:
{resume_text[:1500]}

JD:
{job_description[:1500]}
"""

            gap = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}]
            ).choices[0].message.content

            return {
                "match_score_percentage": round(float(score) * 100, 2),
                "gap_analysis": gap
            }

        except Exception as e:
            return {
                "match_score_percentage": 0,
                "gap_analysis": str(e)
            }


class AIResumeGenerator:
    @staticmethod
    def generate_improved_resume(resume_text):
        try:
            prompt = f"""
You are an expert AI Resume Builder and ATS Optimizer.

Your task is to convert raw resume text into a COMPLETE, PROFESSIONAL, INDUSTRY-READY resume in STRICT HTML format.

You MUST IMPROVE, EXPAND, and COMPLETE the resume intelligently.

=================================================
CORE INTELLIGENCE RULES (VERY IMPORTANT)
=================================================

1. If any section is MISSING, you MUST CREATE it:
   - Professional Summary → ALWAYS generate (even if not present)
   - Experience → infer realistic internship/project-based experience if missing
   - Projects → create relevant projects based on skills and domain
   - Skills → expand with relevant industry-standard skills
   - Achievements → generate logical achievements if none exist

2. Do NOT leave empty sections under ANY condition.

3. You are allowed to ADD CONTENT (not just rewrite):
   - You may enhance weak sentences
   - You may improve formatting
   - You may infer missing professional details logically
   - You may expand short resumes into complete professional resumes

4. DO NOT fabricate personal identity details:
   - Never invent name, email, phone if not present
   - But you CAN enrich content sections

=================================================
OUTPUT FORMAT (STRICT HTML ONLY)
=================================================

<div class="resume">

<h1>Full Name</h1>
<p>Phone | Email | Links</p>

<h2>Professional Summary</h2>
<p>Generate a strong 3–5 line professional summary based on skills, projects, and experience.</p>

<h2>Experience</h2>
<ul>
<li>Include real OR inferred experience based on resume content</li>
</ul>

<h2>Education</h2>
<ul>
<li>Extract or infer education level appropriately</li>
</ul>

<h2>Technical Skills</h2>
<ul>
<li>Expand and normalize skills (add missing relevant tools/tech)</li>
</ul>

<h2>Projects</h2>
<ul>
<li>Create structured, realistic project descriptions based on skills/domain</li>
</ul>

<h2>Achievements</h2>
<ul>
<li>Generate logical achievements if not present</li>
</ul>

</div>

=================================================
STRICT RULES
=================================================

- ONLY HTML output
- NO markdown
- NO explanations
- NO extra text outside HTML
- ALWAYS make resume complete and professional
- ALWAYS improve weak resumes into strong ATS-friendly format

=================================================
Resume Input:
{resume_text[:3000]}
"""

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}]
            )

            html = response.choices[0].message.content or ""
            html = html.replace("```html", "").replace("```", "").strip()

            return {"resume_html": html}

        except Exception as e:
            return {"resume_html": f"<p>Error: {str(e)}</p>"}
