# Tasks & Progress

Legend: `[x]` done · `[~]` in progress · `[ ]` not started

See [README.md](README.md) for the product and [ARCHITECTURE.md](ARCHITECTURE.md) for design.

## Progress summary

| Phase | Goal | Status |
|---|---|---|
| 0 | Project setup | In progress |
| 1 | Week 1–2: One video end to end | Not started |
| 2 | Week 3: Subtitles, music, thumbnails, both aspect ratios | Not started |
| 3 | Week 4: LangGraph flow, fact-check loop, job queue with resume | Not started |
| 4 | Week 5: Vue UI (Review screen first) | Not started |
| 5 | Week 6: YouTube + Facebook publishing and scheduling | Not started |
| 6 | Week 7+: Analytics feedback, Long→Shorts, AI clips, series mode | Not started |
| 7 | Future: SaaS readiness | Not started |

**Overall: 0 / 8 phases complete.** Update this table as phases finish.

---

## Phase 0: Project setup
- [x] Create folder structure (`backend/`, `frontend/`, `storage/`, `brands/`, `prompts/`, `workflows/`)
- [x] `git init`, `.gitignore` (storage/, .env, models)
- [x] Python 3.12 env (uv), `pyproject.toml`, FastAPI skeleton (`/health`)
- [x] `.env.example` + settings loader (`DATABASE_URL`, service URLs, storage path)
- [x] Install Ollama and FFmpeg
- [x] Pull Qwen3 8B
- [ ] Install ComfyUI + SDXL
- [x] Install Kokoro (54 voices) + `services/tts.py`
- [x] Install Chatterbox (emotion + voice cloning) as second TTS engine
- [x] Install Whisper (mlx-whisper, large-v3-turbo) + `services/whisper.py`
- [x] Set up web search (SearXNG in Docker/Colima, port 8080, JSON on)
- [x] Health-check script (`uv run python -m app.health`)

## Phase 1 (Week 1–2): One video end to end
**Goal:** run a CLI command and get one finished MP4.
- [ ] DB models: Brand, Job, Scene, Asset (SQLAlchemy, SQLite)
- [ ] Brand YAML schema (Pydantic) + loader + first brand config
- [ ] `services/llm.py`: Ollama client with JSON output
- [ ] Prompt templates: script (short), storyboard
- [ ] Script generation (hook, body, CTA)
- [ ] Storyboard: scenes with narration, image_prompt, camera_motion, on_screen_text
- [ ] `services/comfy.py` + base SDXL workflow JSON → one image per scene
- [ ] `services/tts.py`: Kokoro narration per scene
- [ ] `services/render.py`: FFmpeg stills + pan/zoom + concat audio → MP4
- [ ] Save every step's output to `storage/{job_id}/` + DB
- [ ] CLI: `python -m app.cli make --brand <slug>`
- [ ] ✅ Milestone: first full video rendered

## Phase 2 (Week 3): Polish the output
- [ ] `services/whisper.py`: word-level timestamps
- [ ] Animated word-by-word captions (ASS) burned in
- [ ] Music library (royalty-free) + selection by brand music style
- [ ] Audio ducking (sidechain) under narration
- [ ] Scene transitions (fade, slide, flash), varied per video
- [ ] 2.5D parallax from depth map
- [ ] Overlays: rain, sakura, light, particles
- [ ] Anime SDXL fine-tune (Animagine/Illustrious) workflow
- [ ] Music rotation (no repeat within 10 videos)
- [ ] 9:16 and 16:9 output (layout/crop per ratio)
- [ ] Long-form script template (separate from Shorts)
- [ ] Thumbnail generation (SDXL + text overlay)
- [ ] Metadata: title, description, tags, hashtags
- [ ] ✅ Milestone: publish-ready Short and long-form video

## Phase 3 (Week 4): Orchestration and reliability
- [ ] LangGraph graph with all nodes
- [ ] Topic research node: web search + trends + LLM scoring
- [ ] Topic memory: skip topics already covered (Topic table + similarity)
- [ ] Fact-check + quality node (scores hook, clarity, originality)
- [ ] Loop back to script when below threshold (max 2 retries)
- [ ] Hook A/B: generate 3 hooks
- [ ] Hook memory (past hooks passed as "do not reuse")
- [ ] Embeddings in sqlite-vec + script similarity check
- [ ] 5–10 rotating script structures per format
- [ ] Job queue: SQLite `jobs` table + single worker process
- [ ] `model_manager`: load/unload so only one heavy model is in memory
- [ ] Checkpointing + resume from last finished step after a crash
- [ ] Retry from any step
- [ ] Human approval via LangGraph `interrupt`
- [ ] FastAPI routes: brands, jobs, batch, retry, approve/reject
- [ ] WebSocket for live step progress + logs
- [ ] ✅ Milestone: queue 3 jobs, kill worker mid-run, it resumes correctly

## Phase 4 (Week 5): Vue dashboard
- [ ] Vue 3 + Vite + router + API client setup
- [ ] **Review screen** (first priority)
  - [ ] Video player
  - [ ] Scene-by-scene editable script
  - [ ] Regenerate one scene's image or voice → re-render
  - [ ] Hook picker (3 options)
  - [ ] Edit title, description, thumbnail
  - [ ] Fact-check report panel
  - [ ] Approve / Reject / Schedule
- [ ] Pipeline view: live progress, logs, retry from step
- [ ] Create screen: brand + format + duration, "Batch: make 10"
- [ ] Dashboard: running, awaiting approval, published today, views per brand
- [ ] Brands screen: edit config, LoRA, voice, music, schedule
- [ ] Settings: models, API keys
- [ ] ✅ Milestone: full review and approve flow from the browser

## Phase 5 (Week 6): Publishing
- [ ] DB models: Publish
- [ ] YouTube OAuth + upload + scheduled publish + AI disclosure flag
- [ ] Facebook Page OAuth + Reels/video upload + scheduling
- [ ] Scheduler: assign approved videos to brand's next time slot per platform
- [ ] Calendar screen with drag-to-reschedule
- [ ] Settings: account connections (OAuth) per brand
- [ ] Copyright-safe check (music only from licensed library)
- [ ] Near-duplicate video check before publish
- [ ] Quota handling + retry/backoff
- [ ] ✅ Milestone: approved video auto-publishes to YouTube and Facebook on schedule

## Phase 6 (Week 7+): Growth features
- [ ] DB model: Stat; analytics poller at 24h / 7d / 30d
- [ ] Analytics screen: views, retention, revenue per brand, top topics
- [ ] Feedback loop: winning topics/formats boost topic scoring
- [ ] Long → Shorts: auto-cut 3–5 Shorts from each long video
- [ ] Optional AI video clips for key scenes
- [ ] Series mode: auto-numbered "Lesson N"
- [ ] Character LoRA per brand (training guide + workflow)
- [ ] Overnight batch mode (scheduled queue of N jobs)
- [ ] ✅ Milestone: brands improve automatically from their own stats

## Phase 7 (Future): SaaS readiness
- [ ] Switch to Postgres via `DATABASE_URL`
- [ ] Multi-tenant: users, `owner_id` on brands, auth
- [ ] Object storage (S3-compatible) for `storage/`
- [ ] Multiple workers / remote GPU pool
- [ ] Billing and usage limits

---

## Changelog
| Date | Change |
|---|---|
| 2026-11-17 | Project docs created (README, ARCHITECTURE, TASKS). No code yet. |
| 2026-11-17 | Added models/limits, video look, uniqueness rules, search, sqlite-vec. |
