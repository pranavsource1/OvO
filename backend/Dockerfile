# ─── Build stage: Python 3.12 slim ───────────────────────────────────────────
FROM python:3.12-slim

# Install system deps: ffmpeg (audio I/O), libsndfile (soundfile backend),
# git (needed by some HF hub downloads), curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# ─── Define standard Hugging Face Space user ─────────────────────────────────
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# ─── Working directory ───────────────────────────────────────────────────────
WORKDIR /app

# ─── Install Python dependencies ─────────────────────────────────────────────
# Copy requirements first so Docker can cache this layer independently
COPY --chown=user requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ─── Pre-download Demucs htdemucs model weights at BUILD time ─────────────────
# This bakes the ~830 MB model into the image so that the very first /ingest
# request does NOT trigger a slow network download inside the container.
# The weights land in /home/user/.cache/torch/hub/ (the default HF Hub cache).
RUN python - <<'EOF'
import torch
from demucs.pretrained import get_model
print("Downloading htdemucs model weights...")
get_model("htdemucs")
print("htdemucs model ready.")
EOF

# ─── Copy application source ──────────────────────────────────────────────────
COPY --chown=user . ./

# ─── Hugging Face Spaces runs on port 7860 ───────────────────────────────────
EXPOSE 7860

# ─── Launch FastAPI via uvicorn ───────────────────────────────────────────────
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
