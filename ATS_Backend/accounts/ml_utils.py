import os
import pandas as pd
import joblib
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

skills = [
    "python","java","sql","machine learning",
    "data science","django","flask",
    "tensorflow","pandas","numpy"
]

def load_models():
    classifier = joblib.load(os.path.join(BASE_DIR, "ml_model/classifier.pkl"))
    regressor = joblib.load(os.path.join(BASE_DIR, "ml_model/regressor.pkl"))
    feature_cols = joblib.load(os.path.join(BASE_DIR, "ml_model/feature_cols.pkl"))

    return classifier, regressor, feature_cols


def extract_features(resume_text, feature_cols):
    text = resume_text.lower()

    skill_matches = [s for s in skills if s in text]
    skill_overlap = len(skill_matches)
    skill_count = len(skill_matches)

    matches = re.findall(r'(\d+)\s+year', text)
    exp_years = sum(int(m) for m in matches) if matches else 0

    edu_score = 1 if ("b.tech" in text or "bachelor" in text or "master" in text) else 0

    has_certifications = 1 if "certification" in text else 0

    weighted_ats_score = skill_overlap * 8 + exp_years * 5

    features = {
        "skill_overlap": skill_overlap,
        "skill_count": skill_count,
        "jd_skill_count": 12,
        "edu_score": edu_score,
        "edu_norm": edu_score,
        "exp_years": exp_years,
        "exp_norm": exp_years / 10,
        "has_certifications": has_certifications,
        "weighted_ats_score": weighted_ats_score,
        "word_overlap_obj": skill_overlap,
        "industry_code": 1
    }

    df = pd.DataFrame([features])

    for col in feature_cols:
        if col not in df:
            df[col] = 0

    df = df[feature_cols]

    return df


def predict_ats_score(resume_text):
    classifier, regressor, feature_cols = load_models()

    X = extract_features(resume_text, feature_cols)

    prediction = classifier.predict(X)[0]
    score = regressor.predict(X)[0]

    return prediction, float(score)