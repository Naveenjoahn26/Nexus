# Use official Python 3.11 slim image
FROM python:3.11-slim

# Hugging Face Spaces requires applications to run on port 7860
ENV PORT=7860
ENV HOST=0.0.0.0

# Set up a new user named "user" with user ID 1000
# (Hugging Face Spaces runs Docker containers as a non-root user for security)
RUN useradd -m -u 1000 user
USER user

# Set environment variables for the user
ENV HOME=/home/user \
	PATH=/home/user/.local/bin:$PATH \
    HF_HOME=/home/user/.cache/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/home/user/.cache/huggingface

# Set the working directory
WORKDIR $HOME/app

# Copy the requirements file first to leverage Docker cache
COPY --chown=user:user requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the heavy ML models during the image build process
# This ensures the container starts instantly on Hugging Face without downloading 250MB
RUN python -c "\
from sentence_transformers import SentenceTransformer, CrossEncoder; \
print('Downloading embedding model...'); \
SentenceTransformer('BAAI/bge-small-en-v1.5'); \
print('Downloading reranker model...'); \
CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2'); \
print('Models ready.')"

# Copy the rest of the backend application code
COPY --chown=user:user . .

# Create the storage directories that the app expects
RUN mkdir -p app/storage/uploads app/storage/generated app/storage/temp app/storage/chromadb

# Expose the required port
EXPOSE 7860

# Start the FastAPI application via Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
