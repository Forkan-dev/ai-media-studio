# Tasks & Progress

Legend: `[x]` done · `[~]` in progress · `[ ]` not started

See [README.md](README.md) for the product and [ARCHITECTURE.md](ARCHITECTURE.md) for design.

## Progress summary

| Phase | Goal | Status |
|---|---|---|
| 0 | Project setup | Done |
| 1 | Week 1–2: One video end to end | In progress |
| 2 | Week 3: Subtitles, music, thumbnails, both aspect ratios | Not started |
| 3 | Week 4: LangGraph flow, fact-check loop, job queue with resume | Not started |
| 4 | Week 5: Vue UI (Review screen first) | Not started |
| 5 | Week 6: YouTube + Facebook publishing and scheduling | Not started |
| 6 | Week 7+: Analytics feedback, Long→Shorts, AI clips, series mode | Not started |
| 7 | Future: SaaS readiness | Not started |

**Overall: 1 / 8 phases complete.** Update this table as phases finish.

---

## Phase 0: Project setup
- [x] Create folder structure (`backend/`, `frontend/`, `storage/`, `brands/`, `prompts/`, `workflows/`)
- [x] `git init`, `.gitignore` (storage/, .env, models)
- [x] Python 3.12 env (uv), `pyproject.toml`, FastAPI skeleton (`/health`)
- [x] `.env.example` + settings loader (`DATABASE_URL`, service URLs, storage path)
- [x] Install Ollama and FFmpeg
- [x] Pull Qwen3 8B
- [x] Install ComfyUI + SDXL (Animagine XL 4.0, Juggernaut XI, DMD2 LoRA)
- [x] Replace FFmpeg with `ffmpeg-full` (libass for captions)
- [x] Manual setup guide in README
- [x] Install Kokoro (54 voices) + `services/tts.py`
- [x] Install Chatterbox (emotion + voice cloning) as second TTS engine
- [x] Install Whisper (mlx-whisper, large-v3-turbo) + `services/whisper.py`
- [x] Set up web search (SearXNG in Docker/Colima, port 8080, JSON on)
- [x] Health-check script (`uv run python -m app.health`)

## Phase 1 (Week 1–2): One video end to end
**Goal:** run a CLI command and get one finished MP4.
- [ ] DB models: Brand, Job, Scene, Asset (SQLAlchemy, SQLite)
- [x] Brand YAML schema (Pydantic) + loader + first brand config (**Mind Facts**)
- [x] Doodle LoRA for SDXL + Mind Facts image style test (Doodle Redmond, testing only)
- [ ] Own Mind Facts doodle LoRA before monetized publishing (license-safe)
- [x] `services/llm.py`: Ollama client with JSON output (schema-constrained, Pydantic-validated)
- [x] Prompt templates as files (`prompts/<brand>/<role>.md`, `app/prompts.py`)
- [x] `services/search.py`: SearXNG search + page text fetch (trafilatura)
- [ ] **Script brain** (prompt template per role in `prompts/<brand>/`):
  - [ ] Topic discovery: ~30 candidates from search, dupes removed
  - [ ] Ranker: score topics (curiosity, relatable, humor, evidence, novelty) → best
  - [x] Research: 4 queries, 8 sources → facts, surprising details, myth/truth + source URLs (~1 min)
  - [x] Writer: 3 hooks + draft, uses research facts + reviewer feedback
  - [x] Script chain (`pipeline/script.py`): 2 drafts → review → max 2 rewrites → passed / below_quality
  - [x] Reviewer calibration: logic criterion, tagged weaknesses, weakness cap enforced in code, temperature 0
  - [ ] Editor: polish wording, flow, pacing, humor
  - [x] Reviewer: rubric scores + reasons + pass rule in code + per-hook accuracy check
  - [ ] Quality gate: pass rule, max 2 rewrites with critic notes, else `below_quality`
  - [~] Fact-check: all sentences in ONE thinking call (Qwen3.5 9B q4_K_M): 9/9 on test set, ~4–5 min. Not yet connected to the chain.
- [ ] **Pipeline flexibility** (see ARCHITECTURE §3 "Pipeline flexibility"):
  - [ ] `pipeline:` block in brand YAML (type, research, fact_check, sensitivity, review)
  - [ ] Adaptive research: extra rounds if facts < `min_facts`; skip topic if still not enough
  - [ ] Steps on/off per brand (e.g. no research/fact-check for fiction)
  - [ ] Sensitivity `high`: 2 sources per claim, Reviewer min 8, no jokes on sensitive part, disclaimer
  - [ ] Ranker flags sensitive topics → strict rules for that video only
- [ ] Storyboard: scenes with narration, image_prompt, camera move, transition, SFX cue
- [x] `services/comfy.py` + base SDXL workflow JSON → one image per scene
- [x] `services/tts.py`: Kokoro + Chatterbox narration
- [x] `services/render.py`: FFmpeg stills + pan/zoom + crossfade + audio + captions → MP4
- [ ] Save every step's output to `storage/{job_id}/` + DB
- [ ] CLI: `python -m app.cli make --brand <slug>`
- [ ] ✅ Milestone: first full video rendered

## Phase 2 (Week 3): Polish the output
- [x] `services/whisper.py`: word-level timestamps
- [x] Animated word-by-word captions (ASS) burned in (`services/captions.py`)
- [ ] Caption fix: active word baseline, position lower, bigger
- [ ] Parametric camera moves (start→end zoom/x/y, easing, random within brand limits)
- [ ] Shake / rotate / perspective moves for impact moments
- [ ] Sound effects library + SFX cues from storyboard (pop, whoosh, boing)
- [ ] Varied shot types (wide/medium/close-up) in storyboard
- [ ] Music library (royalty-free) + selection by brand music style
- [ ] Audio ducking (sidechain) under narration
- [ ] Scene transitions: random from brand's allowed `xfade` types
- [ ] 2.5D parallax from depth map
- [ ] Overlays: rain, sakura, light, particles
- [ ] Anime SDXL fine-tune (Animagine/Illustrious) workflow
- [ ] Music rotation (no repeat within 10 videos)
- [ ] 9:16 and 16:9 output (layout/crop per ratio)
- [ ] Long-form script template (separate from Shorts)
- [ ] **One brand makes both Shorts and long-form** (required): `formats: [short, long]` + duration per format in brand config (now: one format + one duration per brand)
- [ ] Thumbnail generation (SDXL + text overlay)
- [ ] Metadata: title, description, tags, hashtags
- [ ] ✅ Milestone: publish-ready Short and long-form video

## Phase 3 (Week 4): Orchestration and reliability
- [ ] LangGraph graph with all nodes
- [ ] Script brain steps as LangGraph nodes (discovery → ranking → research → write → edit → review → fact_check)
- [ ] Topic memory: skip topics already covered (Topic table + similarity)
- [ ] `reviewer_model` setting (e.g. Qwen3 14B as Reviewer)
- [ ] `below_quality` job status shown on dashboard
- [ ] Scheduler: add jobs per brand from its schedule
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
- [ ] **Video → Shorts clipper** (any long video, incl. gameplay; own/permitted content only)
  - [ ] Download with yt-dlp
  - [ ] Whisper transcript with word times
  - [ ] Qwen3 scores transcript segments (hook, peaks, jokes)
  - [ ] Gameplay: audio-peak + scene-change detection (FFmpeg, PySceneDetect)
  - [ ] Cut best 30–60s clips
  - [ ] 9:16 crop: face tracking (MediaPipe), split layout or blurred background for gameplay
  - [ ] Word-by-word captions + render
  - [ ] Clips go to the Review screen
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
| 2026-11-19 | Phase 0 done. Script brain design (Ranker/Writer/Editor/Reviewer + quality gate), Mind Facts brand, parametric camera moves, SFX. Wan video removed. |
