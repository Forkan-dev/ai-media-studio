<script setup lang="ts">
import type { JobStatus } from '@/api'

defineProps<{ status: JobStatus }>()

const styles: Record<JobStatus, { dot: string; label: string }> = {
  queued: { dot: 'bg-muted animate-pulse', label: 'Queued' },
  running: { dot: 'bg-accent animate-pulse', label: 'Working' },
  waiting: { dot: 'bg-warn', label: 'Your turn' },
  failed: { dot: 'bg-bad', label: 'Failed' },
  done: { dot: 'bg-good', label: 'Done' },
}
</script>

<template>
  <span class="inline-flex items-center gap-1.5 text-xs text-muted">
    <span class="size-1.5 rounded-full" :class="styles[status].dot" />
    {{ styles[status].label }}
  </span>
</template>
