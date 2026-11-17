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
topic_research → script → storyboard → fact_check ──(score < threshold, retries < 2)──► script
                                           │
                                           ▼ pass
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
| `topic_research` | brand config, topic history, past stats | ranked topic list and chosen topic | web search + LLM |
| `script` | topic, format (short/long), prompt template | hook ×3, body, CTA | LLM |
| `storyboard` | script | scenes[]: narration, image_prompt, camera_motion, on_screen_text | LLM |
| `fact_check` | script + search results | claims report, scores (hook, clarity, originality) | search + LLM |
| `visuals` | scenes, brand style, LoRA | image per scene (+ optional AI clip) | ComfyUI / SDXL |
| `voice` | scene narration, brand voice | audio per scene | Kokoro |
| `subtitles` | scene audio | word timings → caption file (ASS) | Whisper |
| `render` | images, audio, captions, music | `final_9x16.mp4` / `final_16x9.mp4` | FFmpeg |
| `thumbnail_metadata` | script, topic | title, description, tags, hashtags, thumbnail | LLM + SDXL |
| `human_approval` | everything above | approve / reject / edits / schedule | UI |
| `publish` | approved job, schedule slot | platform video IDs | YouTube / Facebook API |
| `analytics` | platform IDs | Stat rows at 24h / 7d / 30d | platform APIs |

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
| **Job** | id, brand_id, format (short/long/both), duration, status (queued/running/awaiting_approval/approved/scheduled/published/failed/rejected), current_step, retries, topic, script_json, scores_json, fact_check_json, error, created/updated |
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
| `tts.py` | Kokoro narration per scene |
| `whisper.py` | Word-level timestamps |
| `render.py` | FFmpeg graph building: Ken Burns, transitions, ducking, ASS captions, aspect ratios |
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
| Text | Qwen3 8B (Ollama) | Can confirm false facts. Fact-check only against search results. |
| Search | SearXNG (self-hosted) or Brave Search API | Needed for topic research + fact-check. |
| Images | SDXL + anime/realistic fine-tune + brand LoRA | Slowest step (~20–60s/image). No text in images: all text through FFmpeg. |
| Voice | Kokoro | Languages: EN, JA, ZH, ES, FR, HI, IT, PT only. |
| Captions | Whisper (mlx-whisper / whisper.cpp on Mac) | none |
| Embeddings | Small embedding model + sqlite-vec / numpy | For dedupe only. No RAG, no separate vector DB. |

- One heavy model in memory at a time.
- Approximate time: Short (~10 scenes) 10–20 min; long (~60 scenes) 1h+.
- **Not in scope locally:** real footage, lip-sync (LatentSync/MuseTalk), AI video clips (Wan). These need a cloud GPU.
- **Do not use collected anime/TV footage.** It is copyrighted, so Content ID claims mean no monetization.

## 12. Video look

Still images, one every 3–5s, with:
- Pan/zoom (Ken Burns) and 2.5D parallax from a depth map
- Transitions: fade, slide, flash (FFmpeg `xfade`)
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

## 14. Deployment modes
| Mode | How |
|---|---|
| Local (16GB) | Ollama, ComfyUI and Kokoro on localhost. One worker. Models swapped sequentially. |
| Cloud GPU | Same code. Service URLs point to remote GPU hosts in `.env`. |
| SaaS (future) | Postgres, multi-tenant `owner_id` on Brand, multiple workers, object storage (S3) instead of local `storage/` |
