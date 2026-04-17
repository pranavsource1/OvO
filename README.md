# OVO — Musical Idea Version Control

OVO is a zero-friction, Git-like version control dashboard for musical ideas. It features a Next.js frontend with an interactive 3D evolution tree and a FastAPI backend powered by Groq AI and Supabase.

## Project Structure
- `/frontend` — Next.js 15 app (React Three Fiber, Framer Motion, Tailwind)
- `/backend` — FastAPI application (Librosa audio analysis, Groq AI metadata, Supabase Storage/DB)

---

## Prerequisites
- Node.js (v18+)
- Python (v3.10+)
- [Supabase](https://supabase.com/) project (with a `fragments` table and `ovo_audio` storage bucket)
- [Groq](https://groq.com/) API Key for AI metadata generation

---

## 1. Setting up the Backend
Open a terminal and navigate to the backend folder:

```bash
cd backend
```

**Create a virtual environment and install dependencies:**
*(On Windows)*
```bash
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```
*(On Mac/Linux)*
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Configure API Keys:**
1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and fill in your real Supabase credentials and your Groq API key:
   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-anon-key
   SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
   GROQ_API_KEY=gsk_your_groq_key_here
   ```

**Start the FastAPI Server:**
```bash
# Ensure your virtual environment is active!
python -m uvicorn app.main:app --reload --port 8000
```
*The backend will now be running on `http://localhost:8000`.*

---

## 2. Setting up the Frontend
Open a **new** terminal and navigate to the frontend folder:

```bash
cd frontend
```

**Install dependencies:**
```bash
npm install
```

**Start the Next.js Server:**
```bash
npm run dev
```
*The frontend will now be running on `http://localhost:3000`.*

---

## 3. Usage
1. Open your browser to `http://localhost:3000`.
2. To test the pipeline, drag and drop a `.wav` file into the upload zone.
3. The Next.js frontend will proxy the file to the FastAPI backend.
4. The backend will analyze the BPM/Key, ask Groq for a creative title, upload the audio to Supabase, and save the metadata.
5. The 3D UI will immediately update with the newly processed track!

*(Optional: Daemon)*
If you want to use the background microphone daemon, make sure you activate your backend Python environment, run `pip install sounddevice torch scipy`, and then run `python -m daemon.listener`.
