# backend.py (FastAPI app)
from fastapi import FastAPI
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv
import os

app = FastAPI()
load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class ResumeRequest(BaseModel):
    resume_text: str

class FollowUpRequest(BaseModel):
    parsed_resume: str
    last_answer: str

class FirstQuestionRequest(BaseModel):
    parsed_resume: str

@app.post("/parse-resume/")
def parse_resume(req: ResumeRequest):
    prompt = f"""
    You are an advanced AI resume parser. Your task is to extract structured information from resumes written in any format.

    Always extract the following fields if present:
    - Full Name
    - Email Address
    - Phone Number
    - Skills
    - Education
    - Work Experience

    Additionally, extract these optional fields if you find them under any synonymous section names:
    - Projects (also titled as Personal Projects, Notable Work, Freelance, etc.)
    - Certifications (may appear under Licenses, Courses Completed, etc.)
    - Languages (spoken or programming)
    - Achievements or Key Contributions

    Be tolerant of inconsistent formatting and varied section titles. Return your output in clean JSON format.

    Resume:
    {req.resume_text}
    """

    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    return {"result": response.choices[0].message.content.strip()}

@app.post("/generate-question/")
def generate_first_question(req: FirstQuestionRequest):
    prompt = f"""
    You are an AI interviewer. Based on the candidate's resume (in JSON), ask the first question to begin the interview.
    Be natural and professional. Choose a relevant question based on experience, skills, or projects.

    Resume:
    {req.parsed_resume}
    """
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return {"question": response.choices[0].message.content.strip()}

@app.post("/next-question/")
def next_question(req: FollowUpRequest):
    prompt = f"""
    You are acting as an AI Interviewer. Based on the candidate's resume and the previous response, ask a relevant follow-up question.

    Resume (in JSON):
    {req.parsed_resume}

    Candidate's Previous Response:
    {req.last_answer}

    Your job:
    - Ask one intelligent follow-up or related question.
    - Avoid repeating yourself.
    - Ask technical, behavioral, or role-relevant questions.
    - Return only the question.
    """
    response = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return {"question": response.choices[0].message.content.strip()}