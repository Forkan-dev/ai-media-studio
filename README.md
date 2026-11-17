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

## Long-term direction
The same engine runs your own channels today and is designed to grow into a **SaaS platform for creators and businesses**: multi-tenant brands, per-user accounts and hosted GPU workers.
