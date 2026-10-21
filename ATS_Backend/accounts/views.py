from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm
from .models import ResumeUpload, History, JDupload
# from .industry_mapper import predict_industry
import pdfplumber
from .job_recommender import get_job_recommendations, extract_resume_entities
from .ats_scorer import ATSScorer
from .genai.services import AIResumeGenerator

def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("dashboard")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect("dashboard")
        else:
            return render(request, "accounts/login.html", {
                "error": "Invalid credentials"
            })

    return render(request, "accounts/login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def dashboard(request):
    return render(request, 'accounts/dashboard.html')


def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            content = page.extract_text()
            if content:
                text += content
    return text


@login_required
def ats_check(request):

    if request.method == "POST":

        resume = request.FILES.get("resume")

        if resume and resume.name.endswith(".pdf"):

            text = extract_text_from_pdf(resume)

            uploaded_resume = ResumeUpload.objects.create(
                user=request.user,
                resume_file=resume
            )

            resume_data = extract_resume_entities(text)
            # skills = resume_data.get("skills", [])
            # industry_pred, confidence = predict_industry(skills)
            industry = resume_data.get("industry", "IT")
            scorer = ATSScorer("accounts/ml_model/industry_skills.json")
            result = scorer.score_resume(resume_data, industry)

            jobs = get_job_recommendations(text)
            print("\n========== DEBUG ==========")
            print("RESUME SKILLS:", resume_data.get("skills"))
            print("JOBS:", jobs[:1])

            if jobs:
                print("JOB DESCRIPTION:", jobs[0].get("description"))
                print("JOB SKILLS:", jobs[0].get("skills"))

                temp_job = {
                    "description": jobs[0].get("description", ""),
                    "skills_desc": jobs[0].get("skills", "")
                }

                print("EXTRACTED JD SKILLS:", scorer.extract_jd_skills(temp_job))

            print("========== END DEBUG ==========\n")

            jd_score = 0
            matched = []
            missing = []
            job={}
            if jobs:
                job = {
                    "description": jobs[0].get("description", ""),
                    "skills_desc": jobs[0].get("skills", "")
            }
                
            print("JOB USED:", job)

            jd_result = scorer.score_jd_match(
                resume_data,
                job,
                industry
            )

            print("JD RESULT:", jd_result)

            jd_score = jd_result["jd_score"]
            matched = jd_result["matched"]
            missing = jd_result["missing"]

            improved = AIResumeGenerator.generate_improved_resume(text)

            resume_html = improved.get("resume_html")

            if not resume_html:
                resume_html = "<p>Unable to generate resume. Try again.</p>"

            History.objects.create(
                user=request.user,
                action="resume",
                score=result.get("ats_score"),
                title=resume.name,
                resume=uploaded_resume
            )

            return render(request, 'accounts/analyzer.html', {
                "score": result.get("ats_score"),
                "level": result.get("level"),
                "suggestions": result.get("suggestions"),
                "jobs": jobs,
                "resume_html": resume_html,
                "jd_score": jd_score,
                "matched": matched,
                "missing": missing,
                "uploaded_file": resume.name,
                # "industry_pred": industry_pred,
                # "confidence": confidence,
            })

        else:
            return render(request, 'accounts/analyzer.html', {
                "error": "Upload valid PDF"
            })

    return render(request, 'accounts/analyzer.html')

@login_required
def compare(request):

    if request.method == "POST":

        resume_file = request.FILES.get("resume")
        jd_file = request.FILES.get("Job_Description")

        if not resume_file or not jd_file:
            return render(request, "accounts/compare.html", {
                "error": "Both files required"
            })

        if not resume_file.name.endswith(".pdf") or not jd_file.name.endswith(".pdf"):
            return render(request, "accounts/compare.html", {
                "error": "Only PDF allowed"
            })

        resume_text = extract_text_from_pdf(resume_file)
        jobs = get_job_recommendations(resume_text)
        jd_text = extract_text_from_pdf(jd_file)

        resume_data = extract_resume_entities(resume_text)

        scorer = ATSScorer("accounts/ml_model/industry_skills.json")

        job = {"description": jd_text, "skills_desc": ""}

        industry = resume_data.get("industry", "IT")
        ats = scorer.score_resume(resume_data, industry)
        jd = scorer.score_jd_match(resume_data, job, resume_data["industry"])

        uploaded_resume = ResumeUpload.objects.create(
            user=request.user,
            resume_file=resume_file
        )

        uploaded_jd = JDupload.objects.create(
            user=request.user,
            Jd_file=jd_file
        )

        History.objects.create(
            user=request.user,
            action="job",
            score=jd["jd_score"],
            title=jd_file.name,
            resume=uploaded_resume,
            jd=uploaded_jd
        )

        return render(request, "accounts/compare.html", {
            "match_score": jd["jd_score"],
            "ats_score": ats["ats_score"],
            "level": ats["level"],
            "matched_skills": jd["matched"],
            "gaps": jd["missing"],
            "jobs": jobs
        })

    return render(request, "accounts/compare.html")

from .models import History
@login_required
def history(request):
    history_items = History.objects.filter(user=request.user).order_by('-created_at')
    return render(request, "accounts/history.html",{
         "history_items": history_items
    })


def about(request):
    return render(request, 'accounts/about.html')
