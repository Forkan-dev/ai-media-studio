# AI Media Studio

An AI content studio that runs **multiple faceless video brands from one dashboard**.

You create a brand once — its niche, language, voice, visual style, recurring characters and posting schedule — and the system handles the rest, from topic research to publishing and performance tracking.

> Docs: [ARCHITECTURE.md](ARCHITECTURE.md) · [TASKS.md](TASKS.md) (progress tracker)

---

## What the system does

### 1. Produces videos end to end
For each video the pipeline:

1. **Researches topics.** Web search and trending ideas, scored by the LLM. It skips topics the brand has already covered.
2. **Writes the script.** A hook (first 3 seconds), body and CTA, with separate templates for Shorts and long-form.
3. **Builds a storyboard.** Each scene gets narration, an image prompt, a camera motion and an on-screen text line.
4. **Fact-checks and reviews quality.** It checks claims against search results and scores the hook, clarity and originality. Low scores send it back to rewrite, up to 2 retries.
5. **Generates visuals.** One SDXL image per scene in the brand's style, with a character LoRA for consistent characters. Optional AI video clips for key scenes.
6. **Narrates** each scene with Kokoro TTS.
7. **Adds captions.** Whisper word timings become animated word-by-word captions.
8. **Renders** with FFmpeg: pan/zoom, transitions, music ducked under the voice, and captions, in **9:16** (Shorts/Reels) and/or **16:9** (YouTube).
9. **Writes metadata and a thumbnail:** title, description, tags, hashtags and the thumbnail image.

### 2. Keeps a human in the loop
Every video **stops at a review screen** before it goes out. There you can:
- Watch the video
- Edit the script scene by scene
- Regenerate one scene's image or voice without redoing the whole video
- Pick the best of 3 generated hooks (Hook A/B)
- Edit the title, description and thumbnail
- Read the fact-check report
- **Approve / Reject / Schedule** for YouTube and Facebook

### 3. Learns from performance
After publishing it pulls stats at **24h, 7 days and 30 days**. Topics and formats that performed well feed back into topic selection, so each brand improves without extra manual work.

### 4. Is configurable, not hardcoded
Niche, format, duration, language, voice, art style, characters, music, prompts and publishing rules are all config. It can make any kind of video: language lessons, science explainers, psychology deep-dives, history, storytelling, documentaries, product content. **Adding a new brand means adding a config, not writing code.**

### 5. Stays platform-safe
- AI disclosure labels on by default
- Copyright-safe music and assets only
- Near-duplicate detection blocks repeated videos
- Together these keep every brand eligible for monetization

---

## Key features

| Feature | What it gives you |
|---|---|
| Scene-level regeneration | Fix one bad image or line instead of re-rendering everything |
| Hook A/B | 3 hooks generated, you pick the best in review |
| Topic memory | Never repeats a topic, and does more of what performed |
| Character consistency | A LoRA per brand keeps recurring characters the same |
| Series mode | Auto-numbered "Lesson 1, 2, 3…", e.g. for a Japanese-learning page |
| Long → Shorts | Auto-cuts 3–5 Shorts from every long video |
| Overnight batch | Queue 10 jobs at night, review them in the morning |
| Crash-safe resume | Restarts from the last finished step, not from scratch |

---

## Tech stack (all open models)

| Concern | Tool |
|---|---|
| Writing / reasoning | **Qwen3** via Ollama |
| Images | **SDXL** via **ComfyUI** (+ per-brand LoRA) |
| Voice | **Kokoro** TTS |
| Captions | **Whisper** (word-level timestamps) |
| Rendering | **FFmpeg** |
| Orchestration | **LangGraph** |
| Backend | **FastAPI** |
| Database | **SQLite** to start, Postgres later (configurable URL) |
| Frontend | **Vue 3 + Vite** |
| Publishing | YouTube Data API, Facebook Graph API |

It runs on **local hardware (16GB target) or cloud GPUs with no code changes**.

**Video look:** animated stills (pan/zoom, parallax, overlays, transitions, captions), not real footage. Lip-sync and AI video clips need a cloud GPU. See [ARCHITECTURE.md §11–13](ARCHITECTURE.md).

---

## Setup (manual, macOS / Apple Silicon)

### Tools and models

| Name | Purpose | Size | Install |
|---|---|---|---|
| uv | Python env + packages | small | brew |
| FFmpeg **full** (with libass) | Render, captions | ~60 MB | brew (`ffmpeg-full`, not `ffmpeg`) |
| espeak-ng | Kokoro phonemes fallback | small | brew |
| Ollama + **Qwen3 8B** | Writing / scoring | ~5 GB | brew + `ollama pull` |
| Docker (Colima or Docker Desktop) + **SearXNG** | Web search | ~200 MB | docker |
| **ComfyUI** | Image generation server | ~3 GB (PyTorch) | git clone |
| **Animagine XL 4.0 (opt)** | Anime images | 6.9 GB | download |
| **Juggernaut XI** | Realistic images | 7.1 GB | download |
| **DMD2 LoRA** | Fast images (8 steps) | 0.4 GB | download |
| Kokoro-82M | Voice (fast, 54 voices) | ~0.3 GB | auto on first use |
| Chatterbox | Voice (emotion, cloning) | ~3 GB | auto on first use |
| Whisper large-v3-turbo (MLX) | Word timings | ~1.6 GB | auto on first use |

### Commands

```bash
# 1. System tools
brew install uv ffmpeg-full ollama espeak-ng   # if plain ffmpeg is installed: brew uninstall ffmpeg first
brew services start ollama
ollama pull qwen3:8b

# 2. Backend Python packages
cd backend && uv sync && cd ..

# 3. SearXNG (web search, port 8080, JSON enabled)
mkdir -p infra/searxng
cat > infra/searxng/settings.yml <<EOF
use_default_settings: true
server:
  secret_key: "$(openssl rand -hex 32)"
  limiter: false
search:
  formats: [html, json]
EOF
docker run -d --name searxng --restart unless-stopped -p 8080:8080 \
  -v "$PWD/infra/searxng:/etc/searxng" searxng/searxng

# 4. ComfyUI (outside the project)
mkdir -p ~/AI && cd ~/AI
git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git && cd ComfyUI
uv venv --python 3.12 && uv pip install -r requirements.txt

# 5. Image models (resumable downloads)
HF=https://huggingface.co
curl -L -C - -o models/checkpoints/animagine-xl-4.0-opt.safetensors \
  $HF/cagliostrolab/animagine-xl-4.0/resolve/main/animagine-xl-4.0-opt.safetensors
curl -L -C - -o models/checkpoints/Juggernaut-XI-byRunDiffusion.safetensors \
  $HF/RunDiffusion/Juggernaut-XI-v11/resolve/main/Juggernaut-XI-byRunDiffusion.safetensors
curl -L -C - -o models/loras/dmd2_sdxl_4step_lora_fp16.safetensors \
  $HF/tianweiy/DMD2/resolve/main/dmd2_sdxl_4step_lora_fp16.safetensors
```

### Run

```bash
# ComfyUI (keep running)
cd ~/AI/ComfyUI && .venv/bin/python main.py --listen 127.0.0.1 --port 8188

# Health check: all must be OK
cd backend && uv run python -m app.health
```

Service URLs and model names are set in `.env` (see `.env.example`). To use a different GPU machine (for example an NVIDIA PC), run ComfyUI there and set `COMFY_URL` to its address.

---

## Long-term direction
The same engine runs your own channels today and is designed to grow into a **SaaS platform for creators and businesses**: multi-tenant brands, per-user accounts and hosted GPU workers.
