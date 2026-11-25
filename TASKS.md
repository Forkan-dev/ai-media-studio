# Tasks & Progress

Legend: `[x]` done · `[~]` in progress · `[ ]` not started · `[-]` dropped

See [README.md](README.md) for the product and [ARCHITECTURE.md](ARCHITECTURE.md) for design.

## Progress summary

| Phase | Goal | Status |
|---|---|---|
| 0 | Project setup | Done |
| 1 | Week 1–2: One video end to end | In progress |
| 2 | Week 3: Subtitles, music, thumbnails, both aspect ratios | Not started |
| 3 | Week 4: LangGraph flow, fact-check loop, job queue with resume | Not started |
| 4A | ClipForge: viral clips from long gaming videos | Not started |
| 4 | Week 5: Vue UI (Review screen first) | Not started |
| 5 | Week 6: YouTube + Facebook publishing and scheduling | Not started |
| 6 | Week 7+: Analytics feedback, Long→Shorts, AI clips, series mode | Not started |
| 7 | Future: SaaS readiness | Not started |

**Overall: 1 / 8 phases complete.** Update this table as phases finish.

## Next up (in this order)
1. **Before ClipForge** (things ClipForge depends on):
   - [ ] Commit the open work (Absurd Stories, story mode, emotion voice, per-brand reviewer)
   - [ ] Resume after crash: a job left `running` (process killed) can be continued from its stage
   - [ ] `model_manager`: only one heavy model in memory (LLM / SDXL / Whisper / Chatterbox); restart-safe ComfyUI (image 5 timed out from memory swap)
   - [ ] Caption fix: active word baseline, position, bigger (ClipForge reuses captions)
   - [ ] Audio ducking (sidechain): needed for ClipForge voice-over over game audio
   - [ ] 9:16 and 16:9 output from one render path (ClipForge makes both)
   - [ ] Chatterbox pace: brand `voice.speed` also for Chatterbox (time-stretch), pauses between sentences
2. **ClipForge** (gaming clipper, see Phase 4A)
3. **UI** (Phase 4: gates + ClipForge screens)

Paused: **Absurd Stories** brand (local 9B models cannot write good comedy: 5 tests, all ~6/10). Config kept.
Later: **Bring your own script**: per-brand `writer: local | gemini | manual` (free cloud model or pasted script).

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
- [~] DB models: Topic + Job done; Brand, Scene, Asset (SQLAlchemy, SQLite)
- [x] Brand YAML schema (Pydantic) + loader + first brand config (**Mind Facts**)
- [x] Doodle LoRA for SDXL + Mind Facts image style test (Doodle Redmond, testing only)
- [ ] Own Mind Facts doodle LoRA before monetized publishing (license-safe)
- [x] `services/llm.py`: Ollama client with JSON output (schema-constrained, Pydantic-validated)
- [x] Prompt templates as files (`prompts/<brand>/<role>.md`, `app/prompts.py`)
- [x] `services/search.py`: SearXNG search + page text fetch (trafilatura)
- [ ] **Script brain** (prompt template per role in `prompts/<brand>/`):
  - [x] Topic discovery (`pipeline/topics.py` + `services/topic_service.py`): 6 niche searches → LLM ideas → saved in DB `topics`; made videos + known topics skipped (~3 min)
  - [x] Ranker: curiosity, relatable, evidence, visual (1–10, average); `make` without `--topic` uses the best; topic marked `used` after the video
  - [x] Research: 4 queries, 8 sources → facts, surprising details, myth/truth + source URLs (~1 min)
  - [x] Writer: 3 hooks + draft, uses research facts + reviewer feedback
  - [x] Script chain (`pipeline/script.py`): 2 drafts → review → max 2 rewrites → passed / below_quality
  - [x] Reviewer calibration: logic criterion, tagged weaknesses, weakness cap enforced in code, temperature 0
  - [ ] Editor: polish wording, flow, pacing, humor
  - [x] Reviewer: rubric scores + reasons + pass rule in code + per-hook accuracy check
  - [ ] Quality gate: pass rule, max 2 rewrites with critic notes, else `below_quality`
  - [x] Fact-check: all sentences in ONE thinking call (Qwen3.5 9B q4_K_M): 9/9 on test set, ~4–5 min, connected to the chain
  - [x] Length gate: ±15% of brand target; Writer uses sentence count (13 words/sentence); repeated hook removed in code
  - [x] **Always produce, flag problems**: max 1 repair round, wrong sentences removed by code, status passed / needs_attention, `review.json` per video
  - [x] Research sorted into core fact / established / debated; reliable sources first
  - [x] Review criteria per brand (Mind Facts: relatability instead of humor)
  - [x] Image vision check (Qwen3.5) + `MAIN_CHARACTER` token; thumbnail (plan + SDXL + Impact text); metadata step
  - [x] CLI: `uv run python -m app.cli make --brand <slug> --topic "<topic>" --style <style>`
  - [x] Switched default LLM to Qwen3.5 9B q4_K_M (old Qwen3 8B removed)
- [~] **Pipeline flexibility** (see ARCHITECTURE §3 "Pipeline flexibility"):
  - [x] `pipeline:` block in brand YAML (research, fact_check); `script_mode` facts|story, `script_structures`, `topic_criteria`, `review_criteria`, `review_model`
  - [ ] Adaptive research: extra rounds if facts < `min_facts`; skip topic if still not enough
  - [x] Steps on/off per brand (e.g. no research/fact-check for fiction)
  - [x] Story mode: outline (rule, setup, 3 beats, punchline) before writing; stricter repeat removal
  - [x] Emotion voice: storyboard emotion per scene → Chatterbox intensity (`voice.scene_emotions`)
  - [x] Recurring characters in storyboard (named tokens replaced by one look)
  - [ ] Sensitivity `high`: 2 sources per claim, Reviewer min 8, no jokes on sensitive part, disclaimer
  - [ ] Ranker flags sensitive topics → strict rules for that video only
- [x] Storyboard: code splits scenes + picks motion/transition; LLM writes doodle image prompts; quoted text removed
- [x] `pipeline/produce.py`: storyboard → images + per-scene voice + captions → MP4 (reuses finished files)
- [x] First full Mind Facts video rendered (`storage/tests/first_video/final.mp4`, 66s, ~20 min)
- [ ] Image accuracy: faces mostly neutral, "spotlight" drawn as yellow head, story details missing
- [x] Captions: pass script text to Whisper; captions bottom-middle
- [ ] SFX cues in storyboard
- [x] `services/comfy.py` + base SDXL workflow JSON → one image per scene
- [x] `services/tts.py`: Kokoro + Chatterbox narration
- [x] `services/render.py`: FFmpeg stills + pan/zoom + crossfade + audio + captions → MP4
- [ ] Save every step's output to `storage/{job_id}/` + DB
- [x] CLI: `make --brand <slug>` (topic optional) + `topics --brand <slug> [--find]`
- [x] ✅ Milestone: first full video rendered

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
- [x] Scene transitions: random from brand's allowed `xfade` types
- [ ] 2.5D parallax from depth map
- [ ] Overlays: rain, sakura, light, particles
- [ ] Anime SDXL fine-tune (Animagine/Illustrious) workflow
- [ ] Music rotation (no repeat within 10 videos)
- [ ] 9:16 and 16:9 output (layout/crop per ratio)
- [ ] Long-form script template (separate from Shorts)
- [ ] **One brand makes both Shorts and long-form** (required): `formats: [short, long]` + duration per format in brand config (now: one format + one duration per brand)
- [x] Thumbnail generation (SDXL + text overlay, text in calmest band)
- [x] Metadata: title, description, tags, hashtags
- [ ] ✅ Milestone: publish-ready Short and long-form video

## Phase 3 (Week 4): Orchestration and reliability
- [-] LangGraph graph with all nodes (not needed: jobs + stages + gates cover it)
- [-] Script brain steps as LangGraph nodes (not needed)
- [x] Topic memory: skip topics already covered (Topic table + similarity)
- [x] `review_model` setting per brand (tested Gemma 4 12B: scores everything ~7.5, weak judge)
- [ ] `below_quality` job status shown on dashboard
- [ ] Scheduler: add jobs per brand from its schedule
- [ ] Hook memory (past hooks passed as "do not reuse")
- [ ] Embeddings in sqlite-vec + script similarity check
- [ ] 5–10 rotating script structures per format
- [x] Backend layers: models, Alembic migrations, schemas, repositories, services (TopicService, JobService, one Stage class per step), API routers; `services/` tools moved to `clients/`
- [x] Jobs (`services/job_service.py`, DB `jobs`): stages research → script → storyboard → images → render → thumbnail; pause at gates (research, script, images, thumbnail); approve / redo; failures saved on the job; CLI `make --gates`, `approve`, `redo`, `jobs`
- [ ] Job queue: SQLite `jobs` table + single worker process
- [ ] `model_manager`: load/unload so only one heavy model is in memory
- [ ] Checkpointing + resume from last finished step after a crash
- [x] Retry the current step (`redo`); stages read inputs from folder files, so edits are used
- [~] Human approval: done with job gates (no LangGraph needed so far)
- [~] FastAPI routes: topics (list, discover), jobs (list, get, create, approve, redo) done; brands, batch, edit files, single image redo to do
- [ ] WebSocket for live step progress + logs
- [ ] ✅ Milestone: queue 3 jobs, kill worker mid-run, it resumes correctly

## Phase 4A: ClipForge (viral clips from long gaming videos)
**Goal:** one long stream/gameplay video → 10–20 ranked viral moments → Shorts/Reels (9:16) + a 5–10 min
long-form highlight (16:9), with captions and optional voice-over. Own or permitted content only.
- [ ] **1. Source**: URL (yt-dlp) or local file; audio extract; Whisper transcript with word times;
      chat replay (streams) + "most replayed" heatmap when available; saved in DB (`sources`)
- [ ] **2. Detection**: per-second signals: chat spikes, heatmap, loudness peaks, scene changes, hype words
      → combined score → candidate moments
- [ ] **3. Ranking**: Qwen checks top candidates (why viral, title, score); good start (setup, sentence
      start) and finish (reaction settles, pause); 15–60 s; saved in DB (`clips`, ranked)
- [ ] **4. Short render**: 9:16 layouts (facecam stacked / center crop / blurred background, per channel
      config); word-by-word captions; original audio
- [ ] **5. Voice mode per clip**: original · voice-over (Chatterbox streamer-style lines, original ducked)
      · mix (voice-over hook, then original); lines editable at the gate
- [ ] **6. Long form**: top 8–15 moments in time order, 16:9, transitions, optional title cards, captions
- [ ] **7. Jobs + API**: ClipForge stages as a job (gates: pick clips, approve renders); routes
- [ ] Clean game audio for Whisper (Demucs vocal separation) if transcripts are noisy
- [ ] Metadata + thumbnail per clip (reuse)
- [ ] ✅ Milestone: 1-hour stream → ranked clips → 5 Shorts + 1 highlight video approved

## Phase 4 (Week 5): Vue dashboard
- [ ] **Approval gate after every step** (topics, research, script + rating, images, thumbnail): approve, edit, or keep as is and continue, even with a bad rating
- [ ] Images gate: regenerate single images, approve all, or reject the batch and regenerate all
- [ ] Thumbnail gate: config (auto text position, top / bottom, more) + LLM text options or own text
- [ ] Design: clean, minimal, professional (big-tech look); few buttons, little text
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
- [ ] Brand studio: "Get topics" button (runs discovery) + saved topics list (best first, used topics hidden) → pick one → make video
- [ ] Settings: models, API keys
- [ ] **ClipForge screens**: add source (URL / file) → progress → ranked clip list (score, reason, title)
      → clip preview with trim handles, layout picker, voice toggle (original / voice-over / mix),
      editable voice-over lines and captions → approve → long-form builder (pick + reorder moments)
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
- [ ] Video → Shorts clipper: moved to **Phase 4A ClipForge**
- [ ] Optional AI video clips for key scenes
- [ ] Series mode: auto-numbered "Lesson N"
- [ ] Character LoRA per brand (training guide + workflow)
- [ ] Overnight batch mode (scheduled queue of N jobs)
- [ ] ✅ Milestone: brands improve automatically from their own stats

## Phase 7 (Future): SaaS readiness
- [ ] Switch to Postgres via `DATABASE_URL`
- [ ] Multi-tenant: users, `owner_id` on brands, auth
- [ ] RBAC: roles (owner, editor, viewer) checked in the API layer; UI hides actions a role cannot do
- [ ] API security in the BFF: authentication, rate limiting and throttling (per user / IP), request size limits
- [ ] Tests: API (TestClient) and BFF tests; CI runs `pytest` on every push (service tests exist: `backend/tests`)
- [ ] Object storage (S3-compatible) for `storage/`
- [ ] Multiple workers / remote GPU pool
- [ ] Billing and usage limits

---

## Changelog
| Date | Change |
|---|---|
| 2026-11-17 | Project docs created (README, ARCHITECTURE, TASKS). No code yet. |
| 2026-11-17 | Added models/limits, video look, uniqueness rules, search, sqlite-vec. |
| 2026-11-24 | Architecture: UI → BFF (`bff/`, :8000) → system backend (`backend/`, :8001); system split into `core` + `modules/studio` + `modules/clipforge`. Brands moved to DB (full config). Frontend: Vue (create-vue) + Tailwind, "Framewise". |
| 2026-11-24 | Absurd Stories paused. New Phase 4A ClipForge (gaming clipper). "Next up" order: prerequisites → ClipForge → UI. |
| 2026-11-19 | Phase 0 done. Script brain design (Ranker/Writer/Editor/Reviewer + quality gate), Mind Facts brand, parametric camera moves, SFX. Wan video removed. |
