<script setup lang="ts">
import { computed } from 'vue'
import { Check } from 'lucide-vue-next'
import type { Job } from '@/api'

const props = defineProps<{ stages: { name: string; gate: boolean }[]; job: Job }>()

const current = computed(() =>
  props.job.status === 'done' ? props.stages.length : props.stages.findIndex((s) => s.name === props.job.stage),
)
</script>

<template>
  <ol class="flex items-center gap-2">
    <li v-for="(s, i) in stages" :key="s.name" class="flex items-center gap-2">
      <span
        class="flex h-7 items-center gap-1.5 rounded-full px-3 text-xs capitalize"
        :class="
          i < current
            ? 'text-muted'
            : i === current
              ? job.status === 'failed'
                ? 'bg-bad/15 text-bad'
                : 'bg-accent/15 text-accent'
              : 'text-muted/50'
        "
      >
        <Check v-if="i < current" class="size-3.5 text-good" />
        {{ s.name }}
      </span>
      <span v-if="i < stages.length - 1" class="h-px w-4 bg-line" />
    </li>
  </ol>
</template>
