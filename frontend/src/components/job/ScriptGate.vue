<script setup lang="ts">
/** Script gate: the best version in the editor, its review, and every version to compare or copy. */
import { computed, ref } from 'vue'
import { ArrowUpToLine, Check, Copy } from 'lucide-vue-next'
import BaseCard from '@/components/BaseCard.vue'
import ScoreDot from '@/components/ScoreDot.vue'
import type { ScriptReview } from '@/api'

const props = defineProps<{ text: string; review: ScriptReview | null }>()
const draft = ref(props.text)
const words = computed(() => draft.value.split(/\s+/).filter(Boolean).length)
const versions = computed(() => [...(props.review?.versions ?? [])].sort((a, b) => b.score - a.score))

const copied = ref(-1)
async function copy(i: number, text: string) {
  await navigator.clipboard.writeText(text)
  copied.value = i
  setTimeout(() => (copied.value = -1), 1500)
}

defineExpose({ draft })
</script>

<template>
  <div class="grid gap-5 xl:grid-cols-[1fr_22rem]">
    <div class="space-y-5">
      <BaseCard title="Script">
        <template #actions>
          <span class="text-xs text-muted tabular-nums">
            {{ words }} words · ~{{ Math.round(words / 2.5) }}s
          </span>
        </template>
        <textarea v-model="draft" rows="14" class="field leading-relaxed" />
      </BaseCard>

      <BaseCard v-if="versions.length > 1" title="All versions">
        <ul class="-my-2 divide-y divide-line">
          <li v-for="(v, i) in versions" :key="i" class="group py-3">
            <div class="mb-1.5 flex items-center gap-3">
              <ScoreDot :score="v.score" />
              <span class="text-xs text-muted capitalize">{{ v.structure.replaceAll('_', ' ') }}</span>
              <span v-if="v.best" class="rounded bg-accent/15 px-1.5 text-[10px] text-accent">best</span>
              <div class="ml-auto flex gap-1 opacity-0 transition group-hover:opacity-100">
                <button
                  class="grid size-7 place-items-center rounded-md text-muted hover:bg-raised hover:text-fg"
                  title="Copy"
                  @click="copy(i, v.text)"
                >
                  <Check v-if="copied === i" class="size-3.5 text-good" />
                  <Copy v-else class="size-3.5" />
                </button>
                <button
                  class="grid size-7 place-items-center rounded-md text-muted hover:bg-raised hover:text-fg"
                  title="Put in the editor"
                  @click="draft = v.text"
                >
                  <ArrowUpToLine class="size-3.5" />
                </button>
              </div>
            </div>
            <p class="line-clamp-3 text-sm text-muted">{{ v.text }}</p>
          </li>
        </ul>
      </BaseCard>
    </div>

    <BaseCard v-if="review" title="Review">
      <template #actions><ScoreDot :score="review.review_average" class="text-sm" /></template>
      <ul class="space-y-2">
        <li v-for="(score, name) in review.review_scores" :key="name" class="flex justify-between text-sm">
          <span class="text-muted capitalize">{{ name }}</span>
          <ScoreDot :score="score" />
        </li>
      </ul>

      <div v-if="review.weaknesses.length" class="mt-5 space-y-3 border-t border-line pt-4">
        <div v-for="(w, i) in review.weaknesses" :key="i" class="text-xs">
          <p class="mb-1 font-medium text-warn capitalize">{{ w.criterion }}</p>
          <p class="text-muted">“{{ w.quote }}”</p>
          <p class="mt-0.5">{{ w.problem }}</p>
        </div>
      </div>
    </BaseCard>
  </div>
</template>
