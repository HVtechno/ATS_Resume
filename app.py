from flask import Flask, render_template, request, send_file,jsonify
import os
import tempfile
from utils import extract_pdf_chunks, get_ats_score, rewrite_resume, save_pdf
import sys

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploaded_resumes'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def is_desktop():
    return hasattr(sys, '_MEIPASS') or os.environ.get("PYWEBVIEW_PLATFORM")

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        resume_file = request.files['resume']
        job_desc = request.form['job_description']
        job_title = request.form['job_title']
        company_name = request.form['company_name']

        # Save the resume file
        resume_path = os.path.join(UPLOAD_FOLDER, resume_file.filename)
        resume_file.save(resume_path)

        # Step 2: Extract PDF chunks
        chunks = extract_pdf_chunks(resume_path)

        # Step 3: Generate ATS Score with Google Gemini
        ats_result = get_ats_score(chunks, job_desc, job_title, company_name)
        
        # Example format: "ATS Score: 85 Reason: Your resume is a good match because..."
        try:
            score_part, reason_part = ats_result.split("Reason:", 1)
            ats_score = int(score_part.strip().split(":")[1])
            ats_reason = reason_part.strip()
        except Exception as e:
            ats_score = 0
            ats_reason = "Unable to parse ATS feedback."

        return render_template('index.html',
                               ats_score=ats_score,
                               ats_reason=ats_reason,
                               file_name=resume_file.filename,
                               job_description=job_desc,
                               job_title=job_title,
                               company_name=company_name)

    return render_template('index.html')

@app.route('/rewrite_resume', methods=['POST'])
def rewrite_resume_and_recalculate():
    file_name = request.form['file_name']
    resume_path = os.path.join(UPLOAD_FOLDER, file_name)
    job_desc = request.form['job_description']
    job_title = request.form['job_title']
    company_name = request.form['company_name']

    resume_text = extract_pdf_chunks(resume_path)

    # Step 5: Rewrite resume and recalculate ATS score
    updated_resume = rewrite_resume(resume_text, job_desc, job_title, company_name)

    new_resume_path = os.path.join(UPLOAD_FOLDER, 'rewritten_' + file_name)
    # Save the updated resume as a new PDF
    new_resume_path = save_pdf(updated_resume,new_resume_path)

    # Recalculate ATS score for the new resume
    #new_ats_score = get_ats_score(updated_resume, job_desc, job_title, company_name)

    # Return the updated resume
    return send_file(new_resume_path, as_attachment=True, download_name='rewritten_resume.pdf', mimetype='application/pdf')

if __name__ == "__main__":
    app.run(debug=True)