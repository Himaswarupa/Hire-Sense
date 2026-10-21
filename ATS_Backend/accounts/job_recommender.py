import os
import pickle
import json
import re
from sklearn.metrics.pairwise import cosine_similarity

from .data_preprocessing import load_postings_data, clean_text
from .ats_scorer import ATSScorer, valid_skill_match

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "ml_model")

_GLOBAL_RECOMMENDER = None

def extract_resume_entities(resume_text):

    industry_path = os.path.join(MODEL_DIR, "industry_skills.json")

    with open(industry_path, "r") as f:
        industry_skills = json.load(f)

    text = clean_text(resume_text)

    found_skills = set()

    for skill_list in industry_skills.values():
        for skill in skill_list:
            if valid_skill_match(skill, text):
                found_skills.add(skill)

    scores = {
        ind: sum(1 for s in skills if valid_skill_match(s, text))
        for ind, skills in industry_skills.items()
    }

    industry = max(scores, key=scores.get)

    return {
        "skills": list(found_skills),
        "industry": industry,
        "education": resume_text,
        "experience": resume_text,
        "projects": resume_text
    }


class JobRecommender:

    def __init__(self, postings_csv):

        self.postings_df = load_postings_data(postings_csv)

        self.industry_path = os.path.join(MODEL_DIR, "industry_skills.json")
        self.scorer = ATSScorer(self.industry_path)

        with open(os.path.join(MODEL_DIR, "vectorizer.pkl"), "rb") as f:
            self.vectorizer = pickle.load(f)

        with open(os.path.join(MODEL_DIR, "job_tfidf.pkl"), "rb") as f:
            self.job_tfidf = pickle.load(f)

    def recommend_jobs(self, resume, top_n=5):

        resume_text = " ".join(resume["skills"])
        resume_vec = self.vectorizer.transform([clean_text(resume_text)])

        limited_df = self.postings_df.head(50)
        limited_tfidf = self.job_tfidf[:50]
        sim_scores = cosine_similarity(resume_vec, limited_tfidf).flatten()

        industry = resume.get("industry", "IT")
        ats_score = self.scorer.score_resume(resume, industry)["ats_score"]

        results = []

        for i, (_, job) in enumerate(limited_df.iterrows()):

            job_dict = {
                "description": job["description"],
                "skills_desc": job["skills_desc"]
            }

            jd_result = self.scorer.score_jd_match(
                resume, job_dict, industry
            )

            jd_score = jd_result["jd_score"]
            sim_score = sim_scores[i]

            final = (
                0.5 * sim_score +
                0.3 * (jd_score / 100) +
                0.2 * (ats_score / 100)
            )

            results.append({
                "title": job["title"],
                "company": job["company_name"],
                "description": job["description"],
                "skills": job["skills_desc"],
                "final_score": round(final, 3),
                "ats_score": ats_score,
                "jd_score": jd_score,
                "matched": jd_result["matched"],
                "missing": jd_result["missing"]
            })

        return sorted(results, key=lambda x: x["final_score"], reverse=True)[:top_n]


def get_job_recommendations(resume_text):
    global _GLOBAL_RECOMMENDER
    
    if _GLOBAL_RECOMMENDER is None:
        csv_path = os.path.join(MODEL_DIR, "postings.csv")
        _GLOBAL_RECOMMENDER = JobRecommender(postings_csv=csv_path)

    resume = extract_resume_entities(resume_text)
    return _GLOBAL_RECOMMENDER.recommend_jobs(resume)