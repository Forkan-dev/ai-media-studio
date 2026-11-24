<script setup lang="ts">
import { computed, ref } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { AlertTriangle, ArrowLeft, RotateCcw } from 'lucide-vue-next'
import BaseButton from '@/components/BaseButton.vue'
import StatusBadge from '@/components/StatusBadge.vue'
import FinalPanel from '@/components/job/FinalPanel.vue'
import GateActions from '@/components/job/GateActions.vue'
import ImagesGate from '@/components/job/ImagesGate.vue'
import ResearchGate from '@/components/job/ResearchGate.vue'
import ScriptGate from '@/components/job/ScriptGate.vue'
import StepBar from '@/components/job/StepBar.vue'
import ThumbnailGate from '@/components/job/ThumbnailGate.vue'
import VoiceGate from '@/components/job/VoiceGate.vue'
import { useJob } from '@/composables/useJob'
import { api } from '@/api'

const route = useRoute()
const id = computed(() => Number(route.params.id))
const { page, error, load } = useJob(id)

const acting = ref(false) // approve / redo / save in progress
const actionError = ref('')

const job = computed(() => page.value?.job)
const vertical = computed(() => page.value?.format !== 'long')
const flags = computed(() => (job.value ? (job.value.flags[job.value.stage] ?? []) : []))
/** At a gate: waiting for the human, or redoing one image / voice line there. */
const atGate = computed(() => job.value?.status === 'waiting' || !!job.value?.action)
const pendingScene = computed(() => job.value?.action?.scene ?? null)

/** Suggested instructions for Redo: the warnings and the reviewer's points, ready to edit.
 *  null = this step takes no instructions. */
const redoNotes = computed(() => {
  const p = page.value
  if (job.value?.stage === 'research') return ''
  if (job.value?.stage !== 'script') return null
  const review = (p?.script?.review?.weaknesses ?? []).map(
    (w) => `Fix the ${w.criterion}: ${w.problem} ("${w.quote}")`,
  )
  return [...flags.value, ...review].join('\n')
})

const redoLabels: Record<string, string> = {
  storyboard: 'New scenes',
  images: 'Redraw all',
  voice: 'Record all again',
  thumbnail: 'New image',
}

const researchGate = ref<InstanceType<typeof ResearchGate>>()
const scriptGate = ref<InstanceType<typeof ScriptGate>>()

async function act(fn: () => Promise<unknown>) {
  acting.value = true
  actionError.value = ''
  try {
    await fn()
    await load()
  } catch (e) {
    actionError.value = (e as Error).message
  } finally {
    acting.value = false
  }
}

/** Saves the human's edits (if any), then approves the step. */
const approve = (auto: boolean) =>
  act(async () => {
    const p = page.value!
    if (job.value?.stage === 'research' && researchGate.value) {
      const draft = researchGate.value.draft
      if (JSON.stringify(draft) !== JSON.stringify(p.research)) {
        await api.put(`/studio/jobs/${id.value}/research`, draft)
      }
    }
    if (job.value?.stage === 'script' && scriptGate.value) {
      const text = scriptGate.value.draft
      if (text !== p.script?.text) await api.put(`/studio/jobs/${id.value}/script`, { text })
    }
    await api.post(`/studio/jobs/${id.value}/approve?auto=${auto}`)
  })

const redo = (notes = '') => act(() => api.post(`/studio/jobs/${id.value}/redo`, { notes }))
const setThumbnailText = (text: string) =>
  act(() => api.put(`/studio/jobs/${id.value}/thumbnail`, { text }))

const redraw = (scene: number, prompt?: string, style?: string) =>
  act(() => api.post(`/studio/jobs/${id.value}/scenes/${scene}/image`, { prompt, style }))
const checkImages = () => act(() => api.post(`/studio/jobs/${id.value}/images/check`))
const rerecord = (scene: number, text?: string) =>
  act(() => api.post(`/studio/jobs/${id.value}/scenes/${scene}/voice`, { text }))
</script>

<template>
  <p v-if="error && !page" class="text-sm text-bad">{{ error }}</p>

  <div v-if="page && job">
    <header class="mb-6 flex flex-wrap items-center justify-between gap-4">
      <div class="flex items-center gap-3">
        <RouterLink
          :to="`/studio/${job.brand}`"
          class="grid size-8 place-items-center rounded-lg text-muted hover:bg-surface hover:text-fg"
        >
          <ArrowLeft class="size-4" />
        </RouterLink>
        <div>
          <h2 class="text-lg font-semibold tracking-tight">{{ job.topic }}</h2>
          <p class="text-xs text-muted capitalize">
            {{ job.brand.replaceAll('_', ' ') }} · {{ job.style.replaceAll('_', ' ') }}
          </p>
        </div>
      </div>
      <StatusBadge :status="job.status" />
    </header>

    <StepBar :stages="page.stages" :job="job" class="mb-6" />

    <div v-if="flags.length && atGate" class="mb-5 space-y-1">
      <p v-for="f in flags" :key="f" class="flex items-start gap-2 text-sm text-warn">
        <AlertTriangle class="mt-0.5 size-4 shrink-0" />{{ f }}
      </p>
    </div>
    <p v-if="actionError" class="mb-5 text-sm whitespace-pre-line text-bad">{{ actionError }}</p>

    <!-- queued / working: live progress lines, the last one is happening now -->
    <div v-if="!atGate && (job.status === 'running' || job.status === 'queued')" class="mx-auto max-w-md py-16">
      <span
        v-if="!job.progress.length"
        class="mx-auto block size-5 animate-spin rounded-full border-2 border-accent border-t-transparent"
      />
      <ol class="space-y-2.5 border-l border-line pl-5">
        <li
          v-for="(line, i) in job.progress"
          :key="i"
          class="relative text-sm"
          :class="i === job.progress.length - 1 ? 'text-fg' : 'text-muted'"
        >
          <span
            class="absolute top-1.5 -left-[23px] size-1.5 rounded-full"
            :class="i === job.progress.length - 1 ? 'animate-pulse bg-accent' : 'bg-good'"
          />
          {{ line }}
        </li>
      </ol>
    </div>

    <!-- failed -->
    <div v-else-if="job.status === 'failed'" class="grid place-items-center gap-4 py-20 text-center">
      <AlertTriangle class="size-6 text-bad" />
      <p class="max-w-xl text-sm text-muted">{{ job.error }}</p>
      <BaseButton :loading="acting" @click="redo()"><RotateCcw class="size-4" />Retry</BaseButton>
    </div>

    <!-- finished -->
    <FinalPanel v-else-if="job.status === 'done'" :page="page" :vertical="vertical" />

    <!-- gates: the human's turn -->
    <template v-else>
      <ResearchGate
        v-if="job.stage === 'research' && page.research"
        ref="researchGate"
        :research="page.research"
      />
      <ScriptGate
        v-else-if="job.stage === 'script' && page.script"
        ref="scriptGate"
        :text="page.script.text"
        :review="page.script.review"
      />
      <ImagesGate
        v-else-if="job.stage === 'storyboard' || job.stage === 'images'"
        :mode="job.stage"
        :scenes="page.scenes"
        :styles="page.styles"
        :vertical="vertical"
        :pending="pendingScene"
        :checking="job.action?.type === 'check'"
        :busy="acting || !!job.action"
        @draw="redraw"
        @check="checkImages"
      />
      <VoiceGate
        v-else-if="job.stage === 'voice'"
        :scenes="page.scenes"
        :pending="pendingScene"
        @rerecord="rerecord"
      />
      <ThumbnailGate
        v-else-if="job.stage === 'thumbnail' && page.thumbnail"
        :thumbnail="page.thumbnail"
        :vertical="vertical"
        :saving="acting"
        @set-text="setThumbnailText"
      />

      <GateActions
        :busy="acting || !!job.action"
        :notes="redoNotes"
        :redo-label="redoLabels[job.stage] ?? 'Redo'"
        @redo="redo"
        @approve="approve"
      />
    </template>
  </div>
</template>
