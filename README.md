# Resume Skill Extractor (Streamlit App)

This is a Streamlit web application for extracting structured information (name, email, phone, skills, and work experience) from PDF resumes using OpenAI's GPT models. The app supports uploading multiple PDF files, selecting specific pages, and filtering resumes by skill.

## Features
- Upload and process multiple PDF resumes
- Extracts: name, email, phone, skills, and work experience
- Uses OpenAI GPT models for extraction
- Filter/search resumes by skill
- CSV export of extracted data

## Installation

### 1. Clone the Repository
```
git clone <your-repo-url>
cd <project-directory>
```

### 2. Install Python Dependencies
It is recommended to use a virtual environment:

```
pip install -r requirements.txt
```

### 3. Install Poppler
This app uses the `pdf2image` library, which requires Poppler utilities (specifically `pdfinfo` and `pdftoppm`).

#### **On Windows:**
- Download Poppler for Windows from [https://github.com/oschwartz10612/poppler-windows/](https://github.com/oschwartz10612/poppler-windows/)
- Extract the zip file to a folder (e.g., `C:\poppler`)
- Add the `bin` subfolder (e.g., `C:\poppler\bin`) to your system `PATH` environment variable

#### **On macOS:**
```
brew install poppler
```

#### **On Linux (Debian/Ubuntu):**
```
sudo apt-get update
sudo apt-get install poppler-utils
```

## Setting the Poppler Path in Code
If Poppler is not in your system `PATH`, you must specify the path in the code. In `app.py`, update the `convert_from_path` calls:

```
pdf_images = convert_from_path(path, poppler_path=r"/path/to/poppler/bin")
```
- On Windows, this might be: `poppler_path=r"C:\\poppler\\bin"`
- On Linux/macOS, Poppler is usually in the system `PATH` and you can omit this argument or use `poppler_path="/usr/bin"`

## Running the App

### Locally
```
streamlit run app.py
```

### With Docker
1. Build the Docker image:
   ```
   docker build -t windsurf-streamlit-app .
   ```
2. Run the container:
   ```
   docker run -p 8501:8501 windsurf-streamlit-app
   ```
3. Open your browser and go to [http://localhost:8501](http://localhost:8501)

## Usage
- Enter your OpenAI API key in the sidebar.
- Select the pages to process.
- View and filter extracted information.

## Notes
- Make sure you have a valid OpenAI API key. Which you can obtain from [OpenAI](https://github.com/marketplace/models/azure-openai/gpt-4o/playground).
- Poppler must be installed and accessible for PDF processing to work.
- For large PDFs or many files, processing may take some time.

## Contact
For any issues or contributions, please open an issue or pull request on the GitHub repository.