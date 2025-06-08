import streamlit as st
import tempfile
import os
import base64
import time
import csv
import json  # For work_experience serialization
from pathlib import Path
from pdf2image import convert_from_path

import io
from PIL import Image

from openai import OpenAI

# Initialize session state for extracted resumes
if 'resumes' not in st.session_state:
    st.session_state.resumes = []
if 'total_pages' not in st.session_state:
    st.session_state.total_pages = 0
if 'filter_skill' not in st.session_state:
    st.session_state.filter_skill = ''

endpoint = "https://models.inference.ai.azure.com"
model_name = "gpt-4o"

# Page configuration
st.set_page_config(
    page_title="Resume Skill Extractor",
    page_icon="📚",
    layout="wide"
)

# Form to enter API key
with st.sidebar:
    with st.form(key='api_form'):
        st.markdown("""
        Enter your OpenAI API key :red[*]
        """)
        api_key = st.text_input("Enter your OpenAI API key:", type='password', key = 'token', label_visibility='collapsed')
        st.form_submit_button("SUBMIT",
                            #   disabled=not api_key,
                              use_container_width=True)
        st.caption(
            "To use this app, you need an API key. "
            "You can get one [here](https://github.com/marketplace/models)."
        )

        if not api_key:
            st.warning('Please enter your credentials!', icon = '⚠️')
        else:
            st.success("Proceed to use the app!", icon = '✅')

    st.subheader('Parameters')

    temp = st.sidebar.slider(':blue[Temperature]', min_value=0.0, max_value=1.0, value = 0.5, step = 0.01, help = 'Controls randomness in the response, use lower to be more deterministic.' , disabled=not api_key)
    m_tokens = st.sidebar.slider(':blue[Max Tokens]', min_value=100, max_value=4096, value=4096, step=10, help = 'Limit the maximum output tokens for the model response.', disabled=not api_key)
    t_p = st.sidebar.slider(':blue[Top P]', min_value=0.01, max_value=1.0, value=1.0, step=0.01, help = 'Limit the maximum output tokens for the model response.', disabled=not api_key)

col1, col2 = st.columns(spec=[0.70, 0.30], gap="medium")

if 'total_pages' not in st.session_state:
    st.session_state.total_pages = 0

with col1:
    # Subheader
    st.header("Resume Skill Extractor :open_book:")

    with st.expander("Your Documents"):
        uploaded_files = st.file_uploader(
            label="Upload your PDF here and click on 'Process'",
            type=["pdf"],
            accept_multiple_files=True,
            disabled=not api_key
        )
        
    # Get total pages when file is uploaded
    temp_files = []
    if uploaded_files:
        for uploaded_file in uploaded_files:
            # Save uploaded file to a temp file
            fd, path = tempfile.mkstemp()
            with os.fdopen(fd, 'wb') as tmp:
                tmp.write(uploaded_file.getvalue())
            temp_files.append(path)

            # Use pdf2image to get total pages
            # pdf_images = convert_from_path(path, poppler_path = r"C:\Users\ashis\Downloads\Release-24.08.0-0\poppler-24.08.0\Library\bin")
            pdf_images = convert_from_path(path, poppler_path = r"/usr/bin")
            st.session_state.total_pages = len(pdf_images)
            uploaded_file.seek(0)  # Reset file pointer
    
    if st.session_state.total_pages > 0:
        page_numbers = st.multiselect(
            "Select page numbers",
            options=list(range(1, st.session_state.total_pages + 1)),
            default=[1],
            help=f"Select page numbers between 1 and {st.session_state.total_pages}"
        )
    else:
        st.info("Upload a PDF to view pages")
    
    st.divider()

    # Extract and display resume fields
    # Track temp files for later cleanup
    if uploaded_files:
        for uploaded_file in uploaded_files:
            fd, path = tempfile.mkstemp()
            with os.fdopen(fd, 'wb') as tmp:
                tmp.write(uploaded_file.getvalue())
            temp_files.append(path)

            # PDF-to-image extraction using pdf2image
            images = []
            # pdf_images = convert_from_path(path, poppler_path = r"C:\Users\ashis\Downloads\Release-24.08.0-0\poppler-24.08.0\Library\bin")
            pdf_images = convert_from_path(path, poppler_path = r"/usr/bin")
            for page_number in page_numbers:
                if 1 <= page_number <= len(pdf_images):
                    img = pdf_images[page_number - 1]
                    buffer = io.BytesIO()
                    img.save(buffer, format="PNG")
                    base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
                    images.append(base64_image)

            # Use LLM to extract fields from the images
            client = OpenAI(
                base_url=endpoint,
                api_key=api_key,
            )
            extraction_prompt = (
                "Extract the following fields from this resume: "
                "name, email, phone, skills (as a list), and work experience (as a list of jobs with company, title, and years if available). "
                "Return the result as a JSON object with these keys: name, email, phone, skills, work_experience. "
                "If a field is missing, use an empty string or empty list."
            )
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": extraction_prompt},
                    {"role": "user", "content": [
                        {"type": "text", "text": "Extract fields from this resume."},
                        *[
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image}", "detail": "low"}}
                            for image in images
                        ],
                    ]},
                ],
                model=model_name,
                temperature=0.5,
                max_tokens=4096,
                top_p=1.0
            )
            import json
            # Clean response: remove triple backticks and optional language specifier
            import re
            raw_llm_response = response.choices[0].message.content
            cleaned = raw_llm_response.strip()
            cleaned = re.sub(r'^```[a-zA-Z]*\s*', '', cleaned)
            cleaned = re.sub(r'```$', '', cleaned).strip()
            import json
            try:
                extracted = json.loads(cleaned)
            except Exception:
                extracted = {"name":"","email":"","phone":"","skills":[],"work_experience":[]}
            # Store the result
            st.session_state.resumes.append({
                "filename": uploaded_file.name,
                "fields": extracted
            })

            # Save to CSV
            csv_path = Path("resumes.csv")
            file_exists = csv_path.exists()
            # Prepare row data
            row = {
                "filename": uploaded_file.name,
                "name": extracted.get("name", ""),
                "email": extracted.get("email", ""),
                "phone": extracted.get("phone", ""),
                "skills": ", ".join(extracted.get("skills", [])),
                "work_experience": json.dumps(extracted.get("work_experience", []))
            }
            with open(csv_path, mode='a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=["filename", "name", "email", "phone", "skills", "work_experience"])
                if not file_exists:
                    writer.writeheader()
                writer.writerow(row)

    # PDF display and cleanup handled in col2 below.

    # Filter/search resumes
    st.subheader("Resume Search & Summary")
    filter_skill = st.text_input("Filter by skill (case-insensitive):", value=st.session_state.filter_skill)
    st.session_state.filter_skill = filter_skill
    filtered_resumes = []
    for resume in st.session_state.resumes:
        skills = resume["fields"].get("skills", [])
        if filter_skill.strip() == '' or any(filter_skill.lower() in skill.lower() for skill in skills):
            filtered_resumes.append(resume)
    if filtered_resumes:
        for resume in filtered_resumes:
            st.markdown(f"### {resume['filename']}")
            fields = resume["fields"]
            # Prepare data for table
            import pandas as pd
            summary_data = {
                "Field": ["Name", "Email", "Phone", "Skills"],
                "Value": [
                    fields.get("name", ""),
                    fields.get("email", ""),
                    fields.get("phone", ""),
                    ", ".join(fields.get("skills", []))
                ]
            }
            st.table(pd.DataFrame(summary_data))
            # Work experience as a separate table if present
            work_exp = fields.get("work_experience", [])
            if work_exp and isinstance(work_exp, list) and any(isinstance(job, dict) for job in work_exp):
                exp_data = {
                    "Company": [],
                    "Title": [],
                    "Years": []
                }
                for job in work_exp:
                    exp_data["Company"].append(job.get("company", ""))
                    exp_data["Title"].append(job.get("title", ""))
                    exp_data["Years"].append(job.get("years", ""))
                st.markdown("**Work Experience**")
                st.table(pd.DataFrame(exp_data))
    else:
        st.info("No resumes match the filter or have been processed yet.")

# (Chat input and chat logic removed as per new requirements)
    # (Resume extraction and summary view handled above)

with col2:
    if uploaded_files:
        for idx, uploaded_file in enumerate(uploaded_files):
            # Use the same temp file created in col1
            if idx < len(temp_files):
                path = temp_files[idx]
                with open(path, "rb") as f:
                    data_url = base64.b64encode(f.read()).decode('utf-8')
                    st.markdown(f'<iframe src="data:application/pdf;base64,{data_url}" width="500" height="720" type="application/pdf"></iframe>', unsafe_allow_html=True)
        # After all PDFs are displayed, clean up temp files
        for path in temp_files:
            try:
                os.remove(path)
            except Exception:
                pass
