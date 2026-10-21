import pandas as pd
import json
import re
from ast import literal_eval


def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def safe_parse_list(lst):
    """Safely parse a stringified list"""
    if isinstance(lst, list):
        return [clean_text(str(x)) for x in lst]
    try:
        parsed = literal_eval(lst)
        if isinstance(parsed, list):
            return [clean_text(str(x)) for x in parsed]
        else:
            return []
    except:
        return []

def extract_keywords(text):
    """Split text into words for basic keyword extraction"""
    text = clean_text(text)
    return set(text.split())


def load_resume_data(resume_csv_path):
    df = pd.read_csv(resume_csv_path)
    df['skills'] = df['skills'].apply(safe_parse_list)
    return df

def load_postings_data(postings_csv_path):
    df = pd.read_csv(postings_csv_path, nrows=200)
    df['description'] = df['description'].fillna("")
    df['skills_desc'] = df['skills_desc'].fillna("")
    return df

def load_industry_skills(industry_json_path):
    with open(industry_json_path, "r") as f:
        return json.load(f)