"""
OVO Backend — FastAPI Server
─────────────────────────────
The multi-agent orchestration gateway for OVO.

Endpoints:
  GET  /health            → Health check
  GET  /api/v1/fragments  → List all fragments (newest first)
  POST /api/v1/ingest     → Ingest a .wav file (full pipeline)

Run with:
  cd backend
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
import os
import tempfile
import uuid

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.models import FragmentResponse, IngestResponse, fragment_from_db_row

# ──────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(name)s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("ovo")


# ──────────────────────────────────────────────
# Lifespan (startup / shutdown)
# ──────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs on server startup and shutdown.
    We lazily import the Supabase client here so the module-level
    creation happens AFTER .env is loaded.
    """
    settings = get_settings()
    logger.info("═══════════════════════════════════════════")
    logger.info("  OVO Backend starting up")
    logger.info(f"  Supabase: {settings.supabase_url}")
    logger.info(f"  Groq key: {settings.groq_api_key[:8]}...****")
    logger.info("═══════════════════════════════════════════")

    # Lazily initialize the Supabase client (won't crash if keys are invalid)
    from app.supabase_client import get_supabase
    client = get_supabase()
    if client:
        logger.info("✓ Supabase connected")
    else:
        logger.warning("⚠ Running WITHOUT Supabase — update backend/.env")

    yield  # ← Server is running

    logger.info("OVO Backend shutting down")


# ──────────────────────────────────────────────
# FastAPI App
# ──────────────────────────────────────────────

app = FastAPI(
    title="OVO API",
    description="Zero-friction version control for musical ideas",
    version="0.1.0",
    lifespan=lifespan,
)

# ─── CORS ───
# Allow the Next.js frontend at localhost:3000 to call our API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # Allow all origins for seamless development upload bypassing
    allow_credentials=True,
    allow_methods=["*"],            # GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],            # Accept all headers
)


# ──────────────────────────────────────────────
# Health Check
# ──────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """
    Simple health check endpoint.
    Returns the service name and current server time.
    """
    return {
        "status": "ok",
        "service": "ovo-backend",
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ──────────────────────────────────────────────
# GET /api/v1/fragments — List all fragments
# ──────────────────────────────────────────────

@app.get(
    "/api/v1/fragments",
    response_model=list[FragmentResponse],
    summary="List all fragments",
    description="Returns all fragments from the database, newest first.",
)
async def list_fragments(
    limit: int = Query(default=50, ge=1, le=200, description="Max results"),
):
    """
    Fetches all fragments from Supabase, ordered by created_at descending.
    Converts each DB row into the frontend-expected FragmentResponse shape.
    """
    from app.supabase_client import get_supabase

    client = get_supabase()
    if not client:
        raise HTTPException(
            status_code=503,
            detail="Database not configured. Update backend/.env with Supabase credentials.",
        )

    try:
        response = (
            client.table("fragments")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        fragments = [fragment_from_db_row(row) for row in response.data]
        logger.info(f"📦 Returning {len(fragments)} fragments")
        return fragments

    except Exception as e:
        logger.error(f"❌ Failed to fetch fragments: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ──────────────────────────────────────────────
# POST /api/v1/ingest — Ingest a .wav file
# ──────────────────────────────────────────────

@app.post(
    "/api/v1/ingest",
    response_model=IngestResponse,
    summary="Ingest a .wav audio file",
    description=(
        "Receives a .wav file, analyzes it (BPM, key), generates AI metadata "
        "(title, mood) via Groq, uploads to Supabase Storage, "
        "and inserts the fragment into the database."
    ),
)
async def ingest_audio(
    file: UploadFile = File(..., description="The .wav audio file to ingest"),
    parent_id: str | None = Query(
        default=None,
        description="UUID of the parent fragment (for branching). Leave empty for root.",
    ),
):
    """
    Full ingest pipeline.

    Flow:
      1. Validate the uploaded file is a .wav
      2. Save to temp file, use librosa to extract BPM and key
      3. Call Groq (Llama 3.3 70B) to generate a creative title + mood
      4. Upload the .wav to Supabase Storage (ovo_audio bucket)
      5. Insert the unified record into the fragments table
      6. Return the newly created fragment
    """
    from app.supabase_client import get_supabase
    from app.audio_analysis import analyze_audio
    from app.ai_services import generate_metadata

    # ─── Step 0: Validate file type ───
    if not file.filename or not file.filename.lower().endswith(".wav"):
        raise HTTPException(
            status_code=400,
            detail="Only .wav files are accepted. Please upload a valid WAV file.",
        )

    logger.info(f"🎙️ Received file: {file.filename} ({file.size or 'unknown'} bytes)")

    # ─── Step 1: Verify Supabase ───
    client = get_supabase()
    if not client:
        raise HTTPException(
            status_code=503,
            detail="Database not configured. Update backend/.env with Supabase credentials.",
        )

    # ─── Step 2: Save to temp file + analyze audio ───
    fragment_id = str(uuid.uuid4())
    tmp_path = None

    try:
        # Write uploaded file to a temporary location
        file_content = await file.read()
        tmp_dir = tempfile.mkdtemp(prefix="ovo_")
        tmp_path = os.path.join(tmp_dir, file.filename or "upload.wav")

        with open(tmp_path, "wb") as f:
            f.write(file_content)

        logger.info(f"  → Saved to temp: {tmp_path} ({len(file_content)} bytes)")

        # Analyze with librosa
        audio_meta = analyze_audio(tmp_path)
        bpm = audio_meta["bpm"]
        key = audio_meta["key"]
        duration = audio_meta["duration"]

        # ─── Step 3: Generate AI metadata via Groq ───
        ai_meta = await generate_metadata(
            bpm=bpm,
            key=key,
            duration=duration,
            filename=file.filename or "",
        )
        title = ai_meta["title"]
        mood = ai_meta["mood"]

        # ─── Step 4: Upload to Supabase Storage ───
        storage_path = f"fragments/{fragment_id}.wav"

        try:
            client.storage.from_("ovo_audio").upload(
                path=storage_path,
                file=file_content,
                file_options={"content-type": "audio/wav"},
            )

            # Construct the public URL
            settings = get_settings()
            file_url = f"{settings.supabase_url}/storage/v1/object/public/ovo_audio/{storage_path}"
            logger.info(f"  → Uploaded to storage: {storage_path}")

        except Exception as e:
            logger.warning(f"⚠ Storage upload failed: {e}")
            file_url = ""  # Graceful degradation — fragment still gets created

        # ─── Step 5: Insert into database ───
        db_record = {
            "id": fragment_id,
            "parent_id": parent_id,
            "type": "raw_capture",
            "stems": [],
            "bpm": bpm,
            "key": key,
            "duration": duration,
            "mood": mood,
            "title": title,
            "file_url": file_url,
        }

        result = client.table("fragments").insert(db_record).execute()
        logger.info(f"  → Inserted into DB: {fragment_id}")

        # ─── Step 6: Build and return response ───
        fragment = FragmentResponse(
            id=fragment_id,
            parent_id=parent_id,
            type="raw_capture",
            stems=[],
            bpm=bpm,
            key=key,
            mood=mood,
            duration=duration,
            timestamp="Just now",
            title=title,
            file_url=file_url,
        )

        logger.info(f"✅ Ingest complete: \"{title}\" ({key}, {bpm} BPM, {mood})")

        return IngestResponse(
            success=True,
            fragment=fragment,
            message=f"Fragment '{title}' ingested successfully.",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ingest pipeline failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingest failed: {str(e)}")
    finally:
        # Clean up temp file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
                os.rmdir(os.path.dirname(tmp_path))
            except OSError:
                pass


# ──────────────────────────────────────────────
# Entry point (for running directly)
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )
