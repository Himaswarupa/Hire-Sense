import json
import re
from .data_preprocessing import clean_text, safe_parse_list


STOP_SKILLS = {"mis", "pr", "os", "bi", "it", "hr", "cs"}

def valid_skill_match(skill, text):
    skill = skill.lower()

    if skill in STOP_SKILLS:
        return False

    if len(skill) <= 2:
        return False

    pattern = r'\b' + re.escape(skill) + r'\b'
    return re.search(pattern, text)


class ATSScorer:

    def __init__(self, industry_path=None):

        if industry_path:
            with open(industry_path, "r") as f:
                self.industry_skills = json.load(f)
        else:
            self.industry_skills = {}

        self.common_skills = {
            "python", "java", "sql", "machine learning", "data science",
            "django", "flask", "tensorflow", "pandas", "numpy",
            "react", "node", "mongodb", "aws", "docker"
        }


    def get_feedback(self, ats_score):

        if ats_score < 50:
            return {
                "level": "Poor",
                "suggestions": [
                    "Add more relevant technical skills.",
                    "Include at least 1–2 strong projects.",
                    "Use proper keywords from job roles.",
                    "Improve resume formatting (clear sections).",
                    "Avoid generic descriptions, be specific."
                ]
            }

        elif ats_score < 70:
            return {
                "level": "Average",
                "suggestions": [
                    "Add more industry-relevant keywords.",
                    "Include measurable achievements (e.g., improved accuracy by 20%).",
                    "Strengthen project descriptions with tech stack.",
                    "Add certifications or tools (AWS, Docker, etc.).",
                    "Improve experience section clarity."
                ]
            }

        else:
            return {
                "level": "Good",
                "suggestions": [
                    "Resume is strong. Fine-tune based on specific job descriptions.",
                    "Optimize keywords for each application.",
                    "Keep updating projects and skills.",
                    "Ensure formatting is ATS-friendly."
                ]
            }

    def score_resume(self, resume, industry):

        full_text = clean_text(
            str(resume.get("education", "")) + " " +
            str(resume.get("experience", "")) + " " +
            str(resume.get("projects", "")) + " " +
            str(resume.get("skills", ""))
        )

        words = full_text.split()

        resume_skills = set(
            clean_text(skill) for skill in safe_parse_list(resume.get("skills", []))
        )

        industry_required = set(self.industry_skills.get(industry, []))

        industry_matches = [
            s for s in resume_skills
            if any(s in ind or ind in s for ind in industry_required)
        ]

        industry_score = min(len(industry_matches) / 10, 1.0)

        matched_common = [s for s in self.common_skills if s in full_text]

        exp_matches = re.findall(r'(\d+)\s+year', full_text)
        exp_years = sum(int(x) for x in exp_matches) if exp_matches else 0

        edu_score = 1 if any(x in full_text for x in ["b tech", "bachelor", "master"]) else 0
        cert_score = 1 if "certification" in full_text else 0
        project_score = 1 if resume.get("projects") else 0

        word_score = min(len(words) / 600, 1.0)
        diversity_score = min(len(set(words)) / 350, 1.0)

        if len(resume_skills) < 5:
            skill_score = 0.2
        else:
            skill_score = min(len(resume_skills) / 25, 1.0)

        common_skill_score = min(len(matched_common) / 8, 1.0)

        if exp_years == 0:
            exp_score = 0
        elif exp_years < 2:
            exp_score = 0.4
        elif exp_years < 5:
            exp_score = 0.7
        else:
            exp_score = 1.0

        section_score = (
            0.4 * edu_score +
            0.3 * project_score +
            0.3 * (1 if len(resume_skills) > 0 else 0)
        )

        ats_raw = (
            0.12 * word_score +
            0.10 * diversity_score +
            0.12 * skill_score +
            0.10 * common_skill_score +
            0.15 * exp_score +
            0.08 * section_score +
            0.05 * cert_score +
            0.28 * industry_score
        )

        score = round(ats_raw * 100, 2)

        feedback = self.get_feedback(score)

        return {
            "ats_score": score,
            "level": feedback["level"],
            "suggestions": feedback["suggestions"],
            "features": {
                "skill_score": round(skill_score, 3),
                "industry_score": round(industry_score, 3),
                "exp_score": round(exp_score, 3)

            }
        }


    def extract_jd_skills(self, job):

        jd_text = clean_text(
            str(job.get("description", "")) + " " +
            str(job.get("skills_desc", ""))
        )

        skills = set()

        for skill_list in self.industry_skills.values():
            for skill in skill_list:
                if valid_skill_match(skill, jd_text):
                    skills.add(skill)

        for skill in self.common_skills:
            if valid_skill_match(skill, jd_text):
                skills.add(skill)

        return skills

    def score_jd_match(self, resume, job, industry):

        raw_skills = resume.get("skills") or []
        parsed_skills = safe_parse_list(raw_skills)

        resume_skills = set(clean_text(skill) for skill in parsed_skills)

        jd_skills = self.extract_jd_skills(job)

        if not jd_skills:
            return {
                "jd_score": 0,
                "matched": [],
                "missing": [],
                "error": "No JD skills extracted"
            }

        # improved matching
        overlap = set()
        for r in resume_skills:
            for j in jd_skills:
                if r in j or j in r:
                    overlap.add(j)

        industry_required = set(self.industry_skills.get(industry, []))

        required = overlap & industry_required
        optional = overlap - required

        if len(jd_skills) < 3:
            score = len(overlap) / (len(jd_skills) + 1e-5) * 0.6
        else:
             score = len(overlap) / (len(jd_skills) + 1e-5)

        return {
            "jd_score": round(min(score * 100, 100), 2),
            "matched": list(overlap),
            "missing": list(jd_skills - overlap)
     }