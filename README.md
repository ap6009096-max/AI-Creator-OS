# AI Creator OS

**AI Creator OS — A Multi-Agent Content Production Platform** that transforms ideas, videos, podcasts, and scripts into complete production-ready content packages using a coordinated team of AI employees.

**Powered by** `Gemini` · `LangGraph` · `LangChain` · `Parallel Search API` · `FFmpeg` · `OpenCV` · `Whisper` · `Docker` · `Streamlit`

## Creator journey

The product UI follows a creator-first path (agents stay visible under **Agent Workflow** / **Pipeline**):

```
Create → Understand → Research → Plan → Approve → Produce → Review → Export
```

1. **New Video** — one primary input (YouTube / Upload / Script / Idea) + quick settings; advanced controls stay collapsed  
2. **Pipeline** — seven-stage production checklist + live agent activity  
3. **Production Plan** — content detected + human-in-the-loop **Approve & Create** gate after storyboard  
4. **Storyboard** — scene cards (edit & save)  
5. **Preview / Export** — deliverables and project exports  

Phase A stops after storyboard (`run_video_workflow_until_plan`); Phase B resumes through localization, render, quality, analytics, and export (`run_video_workflow_from_plan`).

## Technology architecture

```
User Input
  ↓
YouTube URL / Video / Podcast / Script / Idea
  ↓
Google Cloud Run
  ↓
Supervisor Agent (Gemini + Google ADK)
  ↓
Input Detection Agent
  ↓
Research Agent
  ↓
Planning Agent
  ↓
Script Agent
  ↓
Storyboard Agent
  ↓
Video Production Agents
  ↓
Optimization Agent
  ↓
Analytics Agent
  ↓
Export Agent
  ↓
Final Video Package
```

### Google Cloud

The platform is designed for Google Cloud Run: scalable, containerized execution for the AI workflow.

Google Cloud is responsible for:

- Hosting the AI Creator OS application
- Running containerized workloads through Cloud Run
- Managing scalable execution of AI agents
- Supporting production deployment workflows
- Enabling secure cloud-based access from anywhere

The application is packaged with Docker and deployed to Google Cloud Run for a consistent environment across development and production.

**Deployment path:**

```
Container Image
  ↓
Google Cloud Artifact Registry
  ↓
Google Cloud Run
  ↓
AI Creator OS
  ↓
Public Web Access
```

### Gemini

Gemini powers the intelligence layer of the platform. It is used throughout the workflow to:

- Understand source content
- Analyze transcripts and uploaded media
- Generate content ideas and story structures
- Create scripts and video narratives
- Perform localization and language adaptation
- Generate audience-specific content variations
- Assist with optimization and publishing preparation
- Support decision-making across multiple agents

Rather than acting as a single chatbot, Gemini serves as the reasoning engine behind the entire Creator Operating System.

### Google ADK (Agent Development Kit)

Google ADK describes the product multi-agent model (specialized collaborators with structured handoffs). The **current runtime** orchestrates those stages with **LangGraph** (see mapping below). Specialized agents include:

- Supervisor Agent
- Input Detection Agent
- Research Agent
- Story / Planning Agent
- Script Agent
- Localization Agent
- Storyboard Agent
- Video Direction Agent
- Optimization Agent
- Analytics Agent
- Export Agent

Each agent has a specific responsibility and contributes structured outputs to the next stage. This modular design makes the system easier to extend, maintain, and scale.

### Parallel Search API

The Parallel Search API supports real-time research and content grounding in the Research Agent. Example usage:

```python
from parallel import Parallel

client = Parallel()  # reads PARALLEL_API_KEY from the environment

search = client.search(
    objective="latest AI video creation trends",
    search_queries=[
        "AI video creation trends",
        "short form video tips",
        "YouTube Shorts best practices",
    ],
    mode="turbo",
)
```

The Research Agent uses Parallel Search to:

- Gather supporting information
- Discover current trends
- Collect contextual knowledge
- Improve content planning
- Enhance factual grounding
- Assist with audience-aware content generation

Set `PARALLEL_API_KEY` in `.env`. When the key is missing or Research is toggled off, the agent soft-skips and the workflow continues.

### Video processing pipeline

After planning is complete, the platform processes media using:

- **FFmpeg** — clipping, reframing, rendering, and A/V composition
- **OpenCV** — video analysis and scene detection
- **Whisper** — speech transcription and caption support

These tools enable video analysis, audio processing, scene detection, transcription, caption generation, smart clip extraction, reframing/rendering, and short-form video creation.

### Core technologies

Google Cloud Run · Gemini · Google ADK · Parallel Search API · Python · Streamlit · LangGraph · LangChain · FFmpeg · OpenCV · Whisper · Docker

## Agent model and runtime mapping

**Product agent chain** (platform design):

Supervisor → Input Detection → Research → Planning → Script → Storyboard → Video Production → Optimization → Analytics → Export

**Current runtime** ([`graph/workflow.py`](graph/workflow.py)) implements the production path as LangGraph nodes with conditional skip edges and a plan approval cut:

```
supervisor → input → source ingest → transcript (video) → understanding → scene/audio/speaker
  → moments → funny?/viral? → smart clips → research? → story → script → storyboard
  ── plan gate ──
  → country → region → language → cultural? → humor?
  → video type → visual style → environment
  → b-roll?/voice?/music? → captions → reframe → platform
  → render → quality (± one re-render) → analytics → export
```

Feature flags and config drive skip edges (for example, Original Voice skips TTS; No Music skips music; Research off or missing `PARALLEL_API_KEY` soft-skips). LangChain drives Gemini prompts and structured output inside agents. FFmpeg, OpenCV, and Whisper run locally when available.

## Local development

Python-first Streamlit UI with LangGraph orchestration. Job artifacts live on the filesystem under `outputs/` — no database, no queue, no OAuth publish.

### Quick start

```bash
cd ai-video-agent
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # macOS / Linux
```

Set `GEMINI_API_KEY` in `.env`. Install [FFmpeg](https://ffmpeg.org/) (leave `FFMPEG_PATH` empty to use PATH).

```bash
streamlit run app.py
pytest
```

### What you can do

1. Provide a YouTube URL, upload a video, or paste a script
2. Choose video type, visual style, environment, country, region, language, humor, platform
3. Toggle AI features (viral/funny moments, B-roll, voice, music, localization, captions, reframe, …)
4. Click **GENERATE VIDEO**
5. Inspect live progress, then results: clips, localization, captions, platform metadata, rendered video, quality checks

### Project layout

Each job writes `outputs/projects/{project_id}/` with:

| Path | Purpose |
|------|---------|
| `project.json` | Project metadata |
| `transcript.json` | Transcript (root alias) |
| `scenes.json`, `analysis.json`, `moments.json`, `clips.json` | Root aliases of analysis JSON |
| `localization.json` | Locale + cultural + humor rollup |
| `video_plan.json` | Creative + A/V + render plan rollup |
| `quality_report.json` | Quality checks alias |
| `source/`, `transcripts/`, `analysis/` | Working data |
| `clips/`, `audio/`, `subtitles/`, `thumbnails/`, `final/` | Deliverable folders |
| `captions/`, `renders/`, `exports/` | Pipeline working + export package |

### Environment variables

See [`.env.example`](.env.example). Common keys:

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google Gemini API key |
| `PARALLEL_API_KEY` | Parallel Search API key (Research Agent) |
| `GEMINI_MODEL` | Model id (default `gemini-3.6-flash`) |
| `WHISPER_MODEL` | Whisper size (`base`, …) |
| `FFMPEG_PATH` | Optional absolute path to `ffmpeg` |
| `YOUTUBE_DOWNLOAD_ENABLED` | Opt-in `yt-dlp` download of authorized YouTube media (`false` by default) |
| `TTS_PROVIDER` | Optional TTS provider (`none` / passthrough by default) |
| `OUTPUT_DIR` | Artifact root (default `outputs`) |
| `LOG_LEVEL` | Logging level |
| `MAX_UPLOAD_MB` | Upload size limit |

### Docker

```bash

# macOS/Linux: -v "$PWD/outputs:/app/outputs"
```

Mount `outputs/` so projects persist outside the container. FFmpeg is installed in the image. The image listens on `$PORT` (default `8501`) so the same container works locally and on Cloud Run.

### Google Cloud Run deployment

```bash
docker build -t ai-video-agent .

docker tag ai-video-agent REGION-docker.pkg.dev/PROJECT/REPO/ai-video-agent

docker push REGION-docker.pkg.dev/PROJECT/REPO/ai-video-agent

gcloud run deploy ai-video-agent \
  --image REGION-docker.pkg.dev/PROJECT/REPO/ai-video-agent \
  --platform managed \
  --allow-unauthenticated
```

Replace `REGION`, `PROJECT`, and `REPO` with your Artifact Registry values. Cloud Run injects `$PORT`; Streamlit binds to it automatically. Configure secrets (for example `GEMINI_API_KEY`, `PARALLEL_API_KEY`) via Cloud Run environment variables or Secret Manager.

### Tests

```bash
pytest
pytest -m integration   # needs FFmpeg for fixture media path
```

### Limitations (MVP)

- No OAuth / automatic publishing (platform pack stays `not_published`)
- No database or job queue — re-run to resume
- TTS / music generation only when a provider is configured; otherwise plans preserve original audio
- YouTube path uses metadata packaging (no unrestricted download)

---

The result is a cloud-native AI Creator Operating System capable of transforming ideas, experiences, scripts, videos, podcasts, and YouTube content into structured video productions through a coordinated multi-agent workflow powered by Google Cloud and Gemini.
#   A I - C r e a t o r - O S  
 