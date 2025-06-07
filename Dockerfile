FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    docker run -p 8501:8501 windsurf-streamlit-app    procps \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["sh", "-c", "streamlit run app.py --server.port=8501 --server.address=0.0.0.0 & sleep 10 && pkill streamlit && pip3 uninstall -y fitz PyMuPDF && pip3 install fitz PyMuPDF && streamlit run app.py --server.port=8501 --server.address=0.0.0.0"]
