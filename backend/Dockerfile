# Use a sleek, multi-purpose Python base image (Debian slim to keep it lightweight)
FROM python:3.12-slim

# Install essential system dependencies (ffmpeg and libsndfile for Demucs/Librosa)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Define standard HF Space user
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# Set working directory inside the container
WORKDIR /app

# Copy explicit requirements first for better caching
COPY --chown=user requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend source code
COPY --chown=user . ./

# Hugging Face runs on 7860
EXPOSE 7860

# Start Uvicorn directly from the entrypoint module
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
