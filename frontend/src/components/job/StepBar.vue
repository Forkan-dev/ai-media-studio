<script setup lang="ts">
/** The job's steps. Reached steps can be clicked to view their result. */
import { computed } from 'vue'
import { Check } from 'lucide-vue-next'
import type { Job } from '@/api'

const props = defineProps<{ stages: { name: string; gate: boolean }[]; job: Job; shown: string }>()
const emit = defineEmits<{ select: [stage: string] }>()

const current = computed(() =>
  props.job.status === 'done'
    ? props.stages.length
    : props.stages.findIndex((s) => s.name === props.job.stage),
)
</script>

<template>
  <ol class="flex flex-wrap items-center gap-2">
    <li v-for="(s, i) in stages" :key="s.name" class="flex items-center gap-2">
      <button
        class="flex h-7 items-center gap-1.5 rounded-full px-3 text-xs capitalize transition disabled:cursor-default"
        :disabled="i > current || (i === stages.length && job.status === 'done')"
        :class="[
          i < current
            ? 'text-muted hover:bg-surface hover:text-fg'
            : i === current
              ? job.status === 'failed'
                ? 'bg-bad/15 text-bad'
                : 'bg-accent/15 text-accent'
              : 'text-muted/50',
          s.name === shown && i < current && 'bg-surface text-fg ring-1 ring-line',
        ]"
        @click="emit('select', s.name)"
      >
        <Check v-if="i < current" class="size-3.5 text-good" />
        {{ s.name }}
      </button>
      <span v-if="i < stages.length - 1" class="h-px w-4 bg-line" />
    </li>
  </ol>
</template>
