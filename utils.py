import os
import fitz
import tempfile
import google.generativeai as genai
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
import tempfile
from textwrap import wrap

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Load Gemini model
model = genai.GenerativeModel("gemini-1.5-pro")

def extract_pdf_chunks(pdf_path):
    """Extracts text content from a PDF using PyMuPDF."""
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def get_ats_score(resume_text, job_description, job_title, company_name):
    """Uses Google Gemini to generate an ATS score based on detailed criteria."""

    prompt = f"""
    You are a senior HR and recruitment AI specializing in Applicant Tracking System (ATS) optimization and resume evaluation.

    Your task is to critically assess how well the following resume aligns with the job description, job title, and company expectations. Consider keyword relevance, role-specific skills, industry terminology, experience match, education, and soft skills.

    Evaluate the resume based on the following aspects:
    1. Keyword and skill match with the job description.
    2. Alignment with job title responsibilities.
    3. Relevance to company/industry context.
    4. Overall clarity, structure, and professional tone of the resume.

    Assign an **ATS match score from 0 to 100** that reflects the resume’s suitability for the role.
    Then, briefly explain your score in a breif concise sentences, focusing on the resume’s strengths and weaknesses in relation to the job.

    ---
    Resume Text:
    {resume_text}

    Job Title: {job_title}
    Company Name: {company_name}
    Job Description:
    {job_description}
    ---

    Respond using this exact format:
    ATS Score: <score>
    Reason: <3–5 sentence explanation>
    """

    response = model.generate_content(prompt)
    return response.text.strip()

def rewrite_resume(resume_text, job_description, job_title, company_name):
    ats_feedback = get_ats_score(resume_text, job_description, job_title, company_name)

    try:
        _, reason = ats_feedback.split("Reason:", 1)
        reason = reason.strip()
    except Exception:
        reason = "No specific feedback was available, so optimize based on standard best practices."

    prompt = f"""
    You are a senior-level professional resume strategist and expert in optimizing documents for Applicant Tracking Systems (ATS) and hiring managers.

    The following resume was evaluated and received the feedback below. Your job is to rewrite and enhance it significantly to resolve the identified weaknesses, improve ATS match, and increase recruiter engagement.

    --- ATS Feedback (Areas to Improve) ---
    {reason}

    --- Instructions ---
    - Prioritize fixing weaknesses mentioned in the feedback.
    - Ensure the resume matches the **job title**, **company**, and **job description** below.
    - Include **relevant industry keywords**, **hard and soft skills**, and **accomplishments** aligned with the role.
    - Use a clear, modern, and professional tone and structure.
    - Maintain measurable impact statements (e.g., "increased revenue by 30%", "led a team of 10 developers").
    - Ensure logical section organization: Summary, Skills, Experience, Education, Certifications (if applicable).
    - If the resume includes **more than 5 years of total experience**, emphasize seniority and strategic contributions.
    - If **team leadership or management is not explicitly mentioned**, and the resume shows over 5 years of experience, **add statements indicating leadership of a small team (e.g., led a team of 2–4 members)** and demonstrate leadership skills.
    - If the resume already mentions leading a team or managing people, do not add or duplicate that information.
    
    --- Original Resume ---
    {resume_text}

    --- Job Title ---
    {job_title}

    --- Company ---
    {company_name}

    --- Job Description ---
    {job_description}

    Return only the rewritten resume text, ready to paste into a document.
    """

    response = model.generate_content(prompt)
    return response.text.strip()

def save_pdf(text, save_path=None):
    """Create a clean, well-formatted PDF with wrapped text and no truncation."""
    # If no path is provided, generate a temporary file path
    if not save_path:
        save_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
    c = canvas.Canvas(save_path, pagesize=letter)
    width, height = letter

    margin = 0.75 * inch
    max_width = width - 2 * margin
    line_height = 14
    y = height - margin
    x = margin

    # Prepare text object for better handling
    text_obj = c.beginText()
    text_obj.setTextOrigin(x, y)
    text_obj.setFont("Helvetica", 11)

    # Split and wrap each line from the input text
    for line in text.split('\n'):
        wrapped_lines = wrap(line, width=100)  # Adjust wrap width if needed
        if not wrapped_lines:
            text_obj.textLine("")  # Keep blank lines
        for w_line in wrapped_lines:
            if text_obj.getY() < margin + line_height:
                c.drawText(text_obj)
                c.showPage()
                text_obj = c.beginText()
                text_obj.setTextOrigin(x, height - margin)
                text_obj.setFont("Helvetica", 11)
            text_obj.textLine(w_line)

    c.drawText(text_obj)
    c.save()
    return save_path