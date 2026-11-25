// Small typed client for the BFF (the dev server forwards /api to it).

export interface Brand {
  slug: string
  name: string
  niche: string
  tone: string
  preset: string
  format: string
  duration: number
  default_style: string
  styles: string[]
}

export interface Preset {
  name: string
  description: string
}

export interface ImageStyle {
  lora_weight: number
  character: string
  others: string
  style: string
  negative: string
}

/** The full brand config (every parameter), edited on the settings screen. */
export interface BrandConfig {
  slug: string
  name: string
  niche: string
  language: string
  tone: string
  format: 'short' | 'long'
  duration: number
  preset: 'facts' | 'story'
  voice: {
    engine: 'kokoro' | 'chatterbox'
    voice: string
    speed: number
    voice_ref: string | null
    exaggeration: number
    cfg_weight: number
    scene_emotions: boolean
  }
  images: {
    checkpoint: string
    lora: string | null
    default_style: string
    styles: Record<string, ImageStyle>
    steps: number
    cfg: number
    sampler: string
    scheduler: string
  }
  look: {
    motions: string[]
    transitions: string[]
    transition_seconds: number
    caption_font_size: number
    caption_max_words: number
  }
  pipeline: { research: boolean; fact_check: boolean }
  min_quality_score: number
  review_criteria: string[]
  review_model: string | null
  script_structures: string[]
  script_mode: 'facts' | 'story'
  topic_criteria: string[]
}

export interface Topic {
  id: number
  title: string
  angle: string
  score: number
  scores: Record<string, number>
}

export type JobStatus = 'queued' | 'running' | 'waiting' | 'failed' | 'done'

export interface Job {
  id: number
  brand: string
  topic: string
  style: string
  stage: string
  status: JobStatus
  flags: Record<string, string[]>
  progress: string[] // live lines of the running stage
  action: { type: string; scene?: number } | null // a queued change at the gate (one image / voice line)
  error: string
  created_at: string
}

export interface Finding {
  text: string
  sources: number[]
}

export interface ResearchResult {
  research: {
    core_fact: Finding
    established: Finding[]
    debated: Finding[]
    surprising_details: Finding[]
    misconceptions: { myth: string; truth: string; sources: number[] }[]
  }
  urls: string[]
}

export interface ScriptReview {
  status: string
  review_scores: Record<string, number>
  review_average: number
  weaknesses: { criterion: string; quote: string; problem: string }[]
  removed_sentences: string[]
  versions?: { structure: string; score: number; text: string; best: boolean }[]
}

export interface Scene {
  narration: string
  image_prompt: string
  image: string | null
  audio: string | null
  seconds: number | null
  style: string // this scene's image style
  check: { ok: boolean; reason: string } | null // vision check, when run
  outdated: boolean // the prompt or style changed after the image was drawn
}

/** Everything the job screen shows, in one call. */
export interface JobPage {
  job: Job
  format: 'short' | 'long'
  styles: string[] // the brand's image styles
  stages: { name: string; gate: boolean }[]
  research: ResearchResult | null
  script: { text: string; review: ScriptReview | null } | null
  scenes: Scene[]
  thumbnail: { plan: { text: string; text_options: string[] }; image: string | null } | null
  metadata: { youtube_title: string; youtube_description: string; tags: string[]; hashtags: string[] } | null
  video: string | null
}

export type BrandOptions = Record<
  | 'review_criteria'
  | 'motions'
  | 'transitions'
  | 'engines'
  | 'formats'
  | 'script_modes'
  | 'kokoro_voices',
  string[]
>

interface ValidationError {
  loc: (string | number)[]
  msg: string
}

/** Readable message from an API error body (validation errors name the field). */
function errorMessage(detail: unknown, fallback: string): string {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return (detail as ValidationError[])
      .map((d) => `${d.loc.slice(1).join(' › ')}: ${d.msg.replace(/^Value error, /, '')}`)
      .join('\n')
  }
  return fallback
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(errorMessage(body.detail, `${res.status} ${res.statusText}`))
  }
  return res.json()
}

const send = (method: string, body?: unknown) => ({
  method,
  body: body === undefined ? undefined : JSON.stringify(body),
})

export const api = {
  get: <T>(path: string) => request<T>(path),
  /** multipart upload (field "file"); no JSON content type so the browser sets the boundary */
  upload: <T>(path: string, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return request<T>(path, { method: 'POST', body: form, headers: {} })
  },
  post: <T>(path: string, body?: unknown) => request<T>(path, send('POST', body)),
  put: <T>(path: string, body: unknown) => request<T>(path, send('PUT', body)),
}
