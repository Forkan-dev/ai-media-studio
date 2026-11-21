# Architecture

See [README.md](README.md) for what the product does and [TASKS.md](TASKS.md) for build progress.

## 1. High-level overview

```
┌──────────────┐     ┌──────────────┐     ┌────────────────────────────────┐
│  Vue 3 UI    │ ──► │   FastAPI    │ ──► │ Job queue (SQLite table)       │
│  (Vite)      │ ◄── │   REST + WS  │     │ + 1 worker process             │
└──────────────┘     └──────────────┘     └───────────────┬────────────────┘
                                                          ▼
                                          ┌────────────────────────────────┐
                                          │       LangGraph pipeline       │
                                          │ (checkpointed after each node) │
                                          └───────────────┬────────────────┘
                                                          ▼
              ┌──────────┬──────────┬──────────┬──────────┬──────────┐
              │  Ollama  │ ComfyUI  │  Kokoro  │ Whisper  │  FFmpeg  │
              │ (Qwen3)  │  (SDXL)  │  (TTS)   │  (STT)   │ (render) │
              └──────────┴──────────┴──────────┴──────────┴──────────┘
                         run ONE AT A TIME (GPU/RAM limit)
                                                          ▼
                                          ┌────────────────────────────────┐
                                          │ Approval queue (LangGraph      │
                                          │ interrupt) → Review screen     │
                                          └───────────────┬────────────────┘
                                                          ▼
                                          ┌────────────────────────────────┐
                                          │ Scheduler → YouTube / Facebook │
                                          │ Analytics poller (24h/7d/30d)  │
                                          └────────────────────────────────┘
```

## 2. Core design decisions

| # | Decision | Reason |
|---|---|---|
| D1 | **One worker, one job at a time** | 16GB can't hold the LLM, SDXL, TTS and Whisper together. Models load and unload in sequence. |
| D2 | **Every step saves output to disk + DB** | A crash resumes from the last finished step instead of restarting the job. |
| D3 | **Brands are YAML/DB configs, not code** | A new page is a new config, with no code change. |
| D4 | **SQLite first, DB URL configurable** | Simple start. Move to Postgres later by changing `DATABASE_URL`. |
| D5 | **Services behind interfaces** | The same code runs on local or cloud GPUs. Only endpoints/URLs in config change. |
| D6 | **Human approval is mandatory** | Nothing publishes without review (LangGraph `interrupt`). |
| D7 | **Scene is the unit of work** | Allows regenerating one scene's image or voice and re-rendering cheaply. |

## 3. Pipeline (LangGraph nodes)

```
topic_discovery → topic_ranking → research → write → edit → review ──(below minimum, retries < 2)──► write
                                                                   │                                (with critic notes)
                                                                   │ still below minimum after 2 retries
                                                                   ├──────────────► status = below_quality (never uploaded)
                                                                   ▼ pass
                                                              fact_check → storyboard
                                                                   │
                                                                   ▼
                visuals → voice → subtitles → render → thumbnail_metadata
                                                             │
                                                             ▼
                                                   human_approval (interrupt)
                                                             │
                                          ┌──────────────────┼──────────────────┐
                                     reject│        regenerate scene X          │approve
                                          ▼                  ▼                   ▼
                                        END       visuals/voice(scene X)      publish
                                                   → render → approval           │
                                                                                 ▼
                                                                  analytics (24h / 7d / 30d)
                                                                                 │
                                                                                 ▼
                                                                feeds topic_research scoring
```

| Node | Input | Output | Service |
|---|---|---|---|
| `topic_discovery` | brand niche, search queries | ~30 candidate topics (dupes vs. topic memory removed) | SearXNG + LLM |
| `topic_ranking` | candidates, past stats | scored list (curiosity, relatable, humor potential, evidence, novelty) → best topic | LLM (**Ranker**) |
| `research` | chosen topic | research notes: key facts + source URLs (3–5 sources) | SearXNG + page fetch + LLM |
| `write` | research notes, brand tone, script structure, critic notes (on retry) | 3 hooks + 2–3 full script drafts | LLM (**Writer**) |
| `edit` | drafts | polished drafts: wording, sentence flow, pacing, humor, length | LLM (**Editor**) |
| `review` | polished drafts, research notes | rubric scores + reasons per draft → best draft, pass / fail | LLM (**Reviewer**) |
| `fact_check` | best draft + research notes | claim-by-claim report; unsupported claims removed | LLM |
| `storyboard` | final script, brand look | scenes[]: narration, image_prompt, camera move, transition, SFX cue, caption emphasis | LLM |
| `visuals` | scenes, brand style, LoRA | image per scene (+ optional AI clip) | ComfyUI / SDXL |
| `voice` | scene narration, brand voice | audio per scene | Kokoro or Chatterbox |
| `subtitles` | scene audio | word timings → caption file (ASS) | Whisper |
| `render` | images, audio, captions, music | `final_9x16.mp4` / `final_16x9.mp4` | FFmpeg |
| `thumbnail_metadata` | script, topic | title, description, tags, hashtags, thumbnail | LLM + SDXL |
| `human_approval` | everything above | approve / reject / edits / schedule | UI |
| `publish` | approved job, schedule slot | platform video IDs | YouTube / Facebook API |
| `analytics` | platform IDs | Stat rows at 24h / 7d / 30d | platform APIs |

### Script quality gate (minimum quality to upload)

The goal is not "perfect". The goal is that **no video below a minimum bar is ever uploaded**.

- **AI roles:** each role is a separate prompt with its own instructions and temperature.

  | Role | Job | Temperature |
  |---|---|---|
  | Ranker | Picks the topic | low |
  | Writer | Creates hooks and drafts | high |
  | Editor | Fixes sentences | medium |
  | Reviewer | Judges the drafts | low |

- **Rubric (each criterion scored 1–10):** hook, accuracy vs. research notes, clarity, humor/tone fit, pacing, originality.
- **Pass rule:** average ≥ `min_quality_score` (brand config, default 7) **and** no criterion below 5 **and** accuracy ≥ 7.
- **Fail:** the Writer rewrites using the Reviewer's notes, up to 2 retries.
- **Still failing after 2 retries:** job status `below_quality`. It is shown on the dashboard and never sent to approval or upload.
- **Bias control:** the Reviewer never sees which draft is newest, compares several candidates, and can run on a larger model (`reviewer_model` in Settings, e.g. Qwen3 14B).
- **Human review stays the final gate** before publishing.

### Pipeline flexibility (business requirement)

The flow is **not** identical for every brand or topic. It has one shared skeleton with three levels of flexibility:

1. **Per brand (YAML `pipeline:` block):** steps can be turned on or off and tuned.
   - Fiction or storytelling brand: `research: off`, `fact_check: off`.
   - A truly different flow (e.g. Video → Shorts clipper) is a separate `pipeline.type`.
   ```yaml
   pipeline:
     type: script_video          # script_video | clipper
     research: { min_facts: 6, max_rounds: 2 }
     fact_check: { required: true, min_sources_per_claim: 1 }
     sensitivity: normal         # normal | high
     review: { min_score: 7, max_rewrites: 2 }
   ```
2. **Per topic (automatic):**
   - **Little information online:** if research finds fewer than `min_facts`, it runs another round with more queries and pages, up to `max_rounds`.
   - **Still not enough:** the topic is skipped and the Ranker picks the next one. No script is written without enough facts.
3. **Sensitivity (per brand or per topic):**
   - `sensitivity: high` (e.g. health, finance) means:
     - every claim needs 2 sources
     - Reviewer minimum 8
     - no jokes about the sensitive part
     - a disclaimer line if needed
   - The Ranker can flag a single topic as sensitive (e.g. mental illness in Mind Facts), and the strict rules apply to that video only.

### Walkthrough: one Mind Facts video

1. **Topic discovery** searches psychology topics and finds ~30 candidates. Already-used topics are removed.
2. **Ranker** scores them and picks **"the spotlight effect"**.
3. **Research** reads 8 sources and extracts:
   - 8 facts, e.g. the T-shirt study: ~50% guessed vs. ~25% noticed
   - surprising details, e.g. the Barry Manilow T-shirt
   - 3 myth/truth pairs
4. **Writer** writes 3 hooks and 2 drafts from that research, using one topic for one video.
5. **Editor** polishes them. **Reviewer** scores them, and the best passing draft wins. Otherwise the Writer rewrites (max 2), or the job ends as `below_quality`.
6. **Fact-check** checks each claim against the research.
7. **Storyboard** produces scenes with narration, a doodle image prompt, motion, transition and SFX.
8. **Visuals** (doodle LoRA), **voice**, **captions** and **render** produce the 9:16 video. Then the thumbnail and title.
9. **Human review**, then publish. Stats feed back into the Ranker.
10. The next video uses the next best topic.

### Continuous production

- A **scheduler** adds jobs for each brand from its schedule (e.g. 3 per day).
- **One worker** processes them in order and resumes after a crash.
- Finished videos wait on the Review screen.

**Resume model:** each node writes its artifacts to `storage/{job_id}/...` and a row in DB (`Job.current_step`, `Asset`). LangGraph checkpointer uses SQLite. On restart, the worker picks up `running` jobs and continues from the last checkpoint.

## 4. Data model (`app/models/`)

```
Brand ──< Job ──< Scene ──< Asset
  │        │
  │        └──< Publish ──< Stat
  └──< Topic (history / memory)
```

| Table | Key fields |
|---|---|
| **Brand** | id, slug, name, niche, language, voice, visual_style, lora, music_style, prompt_set, schedule (cron per platform), accounts, series_counter, rules |
| **Job** | id, brand_id, format (short/long/both), duration, status (queued/running/below_quality/awaiting_approval/approved/scheduled/published/failed/rejected), current_step, retries, topic, script_json, scores_json, fact_check_json, error, created/updated |
| **Scene** | id, job_id, index, narration, image_prompt, camera_motion, on_screen_text, duration, version |
| **Asset** | id, job_id, scene_id?, kind (image/clip/audio/captions/render/thumbnail/music), path, meta_json, version |
| **Publish** | id, job_id, platform, scheduled_at, published_at, platform_video_id, status, ai_disclosure |
| **Stat** | id, publish_id, checkpoint (24h/7d/30d), views, watch_time, retention, ctr, revenue |
| **Topic** | id, brand_id, title, embedding/hash, job_id, performance_score |

## 5. Brand config (YAML)

```yaml
# backend/brands/japanese_daily.yaml
slug: japanese_daily
name: Japanese Daily
niche: japanese-language-lessons
language: en
formats: [short, long]
duration: { short: 45, long: 480 }
voice: { engine: kokoro, voice_id: af_bella, speed: 1.0 }
visual_style:
  base_prompt: "anime style, soft lighting, clean lines"
  negative_prompt: "text, watermark, blurry"
  lora: { name: jd_characters, weight: 0.8 }
  workflow: sdxl_lora.json
characters: [ { name: Yuki, trigger: "yuki_jd" } ]
music: { style: lofi, library: royalty_free/lofi, duck_db: -18 }
prompts: { set: language_lesson }
series: { enabled: true, pattern: "Lesson {n}" }
schedule:
  youtube:  { cron: "0 17 * * *", formats: [short, long] }
  facebook: { cron: "0 19 * * *", formats: [short] }
look:
  scene_seconds: [3, 5]
  motions: [zoom_in, zoom_out, pan_left, pan_right, parallax]
  transitions: [fade, slide, flash]
  overlays: [sakura, light]
  captions: { style: word_pop, position: center }
uniqueness:
  script_structures: [question, list, story, myth_vs_fact, comparison]
  hook_memory: true
  music_no_repeat_within: 10
  hook_temperature: 0.9
rules: { ai_disclosure: true, min_quality_score: 7, dedupe_threshold: 0.85 }
```

All values above are editable per brand on the Brands screen. Global defaults (models, service URLs) are on the Settings screen.

## 6. Services layer (`app/services/`)

Each service is a thin client with one interface, configured by URL/env, so local and cloud are the same code.

| Service | Responsibility |
|---|---|
| `llm.py` | Ollama chat / JSON-mode calls (Qwen3), prompt template rendering |
| `search.py` | Web search + trend sources for research and fact-check |
| `comfy.py` | Submit ComfyUI workflow JSON, poll, download images |
| `tts.py` | Narration per scene: Kokoro (fast) or Chatterbox (emotion, voice cloning) |
| `whisper.py` | Word-level timestamps |
| `captions.py` | Word timings → animated word-by-word ASS captions |
| `render.py` | FFmpeg graph building: camera moves, transitions, SFX, ducking, captions, aspect ratios |
| `youtube.py` | OAuth, upload, schedule, AI-disclosure flag, stats |
| `facebook.py` | Page token, upload Reels/videos, schedule, insights |
| `dedupe.py` | Topic and script similarity checks (embeddings/hash) |
| `model_manager.py` | Load/unload models so only one heavy model is in memory |

## 7. API (`app/api/`)

| Area | Endpoints (sketch) |
|---|---|
| Brands | `GET/POST/PUT/DELETE /brands` |
| Jobs | `POST /jobs` (single), `POST /jobs/batch` (n), `GET /jobs`, `GET /jobs/{id}`, `POST /jobs/{id}/retry?from_step=` |
| Live | `WS /jobs/{id}/events`: step progress and logs |
| Review | `PUT /jobs/{id}/script`, `POST /jobs/{id}/scenes/{n}/regenerate?part=image\|voice`, `PUT /jobs/{id}/metadata`, `POST /jobs/{id}/hook`, `POST /jobs/{id}/approve`, `POST /jobs/{id}/reject` |
| Schedule | `GET /calendar`, `PUT /publish/{id}` (reschedule) |
| Analytics | `GET /analytics?brand=`, `GET /analytics/topics` |
| Settings | `GET/PUT /settings`, `GET /oauth/{platform}/start`, `GET /oauth/{platform}/callback` |
| Media | `GET /media/{job_id}/{path}` (serve storage) |

## 8. Frontend screens (`frontend/`)

| Screen | Purpose |
|---|---|
| Dashboard | Running jobs, awaiting approval, published today, views per brand |
| Brands | Edit brand config, connected accounts |
| Create | Brand + format + duration → generate; "Batch: make 10" |
| Pipeline view | Live per-step progress, logs, retry from any step |
| **Review** (most important) | Player, scene-by-scene script editor, per-scene regenerate, hook picker, metadata/thumbnail editor, fact-check panel, Approve/Reject/Schedule |
| Calendar | Scheduled posts per brand/platform, drag to reschedule |
| Analytics | Views, retention, revenue per brand; top topics |
| Settings | Models, API keys, OAuth connections |

## 9. Folder structure

```
backend/
  app/api/          # FastAPI routes
  app/pipeline/     # LangGraph graph + nodes
  app/services/     # llm, comfy, tts, whisper, render, youtube, facebook
  app/models/       # DB tables: Brand, Job, Scene, Asset, Publish, Stat
  brands/           # YAML brand configs
  prompts/          # prompt templates per niche + format
  workflows/        # ComfyUI JSON workflows
storage/            # images, audio, renders per job
frontend/           # Vue 3 + Vite
```

Storage layout per job:
```
storage/{job_id}/
  script.json  storyboard.json  fact_check.json
  scenes/{n}/image_v{k}.png  audio_v{k}.wav  words.json
  captions.ass  music.mp3
  final_9x16.mp4  final_16x9.mp4  thumbnail.png  metadata.json
```

## 10. Platform and compliance rules
- **AI disclosure**: the "altered/synthetic content" flag is set on every upload by default.
- **Copyright-safe assets**: music comes only from a licensed or royalty-free library folder. Images are generated, never scraped.
- **Duplicate blocking**: topic and script similarity against the brand's history blocks near-duplicates before generation and again before publish.
- **Rate and quota awareness**: the publisher respects YouTube API quotas and backs off with retries.

## 11. Models and limits (16GB Apple M5)

| Step | Model | Limit / note |
|---|---|---|
| Text | Qwen3.5 9B `q4_K_M` (Ollama) | Misses reversed claims ("more" vs "less") without thinking. Fact-check uses ONE thinking call per script (~4–5 min, 9/9 on test set). NVFP4 tag has no JSON output in Ollama. |
| Search | SearXNG (self-hosted) or Brave Search API | Needed for topic research + fact-check. |
| Images | SDXL + anime/realistic fine-tune + brand LoRA | Slowest step (~20–60s/image). No text in images: all text through FFmpeg. |
| Voice | Kokoro (54 voices) | Fast. No emotion control. Languages: EN, JA, ZH, ES, FR, HI, IT, PT only. |
| Voice (emotion) | Chatterbox | Emotion (`exaggeration`) + voice cloning. ~20× slower than Kokoro. |
| Captions | Whisper (mlx-whisper / whisper.cpp on Mac) | none |
| Embeddings | Small embedding model + sqlite-vec / numpy | For dedupe only. No RAG, no separate vector DB. |

- One heavy model in memory at a time.
- Approximate time: Short (~10 scenes) 10–20 min; long (~60 scenes) 1h+.
- **Not in scope locally:** real footage, lip-sync (LatentSync/MuseTalk), AI video clips (Wan). These need a cloud GPU.
- **Do not use collected anime/TV footage.** It is copyrighted, so Content ID claims mean no monetization.

## 12. Video look

Still images, one every 2–5s, with:
- **Parametric camera moves:** each move = start (zoom, x, y) → end (zoom, x, y) with easing, randomized within brand limits. Gives unlimited variations, not a fixed list.
- Extra moves: shake on impact words, slow rotate, perspective tilt
- 2.5D parallax from a depth map
- Transitions: any of ~50 FFmpeg `xfade` types, limited per brand (e.g. playful: slide, circle open, zoom, pixelize)
- Sound effects (pop, whoosh, boing) on scene changes and jokes, cued by the storyboard
- Overlays: rain, sakura, light, particles
- Word-by-word captions, narration, ducked music
- Same characters through the brand LoRA

## 13. Uniqueness (anti-repetition)

Platforms demonetize repetitive or mass-produced content. Every video must differ in content and structure:
- Topic memory + topic similarity check
- Script similarity check (embeddings vs. brand history)
- Hook memory: past hooks are passed to the LLM as "do not reuse"
- 5–10 script structures per format, rotated (question, list, story, myth vs. fact, comparison)
- Music rotation: no repeat within 10 videos
- Varied camera motions and transitions
- New random seed per image; higher temperature for hooks

## 14. First brand: Mind Facts

| Setting | Value |
|---|---|
| Niche | Psychology facts |
| Image style | Doodle (fixed for every video), using SDXL with a doodle LoRA |
| Tone | Funny, smart, simple |
| Transitions | Playful: slide, circle open, zoom, pixelize |
| Sound | SFX (pop, whoosh, boing) and light music |
| Voice | One fixed, energetic voice |
| Format | 9:16 Shorts, ~60s |

## 15. Deployment modes
| Mode | How |
|---|---|
| Local (16GB) | Ollama, ComfyUI and Kokoro on localhost. One worker. Models swapped sequentially. |
| Cloud GPU | Same code. Service URLs point to remote GPU hosts in `.env`. |
| SaaS (future) | Postgres, multi-tenant `owner_id` on Brand, multiple workers, object storage (S3) instead of local `storage/` |
